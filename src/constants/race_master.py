"""
race_master.py の概要

レースに関する定数の定義を行う。
"""

from enum import Enum

class TrackCondition(Enum):
    """競馬の馬場状態を定義するEnum"""
    GOOD = "良"
    YIELDING = "稍"
    SOFT = "重"
    BAD = "不"
    ANY = "未"

    @classmethod
    def from_str(cls, text: str):
        """文字列からEnumを取得するヘルパーメソッド（CSV読み込み時などに便利）"""
        for condition in cls:
            if condition.value == text:
                return condition
        # 不明、あるいは空欄の場合はANYを返す
        return cls.ANY
        # raise ValueError(f"不明な馬場状態です: {text}")

class TrackWeather(Enum):
    """競馬の天候を定義するEnum"""
    SUNNY = "晴"
    CLOUDY = "曇"
    RAIN = "雨"
    SNOW = "雪"
    ANY = "未"

    @classmethod
    def from_str(cls, text: str):
        """文字列からEnumを取得するヘルパーメソッド（CSV読み込み時などに便利）"""
        for condition in cls:
            if condition.value == text:
                return condition
        # 不明、あるいは空欄の場合はANYを返す
        return cls.ANY
        #raise ValueError(f"不明な馬場状態です: {text}")
