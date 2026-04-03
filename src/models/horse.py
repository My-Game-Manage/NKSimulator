"""
horse.py の概要

馬の色々な状態について管理するクラス
"""


from dataclasses import dataclass, field
from typing import Optional

from models.params import StaticParams
from models.tactics import TacticsAI
from constants.schema import SegmentType
from constants.strategy import StrategyType

@dataclass
class HorseState:
    """馬の動的な状態を保持する"""
    current_velocity: float = 0.0
    current_position: float = 0.0  # スタートからの距離(m)
    current_stamina: float = 0.0
    
    # 状態フラグ
    is_spurt: bool = False         # スパート中か
    is_exhausted: bool = False     # バテているか
    current_lane: float = 0.0          # 現在走っているレーン
    remaining_stamina: float = 0.0
    is_drafting: bool = False
    
    # --- 計測用に追加 ---
    time_at_600m: float = 0.0  # 残り600m地点を通過した時の時刻
    last_3f_time: float = 0.0  # 算出された上がり3Fタイム
    spurt_dist: float = 0.0    # スパートを始めた位置の記録
    passing_ranks: list[int] = field(default_factory=list)  # 通過順位を格納するリスト [2, 2, 3] のようなイメージ
    distance_to_front: float = 999.0
    time_at_200m: float = 0.0  # 200m通過タイム
    velocity_at_200m: float = 0.0 # 200m地点の速度

class Horse:
    def __init__(self, horse_id: str, name: str, bracket_num: int, horse_num: int, params: StaticParams, strategy: str):
        self.horse_id = horse_id
        self.horse_name = name
        self.params = params
        self.strategy = strategy
        self.bracket_num = bracket_num
        self.horse_num = horse_num
        
        # 初期状態の設定
        self.state = None
        self.reset_state()
        
        # 意思決定エンジンの搭載
        self.tactics = TacticsAI(self)
        
    def reset_state(self):
        """レース開始時の状態にリセットする"""
        self.state = HorseState(
            current_stamina=self.params.stamina_capacity,
            current_lane=0.0 # 初期値。実際には枠順等で初期化
        )

    def update_physics(self, target_v: float, target_lane: float, dt: float, friction: float, loss_coeff: float):
        """
        Engineから与えられた目標値に基づき、物理状態（速度・位置・スタミナ）を更新する。
        """
        # 1. 加速度の計算 (Engineにあったロジックをここに集約)
        # コーナーロス等を適用した実質的な目標速度
        effective_target_v = target_v * loss_coeff
        
        v_diff = effective_target_v - self.state.current_velocity
        accel = (v_diff * self.params.base_acceleration) - friction
        
        # 2. 速度と位置の更新
        self.state.current_velocity += accel * dt
        # 速度がマイナスにならないよう制限
        self.state.current_velocity = max(0.0, self.state.current_velocity)
        
        self.state.current_position += self.state.current_velocity * dt
        
        # 3. レーンの更新（目標レーンへじわじわ近づく）
        lane_diff = target_lane - self.state.current_lane
        # レーン移動速度（定数またはパラメータ化）
        lane_change_speed = 0.5 * dt 
        if abs(lane_diff) > lane_change_speed:
            self.state.current_lane += lane_change_speed if lane_diff > 0 else -lane_change_speed
        else:
            self.state.current_lane = target_lane

    def consume_stamina(self, dt: float):
        """
        現在の速度に基づきスタミナを消費させる。
        """
        # 速度の2乗に比例して消費（既存ロジックの継承）
        consumption = (self.state.current_velocity ** 2) * 0.01 * dt
        self.state.remaining_stamina -= consumption
        
        if self.state.remaining_stamina <= 0:
            self.state.remaining_stamina = 0
            self.state.is_exhausted = True
