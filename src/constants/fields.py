"""
fields.py の概要

各データクラスのフィールドのEnum
"""
from enum import Enum

# ---------------------------------------------------------
# Race data
# ---------------------------------------------------------
class SectionField(str, Enum):
    TYPE = "type"
    DISTANCE = "distance"
    START_AT = "start_at"
    NAME = "name"
    SLOPE = "slope"

class RaceRawField(str, Enum):
    RACE_ID = "race_id"
    COURSE = "course"
    RACE_NUM= "race_num"
    ENTRIES = "entries"
    HISTORIES = "histories"

class RaceProfField(str, Enum):
    # 基本情報
    RACE_ID = "race_id"
    COURSE = "course"
    RACE_NAME = "race_name"
    RACE_NUM = "race_num"
    NUM_HORSES = "num_horses"
    # 基本データ
    DISTANCE = "distance"
    SURFACE = "surface"
    CONDITION = "condition"
    WEATHER = "weather"
    # コースデータ
    TRACK_WIDTH = "track_width"
    CORNER_PENALTY = "corner_penalty"
    CORNER_RADIUS = "corner_radius"
    TURF_FRICTION = "turf_friction"
    SURFACE_FRICTION = "surface_friction"
    SECTIONS = "sections"
    # 記録用
    CHECKPOINTS = "checkpoints"
    # 馬の辞書
    HORSES = "horses"

class RaceSnapField(str, Enum):
    RACE_ID = "race_id"
    STEP = "step"
    ELAPSED_TIME = "elapsed_time"
    # 馬Stateの辞書（horse_id: h_state）
    HORSES = "horses"
    # 現在の順位辞書（horse_id: rank）
    RANKS = "ranks"

class RaceInfoField(str, Enum):
    RACE_ID = "race_id"
    PROFILE = "profile"
    SNAPSHOT = "snapshot"



# ---------------------------------------------------------
# Horse data
# ---------------------------------------------------------
class HorseProfField(str, Enum):
    # 基本情報
    HORSE_ID = "horse_id"
    NAME = "name"
    BRACKET_NUM = "bracket_num"
    HORSE_NUM = "horse_num"
    JOCKEY = "jockey"
    HORSE_WEIGHT = "horse_weight"
    WEIGHT_CARRIED = "weight_carried"
    # 能力値
    # スピード
    BASE_SPEED = "base_speed"
    BASE_SPURT_SPEED = "base_spurt_speed"
    CRUISE_SPEED = "cruise_speed"
    LAST_3F_SPEED = "last_3f_speed"
    MIN_SPEED = "min_speed"
    ACCELERATION= "acceleration"
    # スタミナ
    TOTAL_STAMINA = "total_stamina"
    STAMINA_WASTE_RATE = "stamina_waste_rate"
    # 適性・性格
    CORNER_ABILITY = "cornering_ability"
    GATE_REACTION = "gate_reaction"
    STABILITY_FACTOR = "stability_factor"
    BASE_AGILITY = "base_agility"
    LANE_CHANGE_FREQUENCY = "lane_change_frequency"
    PREFERS_INSIDE = "prefers_inside"
    # 戦略
    STRATEGY = "strategy"
    TARGET_SPURT_DIST = "target_spurt_dist"

class HorseSnapField(str, Enum):
    # 認識用
    HORSE_ID = "horse_id"
    # --- 基本物理量 ---
    STEP = "step"
    ELAPSED_TIME = "elapsed_time"
    ACCEL_POWER = "accel_power"
    ACCEL = "accel"
    TARGET_VELOCITY = "target_velocity"
    VELOCITY = "velocity"
    DISTANCE = "distance"
    # --- 内部状態・意思決定 ---
    STAMINA = "stamina"
    # --- 環境・戦略 ---
    LANE = "lane"
    DIST_TO_FRONT = "dist_to_front"
    SECTION = "section"
    # --- 記録 ---
    IS_FINISHED = "is_finished"
    FINISH_TIME = "finish_time"
    LAST_3F = "last_3f"
    TIME_AT_600M = "time_at_600m"
    LAPTIMES = "laptimes"
    CHECKPOINT_RANKS = "checkpoints_time"
    # --- Stateパターン用のフィールド ---
    # デフォルトはRacingStateから開始
    BEHAVIOR = "behavior"
    STRATEGY = "strategy"

class HorseEnvField(str, Enum):
    # 環境情報
    RACE_DISTANCE = "race_distance"
    SURFACE = "surface"
    CONDITION = "condition"
    SECTION = "section"
    DIST_TO_CONTEXT = "dist_to_context"
    DIST_TO_FRONT = "dist_to_front"
    DIST_TO_FRONT_LEFT = "dist_to_front_left"
    DIST_TO_FRONT_RIGHT = "dist_to_front_right"
    DIST_TO_SIDE_LEFT = "dist_to_side_left"
    DIST_TO_SIDE_RIGHT = "dist_to_side_right"
    RANK = "rank"
    NUM_HORSES = "num_horses"
    # 補正情報
    FRICTION = "friction"
    CORNER_PENALTY = "corner_penalty"
    CORNER_RADIUS = "corner_radius"

class HorseTacField(str, Enum):
    # 移動意思
    TARGET_LANE = "target_lane"
    ACCEL_BOOST = "accel_boost"
    OVERTAKE_DECISION = "overtake_decision"

class HorseParamField(str, Enum):
    # 速度
    TARGET_V = "target_v"
    ACCEL_P = "accel_p"
    ACCEL = "accel"
    # 更新する値
    NEXT_V = "next_v"
    NEXT_DIST = "next_dist"
    NEXT_STAMINA = "next_stamina"
    NEXT_LANE = "next_lane"

class HorseOvertake(str, Enum):
    # 追い抜き判断
    OVERTAKE = "overtake"       # 追い抜き
    SORROUNDED = "sorrounded"   # 囲まれている
    STAY = "stay"               # 現状維持
