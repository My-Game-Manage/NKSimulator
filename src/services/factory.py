"""
factory.py の概要

レースと出走馬の情報を取得し、RaceInfoのリストを返す。
"""
import pandas as pd
from pathlib import Path
import logging

# ロガーの取得（__name__ はファイル名/モジュール名になる）
logger = logging.getLogger(__name__)

from abc import ABC, abstractmethod

from src.constants.enums import HorseBehaviorType
from src.constants.fields import RaceProfField, HorseProfField
from src.constants.schema import RaceCol
from src.models.race_data import RaceInfo, RaceRawData, RaceProfile, RaceSnapshot
from src.models.horse_data import HorseProfile, HorseSnapshot
from src.utils.utils import full_races_csv_filename_from, horse_history_csv_filename_from, race_id_from, track_name_from, checkpoints_from_sections
from src.utils.normalizer import valid_race_shutuba_df
from src.constants.course_master import NAME_TO_COURSE, DEFAULT_COURSE_SPEC_KEY, TRACK_DATA, DEFAULT_TRACK_DATA_KEY, TrackSection
import src.services.ability_analyzer as abi


_DATA_DIR = "data"


class RaceFactory(ABC):
    """レース用データを作成する基底クラス"""
    @abstractmethod
    def create_races(self, **kwargs) -> list[RaceInfo]:
        pass

    @abstractmethod
    def create_race(self, **kwargs) -> RaceInfo:
        pass

    @abstractmethod
    def create_race_profile(self, **kwargs) -> RaceProfile:
        pass

    @abstractmethod
    def create_race_snapshot(self, **kwargs) -> RaceSnapshot:
        pass


class HorseFactory(ABC):
    """馬用データを作成する基底クラス"""
    @abstractmethod
    def create_horse_profile(self, **kwargs) -> HorseProfile:
        pass

    @abstractmethod
    def create_horse_snapshot(self, **kwargs) -> HorseSnapshot:
        pass

# ---------------------------------------------------------
# Race data (CSV)
# ---------------------------------------------------------
class CSVRaceFactory(RaceFactory):
    """CSVデータからレース用データを作成する"""
    def __init__(self):
        super().__init__()
        self.horse_factory = CSVHorseFactory()

    def create_races(self, date: str, course: str, race_nums: list[int]) -> list[RaceInfo]:
        return [self.create_race(date, course, num) for num in race_nums]
    
    def create_race(self, date: str, course: str, race_num: int) -> RaceInfo:
        raw_data = CSVProvider.get_target_race_raw_data(date, course, race_num)
        profile = self.create_race_profile(raw_data)
        snapshot = self.create_race_snapshot(raw_data.race_id, profile.horses)
        return RaceInfo(
            race_id=raw_data.race_id,
            profile=profile,
            snapshot=snapshot,
        )
    
    def create_race_profile(self, raw_data: RaceRawData) -> RaceProfile:
        """RaceProfileの作成"""
        base_prof = self._create_base_profile(raw_data)
        prof_param = self._create_profile_param(base_prof[RaceProfField.COURSE.value],
                                                base_prof[RaceProfField.DISTANCE.value],
                                                base_prof[RaceProfField.SURFACE.value])
        distance = base_prof[RaceProfField.DISTANCE.value]
        horses = {}
        for _, row in raw_data.entries.iterrows():
            horse_id = row[RaceCol.HORSE_ID]
            history_df = raw_data.histories[RaceCol.HORSE_ID == horse_id]
            horses[horse_id] = self.horse_factory.create_horse_profile(distance, row, history_df)
        # 辞書型なので**base_profでフィールド自動入力される
        prof = {**base_prof, **prof_param}
        return RaceProfile(horses=horses, **prof)
    
    def create_race_snapshot(self, race_id: str, h_profiles: dict[str, HorseProfile]) -> RaceSnapshot:
        """RaceSnapshot（初期値）の作成"""
        horses = {h_id: self.horse_factory.create_horse_snapshot(
            h_id, h_profiles[h_id].horse_num, h_profiles[h_id].strategy) for h_id in h_profiles.keys()}
        ranks = {h_id: 1 for h_id in h_profiles.keys()}
        return RaceSnapshot(
            race_id=race_id,
            step=0,
            elapsed_time=0.0,
            horses=horses,
            ranks=ranks,
        )
    
    def _create_base_profile(self, raw_data: RaceRawData) -> dict:
        """基本データ部分の作成"""
        # 共通部分だから最初だけ抜き出す
        first_row = raw_data.entries.iloc[0]
        return {
            RaceProfField.RACE_ID.value: raw_data.race_id,
            RaceProfField.COURSE.value: raw_data.course,
            RaceProfField.RACE_NAME.value: first_row[RaceCol.RACE_NAME],
            RaceProfField.RACE_NUM.value: raw_data.race_num,
            RaceProfField.NUM_HORSES.value: first_row[RaceCol.NUM_HORSES],
            RaceProfField.DISTANCE.value: first_row[RaceCol.DISTANCE],
            RaceProfField.SURFACE.value: first_row[RaceCol.SURFACE],
            RaceProfField.CONDITION.value: first_row[RaceCol.TRACK_CONDITION],
            RaceProfField.WEATHER.value: first_row[RaceCol.WEATHER],
        }
    
    def _create_profile_param(self, course: str, distance: int, surface: str) -> dict:
        """パラメータ部分の作成"""
        # マスタからCourseSpec取得
        course_spec = NAME_TO_COURSE.get(course, DEFAULT_COURSE_SPEC_KEY)
        sections = TRACK_DATA.get(f"{track_name_from(course, distance, surface)}", DEFAULT_TRACK_DATA_KEY)
        checkpoints = checkpoints_from_sections(sections)
        return {
            RaceProfField.TRACK_WIDTH.value: course_spec.track_width,
            RaceProfField.CORNER_PENALTY.value: course_spec.corner_penalty,
            RaceProfField.TURF_FRICTION.value: course_spec.turf_friction,
            RaceProfField.SURFACE_FRICTION.value: course_spec.surface_friction,
            RaceProfField.SECTIONS.value: sections,
            RaceProfField.CHECKPOINTS.value: checkpoints,
        }


class CSVProvider:
    """目的のCSVデータを取得する"""
    @staticmethod
    def get_target_race_raw_data(date: str, course: str, race_num: int) -> RaceRawData:
        """出馬表（CSV）から目的の箇所のデータだけ取得"""
        shutuba_df = valid_race_shutuba_df(__class__._fetch_shutuba_csv(date))
        histories_df = __class__._fetch_horse_history_scv(date)
        entries_df = __class__._filtered_shutuba_df(course, race_num, shutuba_df) 
        return RaceRawData(
            race_id=race_id_from(date, course, race_num),
            course=course,
            race_num=race_num,
            entries=entries_df,
            histories=histories_df,
        )
    
    @classmethod
    def _filtered_shutuba_df(cls, course: str, race_num: int, df: pd.DataFrame) -> pd.DataFrame:
        """該当するコースとレース番号で抽出する"""
        return df[
            (df[RaceCol.COURSE] == course) & 
            (df[RaceCol.RACE_NUMBER] == race_num)
        ]

    @classmethod
    def _fetch_shutuba_csv(cls, date: str) -> pd.DataFrame:
        """目的のCSVファイルを取得"""
        file_path = Path(_DATA_DIR) / full_races_csv_filename_from(date)
        try:
            race_df = pd.read_csv(file_path)
            return race_df
        except pd.errors.EmptyDataError:
            logger.warning(f"{file_path}はありません。")
            return pd.DataFrame()
    
    @classmethod
    def _fetch_horse_history_scv(cls, date: str) -> pd.DataFrame:
        """目的の過去レース履歴CSVファイルを取得"""
        file_path = Path(_DATA_DIR) / horse_history_csv_filename_from(date)
        try:
            h_df = pd.read_csv(file_path)
            return h_df
        except pd.errors.EmptyDataError:
            logger.warning(f"{file_path}はありません。")
            return pd.DataFrame()

# ---------------------------------------------------------
# Horse data (csv)
# ---------------------------------------------------------
class CSVHorseFactory(HorseFactory):
    """馬のレース用データをCSVデータから作成する"""
    def create_horse_profile(self, distance: int, race_row: pd.Series, history_df: pd.DataFrame) -> HorseProfile:
        base_prof = self._create_base_prof(race_row)
        ability = self._create_horse_ability(distance, history_df)
        prof = {**base_prof, **ability}
        return HorseProfile(**prof)
    
    def create_horse_snapshot(self, horse_id: str, horse_num: int, strategy: str) -> HorseSnapshot:
        return HorseSnapshot(
            horse_id=horse_id,
            step=0,
            elapsed_time=0.0,
            velocity=0.0,
            distance=0.0,
            stamina=0.0,
            lane=float(horse_num),
            is_finished=False,
            finish_time=None,
            behavior=HorseBehaviorType.IN_GATE.value,
            strategy=strategy,
        )
    
    def _create_base_prof(self, row: pd.Series) -> dict:
        """馬の基本データ部分作成"""
        return {
            HorseProfField.HORSE_ID.value: row[RaceCol.HORSE_ID],
            HorseProfField.NAME.value: row[RaceCol.HORSE_NAME],
            HorseProfField.BRACKET_NUM.value: row[RaceCol.BRACKET_NUM],
            HorseProfField.HORSE_NUM.value: row[RaceCol.HORSE_NUM],
            HorseProfField.JOCKEY.value: row[RaceCol.JOCKEY],
            HorseProfField.HORSE_WEIGHT.value: row[RaceCol.HORSE_WEIGHT],
            HorseProfField.WEIGHT_CARRIED.value: row[RaceCol.WEIGHT_CARRIED],
        }
    
    def _create_horse_ability(self, distance: int, history: pd.DataFrame) -> dict:
        """馬の能力値算出"""
        max_speed, min_speed = abi.calculate_min_max_speed(history)
        total_stamina, stamina_waste_rate = abi.calculate_stamina_params(history)
        strategy = abi.determine_strategy(history)
        return {
            HorseProfField.MAX_SPEED.value: max_speed,
            HorseProfField.MIN_SPEED.value: min_speed,
            HorseProfField.ACCELERATION.value: abi.calculate_acceleration(history),
            HorseProfField.TOTAL_STAMIN.value: total_stamina,
            HorseProfField.STAMINA_WASTE_RATE.value: stamina_waste_rate,
            HorseProfField.CORNER_ABILITY.value: abi.calculate_cornering_ability(history),
            HorseProfField.GATE_REACTION.value: abi.calculate_gate_reaction(history),
            HorseProfField.STRATEGY.value: strategy,
            HorseProfField.TARGET_SPURT_DIST.value: abi.calculate_spurt_dist(strategy, history),
        }    
    
# ---------------------------------------------------------
# Race data (debug)
# ---------------------------------------------------------


# ---------------------------------------------------------
# Horse data (debug)
# ---------------------------------------------------------
