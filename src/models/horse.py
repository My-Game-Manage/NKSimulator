"""
horse.py の概要

馬の色々な状態について管理するクラス
"""
from dataclasses import dataclass, field

from src.models.params import StaticParams
from src.constants.strategy import StrategyType

@dataclass
class HorseState:
    current_velocity: float = 0.0
    current_position: float = 0.0  # スタートからの距離(m)
    current_stamina: float = 0.0
    
    # 状態フラグ
    is_spurt: bool = False         # スパート中か
    is_exhausted: bool = False     # バテているか
    current_lane: float = 1.0          # 現在走っているレーン
    
    # --- 計測用に追加 ---
    time_at_600m: float = 0.0  # 残り600m地点を通過した時の時刻
    last_3f_time: float = 0.0  # 算出された上がり3Fタイム
    spurt_dist: float = 0.0    # スパートを始めた位置の記録
    passing_ranks: list[int] = field(default_factory=list)  # 通過順位を格納するリスト [2, 2, 3] のようなイメージ
  
class Horse:
    def __init__(self, horse_id: str, name: str, bracket_num: int, horse_num: int, params: StaticParams, strategy: StrategyType, lane: int):
        self.horse_id = horse_id
        self.name = name
        self.bracket_num = bracket_num
        self.horse_num = horse_num
        self.params = params
        self.strategy = strategy
        self.lane = lane
        
        # 状態の初期化（レース開始時にリセット可能にする）
        self.state = None
        self.reset_state()

    def reset_state(self):
        """レース開始時の状態にリセットする"""
        self.state = HorseState(
            current_stamina=self.params.stamina_capacity,
            current_lane=float(self.lane),
        )

    def update_physics(self, dt: float, acceleration: float, effective_v: float):
        """Engineから計算された加速度を受け取り、位置と速度を更新する"""
        self.state.current_velocity += acceleration * dt
        # 速度がマイナスにならないようにガード
        self.state.current_velocity = max(0, self.state.current_velocity)
        
        # 位置の更新には effective_v を使い、速度の保持には本来の accel を使う
        #self.state.current_position += self.state.current_velocity * dt
        self.state.current_position += effective_v * dt
