"""
race_info.py の概要

レースの開催会場とコース等の静的データを保持するデータクラス。
"""
from dataclasses import dataclass, field, replace
import pandas as pd

from src.constants.race_master import TrackCondition, TrackWeather
from src.models.section import TrackSection
from src.models.horse_info import HorseProfile, HorseState


@dataclass(frozen=True)
class RaceRawData:
    """レースデータ（出馬表のDataFrameと馬の過去レースデータDataFrameを持つ）"""
    race_id: str
    course: str
    race_num: int
    entries: pd.DataFrame
    histories: pd.DataFrame


@dataclass(frozen=True)
class RaceProfile:
    """レースの固定データを保持するデータクラス"""
    # 基本情報
    race_id: str
    course_name: str
    race_name: str
    race_num: int
    num_horses: int
    # 基本データ
    distance: int
    surface: str
    condition: TrackCondition
    weather: TrackWeather
    # コースデータ
    track_width: float          # コース幅
    corner_penalty: float       # コーナー係数
    turf_friction: float        # 芝摩擦係数
    surface_friction: float     # ダート摩擦係数
    sections: list[TrackSection] = field(default_factory=list)
    # 記録用
    checkpoints: list[int] = field(default_factory=list)
    # 馬の辞書
    horses: dict[str, HorseProfile] = field(default_factory=dict)


@dataclass(frozen=True)
class RaceState:
    """レースの動的データを保持するデータクラス"""
    race_id: str
    step_count: int
    elapsed_time: float
    # 馬Stateの辞書（horse_id: h_state）
    horses: dict[str, HorseState] = field(default_factory=dict)
    # 現在の順位辞書（horse_id: rank）
    ranks: dict[str, int] = field(default_factory=dict)

    def update_ranks(self, new_ranks: dict):
        return replace(self, ranks=new_ranks)


@dataclass(frozen=True)
class RaceInfo:
    """レース関連のデータクラスをまとめるデータクラス"""
    race_id: str
    profile: RaceProfile
    state: RaceState
