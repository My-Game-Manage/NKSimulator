"""
constants.py の概要

各所で利用する定数を定義する。
"""
from src.constants.enums import TrackConditionType, HorseStrategyType


# ---------------------------------------------------------
# Horse - size
# ---------------------------------------------------------
HORSE_BASE_LENGTH = 3.0         # 2.8m 〜 3.0m／走行中の前肢・後肢の伸びを考慮。これより詰めすぎると、前の馬の脚に接触する挙動になります。
HORSE_BASE_SIDE_LENGTH = 0.9    # 0.8m 〜 0.9m／実際の幅（0.7m）に、ジョッキーの膝の張り出しや、左右へのわずかなフラつき分を加味。

# ---------------------------------------------------------
# Horse - Correct Time
# ---------------------------------------------------------
CONDITION_CORRECT_TIME_FACTOR = {
    '良': 0.0,
    '稍': 0.6,
    '重': 1.2,
    '不': 1.8,
}

DISTANCE_CORRECT_TIME_FACTOR = {
    800: 2.071,
    1200: 1.353,
    1600: 1.000,
    2000: 0.792,
    2400: 0.653,
    3000: 0.518,
    3600: 0.428,
}

TURF_CORRECT_TIME_FACTOR = 1.035        # 芝の1600mタイム補正用の係数
DIRT_CORRECT_TIME_FACTOR = 1.06         # ダートの1600mタイム補正用の係数


# ---------------------------------------------------------
# Horse - Cruise speed
# ---------------------------------------------------------
SPEED_DIFF_PER_100M = 0.15      # 100mあたりの速度変化係数 (分析データより)
STARTING_TIME_LOSS = 1.0        # 速度換算用の補正値。スタート時のタイムロス分

# ---------------------------------------------------------
# Horse - Start speed
# ---------------------------------------------------------
START_DIFF_PER_100M = 0.02      # 100mあたりのスタート速度変化係数※一旦スパートと同じに (分析データより 0.016〜0.02)／巡航速度(0.15)に比べて、スパート速度は距離の影響を受けにくい

# ---------------------------------------------------------
# Horse - Spurt speed
# ---------------------------------------------------------
SPURT_DIFF_PER_100M = 0.02      # 100mあたりのスパート速度変化係数 (分析データより 0.016〜0.02)／巡航速度(0.15)に比べて、スパート速度は距離の影響を受けにくい

# ---------------------------------------------------------
# Horse - Acceleration
# ---------------------------------------------------------
STARNDARD_ACCEL_POWER = 1.0     # 標準的な加速力

CRUISE_ACCELERATION_RATE = 0.5  # 巡航時の加速力の割合

# ---------------------------------------------------------
# Horse - Last 3F
# ---------------------------------------------------------
TURF_LAST_3F_BASELINE = {
    1200: 35.0,
    1400: 35.5,
    1600: 35.8,
    1800: 36.0,
    2000: 36.5,
}

DIRT_LAST_3F_BASELINE = {
    1200: 38.5,
    1400: 39.0,
    1600: 39.5,
    1800: 40.0,
    2000: 40.5,
}

# ---------------------------------------------------------
# Horse - Stability
# ---------------------------------------------------------
DEFAULT_STABILITY = 0.90
STABILITY_FACTOR_BASE = 0.96
MIN_STABILITY_FACTOR = 0.85

# ---------------------------------------------------------
# Target speed
# ---------------------------------------------------------
TARGET_V_IN_EXHAUSTED = 0.9             # バテ時の速度補正
TARGET_V_IN_CORNER_FACTOR = 0.95        # コーナリング時の補正
TARGET_V_OVERTAKE_PERCENT = 1.02        # 追い抜き時の速度補正
TARGET_V_SORROUNDED_PERCENT = 0.98      # 囲まれ時の速度補正

# ---------------------------------------------------------
# Acceleration
# ---------------------------------------------------------
ACCEL_WEIGHT_CARRIED_FACTOR = 0.005     # 50kgから1kg増える毎の補正
ACCEL_P_IN_EXHAUSTED = 0.95             # バテた時の加速補正

# ---------------------------------------------------------
# Distance
# ---------------------------------------------------------
# Dist Context に使う数値
DIST_TO_FRONT_MAX = 999.0       # 前方の初期値（999.0で前の障害物が存在しない
DIST_FRONT_RANGE = 15.0         # 前に何かある判定のレンジ
DIST_JUST_FRONT = 0.5           # 直前判定（馬の前後体長の半分に設定）
DIST_DIAGONALLY_IN_FRONT = 1.5  # 斜め前判定の幅
DIST_BESIDE_RANGE = 1.0         # 真横判定
DIST_BESIDE_RANGE_MIN = 0.1     # 真横判定（最小値）

DISTANCE_LANE_FACTOR = 0.5      # レーンによる距離補正

# ---------------------------------------------------------
# Lane
# ---------------------------------------------------------
SAME_LANE_WIDTH = 0.5       # 同一レーン判定の幅
LANE_WIDTH = 1.0            # レーン幅
BASE_LANE_MOVE_SPEED = 2.0  # レーン移動速度の基礎値
# Target Laneに使う数値
RELEVANT_DIST_AREA = 0.2            # 関係判定エリアの数値
RELEVANT_DIST_JUST_FRONT = 3.0      # 直前判定
RELEVANT_DIST_AROUND_FRONT = 8.0    # 前方に迫っている判定
RELEVANT_DIST_BESIDE = 0.8          # 真横判定

# ---------------------------------------------------------
# Corner
# ---------------------------------------------------------
RESIST_CORNER_GRAVITY = 3.0     # コーナーで耐えられるGの値
CORNER_SLOWDOWN_PERCENT = 0.98  # コーナーでの減速％

# ---------------------------------------------------------
# Stamina
# ---------------------------------------------------------
# スタミナ消費調整用の定数
STAMINA_DRAIN_COEFFICIENT = 0.075

# バテ状態判定の閾値（残り5%）
EXHAUSTED_LIMIT_PERCENT = 0.01

# ---------------------------------------------------------
# Race Time
# ---------------------------------------------------------
RACE_TIME_AVERAGE_MAP = {
    # 距離／平均タイム／走破タイム目安／備考
    800: 18.2,          # 0:43.9 - 超短距離。ほぼ加速とスパート。
    1000: 17.8,         # 0:56.2
    1200: 17.4,         # 1:08.9 - スプリント戦の基準
    1400: 17.1,         # 1:21.8
    1600: 16.8,         # 1:35.2 - マイル。ここから巡航の比重が増す
    1800: 16.5,         # 1:49.0
    2000: 16.3,         # 2:02.7 - 中距離の王道
    2200: 16.1,         # 2:16.6
    2400: 16.0,         # 2:30.0 - クラシック距離
    2600: 15.8,         # 2:44.5
    3000: 15.6,         # 3:12.3 - 長距離。スタミナ温存が顕著
    3600: 15.3,         # 3:55.2 - マラソンレース
}

TURF_TIME_ADJUST = 0.5  # 芝レースではbase_speedから早くなる
DIRT_TIME_ADJUST = -0.5 # ダートレースではbase_speedから遅くなる


# ---------------------------------------------------------
# Running Style
# ---------------------------------------------------------
START_SPEED_STYLE_FACTOR = {
    HorseStrategyType.LEADER: 1.10,
    HorseStrategyType.STALKER: 1.05,
    HorseStrategyType.CLOSER: 0.98,
    HorseStrategyType.REAR: 0.95,
}

CRUISE_SPEED_STYLE_FACTOR = {
    HorseStrategyType.LEADER: 1.01,
    HorseStrategyType.STALKER: 1.00,
    HorseStrategyType.CLOSER: 0.99,
    HorseStrategyType.REAR: 0.98,
}

SPURT_SPEED_STYLE_FACTOR = {
    HorseStrategyType.LEADER: 0.98,
    HorseStrategyType.STALKER: 0.99,
    HorseStrategyType.CLOSER: 1.00,
    HorseStrategyType.REAR: 1.05,
}

LONG_SPURT_DISTANCE_AS_STYLE = {
    HorseStrategyType.LEADER: 700,
    HorseStrategyType.STALKER: 600,
    HorseStrategyType.CLOSER: 500,
    HorseStrategyType.REAR: 450,
}

# ---------------------------------------------------------
# Condition
# ---------------------------------------------------------
# 馬場コンディションの係数
TURF_CONDITION_ACCEL_FACTOR_MAP = {
    TrackConditionType.FIRM: 1.00,
    TrackConditionType.GOOD: 0.98,
    TrackConditionType.HEAVY: 0.95,
    TrackConditionType.MUDDY: 0.92,
}

DIRT_CONDITION_ACCEL_FACTOR_MAP = {
    TrackConditionType.FIRM: 1.00,
    TrackConditionType.GOOD: 1.02,
    TrackConditionType.HEAVY: 1.04,
    TrackConditionType.MUDDY: 1.06,
}

TURF_CONDITION_STAMINA_FACTOR_MAP = {
    TrackConditionType.FIRM: 1.00,
    TrackConditionType.GOOD: 1.05,
    TrackConditionType.HEAVY: 1.15,
    TrackConditionType.MUDDY: 1.25,
}

DIRT_CONDITION_STAMINA_FACTOR_MAP = {
    TrackConditionType.FIRM: 1.00,
    TrackConditionType.GOOD: 0.98,
    TrackConditionType.HEAVY: 0.96,
    TrackConditionType.MUDDY: 0.94,
}
