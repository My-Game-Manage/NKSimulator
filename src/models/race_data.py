"""
race_info.py の概要

レースの開催会場とコース等の静的データを保持するデータクラス。
"""
from dataclasses import dataclass, field, replace
import pandas as pd

from src.models.horse_data import HorseProfile, HorseSnapshot
from src.models.track_data import TrackSection


@dataclass(frozen=True)
class CourseSpec:
    name: str
    is_jra: bool                # 中央判定
    is_excluded: bool           # 除外判定
    track_width: int            # トラック幅
    corner_penalty: float       # コーナー係数
    corner_radius: float        # コーナー半径
    turf_friction: float        # 芝係数
    surface_friction: float     # ダート係数


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
    race_id: str                # (?) レースID
    course: str                 # (?) 会場名
    race_name: str              # (?) レース名
    race_num: int               # (n) レース番号
    num_horses: int             # (n) 出走頭数
    # 基本データ
    distance: int               # (m)コース距離
    surface: int                # (Index) 0:芝／1:ダ／2:障／3:ば
    condition: int              # (Index) 0:良／1:稍／2:重／3:不
    weather: int                # (Index) 0:晴／1:曇／2:雨／3:雪
    # コースデータ
    track_width: float          # (m) コース幅
    corner_penalty: float       # (K) コーナー係数
    corner_radius: float        # (r) コーナー半径
    turf_friction: float        # (K) 芝摩擦係数
    surface_friction: float     # (K) ダート摩擦係数
    sections: list[TrackSection] = field(default_factory=list)
    # 記録用
    checkpoints: list[int] = field(default_factory=list)
    # 馬の辞書
    horses: dict[str, HorseProfile] = field(default_factory=dict)


@dataclass(frozen=True)
class RaceSnapshot:
    """レースの動的データを保持するデータクラス"""
    race_id: str                # (?) レースID
    step: int                   # (pt) ステップ数
    elapsed_time: float         # (msec) 経過秒数
    # 馬Stateの辞書（horse_id: h_state）
    horses: dict[str, HorseSnapshot] = field(default_factory=dict)
    # 現在の順位辞書（horse_id: rank）
    ranks: dict[str, int] = field(default_factory=dict)

    def update_ranks(self, new_ranks: dict):
        return replace(self, ranks=new_ranks)
    
    def next_step(self):
        return replace(self, step=self.step + 1)


@dataclass(frozen=True)
class RaceInfo:
    """レース関連のデータクラスをまとめるデータクラス"""
    race_id: str
    profile: RaceProfile
    snapshot: RaceSnapshot
