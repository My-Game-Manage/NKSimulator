"""
course_master.py の概要

開催会場のコードの定義と、会場毎の特性（Spec）を定義している。
"""
from dataclasses import dataclass
from typing import Dict, Optional

@dataclass(frozen=True)
class CourseSpec:
    name: str
    is_jra: bool
    is_excluded: bool

COURSE_MASTER: Dict[str, CourseSpec] = {
    # JRA
    '01': CourseSpec('札幌', True, False),
    '02': CourseSpec('函館', True, False),
    '03': CourseSpec('福島', True, False),
    '04': CourseSpec('新潟', True, False),
    '05': CourseSpec('東京', True, False),
    '06': CourseSpec('中山', True, False),
    '07': CourseSpec('中京', True, False),
    '08': CourseSpec('京都', True, False),
    '09': CourseSpec('阪神', True, False),
    '10': CourseSpec('小倉', True, False),
    # NAR
    '30': CourseSpec('門別', False, False),
    '35': CourseSpec('盛岡', False, False),
    '36': CourseSpec('水沢', False, False),
    '42': CourseSpec('浦和', False, False),
    '43': CourseSpec('船橋', False, False),
    '44': CourseSpec('大井', False, False),
    '45': CourseSpec('川崎', False, False),
    '46': CourseSpec('金沢', False, False),
    '47': CourseSpec('笠松', False, False),
    '48': CourseSpec('名古屋', False, False),
    '50': CourseSpec('園田', False, False),
    '51': CourseSpec('姫路', False, False),
    '54': CourseSpec('高知', False, False),
    '55': CourseSpec('佐賀', False, False),
    '65': CourseSpec('帯広', False, True),
    '99': CourseSpec('不明', False, True),
}

# 地方競馬(NAR)か中央競馬(JRA)かを判定する境界
JRA_MAX_COURSE_CODE = 10

# 名称から引くための逆引き辞書を生成
# { '東京': CourseSpec(...), '佐賀': CourseSpec(...), ... }
NAME_TO_COURSE: Dict[str, CourseSpec] = {
    spec.name: spec for spec in COURSE_MASTER.values()
}