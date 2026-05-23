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
    SEX = "sex"
    AGE = "age"
    HORSE_WEIGHT = "horse_weight"
    WEIGHT_CARRIED = "weight_carried"
    # 能力値
    # 速度系（Speed & Acceleration）
    START_SPEED = "start_speed"
    CRUISE_SPEED = "cruise_speed"
    SPURT_SPEED = "spurt_speed"
    START_ACCELERATION= "start_acceleration"
    CRUISE_ACCELERATION= "cruise_acceleration"
    SPURT_ACCELERATION= "spurt_acceleration"
    TOP_SPEED_POTENTIAL = "top_speed_potential"
    # 体力系（Stamina & Efficiency）
    TOTAL_STAMINA = "total_stamina"
    STAMINA_WASTE_RATE = "stamina_waste_rate"
    HEAVY_TRACK_APTITUDE = "heavy_track_aptitude"
    WEIGHT_TOLERANCE = "weight_tolerance"
    DISTANCE_FLEXIBILITY = "distance_flexibility"
    # 器用系（Agility & Adaptability）
    CORNER_ABILITY = "cornering_ability"
    GATE_REACTION = "gate_reaction"
    STABILITY_FACTOR = "stability_factor"
    BASE_AGILITY = "base_agility"
    LANE_CHANGE_FREQUENCY = "lane_change_frequency"
    PREFERS_INSIDE = "prefers_inside"
    PACE_SWITCHING_AGILITY = "pace_switching_agility"
    COURSE_CORNERING_EFFICIENCY = "course_cornering_efficiency"
    # 性質系（Temperament & Strategy）
    STRATEGY = "strategy"
    PACING_STRATEGY_BIAS = "pacing_strategy_bias"
    GRIT_FACTOR = "grit_factor"
    MENTAL_STABILITY = "mental_stability"
    SPURT_TRIGGER_DISTANCE = "spurt_trigger_distance"
    SPURT_TRIGGER_TYPE = "spurt_trigger_type"

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
    TARGET_LANE = "target_lane"
    LANE = "lane"
    DIST_TO_FRONT = "dist_to_front"
    DIST_TO_FRONT_LEFT = "dist_to_front_left"
    DIST_TO_FRONT_RIGHT = "dist_to_front_right"
    DIST_TO_SIDE_LEFT = "dist_to_side_left"
    DIST_TO_SIDE_RIGHT = "dist_to_side_right"
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


class DistCtxField(str, Enum):
    DIST_TO_FRONT = "dist_to_front"
    DIST_TO_FRONT_LEFT = "dist_to_front_left"
    DIST_TO_FRONT_RIGHT = "dist_to_front_right"
    DIST_TO_SIDE_LEFT = "dist_to_side_left"
    DIST_TO_SIDE_RIGHT = "dist_to_side_right"

class HorseEnvField(str, Enum):
    # 環境情報
    RACE_DISTANCE = "race_distance"
    SURFACE = "surface"
    CONDITION = "condition"
    FRICTION = "friction"
    CORNER_RADIUS = "corner_radius"
    NUM_HORSES = "num_horses"
    RANK = "rank"
    DIST_CONTEXT = "dist_context"
    SECTION = "section"

class HorseTacField(str, Enum):
    # 速度
    TARGET_VELOCITY = "target_velocity"
    ACCEL_POWER = "accel_power"
    # 移動・意思決定
    TARGET_LANE = "target_lane"
    RACE_DECISION = "race_decision"

class HorseParamField(str, Enum):
    # 速度
    TARGET_VELOCITY = "target_velocity"
    ACCEL_POWER = "accel_power"
    ACTUAL_ACCEL = "actual_accel"
    # 更新する値
    NEXT_VELOCITY = "next_velocity"
    NEXT_DISTANCE = "next_distance"
    NEXT_STAMINA = "next_stamina"
    NEXT_LANE = "next_lane"

class RStDecisionField(str, Enum):
    # 現状維持
    KEEP_PACE = "keep_pace"
    HOLD_BACK = "hold_back"
    MOVE_POSITION = "move_position"
    # 加速・攻め
    ACCELERATE_PACE = "accelerate_pace"
    OVERTAKE = "overtake"
    SPURT = "spurt"
    # 減速・防御
    BRAKE = "brake"
    CHECK_PACE = "check_pace"
