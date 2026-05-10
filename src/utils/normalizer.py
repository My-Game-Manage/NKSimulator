"""
normalizer.py の概要

正常化、正規化のための簡単なヘルパー関数群。
"""
import pandas as pd

from src.constants.schema import RaceCol
from src.constants.enums import TrackConditionType, TrackWeatherType, RaceSurfaceType


SURFACE_MAP = {
    "芝": RaceSurfaceType.TURF,
    "ダ": RaceSurfaceType.DIRT,
    "ダート": RaceSurfaceType.DIRT,
    "障": RaceSurfaceType.JUMP,
    "障害": RaceSurfaceType.JUMP,
    "ば": RaceSurfaceType.DRAFT,
    "ばんえい": RaceSurfaceType.DRAFT,
    "": RaceSurfaceType.UNKNOWN,
}

CONDITION_MAP = {
    "良": TrackConditionType.STANDARD,
    "稍": TrackConditionType.GOOD,
    "稍重": TrackConditionType.GOOD,
    "重": TrackConditionType.MUDDY,
    "不": TrackConditionType.HEAVY,
    "不良": TrackConditionType.HEAVY,
    "": TrackConditionType.UNKNOWN,
}

WEATHER_MAP = {
    "晴": TrackWeatherType.SKY,
    "晴れ": TrackWeatherType.SKY,
    "曇": TrackWeatherType.CLOUDY,
    "曇り": TrackWeatherType.CLOUDY,
    "雨": TrackWeatherType.RAINY,
    "雪": TrackWeatherType.SNOW,
    "": TrackWeatherType.UNKNOWN,
}


def valid_race_shutuba_df(df: pd.DataFrame) -> pd.DataFrame:
    """出馬表DFを正規化（レース番号）"""
    # レース番号を数値型に変換
    df[RaceCol.RACE_NUMBER] = df[RaceCol.RACE_NUMBER].astype(int)
    return df

def valid_horse_history_df(df: pd.DataFrame) -> pd.DataFrame:
    """0や空欄を除去したDataFrame"""
    valid_df = df[(df[RaceCol.TIME] > 0) & (df[RaceCol.LAST_3F] > 0)].dropna(subset=[RaceCol.TIME, RaceCol.LAST_3F])
    return valid_df

def valid_surface_str(surface: str) -> str:
    """正規化したSurafceを取得"""
    if surface in list(RaceSurfaceType): return surface
    return SURFACE_MAP[surface] if surface else RaceSurfaceType.UNKNOWN

def valid_track_condition_str(condition: str) -> str:
    """正規化したConditionを取得"""
    if condition in list(TrackConditionType): return condition
    return CONDITION_MAP[condition] if condition else TrackConditionType.UNKNOWN

def valid_track_weather_str(weather: str) -> str:
    """正規化したWeatherを取得"""
    if weather in list(TrackWeatherType): return weather
    return WEATHER_MAP[weather] if weather else TrackWeatherType.UNKNOWN
