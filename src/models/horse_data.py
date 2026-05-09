"""
horse_info.py の概要

馬の情報を保持し、管理するデータクラス。
"""
from dataclasses import dataclass, replace, field


@dataclass(frozen=True)
class HorseProfile:
    """馬の静的データ、能力値（固定値）を保持するデータクラス"""
    # 基本情報
    horse_id: str
    name: str
    # sex: str
    # age: int
    bracket_num: int
    horse_num: int
    jockey: str                 # ジョッキー名
    horse_weight: float         # 馬体重（未発表時は近走平均）
    weight_carried: float       # 斤量
    # 能力値
    # スピード
    base_speed: float           # 基準速度
    base_spurt_speed: float     # 基準スパート速度
    cruise_speed: float         # 巡航速度
    last_3f_speed: float        # スパート時速度
    min_speed: float            # 最低速度
    acceleration: float         # 加速力
    # スタミナ
    total_stamina: float        # 最大スタミナ
    stamina_waste_rate: float   # 消費効率
    # 適性・性格
    cornering_ability: float    # コーナー能力
    gate_reaction: float        # スタート反応
    stability_factor: float     # 安定感
    base_agility: float         # 器用さ
    lane_change_frequency: float# レーン変更頻度
    prefers_inside: float       # 内枠志向
    # 戦略
    strategy: str               # 脚質
    target_spurt_dist: float    # スパート開始距離


@dataclass(frozen=True)
class HorseSnapshot:
    """レース中に変化する動的な馬のデータ（Engineに渡し、受け取る）"""
    # 認識用
    horse_id: str
    # --- 基本物理量 ---
    step: int                   # step数
    elapsed_time: float         # 経過時間
    accel: float                # 加速度
    target_velocity: float      # 目標速度
    velocity: float             # 現在の速度
    distance: float             # 進んだ距離
    # --- 内部状態・意思決定 ---
    stamina: float              # 残りスタミナ
    # --- 環境・戦略 ---
    lane: float                 # 横位置 (ゲート幅は0.9mで実質1.0mずつズレていく）
    dist_to_front: float        # 前までの距離
    section: str                # セクション名
    # --- Stateパターン用のフィールド ---
    # デフォルトはRacingStateから開始
    behavior: str               # BehaviorStateのKeyを保存
    strategy: str               # 現在の戦術
    # --- 記録 ---
    is_finished: bool = False
    finish_time: float | None = None
    time_at_600m: float | None = None
    checkpoints_time: list[float] = field(default_factory=list)
    
    def next_step(self) -> 'HorseSnapshot':
        """ステップだけ更新した新しいStateを返す"""
        return replace(self, step=self.step + 1)

