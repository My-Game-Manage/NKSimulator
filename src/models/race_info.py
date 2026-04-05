"""
race_info.py の概要

レースの開催会場とコース等の静的データを保持するデータクラス。
"""
from dataclasses import dataclass, replace

from src.constants.race_master import TrackCondition, TrackWeather
from src.models.section import TrackSection
from src.models.horse_info import HorseInfo
from src.constants.schema import RaceCol


@dataclass(frozen=True)
class RaceInfo:
    # 基本情報
    race_id: str
    # CSVから取得するレース情報
    course_name: str
    race_name: str
    race_num: int
    # grade: RaceGrade
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
    sections: list[TrackSection]
    # 馬のリスト
    horses: list[HorseInfo]

    def get_horse(self, horse_id: str):
        """指定したIDに一致するHorseInfoを返す。見つからない場合はNone。"""
        return next((h_info for h_info in self.horses if h_info.horse_id == horse_id), None)
