"""
horse_info.py の概要

馬の情報を保持し、管理するデータクラス。
"""
from dataclasses import dataclass, replace, field


@dataclass(frozen=True)
class HorseProfile:
    """馬の静的データ、能力値（固定値）を保持するデータクラス"""
    # 基本情報
    horse_id: str               # (id) 識別番号
    name: str                   # (?) 馬名
    bracket_num: int            # (n) 枠番
    horse_num: int              # (n) 馬番
    jockey: str                 # (?) ジョッキー名
    sex: int                    # (Index) 0: male／1: female／2: gelding
    age: int                    # (n) 年齢
    horse_weight: float         # (kg) 馬体重（未発表時は近走平均）
    weight_carried: float       # (kg) 斤量
    # 能力値
    # 1. 速度系（Speed & Acceleration）
    start_speed: float          # (m/s) スタート時速度＞12.0 〜 14.5
    cruise_speed: float         # (m/s) 巡航速度＞15.0 〜 16.5
    spurt_speed: float          # (m/s) スパート時速度＞17.0 〜 18.5
    start_acceleration: float   # (m/s²) スタート加速力＞2.5 〜 3.5
    cruise_acceleration: float  # (m/s²) 巡航時加速力＞0.4 〜 0.6
    spurt_acceleration: float   # (m/s²) スパート時加速力＞0.8 〜 1.2
    top_speed_potential: float  # (m/s) 物理的限界上限＞18.0 〜 19.0
    # 2. 体力系（Stamina & Efficiency）
    total_stamina: float        # (pt) 最大スタミナ＞1600 〜 2400
    stamina_waste_rate: float   # (%) 消費効率＞0.95 〜 1.05
    heavy_track_aptitude: float # (%) 重・不良馬場時の消費ペナルティ＞0.90 〜 1.10
    weight_tolerance: float     # (%) 斤量1kg増減ごとのスタミナ・加速へのデバフ＞0.98 〜 1.02
    distance_flexibility: float # (%) 適性距離外に出走した際の、スタミナの減衰率＞0.85 〜 1.00
    # 3. 器用系（Agility & Adaptability）
    cornering_ability: float    # (%) カーブ時の速度維持率＞0.85 〜 0.98
    gate_reaction: float        # (sec) ゲートが開いてから start_speed に移行するまでのタイムラグ＞-0.20 〜 +0.20
    stability_factor: float     # (/frames) 安定感。巡航速度の揺らぎ＞0.01 〜 0.05
    base_agility: float         # (m/s) レーンを横に移動する際の横軸の最大移動速度＞1.0 〜 2.5
    lane_change_frequency: float# (P) 前方が詰まっていない平時に、レーンを動こうとする1秒あたりの確率＞0.05 〜 0.20
    prefers_inside: float       # (P) 1〜3枠を引いた際、通常より前目のポジション（1・2番手）を取りにいく確率＞0.10 〜 0.80
    pace_switching_agility: float       # (sec)前方のペース変化を検知してから、自身の加速・減速を開始するまでのラグ＞0.5 〜 1.5
    course_cornering_efficiency:float   # (%)特定の競馬場（右回り・左回り、大井などの大井特有の砂）への乗算補正＞0.95 〜 1.05
    # 4. 性質系（Temperament & Strategy）
    strategy: int               # (Index) 0: LEADER／1: STALKER／2: CLOSER／3: REAR　脚質
    pacing_strategy_bias: float # (ratio)「全出走頭数の前方から何％の位置をキープしたいか」（逃げなら0.05、追込なら0.90）＞0.05 〜 0.95
    grit_factor: float          # (%) 直線で他馬と横並び（例: 側対地距離0.5m以内）の時、一時的に上がる速度（またはスタミナ軽減）係数＞1.01 〜 1.04
    mental_stability: float     # (%) 馬体重の増減データから逆算。レース開始時に全能力の最大値を ±5% 程度ランダムに上下させる＞0.95 〜 1.05
    spurt_trigger_distance: float   # (m) スパート開始残り距離＞200m 〜 700m
    spurt_trigger_type: int     # (Index) 0: DISTANCE_BASED／1: LEAD_HORSE_BASED／2: PACING_UP_BASED


@dataclass(frozen=True)
class HorseSnapshot:
    """レース中に変化する動的な馬のデータ（Engineに渡し、受け取る）"""
    # 認識用
    horse_id: str
    # --- 基本物理量 ---
    step: int                   # (pt)step数
    elapsed_time: float         # (msec)経過時間
    accel_power: float          # (m/s²)加速力
    accel: float                # (m/s²)加速度（実際の加速度）
    target_velocity: float      # (m/s)目標速度
    velocity: float             # (m/s)現在の速度
    distance: float             # (m)進んだ距離
    # --- 内部状態・意思決定 ---
    stamina: float              # 残りスタミナ
    # --- 環境・戦略 ---
    target_lane: float          # (m)目標レーン
    lane: float                 # (m)横位置 (ゲート幅は0.9mで実質1.0mずつズレていく）
    dist_to_front: float        # (m)前までの距離
    dist_to_front_left: float   # (m)前左までの距離
    dist_to_front_right: float  # (m)前右までの距離
    dist_to_side_left: float    # (m)左までの距離
    dist_to_side_right: float   # (m)右までの距離
    section: int                # (Index)セクション
    # --- Stateパターン用のフィールド ---
    # デフォルトはRacingStateから開始
    behavior: int               # (Index)BehaviorStateのKeyを保存
    strategy: int               # (Index)現在の戦術
    # --- 記録 ---
    is_finished: bool = False
    finish_time: float | None = None
    last_3f: float | None = None
    time_at_600m: float | None = None                           # ゴール前600m地点のタイムを記録＝上り3F用
    laptimes: list[float] = field(default_factory=list)         # ラップタイム。1F（200m）毎のタイムを記録
    checkpoint_ranks: list[int] = field(default_factory=list)   # コーナー毎の通過順位を記録
    
    def next_step(self) -> 'HorseSnapshot':
        """ステップだけ更新した新しいStateを返す"""
        return replace(self, step=self.step + 1)

