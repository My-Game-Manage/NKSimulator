"""
engine.py の概要

レースContextと各馬のインスタンスを使い、1フレームずつ時間を進める処理を行う
"""
from utils.logger import setup_logger
from models.horse import Horse
from models.context import RaceContext
from typing import List

class RaceEngine:
    def __init__(self, context: RaceContext, participants: List[Horse], dt: float = 0.1):
        _CLASSNAME = "Engine"
        # クラス名を名前としてロガーを作成
        self.logger = setup_logger(_CLASSNAME)

        self.logger.info("初期化中...")
        
        self.context = context
        self.participants = participants
        self.dt = dt  # 1ステップあたりの秒数 (0.1秒単位)
        self.elapsed_time = 0.0
        self.is_finished = False

    def step(self):
        """1ステップ(dt秒)時間を進める"""
        if self.is_finished:
            return

        all_finished = True
        for horse in self.participants:
            # 1. ゴール済みならスキップ
            if horse.state.current_position >= self.context.distance:
                continue
            
            all_finished = False
            
            # 2. 現在のコース区間（直線 or コーナー）を特定
            segment_type = self._get_current_segment_type(horse.state.current_position)
            
            # 3. 加速度の計算（簡易モデル）
            accel = self._calculate_acceleration(horse, segment_type)
            
            # 4. 物理状態の更新（Horseクラスのメソッドを呼び出し）
            horse.update_physics(self.dt, accel)
            
            # 5. スタミナ消費
            self._consume_stamina(horse)

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
        """加速度の決定ロジック"""
        target_v = horse.params.max_velocity
        
        # コーナーなら減速ペナルティを適用
        if segment_type == "curve":
            target_v -= self.context.corner_radius
            
        # スタミナ切れなら大幅減速
        if horse.state.current_stamina <= 0:
            target_v *= 0.6
            
        # P制御に近い簡易的な加速（目標速度に近づける）
        v_diff = target_v - horse.state.current_velocity
        return v_diff * horse.params.base_acceleration - self.context.surface_friction

    def _consume_stamina(self, horse):
        """速度に応じたスタミナ消費"""
        # 速度が高いほどスタミナを激しく使う（速度の2乗に比例）
        loss = (horse.state.current_velocity ** 2) * 0.01 * self.dt
        horse.state.current_stamina -= loss

    def run_race(self):
        """全馬がゴールするまでループ"""
        self.logger.info(f"Race Start: {self.context.distance}m")
        while not self.is_finished:
            self.step()
        self.logger.info(f"Race Finished! Time: {self.elapsed_time:.2f}s")
