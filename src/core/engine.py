"""
engine.py の概要

レースContextと各馬のインスタンスを使い、1フレームずつ時間を進める処理を行う

現在のロジック：

1. セグメント判定 (_get_current_segment_type)
    馬の現在位置（current_position）を、コース全体のレイアウト（segments）と照合します。
    「今、自分が直線にいるのか、コーナーにいるのか」という環境情報を確定させます。
2. 加速度の算出 (_calculate_acceleration)
    目標速度の決定: 基本は馬の最高速度（max_velocity）ですが、コーナーであれば corner_penalty を差し引き、スタミナ切れならデバフをかけます。
    駆動力の計算: 目標速度と現在速度の差分（v_diff）に、馬固有の加速能力（base_acceleration）を掛け合わせます。
    環境抵抗の減算: 算出された力から、馬場状態による抵抗（surface_friction）をマイナスします。
3. 物理状態の更新 (update_physics)
    速度更新: 速度 = 速度 + (加速度 * 経過時間)
    位置更新: 位置 = 位置 + (速度 * 経過時間)
    これにより、コンマ数秒後の「未来の場所」が決定します。
4. スタミナ消費 (_consume_stamina)
    速度の2乗に比例してスタミナを減らします。
    「速く走れば走るほど、指数関数的に疲れる」という競馬の基本原則を表現しています。
"""
from typing import List

from utils.logger import setup_logger
from constants.config import SimConfig
from constants.strategy import StrategyConfig, StrategyParamKey, STRATEGY_LANE_MAP
from models.horse import Horse
from models.context import RaceContext
from services.saver import ResultSaver

class RaceEngine:
    def __init__(self, context: RaceContext, participants: List[Horse], saver: ResultSaver, dt: float = SimConfig.DT):
        _CLASSNAME = "Engine"
        # クラス名を名前としてロガーを作成
        self.logger = setup_logger(_CLASSNAME)

        self.logger.info("初期化中...")
        
        self.context = context
        self.participants = participants
        self.saver = saver # Saverを受け取る
        self.dt = dt  # 1ステップあたりの秒数 (0.1秒単位)
        self.elapsed_time = 0.0
        self.is_finished = False

        self.finished_horse_ids = set() # 重複記録防止用
        
        # 通過順位を記録するチェックポイント (例: 第1、第2、第3、第4コーナー付近)
        # 1600mなら [400, 800, 1200] などの地点を設定
        self.checkpoints = [400.0, 800.0, 1200.0]
        self.reached_checkpoints = []

    def step(self):
        """1ステップ(dt秒)時間を進める"""
        if self.is_finished:
            return

        all_finished = True
        for horse in self.participants:
            # すでにゴール済みの馬はスキップ
            if horse.horse_id in self.finished_horse_ids:
                continue
            
            # ゴール判定
            if horse.state.current_position >= self.context.distance:
                self.finished_horse_ids.add(horse.horse_id)
                # Saverに記録
                self.saver.record_finish(horse, self.elapsed_time, self.context)
                continue
            
            all_finished = False
            
            # 1. 現在のコース区間（直線 or コーナー）を特定
            segment_type = self._get_current_segment_type(horse.state.current_position)

            # 2. 進路取りの更新（位置更新の前に行う）
            self._update_lane_position(horse)
            
            # 3.【ここに追加】馬の状態（スパート、バテ）を最新の位置・スタミナに基づいて更新
            self._update_horse_status(horse)
            
            # 4. 加速度の計算（簡易モデル）
            accel = self._calculate_acceleration(horse, segment_type)
            
            # 5. 物理状態の更新の箇所を以下のように調整
            effective_v = self._calculate_effective_speed(horse, segment_type, accel)
            
            # 6. 物理状態の更新（Horseクラスのメソッドを呼び出し）
            horse.update_physics(self.dt, accel, effective_v)
            
            # 7. スタミナ消費
            self._consume_stamina(horse)
            
            # 残り600m地点の通過チェック
            remaining_dist = self.context.distance - horse.state.current_position
            if remaining_dist <= 600.0 and horse.state.time_at_600m == 0.0:
                # 初めて600mを切った瞬間の経過時間を記録
                horse.state.time_at_600m = self.elapsed_time

            # チェックポイントの通過判定
            for cp in self.checkpoints:
                if cp not in self.reached_checkpoints:
                    # 全馬がその地点を越えたか、あるいは先頭が越えた瞬間の順位を取るか
                    # 一般的な通過順位は「そのコーナーを通過した順」なので、
                    # ここでは「先頭が通過した瞬間」の全馬の順位を記録する例にします
                    leader_pos = max(h.state.current_position for h in self.participants)
                
                    if leader_pos >= cp:
                        self._record_passing_ranks()
                        self.reached_checkpoints.append(cp)
                        
        # delta time
        self.elapsed_time += self.dt
        self.is_finished = all_finished

    def _record_passing_ranks(self):
        """現時点での位置に基づいて全馬の順位を確定し、Stateに保存する"""
        # 位置が遠い順（降順）に並べ替え
        sorted_horses = sorted(
            self.participants, 
            key=lambda h: h.state.current_position, 
            reverse=True
        )
        
        for i, horse in enumerate(sorted_horses):
            horse.state.passing_ranks.append(i + 1)

    def _get_current_segment_type(self, position: float) -> str:
        """現在の位置から、直線かコーナーかを判定する"""
        accumulated_dist = 0
        for seg in self.context.segments:
            accumulated_dist += seg['length']
            if position <= accumulated_dist:
                return seg['type']
        return "straight" # 予備

    def _calculate_acceleration(self, horse, segment_type: str) -> float:
        """
        スパートロジックを組み込んだ加速度計算
        """
        # その馬の脚質設定を取得
        strat_params = StrategyConfig.get(horse.strategy)
        
        # 1. 基本となる目標速度（StaticParamsから取得）
        base_v = horse.params.max_velocity

        # 目標速度の決定
        if horse.state.is_exhausted:
            # バテた時：大幅減速
            # 【修正後】脚質ごとの「粘り」係数を適用
            exhaust_coeff = strat_params[StrategyParamKey.EXHAUST_SPEED_COEFF]
            target_v = base_v * exhaust_coeff
        elif horse.state.is_spurt:
            # スパート中：最高速度
            target_v = base_v
        else:
            # 道中：脚質ごとの巡航速度
            target_v = base_v * strat_params[StrategyParamKey.CRUISING_COEFF]

        # 前が詰まっている（1.5m以内）なら強制的に速度制限
        if horse.state.distance_to_front < 1.5:
            # 前の馬にぶつからないよう、目標速度を現在の速度の90%に抑える
            target_v = min(target_v, horse.state.current_velocity * 0.9)
    
        # スタミナによるブースト（例：残量1000につき +0.5m/s）
        # これにより、1600残っている馬はさらに加速しようとします
        stamina_bonus = horse.state.current_stamina * 0.0005
        target_v += stamina_bonus

        # 3. コーナーペナルティの適用
        if segment_type == "curve":
            target_v -= self.context.corner_penalty

        # 4. スタミナ切れ（バテ）の判定
        if horse.state.current_stamina <= 0:
            horse.state.is_exhausted = True
            horse.state.is_spurt = False
            target_v *= SimConfig.EXHAUSTED_SPEED_COEFF  # 大幅な減速
        
        # 5. 現在速度との差分から加速度を決定
        v_diff = target_v - horse.state.current_velocity
        accel = v_diff * horse.params.base_acceleration - self.context.surface_friction
    
        return accel
        
    def _consume_stamina(self, horse):
        """
        スパート中の激しい消費をシミュレート
        """
        # 速度の2乗に比例した基本消費
        #base_loss = (horse.state.current_velocity ** 2) * 0.005
        # 速度の2乗に戻す（安定性のため）
        speed_factor = horse.state.current_velocity ** SimConfig.CONSUMPTION_RATE
        
        # スパート中は消費を 1.5倍〜2.0倍 に増やす->1.5倍 程度に抑える
        multiplier = SimConfig.SPART_MULTIPLIER if horse.state.is_spurt else SimConfig.NORMAL_SPART_MULTIPLIER

        # 【追加】距離による消費係数の補正 (1600mを基準=1.0とする)
        # 1200mなら 1200/1600 = 0.75倍 に消費を抑える
        # これにより、同じ速度で走っても短距離の方がスタミナが持ちます
        dist_adjustment = self.context.distance / 1600.0
    
        #loss = speed_factor * SimConfig.STAMINA_LOSS_COEFF * dist_adjustment * self.dt
        loss = speed_factor * SimConfig.STAMINA_LOSS_COEFF * dist_adjustment * multiplier * self.dt
        horse.state.current_stamina -= loss
        
        # 最終的な消費量
        # 係数を 0.008 前後に調整（1600m走るのに適した消費量）
        #loss = speed_factor * SimConfig.STAMINA_LOSS_COEFF * multiplier * self.dt
        #horse.state.current_stamina -= loss
    
        if horse.state.current_stamina < 0:
            horse.state.current_stamina = 0

    def _update_horse_status(self, horse):
        """馬の状態（スパート、バテ）を更新する"""
        # 1. バテ判定（既存ロジックに近いもの）
        if horse.state.current_stamina <= 0:
            horse.state.is_exhausted = True
            horse.state.is_spurt = False # バテたらスパート終了
            return

        # 2. スパート開始判定
        if not horse.state.is_spurt:
            strat_params = StrategyConfig.get(horse.strategy)
            remaining_dist = self.context.distance - horse.state.current_position
        
            # 残り距離が脚質ごとのスパート開始距離に入ったらスイッチON
            if remaining_dist <= strat_params[StrategyParamKey.SPURT_DIST]:
                horse.state.is_spurt = True
                horse.state.spurt_dist = remaining_dist
                self.logger.info(f"{horse.name} がスパート開始！ 残り: {remaining_dist:.1f}m")

    def _update_lane_position(self, horse):
        """
        馬番に応じた初期位置から、脚質ごとの理想レーンへ徐々に移動させる
        """
        # 前方の馬との距離を取得
        dist_to_front = self._get_distance_to_front_horse(horse)
        # 保存用
        horse.state.distance_to_front = dist_to_front

        # 基本の目標レーン
        ideal_lane = STRATEGY_LANE_MAP.get(horse.strategy, 1)

        # もし前との距離が 3m 以内なら「壁」とみなす
        current_lane = horse.state.current_lane
        if dist_to_front < 3.0:
            # 外側（レーン番号が増える方向）に回避を試みる
            target_lane = current_lane + 1.0
            # コース幅（track_width）を超えないように制限
            target_lane = min(target_lane, 15.0) 
        else:
            # 前が空いていれば、理想のレーンに戻ろうとする
            target_lane = ideal_lane
            
        # 2. 移動速度の設定
        # 1秒間に最大 0.5 レーン分移動すると仮定 (急激な横移動を防ぐ)
        lane_change_speed = 0.5 
    
        # 3. 目標レーンとの差分を計算
        lane_diff = target_lane - current_lane
    
        if abs(lane_diff) > 0.01:
            # 1フレームあたりの移動量を計算
            move_amount = lane_change_speed * self.dt
        
            # 目標に近づける
            if lane_diff > 0:
                horse.state.current_lane = min(current_lane + move_amount, target_lane)
            else:
                horse.state.current_lane = max(current_lane - move_amount, target_lane)
                
    def _calculate_effective_speed(self, horse, segment_type, actual_accel):
        """
        レーン（内外）によるコーナーでの距離ロスを計算する
        """
        velocity = horse.state.current_velocity
    
        if segment_type == "curve":
            # 大井のコーナー半径を約80mと仮定
            # レーン幅を1.5mとすると、1レーン外にいくごとに距離は約2%弱伸びる
            # 簡易計算式: 補正係数 = (半径) / (半径 + レーン位置)
            radius = 80.0
            lane_width = 1.5
        
            # 外側にいればいるほど、1フレームで進める「コース上の距離」が短くなる
            # lane 0 = 1.0 / lane 3 = 0.946... (約5%のロス)
            loss_coeff = radius / (radius + (horse.lane * lane_width))
            return velocity * loss_coeff
    
        return velocity

    def _get_distance_to_front_horse(self, horse: Horse) -> float:
        """
        同一レーン上の最も近い前方馬との距離を返す。いない場合は十分な距離(999m)を返す。
        """
        min_dist = 999.0
        for other in self.participants:
            if horse.horse_id == other.horse_id:
                continue
        
            # 同じレーン（幅0.8程度の範囲）にいるか判定
            if abs(horse.state.current_lane - other.state.current_lane) < 0.8:
                dist = other.state.current_position - horse.state.current_position
                if 0 < dist < min_dist:
                    min_dist = dist
        return min_dist
        
    def run_race(self):
        """全馬がゴールするまでループ"""
        self.logger.info(f"Race Start: {self.context.distance}m")
        while not self.is_finished:
            self.step()
        self.logger.info(f"Race Finished! Time: {self.elapsed_time:.2f}s")
