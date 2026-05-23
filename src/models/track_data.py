"""
track_data.py の概要

トラック・コースに関するデータクラスの定義
"""
from dataclasses import dataclass, replace, field
from src.constants.enums import SectionName, SectionType


@dataclass(frozen=True)
class TrackSection:
    type: SectionType
    distance: float     # その区間の長さ (m)
    start_at: float     # スタート地点からの累積距離 (m)
    name: SectionName   # "向こう正面" "第3コーナー" など
    slope: float = 0.0  # 勾配（%）。プラスなら上り坂、マイナスなら下り坂

