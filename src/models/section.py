"""
section.py の概要

コースの内訳（Section）について定義したデータクラス。
"""
from enum import Enum
from dataclasses import dataclass

class SectionName(Enum):
    IN_GATE = "in gate"                 # ゲート内
    STARTING = "starting straight"      # スタート直線
    HOMESTRETCH = "homa stretch"        # ゴール前直線
    BACKSTRETCH = "back stretch"        # 向こう正面
    TURN_1ST_2ND = "1st and 2nd turns"  # 1-2角
    TURN_3RD_4TH = "3rd and 4th turns"  # 3-4角


class SectionType(Enum):
    STRAIGHT = "直線"
    CURVE = "コーナー"

@dataclass(frozen=True)
class TrackSection:
    type: SectionType
    distance: float     # その区間の長さ (m)
    start_at: float     # スタート地点からの累積距離 (m)
    name: SectionName   # "向こう正面" "第3コーナー" など
    slope: float = 0.0  # 勾配（%）。プラスなら上り坂、マイナスなら下り坂