"""
track_master.py の概要

コースの各トラックについて定義した辞書。
"""
from src.models.section import TrackSection, SectionType, SectionName

DEFAULT_TRACK_DATA_KEY = "DEFAULT_1600"

# コースのセクションのリスト
# Keyは「会場名」_「距離」
# 芝の時だけsufixで_「芝」
TRACK_DATA = {
    "DEFAULT_1600": [
        TrackSection(SectionType.STRAIGHT, 200, 0, SectionName.STARTING),
        TrackSection(SectionType.CURVE, 300, 200, SectionName.TURN_1ST_2ND),
        TrackSection(SectionType.STRAIGHT, 400, 500, SectionName.BACKSTRETCH),
        TrackSection(SectionType.CURVE, 400, 900, SectionName.TURN_3RD_4TH),
        TrackSection(SectionType.STRAIGHT, 300, 1300, SectionName.HOMESTRETCH)
    ],
    "大井_1200": [
        TrackSection(SectionType.STRAIGHT, 500, 0, SectionName.STARTING),
        TrackSection(SectionType.CURVE, 400, 500, SectionName.TURN_3RD_4TH),
        TrackSection(SectionType.STRAIGHT, 300, 900, SectionName.HOMESTRETCH)
    ],
    "大井_1600": [
        TrackSection(SectionType.STRAIGHT, 200, 0, SectionName.STARTING),
        TrackSection(SectionType.CURVE, 300, 200, SectionName.TURN_1ST_2ND),
        TrackSection(SectionType.STRAIGHT, 400, 500, SectionName.BACKSTRETCH),
        TrackSection(SectionType.CURVE, 400, 900, SectionName.TURN_3RD_4TH),
        TrackSection(SectionType.STRAIGHT, 300, 1300, SectionName.HOMESTRETCH)
    ],
}

