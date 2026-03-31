"""
engine.py の概要

レースContextと各馬のインスタンスを使い、1フレームずつ時間を進める処理を行う

現在のロジック：

1. セグメント判定 (_get_current_segment_type)
    馬の現在位置（current_position）を、コース全体のレイアウト（segments）と照合します。
    「今、自分が直線にいるのか、コーナーにいるのか」という環境情報を確定させます。
2. 加速度の算出 (_calculate_acceleration)
    目標速度の決定: 基本は馬の最高速度（max_velocity）ですが、コーナーであれば corner_radius を差し引き、スタミナ切れならデバフをかけます。
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
from models.horse import Horse
from models.context import RaceContext
from services.saver import ResultSaver

class RaceEngine:
    def __init__(self, context: RaceContext, participants: List[Horse], saver: ResultSaver, dt: float = 0.1):
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

            # 残り600m地点の通過チェック
            remaining_dist = self.context.distance - horse.state.current_position
            if remaining_dist <= 600.0 and horse.state.time_at_600m == 0.0:
                # 初めて600mを切った瞬間の経過時間を記録
                horse.state.time_at_600m = self.elapsed_time
            
            # 1. 現在のコース区間（直線 or コーナー）を特定
            segment_type = self._get_current_segment_type(horse.state.current_position)
            
            # 2. 加速度の計算（簡易モデル）
            accel = self._calculate_acceleration(horse, segment_type)
            #accel = self._calculate_acceleration_hard(horse, segment_type)
            
            # 3. 物理状態の更新（Horseクラスのメソッドを呼び出し）
            horse.update_physics(self.dt, accel)
            
            # 4. スタミナ消費
            self._consume_stamina(horse)
            #self._consume_stamina_hard(horse)

        self.elapsed_time += self.dt
        self.is_finished = all_finished

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
        # 1. 基本となる目標速度（StaticParamsから取得）
        target_v = horse.params.max_velocity
    
        # 2. スパート判定 (残り距離 600m を基準)
        remaining_dist = self.context.distance - horse.state.current_position
    
        # 馬の知能(intelligence)によってスパート開始位置を前後させる (例: 1.0なら600m)
        spurt_line = 600 * horse.params.intelligence 
    
        if remaining_dist <= spurt_line and not horse.state.is_exhausted:
            horse.state.is_spurt = True
            # スパート時は最高速度をさらに引き上げる (根性値を加味)
            target_v += (1.5 * horse.params.grit) 
        else:
            # 道中はスタミナ温存のため、最高速度の 90% 程度に抑える
            target_v *= 0.9

        # 3. コーナーペナルティの適用
        if segment_type == "curve":
            target_v -= self.context.corner_radius

        # 4. スタミナ切れ（バテ）の判定
        if horse.state.current_stamina <= 0:
            horse.state.is_exhausted = True
            horse.state.is_spurt = False
            target_v *= 0.5  # 大幅な減速
        
        # 5. 現在速度との差分から加速度を決定
        v_diff = target_v - horse.state.current_velocity
        accel = v_diff * horse.params.base_acceleration - self.context.surface_friction
    
        return accel
        
    def _calculate_acceleration_hard(self, horse, segment_type: str) -> float:
        # 1. 基本最高速度
        base_v = horse.params.max_velocity
        remaining_dist = self.context.distance - horse.state.current_position
    
        # 2. スパート判定（残り600m以下 かつ スタミナに余裕がある）
        # スタミナ残量に応じてスパートの「強さ」を変える
        if remaining_dist <= 600 and horse.state.current_stamina > 0:
            horse.state.is_spurt = True
        
            # 【調整ポイント】スタミナが余っているほど目標速度を上乗せする
            # 例: 残スタミナ / 500 を速度に加算（4000残っていれば +8m/s）
            stamina_bonus = horse.state.current_stamina / 500.0
            target_v = base_v + (horse.params.grit * 2.0) + stamina_bonus
        
        else:
            # 道中も少しペースを上げる（0.9 → 0.95）
            target_v = base_v * 0.95

        # 3. コーナー等の補正（既存ロジック）
        if segment_type == "curve":
            target_v -= self.context.corner_radius
        
        if horse.state.current_stamina <= 0:
            target_v *= 0.5  # バテ
        
        v_diff = target_v - horse.state.current_velocity
        return v_diff * horse.params.base_acceleration - self.context.surface_friction

    def _consume_stamina(self, horse):
        """
        スパート中の激しい消費をシミュレート
        """
        # 速度の2乗に比例した基本消費
        base_loss = (horse.state.current_velocity ** 2) * 0.005
    
        # スパート中は消費を 1.5倍〜2.0倍 に増やす
        multiplier = 2.0 if horse.state.is_spurt else 1.0
    
        # 最終的な消費量
        loss = base_loss * multiplier * self.dt
        horse.state.current_stamina -= loss
    
        if horse.state.current_stamina < 0:
            horse.state.current_stamina = 0
            
    def _consume_stamina_hard(self, horse):
        # 速度の2.5乗くらいにすると、高速域での消費が劇的に増えます
        speed_factor = horse.state.current_velocity ** 2.5
    
        # スパート中はさらに係数を上げる
        multiplier = 3.0 if horse.state.is_spurt else 1.0
    
        # 定数（0.01）を調整して、ゴール時にスタミナがほぼ0になるよう追い込む
        loss = speed_factor * 0.02 * multiplier * self.dt
        horse.state.current_stamina -= loss
    
        if horse.state.current_stamina < 0:
            horse.state.current_stamina = 0
        
    def run_race(self):
        """全馬がゴールするまでループ"""
        self.logger.info(f"Race Start: {self.context.distance}m")
        while not self.is_finished:
            self.step()
        self.logger.info(f"Race Finished! Time: {self.elapsed_time:.2f}s")
