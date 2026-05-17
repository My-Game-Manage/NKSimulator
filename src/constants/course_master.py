"""
course_master.py の概要

開催会場のコードの定義と、会場毎の特性（Spec）を定義している。
"""
from src.models.race_data import CourseSpec, TrackSection
from src.constants.enums import SectionType, SectionName


# ---------------------------------------------------------
# Course data
# ---------------------------------------------------------

DEFAULT_WIDTH = 25
DEFAULT_CORNER_PENA = 0.1
DEFAULT_RADIUS = 100
DEFAULT_SURF_FRICTION = 0.05
DEFAULT_TURF_FRICTION = 0.01

DEFAULT_COURSE_SPEC_KEY = "不明"


COURSE_MASTER: dict[str, CourseSpec] = {
    # JRA
    '01': CourseSpec('札幌', True, False, DEFAULT_WIDTH, DEFAULT_CORNER_PENA, DEFAULT_RADIUS, DEFAULT_TURF_FRICTION, DEFAULT_SURF_FRICTION),
    '02': CourseSpec('函館', True, False, DEFAULT_WIDTH, DEFAULT_CORNER_PENA, DEFAULT_RADIUS, DEFAULT_TURF_FRICTION, DEFAULT_SURF_FRICTION),
    '03': CourseSpec('福島', True, False, DEFAULT_WIDTH, DEFAULT_CORNER_PENA, DEFAULT_RADIUS, DEFAULT_TURF_FRICTION, DEFAULT_SURF_FRICTION),
    '04': CourseSpec('新潟', True, False, DEFAULT_WIDTH, DEFAULT_CORNER_PENA, DEFAULT_RADIUS, DEFAULT_TURF_FRICTION, DEFAULT_SURF_FRICTION),
    '05': CourseSpec('東京', True, False, DEFAULT_WIDTH, DEFAULT_CORNER_PENA, DEFAULT_RADIUS, DEFAULT_TURF_FRICTION, DEFAULT_SURF_FRICTION),
    '06': CourseSpec('中山', True, False, DEFAULT_WIDTH, DEFAULT_CORNER_PENA, DEFAULT_RADIUS, DEFAULT_TURF_FRICTION, DEFAULT_SURF_FRICTION),
    '07': CourseSpec('中京', True, False, DEFAULT_WIDTH, DEFAULT_CORNER_PENA, DEFAULT_RADIUS, DEFAULT_TURF_FRICTION, DEFAULT_SURF_FRICTION),
    '08': CourseSpec('京都', True, False, DEFAULT_WIDTH, DEFAULT_CORNER_PENA, DEFAULT_RADIUS, DEFAULT_TURF_FRICTION, DEFAULT_SURF_FRICTION),
    '09': CourseSpec('阪神', True, False, DEFAULT_WIDTH, DEFAULT_CORNER_PENA, DEFAULT_RADIUS, DEFAULT_TURF_FRICTION, DEFAULT_SURF_FRICTION),
    '10': CourseSpec('小倉', True, False, DEFAULT_WIDTH, DEFAULT_CORNER_PENA, DEFAULT_RADIUS, DEFAULT_TURF_FRICTION, DEFAULT_SURF_FRICTION),
    # NAR
    '30': CourseSpec('門別', False, False, DEFAULT_WIDTH, DEFAULT_CORNER_PENA, DEFAULT_RADIUS, DEFAULT_TURF_FRICTION, DEFAULT_SURF_FRICTION),
    '35': CourseSpec('盛岡', False, False, DEFAULT_WIDTH, DEFAULT_CORNER_PENA, DEFAULT_RADIUS, DEFAULT_TURF_FRICTION, DEFAULT_SURF_FRICTION),
    '36': CourseSpec('水沢', False, False, DEFAULT_WIDTH, DEFAULT_CORNER_PENA, DEFAULT_RADIUS, DEFAULT_TURF_FRICTION, DEFAULT_SURF_FRICTION),
    '42': CourseSpec('浦和', False, False, DEFAULT_WIDTH, DEFAULT_CORNER_PENA, DEFAULT_RADIUS, DEFAULT_TURF_FRICTION, DEFAULT_SURF_FRICTION),
    '43': CourseSpec('船橋', False, False, DEFAULT_WIDTH, DEFAULT_CORNER_PENA, DEFAULT_RADIUS, DEFAULT_TURF_FRICTION, DEFAULT_SURF_FRICTION),
    '44': CourseSpec('大井', False, False, 25, 0.15, 110, DEFAULT_TURF_FRICTION, 0.05),
    '45': CourseSpec('川崎', False, False, DEFAULT_WIDTH, DEFAULT_CORNER_PENA, DEFAULT_RADIUS, DEFAULT_TURF_FRICTION, DEFAULT_SURF_FRICTION),
    '46': CourseSpec('金沢', False, False, DEFAULT_WIDTH, DEFAULT_CORNER_PENA, DEFAULT_RADIUS, DEFAULT_TURF_FRICTION, DEFAULT_SURF_FRICTION),
    '47': CourseSpec('笠松', False, False, 20, 0.20, 90, DEFAULT_TURF_FRICTION, 0.07),
    '48': CourseSpec('名古屋', False, False, DEFAULT_WIDTH, DEFAULT_CORNER_PENA, DEFAULT_RADIUS, DEFAULT_TURF_FRICTION, DEFAULT_SURF_FRICTION),
    '50': CourseSpec('園田', False, False, DEFAULT_WIDTH, DEFAULT_CORNER_PENA, DEFAULT_RADIUS, DEFAULT_TURF_FRICTION, DEFAULT_SURF_FRICTION),
    '51': CourseSpec('姫路', False, False, DEFAULT_WIDTH, DEFAULT_CORNER_PENA, DEFAULT_RADIUS, DEFAULT_TURF_FRICTION, DEFAULT_SURF_FRICTION),
    '54': CourseSpec('高知', False, False, DEFAULT_WIDTH, DEFAULT_CORNER_PENA, DEFAULT_RADIUS, DEFAULT_TURF_FRICTION, DEFAULT_SURF_FRICTION),
    '55': CourseSpec('佐賀', False, False, DEFAULT_WIDTH, DEFAULT_CORNER_PENA, DEFAULT_RADIUS, DEFAULT_TURF_FRICTION, DEFAULT_SURF_FRICTION),
    '65': CourseSpec('帯広', False, True, DEFAULT_WIDTH, DEFAULT_CORNER_PENA, DEFAULT_RADIUS, DEFAULT_TURF_FRICTION, DEFAULT_SURF_FRICTION),
    '99': CourseSpec('不明', False, True, DEFAULT_WIDTH, DEFAULT_CORNER_PENA, DEFAULT_RADIUS, DEFAULT_TURF_FRICTION, DEFAULT_SURF_FRICTION),
    '00': CourseSpec('DEMO', False, True, DEFAULT_WIDTH, DEFAULT_CORNER_PENA, DEFAULT_RADIUS, DEFAULT_TURF_FRICTION, DEFAULT_SURF_FRICTION),
}

# 地方競馬(NAR)か中央競馬(JRA)かを判定する境界
JRA_MAX_COURSE_CODE = 10

# 名称から引くための逆引き辞書を生成
# { '東京': CourseSpec(...), '佐賀': CourseSpec(...), ... }
NAME_TO_COURSE: dict[str, CourseSpec] = {
    spec.name: spec for spec in COURSE_MASTER.values()
}
# 名前から会場コードを取得するために生成
NAME_TO_CODE = {v.name: k for k, v in COURSE_MASTER.items()}

# ---------------------------------------------------------
# Track data
# ---------------------------------------------------------
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
    "DEMO_1600": [
        TrackSection(SectionType.STRAIGHT, 200, 0, SectionName.STARTING),
        TrackSection(SectionType.CURVE, 300, 200, SectionName.TURN_1ST_2ND),
        TrackSection(SectionType.STRAIGHT, 400, 500, SectionName.BACKSTRETCH),
        TrackSection(SectionType.CURVE, 400, 900, SectionName.TURN_3RD_4TH),
        TrackSection(SectionType.STRAIGHT, 300, 1300, SectionName.HOMESTRETCH)
    ],
    "大井_1200": [
        # 外回りを使用。最初の直線が長く、3-4角を経て386mの直線へ。
        TrackSection(SectionType.STRAIGHT, 414, 0, SectionName.STARTING),
        TrackSection(SectionType.CURVE, 400, 414, SectionName.TURN_3RD_4TH),
        TrackSection(SectionType.STRAIGHT, 386, 814, SectionName.HOMESTRETCH)
    ],
    "大井_1400": [
        TrackSection(SectionType.STRAIGHT, 712, 0, SectionName.STARTING),
        TrackSection(SectionType.CURVE, 402, 712, SectionName.TURN_3RD_4TH),
        TrackSection(SectionType.STRAIGHT, 286, 1114, SectionName.HOMESTRETCH)
    ],
    "大井_1600": [
        # 内回りを使用。スタート後すぐに1角があるため最初の直線は短い。
        TrackSection(SectionType.STRAIGHT, 200, 0, SectionName.STARTING),
        TrackSection(SectionType.CURVE, 350, 200, SectionName.TURN_1ST_2ND),
        TrackSection(SectionType.STRAIGHT, 414, 550, SectionName.BACKSTRETCH),
        TrackSection(SectionType.CURVE, 350, 964, SectionName.TURN_3RD_4TH),
        TrackSection(SectionType.STRAIGHT, 286, 1314, SectionName.HOMESTRETCH)
    ],
    "大井_1800": [
        TrackSection(SectionType.STRAIGHT, 300, 0, SectionName.STARTING),
        TrackSection(SectionType.CURVE, 312, 300, SectionName.TURN_1ST_2ND),
        TrackSection(SectionType.STRAIGHT, 500, 612, SectionName.BACKSTRETCH),
        TrackSection(SectionType.CURVE, 402, 1112, SectionName.TURN_3RD_4TH),
        TrackSection(SectionType.STRAIGHT, 286, 1514, SectionName.HOMESTRETCH)
    ],
    "大井_2000": [
        TrackSection(SectionType.STRAIGHT, 500, 0, SectionName.STARTING),
        TrackSection(SectionType.CURVE, 312, 500, SectionName.TURN_1ST_2ND),
        TrackSection(SectionType.STRAIGHT, 500, 812, SectionName.BACKSTRETCH),
        TrackSection(SectionType.CURVE, 402, 1312, SectionName.TURN_3RD_4TH),
        TrackSection(SectionType.STRAIGHT, 286, 1714, SectionName.HOMESTRETCH)
    ],
}

