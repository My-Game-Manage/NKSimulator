"""
race_info.py の概要

レースの開催会場とコース等の静的データを保持するデータクラス。
"""
from dataclasses import dataclass, field

from src.constants.race_master import TrackCondition, TrackWeather
from src.models.section import TrackSection
from src.models.horse_info import HorseInfo, HorseParam, HorseState


@dataclass(frozen=True)
class RaceInfo:
    """
    レースの基本情報を保持するデータクラス（レース準備で利用するだけ）
    """
    # 基本情報
    race_id: str
    # CSVから取得するレース情報
    course_name: str
    race_name: str
    race_num: int
    # num_horses: int
    # grade: RaceGrade
    # 馬Infoの辞書（horse_id: h_info）
    horses: dict[str, HorseInfo] = field(default_factory=dict)


@dataclass(frozen=True)
class RaceParam:
    """
    レースの静的データを保持するデータクラス（Engineに渡す静的数値）
    """
    race_id: str
    distance: int
    surface: str
    condition: TrackCondition
    weather: TrackWeather
    # コースデータから取得する静的数値
    track_width: float      # コース幅
    corner_penalty: float   # コーナー係数
    surface_friction: float # 馬場摩擦係数
    # --- コースレイアウト (区間データ) ---
    # 距離に応じて個数が変わるセグメントリスト
    sections: list[TrackSection] = field(default_factory=list)
    # 記録するチェックポイント距離のリスト
    checkpoints: list[int] = field(default_factory=list)
    # 馬Paramの辞書（hores_id: h_param）
    horses: dict[str, HorseParam] = field(default_factory=dict)


@dataclass(frozen=True)
class RaceState:
    """
    レースの動的データを保持するクラス（Engineに渡し、受け取る）
    """
    race_id: str
    step_count: int
    elapsed_time: float
    # 馬Stateの辞書（horse_id: h_state）
    horses: dict[str, HorseState] = field(default_factory=dict)
    # 現在の順位辞書（horse_id: rank）
    ranks: dict[str, int] = field(default_factory=dict)


@dataclass(frozen=True)
class RaceDataSet:
    """
    レースのデータセット
    """
    race_id: str
    info: RaceInfo
    param: RaceParam
    state: RaceState
