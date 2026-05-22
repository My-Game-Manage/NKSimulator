"""
enums.py の概要

各Enumクラスを定義する
"""
from enum import Enum


# ---------------------------------------------------------
# Track data
# ---------------------------------------------------------
class SectionType(int, Enum):
    STRAIGHT = 0        # straight
    CURVE = 1           # corner

    def to_str(self) -> str:
        _STRS = {
            0: "straight",
            1: "curve",
        }
        return _STRS[self.value]
    
    @staticmethod
    def from_str(val: str) -> 'SectionType':
        _VALS = {
            "straight": 0,
            "curve": 1,
            "直線": 0,
            "カーブ": 1,
        }
        return SectionType(_VALS[val])


class SectionName(int, Enum):
    IN_GATE = 0 #"in gate"                 # ゲート内
    STARTING = 1 #"starting straight"      # スタート直線
    HOMESTRETCH = 2 #"home stretch"        # ゴール前直線
    BACKSTRETCH = 3 #"back stretch"        # 向こう正面
    TURN_1ST_2ND = 4 #"1st and 2nd turns"  # 1-2角
    TURN_3RD_4TH = 5 #"3rd and 4th turns"  # 3-4角
    HOME_STRAIGHT = 99 #"home straight"     # ホームストレート（デフォルト）

    def to_str(self) -> str:
        _STRS = {
            0: "in gate",
            1: "starting straight",
            2: "home stretch",
            3: "back stretch",
            4: "1st and 2nd turns",
            5: "3rd and 4th turns",
            99: "home straight", 
        }
        return _STRS[self.value]

    @staticmethod
    def from_str(val: str) -> 'SectionName':
        _VALS = {
            "in gate": 0,
            "starting straight": 1,
            "home stretch": 2,
            "back stretch": 3,
            "1st and 2nd turns": 4,
            "3rd and 4th turns": 5,
            "home straight": 99,
        }
        return SectionName(_VALS[val])


# ---------------------------------------------------------
# Race data
# ---------------------------------------------------------
class RaceSurfaceType(int, Enum):
    TURF = 0 #"turf"           # 芝
    DIRT = 1 #"dirt"           # ダート
    JUMP = 2 #"jump"           # 障害
    DRAFT = 3 #"draft"         # ばんえい

    def to_str(self) -> str:
        _STRS = {
            0: "turf",
            1: "dirt",
            2: "jump",
            3: "draft",
        }
        return _STRS[self.value]
    
    @staticmethod
    def from_str(val: str) -> 'RaceSurfaceType':
        _VALS = {
            "turf": 0,
            "dirt": 1,
            "jump": 2,
            "draft": 3,
            "芝": 0,
            "ダ": 1,
            "ダート": 1,
            "障": 2,
            "障害": 2,
            "ば": 3,
            "ばんえい": 3,
        }
        return RaceSurfaceType(_VALS[val])


class TrackConditionType(int, Enum):
    FIRM = 0 #"firm"           # 良
    GOOD = 1 #"good"           # 稍良
    HEAVY = 2 #"heavy"         # 重
    MUDDY = 3 #"muddy"         # 不良
    UNKNOWN = 99 #"unknown"     # 未定

    def to_str(self) -> str:
        _STRS = {
            0: "firm",
            1: "good",
            2: "heavy",
            3: "muddy",
            99: "unknown",
        }
        return _STRS[self.value]
    
    @staticmethod
    def from_str(val: str) -> 'TrackConditionType':
        _VALS = {
            "firm": 0,
            "good": 1,
            "heavy": 2,
            "muddy": 3,
            "unknown": 99,
            "良": 0,
            "稍": 1,
            "稍重": 1,
            "重": 2,
            "不": 3,
            "不良": 3,
            "": 99,
            " ": 99,
            "　": 99,
        }
        return TrackConditionType(_VALS[val])


class TrackWeatherType(int, Enum):
    SKY = 0 #"sky"             # 晴れ
    CLOUDY = 1 #"cloudy"       # 曇り
    RAINY = 2 #"rainy"         # 雨
    SNOW = 3 #"snow"           # 雪
    UNKNOWN = 99 #"unknown"     # 未定

    def to_str(self) -> str:
        _STRS = {
            0: "sky",
            1: "cloudy",
            2: "rainy",
            3: "snow",
            99: "unknown",
        }
        return _STRS[self.value]
    
    @staticmethod
    def from_str(val: str) -> 'TrackWeatherType':
        _VALS = {
            "sky": 0,
            "cloudy": 1,
            "rainy": 2,
            "snow": 3,
            "unknown": 99,
            "晴": 0,
            "晴れ": 0,
            "曇": 1,
            "曇り": 1,
            "雨": 2,
            "雪": 3,
            "": 99,
            " ": 99,
            "　": 99,
        }
        return TrackConditionType(_VALS[val])


# ---------------------------------------------------------
# Horse data
# ---------------------------------------------------------
class HorseStrategyType(int, Enum):
    LEADER = 0 #"leader"       # 逃げ
    STALKER = 1 #"stalker"     # 先行
    CLOSER = 2 #"closer"       # 差し
    REAR = 3 #"rear"           # 追い込み

    def to_str(self) -> str:
        _STRS = {
            0: "leader",
            1: "stalker",
            2: "closer",
            3: "rear",
        }
        return _STRS[self.value]
    
    @staticmethod
    def from_str(val: str) -> 'HorseStrategyType':
        _VALS = {
            "leader": 0,
            "stalker": 1,
            "closer": 2,
            "rear": 3,
            "逃": 0,
            "逃げ": 0,
            "先": 1,
            "先行": 1,
            "差": 2,
            "差し": 2,
            "追": 3,
            "追い込み": 3,
        }
        return HorseStrategyType(_VALS[val])


class HorseBehaviorType(int, Enum):
    IN_GATE = 0 #"in gate"     # スタート前
    STARTING = 1 #"starting"   # スタートフェーズ
    RACING = 2 #"racing"       # レース中（通常時）
    BLOCKED = 3 #"blocked"     # レース中（詰まっている）
    SPURTING = 4 #"spurting"   # レース中（スパートフェーズ）
    EXHAUSTED = 5 #"exhausted" # レース中（バテている）
    FINISHED = 99 #"finished"   # ゴール後

    def to_str(self) -> str:
        _STRS = {
            0: "in gate",
            1: "starting",
            2: "racing",
            3: "blocked",
            4: "spurting",
            5: "exhausted",
            99: "finished",
        }
        return _STRS[self.value]
    
    @staticmethod
    def from_str(val: str) -> 'HorseBehaviorType':
        _VALS = {
            "in gate": 0,
            "starting": 1,
            "racing": 2,
            "blocked": 3,
            "spurting": 4,
            "exhausted": 5,
            "finished": 99,
        }
        return HorseBehaviorType(_VALS[val])


class SpurtTriggerType(int, Enum):
    DISTANCE_BASED = 0
    LEAD_HORSE_BASED = 1
    PACING_UP_BASED = 2

    def to_str(self) -> str:
        _STRS = {
            0: "distance_based",
            1: "lead_horse_based",
            2: "pacing_up_based",
        }
        return _STRS[self.value]


# ---------------------------------------------------------
# Event data
# ---------------------------------------------------------
class RaceEvent(str, Enum):
    PREPARE = "prepare"     # 準備
    START = "start"         # レース開始
    GOAL = "goal"           # ゴール
    FINISH = "finish"       # レース終了
    SAVE = "save"           # Save
