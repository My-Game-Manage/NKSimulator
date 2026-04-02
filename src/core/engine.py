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
from constants.strategy import StrategyConfig, StrategyParamKey, STRATEGY_LANE_MAP, StrategyType
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

            # 200m通過時の記録
            if horse.state.time_at_200m == 0.0 and horse.state.current_position >= 200.0:
                horse.state.time_at_200m = self.elapsed_time
                horse.state.velocity_at_200m = horse.state.current_velocity
                
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
        
    def _calculate_acceleration(self, horse, segment_type):
        """
        加速度の算出：目標速度の決定と、前方馬との同期・回避・ブレーキを統合
        """
        strat_params = StrategyConfig.get(horse.strategy)
    
        # 1. 基本となる目標速度 (target_v) の決定
        # スタートダッシュ(300m以内)
        if horse.state.current_position < 300.0:
            if horse.strategy in [StrategyType.LEAD, StrategyType.FRONT]:
                target_v = horse.params.max_velocity * 1.05
            else:
                target_v = horse.params.max_velocity * 1.00
        # バテ
        elif horse.state.is_exhausted:
            target_v = horse.params.max_velocity * strat_params[StrategyParamKey.EXHAUST_SPEED_COEFF]
        # スパート
        elif horse.state.is_spurt:
            target_v = horse.params.max_velocity
        # 巡航
        else:
            target_v = horse.params.max_velocity * strat_params[StrategyParamKey.CRUISING_COEFF]

        # 2. 縦方向の隊列制御（同期・ブレーキの一本化）
        dist = horse.state.distance_to_front
    
        # スタート直後（100m以内）は密集するため、極端なブレーキを無効化して縦に伸ばす
        if horse.state.current_position > 100.0:
            if dist < 5.0:
                front_horse = self._get_front_horse_object(horse)
                if front_horse:
                    front_v = front_horse.state.current_velocity
                
                    if dist < 1.5:
                        # 【ブレーキ】前の馬の速度を基準に、少しだけ減速して車間を保つ
                        # 自分の現在速度ではなく、相手の速度(front_v)を基準にするのがポイント
                        target_v = min(target_v, front_v * 0.98)
                    else:
                        # 【同期】1.5m〜5.0mの間は、前の馬の速度 +α で追走（隊列形成）
                        # わずかに速く設定することで、隙があれば抜こうとする圧を表現
                        target_v = min(target_v, front_v + 0.1)

        # 3. 加速度の計算
        # 目標速度と現在速度の差分から駆動力を算出
        v_diff = target_v - horse.state.current_velocity
        accel = v_diff * horse.params.base_acceleration
    
        # 環境抵抗（馬場状態など）を減算
        actual_accel = accel - self.context.surface_friction
    
        # 急激な減速・加速の制限（物理的な限界）
        # 必要に応じて上限・下限を設けるとより安定します
    
        return actual_accel

    def _calculate_acceleration_old(self, horse, segment_type: str) -> float:
        """
        スパートロジックを組み込んだ加速度計算
        """
        # その馬の脚質設定を取得
        strat_params = StrategyConfig.get(horse.strategy)
        
        # 1. 基本となる目標速度（StaticParamsから取得）
        base_v = horse.params.max_velocity

        # 目標速度の決定
        # --- テンの攻防ロジックを追加 ---
        if horse.state.current_position < 300.0:
            # スタートから300m（向こう正面の半ば）までは、脚質に関わらず位置を取りに行く
            # 逃げ・先行なら最高速度の 105%、差し・追込でも 100% を出すイメージ
            if horse.strategy in [StrategyType.LEAD, StrategyType.FRONT]:
                target_v = horse.params.max_velocity * 1.05
            else:
                target_v = horse.params.max_velocity * 1.00
        elif horse.state.is_exhausted:
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

        # --- 追走・同期ロジックの追加 ---
        dist = horse.state.distance_to_front
        if dist < 5.0:  # 5m以内に馬がいる場合
            front_horse = self._get_front_horse_object(horse)
            if front_horse:
                front_v = front_horse.state.current_velocity
            
                if dist < 1.5:
                    # 【ブレーキ】近すぎる場合は、前の馬より少し遅い速度を目標にする
                    target_v = min(target_v, front_v * 0.95)
                elif 1.5 <= dist < 4.0:
                    # 【追走同期】適切な車間距離なら、前の馬と同じペースで走る
                    # わずかに (+0.1) 速く設定することで、隙があれば抜こうとする圧を表現
                    target_v = min(target_v, front_v + 0.1)
                
                    # ※ここでスタミナ消費軽減フラグを立てるのも有効です
                    horse.state.is_drafting = True
    
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
        進路取りの動態化：馬番単位（0-15）のスケールに合わせる
        """
        # 前方の馬との距離を取得
        dist = self._get_distance_to_front_horse(horse)
        # 保存用
        horse.state.distance_to_front = dist

        # 基本の目標レーン
        ideal_lane = STRATEGY_LANE_MAP.get(horse.strategy, 1)
        
        # 1. 基本は理想のレーンを目指す
        target_lane = ideal_lane
    
        # 2. 壁判定のロジック
        if dist < 4.0: # 4m以内を検知対象にする
            front_horse = self._get_front_horse_object(horse)
            if front_horse:
                # 自分の本来出したい速度（target_v）と前の馬の速度を比較
                # ※ここで使う ideal_v は、同期ロジック適用前の「素」の目標速度
                ideal_v = self._calculate_base_target_velocity(horse) 
            
                # 【重要】自分の方が 0.2m/s 以上速いポテンシャルがあるなら「壁」
                if ideal_v > (front_horse.state.current_velocity + 0.2):
                    # 外に持ち出して追い抜きを試みる
                    target_lane = horse.state.current_lane + 1.2
                else:
                    # 前の馬の方が速い、あるいは同等なら「壁」ではない。
                    # そのまま後ろについてスリップストリーム（同期）を狙う
                    target_lane = horse.state.current_lane
        # 3. 復帰ロジック
        elif horse.state.current_lane > ideal_lane:
            # 前に馬がいない（dist > 5.0など）なら、理想のレーン（内側）へ戻る
            target_lane = ideal_lane    

        # 境界チェック
        target_lane = max(0.0, min(target_lane, 15.0))
        # とりあずレーン間の移動速度を上げる＞2.5
        lane_change_speed = 2.5

        # 3. 移動処理、目標レーンとの差分を計算
        lane_diff = target_lane - horse.state.current_lane
        if abs(lane_diff) > 0.01:
            # 1フレームあたりの移動量を計算
            move_amount = lane_change_speed * self.dt
            if lane_diff > 0:
                horse.state.current_lane = min(horse.state.current_lane + move_amount, target_lane)
            else:
                horse.state.current_lane = max(horse.state.current_lane - move_amount, target_lane)

    def _calculate_effective_speed(self, horse, segment_type, actual_accel):
        """
        コーナーでの距離ロス計算のスケール修正
        """
        velocity = horse.state.current_velocity
        if segment_type == "curve":
            radius = 80.0
            # 16レーンに分かれたため、1レーンあたりの実質的な「幅」を小さく見積もる
            # (枠単位の1.5mを、馬番単位の 0.6m〜0.8m 程度に修正)
            effective_lane_width = 0.7 
        
            loss_coeff = radius / (radius + (horse.state.current_lane * effective_lane_width))
            return velocity * loss_coeff
        return velocity
        
    def _get_distance_to_front_horse(self, horse: Horse) -> float:
        """
        同一レーン上の最も近い前方馬との距離を返す。いない場合は十分な距離(999m)を返す。
        同一レーン判定の閾値を調整
        """
        min_dist = 999.0
        for other in self.participants:
            if horse.horse_id == other.horse_id: continue
            # 16レーンあるため、幅 0.5 程度を「同じ進路」とみなす
            if abs(horse.state.current_lane - other.state.current_lane) < 0.5:
                dist = other.state.current_position - horse.state.current_position
                if 0 < dist < min_dist:
                    min_dist = dist
        return min_dist

    def _get_front_horse_object(self, horse: Horse):
        """同一レーン上で最も近い前方の馬オブジェクトを返す"""
        min_dist = 999.0
        front_horse = None
        for other in self.participants:
            if horse.horse_id == other.horse_id: continue
            # 同一レーン判定（幅0.5）
            if abs(horse.state.current_lane - other.state.current_lane) < 0.5:
                dist = other.state.current_position - horse.state.current_position
                if 0 < dist < min_dist:
                    min_dist = dist
                    front_horse = other
        return front_horse

    def _calculate_base_target_velocity(self, horse):
        """同期ロジックを適用する前の、脚質・区間・スタミナに基づく目標速度"""
        strat_params = StrategyConfig.get(horse.strategy)
        if horse.state.current_position < 300.0:
            return horse.params.max_velocity * (1.05 if horse.strategy in [StrategyType.LEAD, StrategyType.FRONT] else 1.0)
        if horse.state.is_exhausted:
            return horse.params.max_velocity * strat_params[StrategyParamKey.EXHAUST_SPEED_COEFF]
        if horse.state.is_spurt:
            return horse.params.max_velocity
        return horse.params.max_velocity * strat_params[StrategyParamKey.CRUISING_COEFF]
        
    def run_race(self):
        """全馬がゴールするまでループ"""
        self.logger.info(f"Race Start: {self.context.distance}m")
        while not self.is_finished:
            self.step()
        self.logger.info(f"Race Finished! Time: {self.elapsed_time:.2f}s")
