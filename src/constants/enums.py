"""
enums.py の概要

各Enumクラスを定義する
"""
from enum import Enum


# ---------------------------------------------------------
# Track data
# ---------------------------------------------------------
class SectionType(str, Enum):
    STRAIGHT = "straight"
    CURVE = "corner"

class SectionName(Enum):
    IN_GATE = "in gate"                 # ゲート内
    STARTING = "starting straight"      # スタート直線
    HOMESTRETCH = "home stretch"        # ゴール前直線
    BACKSTRETCH = "back stretch"        # 向こう正面
    TURN_1ST_2ND = "1st and 2nd turns"  # 1-2角
    TURN_3RD_4TH = "3rd and 4th turns"  # 3-4角
    HOME_STRAIGHT = "home straight"     # ホームストレート（デフォルト）

# ---------------------------------------------------------
# Race data
# ---------------------------------------------------------
class RaceSurfaceType(str, Enum):
    TURF = "turf"           # 芝
    DIRT = "dirt"           # ダート
    JUMP = "jump"           # 障害
    DRAFT = "draft"         # ばんえい

class TrackConditionType(Enum):
    STANDARD = "standard"   # 良
    GOOD = "good"           # 稍良
    MUDDY = "muddy"         # 重
    HEAVY = "heavy"         # 不良

class TrackWeatherType(Enum):
    SKY = "sky"             # 晴れ
    CLOUDY = "cloudy"       # 曇り
    RAINY = "rainy"         # 雨
    SNOW = "snow"           # 雪

# ---------------------------------------------------------
# Horse data
# ---------------------------------------------------------
class HorseStrategyType(str, Enum):
    LEADER = "leader"       # 逃げ
    STALKER = "stalker"     # 先行
    CLOSER = "closer"       # 差し
    REAR = "rear"           # 追い込み

class HorseBehaviorType(str, Enum):
    IN_GATE = "in gate"     # スタート前
    STARTING = "starting"   # スタートフェーズ
    RACING = "racing"       # レース中（通常時）
    BLOCKED = "blocked"     # レース中（詰まっている）
    EXHAUSTED = "exhausted" # レース中（バテている）
    FINISHED = "finished"   # ゴール後

# ---------------------------------------------------------
# Event data
# ---------------------------------------------------------
class RaceEvent(str, Enum):
    PREPARE = "prepare"     # 準備
    START = "start"         # レース開始
    GOAL = "goal"           # ゴール
    FINISH = "finish"       # レース終了
    SAVE = "save"           # Save
