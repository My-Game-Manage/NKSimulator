"""
factory.py の概要

レースと出走馬の情報を取得し、RaceInfoのリストを返す。
"""
import pandas as pd
import numpy as np
import logging

# ロガーの取得（__name__ はファイル名/モジュール名になる）
logger = logging.getLogger(__name__)


from dataclasses import dataclass, replace

from src.constants.schema import RaceCol
from src.models.race_raw_data import RaceRawData
from src.models.race_info import RaceInfo, RaceParam, RaceState
from src.constants.race_master import TrackCondition, TrackWeather
from src.constants.course_master import CourseSpec, NAME_TO_COURSE, DEFAULT_COURSE_SPEC_KEY
from src.constants.track_master import TRACK_DATA, DEFAULT_TRACK_DATA_KEY
from src.services.horse_factory import HorseFactory
from src.models.section import TrackSection


class RaceInfoFactory:
    """
    レースに関する各データクラスを作成する
    """
    def __init__(self):
        logger.info("初期化中...")
        self.horse_factory = HorseFactory()

    def create_race_info(self, raw_data: RaceRawData) -> RaceInfo:
        """RaceInfoを作成する"""
        first_row = raw_data.entries.iloc[0]
        return RaceInfo(
            race_id=raw_data.race_id,
            course_name=raw_data.course,
            race_name=first_row[RaceCol.RACE_NAME],
            race_num=raw_data.race_num,
            horses={},
        )
    
    def create_race_info_with_horse_infos(self, raw_data: RaceRawData) -> RaceInfo:
        """RaceInfo（完全版）を作成する"""
        race_info_proto = self.create_race_info(raw_data)
        horse_infos = self.horse_factory.create_horse_infos(raw_data.entries)
        return self.append_horse_infos_in_race_info(race_info_proto, horse_infos)
    
    def append_horse_infos_in_race_info(self, race_info: RaceInfo, horse_infos: dict) -> RaceInfo:
        """RaceInfo（ベース）にHorseInfoの辞書を追加する"""
        return replace(race_info, horses=horse_infos)
    
    def create_race_param(self, raw_data: RaceRawData) -> RaceParam:
        """RaceParamを作成する"""
        first_row = raw_data.entries.iloc[0]
        course_name = first_row[RaceCol.COURSE]

        # マスタからCourseSpec取得
        course_spec = NAME_TO_COURSE.get(course_name, DEFAULT_COURSE_SPEC_KEY)

        # セクション取得
        distance = first_row[RaceCol.DISTANCE]
        surface = first_row[RaceCol.SURFACE]
        sections = TRACK_DATA.get(f"{self._get_track_name(course_name, distance, surface)}", DEFAULT_TRACK_DATA_KEY)

        return RaceParam(
            race_id=raw_data.race_id,
            distance=distance,
            surface=surface,
            condition=TrackCondition.from_str(first_row[RaceCol.TRACK_CONDITION]),
            weather=TrackWeather.from_str(first_row[RaceCol.WEATHER]),
            track_width=course_spec.track_width,
            corner_penalty=course_spec.corner_penalty,
            surface_friction=course_spec.surface_friction,
            sections=sections,
            checkpoints=self.create_checkpoints_from_sections(sections),
            horses={},
        )
    
    def create_race_param_with_horse_params(self, raw_data: RaceRawData) -> RaceParam:
        """RaceParam（完全版）を作成する"""
        race_param_proto = self.create_race_param(raw_data)
        horse_params = self.horse_factory.create_horse_params(raw_data.entries, raw_data.histories, race_param_proto.distance)
        return self.append_horse_params_in_race_param(race_param_proto, horse_params)
    
    def append_horse_params_in_race_param(self, race_param: RaceParam, horse_params: dict) -> RaceParam:
        """RaceParam（ベース）にHorseParamの辞書を追加する"""
        return replace(race_param, horses=horse_params)
    
    def create_race_state(self, race_id: str) -> RaceState:
        """RaceState（初期値）を作成する"""
        return RaceState(
            race_id=race_id,
            step_count=0.0,
            elapsed_time=0.0,
            horses={},
            ranks={},
        )
    
    def create_race_state_with_horse_states(self, race_id: str, h_infos: dict, h_params: dict) -> RaceState:
        """RaceState（完全版）を作成する"""
        race_state = self.create_race_state(race_id)
        horse_states = self.horse_factory.create_horse_states(h_infos, h_params)
        return self.append_horse_states_in_race_state(race_state, horse_states)
    
    def append_horse_states_in_race_state(self, race_state: RaceState, horse_states: dict) -> RaceState:
        """RaceState（ベース）にHorseStateの辞書を追加する"""
        ranks = {h_id:1 for h_id in horse_states.keys()}
        return replace(race_state, horses=horse_states, ranks=ranks)
        
    def _get_track_name(self, course_name: str, distance: int, surface: str) -> str:
        """コース構成用の名前取得"""
        suffix = "" if surface == "ダ" else "_芝"
        return f"{course_name}_{distance}{suffix}"

    def create_checkpoints_from_sections(self, sections: list[TrackSection]) -> list[float]:
        """セクション情報から記録地点のリストを返す"""
        return [s.start_at for s in sections if s.start_at > 0]
    
    def _get_checkpoints_from_sections(self, sections: list[TrackSection]) -> list[float]:
        """セクション情報から記録地点のリストを返す"""
        return [s.start_at for s in sections if s.start_at > 0]