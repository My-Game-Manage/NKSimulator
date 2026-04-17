"""
fields.py の概要

各データクラスのフィールドのEnum
"""
from enum import Enum

# ---------------------------------------------------------
# Race data
# ---------------------------------------------------------
class SectionField(Enum):
    TYPE = "type"
    DISTANCE = "distance"
    START_AT = "start_at"
    NAME = "name"
    SLOPE = "slope"

class RaceRawField(Enum):
    RACE_ID = "race_id"
    COURSE = "course"
    RACE_NUM= "race_num"
    ENTRIES = "entries"
    HISTORIES = "histories"

class RaceProfField(Enum):
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
    TURF_FRICTION = "turf_friction"
    SURFACE_FRICTION = "surface_friction"
    SECTIONS = "sections"
    # 記録用
    CHECKPOINTS = "checkpoints"
    # 馬の辞書
    HORSES = "horses"

class RaceSnapField(Enum):
    RACE_ID = "race_id"
    STEP = "step"
    ELAPSED_TIME = "elapsed_time"
    # 馬Stateの辞書（horse_id: h_state）
    HORSES = "horses"
    # 現在の順位辞書（horse_id: rank）
    RANKS = "ranks"

class RaceInfoField(Enum):
    RACE_ID = "race_id"
    PROFILE = "profile"
    SNAPSHOT = "snapshot"



# ---------------------------------------------------------
# Horse data
# ---------------------------------------------------------
class HorseProfField(Enum):
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
    MAX_SPEED = "max_speed"
    MIN_SPEED = "min_speed"
    ACCELERATION= "acceleration"
    # スタミナ
    TOTAL_STAMIN = "total_stamina"
    STAMINA_WASTE_RATE = "stamina_waste_rate"
    # 適性・性格
    CORNER_ABILITY = "cornering_ability"
    GATE_REACTION = "gate_reaction"
    # 戦略
    STRATEGY = "strategy"
    TARGET_SPURT_DIST = "target_spurt_dist"

class HorseSnapField(Enum):
    # 認識用
    HORSE_ID = "horse_id"
    # --- 基本物理量 ---
    STEP = "step"
    ELAPSED_TIME = "elapsed_time"
    VELOCITY = "velocity"
    DISTANCE = "distance"
    # --- 内部状態・意思決定 ---
    STAMINA = "stamina"
    # --- 環境・戦略 ---
    LANE = "lane"
    # --- 記録 ---
    IS_FINISHED = "is_finished"
    FINISH_TIME = "finish_time"
    # --- Stateパターン用のフィールド ---
    # デフォルトはRacingStateから開始
    BEHAVIOR = "behavior"
    STRATEGY = "strategy"
