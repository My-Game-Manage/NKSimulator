"""
factory.py の概要

レースと出走馬の情報を取得し、RaceInfoのリストを返す。
"""
import pandas as pd
import numpy as np
import logging

# ロガーの取得（__name__ はファイル名/モジュール名になる）
logger = logging.getLogger(__name__)


from dataclasses import dataclass, field

from src.constants.schema import RaceCol
from src.models.race_data import RaceInfo, RaceProfile, RaceState, RaceRawData
from src.constants.race_master import TrackCondition, TrackWeather
from src.constants.course_master import CourseSpec, NAME_TO_COURSE, DEFAULT_COURSE_SPEC_KEY
from src.constants.track_master import TRACK_DATA, DEFAULT_TRACK_DATA_KEY
from src.services.horse_factory import HorseFactory
from src.models.section import TrackSection
from src.models.horse_data import HorseProfile


@dataclass(frozen=True)
class _RaceBaseProf:
    """レースの基本情報を一時保存するインナークラス"""
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

@dataclass(frozen=True)
class _RaceParam:
    """レースのパラメータを一時保存するインナークラス"""
    # コースデータ
    track_width: float          # コース幅
    corner_penalty: float       # コーナー係数
    turf_friction: float        # 芝摩擦係数
    surface_friction: float     # ダート摩擦係数
    sections: list[TrackSection] = field(default_factory=list)
    # 記録用
    checkpoints: list[int] = field(default_factory=list)


class RaceInfoFactory:
    """
    レースに関する各データクラスを作成する
    """
    def __init__(self):
        logger.info("初期化中...")
        self.horse_factory = HorseFactory()

    def create_race_profile(self, raw_data: RaceRawData) -> RaceProfile:
        """Profile作成"""
        base_prof = self._race_base_prof_from(raw_data)
        param = self._race_param_from(base_prof.course_name, base_prof.distance, base_prof.surface)
        horses = self.horse_factory.create_all_horse_profiles(raw_data.entries, raw_data.histories, base_prof.distance)
        return RaceProfile(
            race_id=base_prof.race_id,
            course_name=base_prof.course_name,
            race_name=base_prof.race_name,
            race_num=base_prof.race_num,
            num_horses=base_prof.num_horses,
            distance=base_prof.distance,
            surface=base_prof.surface,
            condition=base_prof.condition,
            weather=base_prof.weather,
            track_width=param.track_width,
            corner_penalty=param.corner_penalty,
            turf_friction=param.turf_friction,
            surface_friction=param.surface_friction,
            sections=param.sections,
            checkpoints=param.checkpoints,
            horses=horses,
        )
    
    def _race_base_prof_from(self, raw_data: RaceRawData) -> _RaceBaseProf:
        """レースの基本情報を取得して返す"""
        # 共通部分だから最初だけ抜き出す
        first_row = raw_data.entries.iloc[0]
        # 各値を取得
        race_id = raw_data.race_id
        course_name = raw_data.course
        race_name = first_row[RaceCol.RACE_NAME]
        race_num = raw_data.race_num
        num_horses = first_row[RaceCol.NUM_HORSES]
        distance = first_row[RaceCol.DISTANCE]
        surface = first_row[RaceCol.SURFACE]
        condition=TrackCondition.from_str(first_row[RaceCol.TRACK_CONDITION])
        weather=TrackWeather.from_str(first_row[RaceCol.WEATHER])
        return _RaceBaseProf(
            race_id=race_id,
            course_name=course_name,
            race_name=race_name,
            race_num=race_num,
            num_horses=num_horses,
            distance=distance,
            surface=surface,
            condition=condition,
            weather=weather,
        )
    
    def _race_param_from(self, course_name, distance, surface) -> _RaceParam:
        """レースのパラメータを取得して返す"""
        # マスタからCourseSpec取得
        course_spec = NAME_TO_COURSE.get(course_name, DEFAULT_COURSE_SPEC_KEY)
        track_width = course_spec.track_width
        corner_penalty = course_spec.corner_penalty
        turf_friction = course_spec.turf_friction
        surface_friction = course_spec.surface_friction
        sections = TRACK_DATA.get(f"{self._get_track_name(course_name, distance, surface)}", DEFAULT_TRACK_DATA_KEY)
        checkpoints = self._checkpoints_from_sections(sections)
        return _RaceParam(
            track_width=track_width,
            corner_penalty=corner_penalty,
            turf_friction=turf_friction,
            surface_friction=surface_friction,
            sections=sections,
            checkpoints=checkpoints,
        )
    
    def create_race_state(self, race_id: str, h_profiles: dict[str, HorseProfile]) -> RaceState:
        """RaceState（初期値）を作成する"""
        horses = self.horse_factory.create_horse_states(h_profiles)
        ranks = {h_id: 1 for h_id in h_profiles.keys()}
        return RaceState(
            race_id=race_id,
            step_count=0.0,
            elapsed_time=0.0,
            horses=horses,
            ranks=ranks,
        )    
    
    def _get_track_name(self, course_name: str, distance: int, surface: str) -> str:
        """コース構成用の名前取得"""
        suffix = "" if surface == "ダ" else "_芝"
        return f"{course_name}_{distance}{suffix}"

    def _checkpoints_from_sections(self, sections: list[TrackSection]) -> list[float]:
        """セクション情報から記録地点のリストを返す"""
        return [s.start_at for s in sections if s.start_at > 0]
