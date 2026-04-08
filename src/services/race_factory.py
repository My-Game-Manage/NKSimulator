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

    def get_race_info_list(self, race_data_sets: list[dict]) -> list[RaceInfo]:
        """レース情報のリストを返す"""
        race_info_list = []

        for race_data in race_data_sets:
            race_id = race_data[RaceCol.RACE_ID]
            entries_df = race_data[RaceCol.ENTRIES]
            histories_df = race_data[RaceCol.HISTORIES]
            race_info = self.create_race_info_from_df(race_id, entries_df, histories_df)
            race_info_list.append(race_info)

        return race_info_list
    
    def create_race_info_from_df(self, race_id: str, df: pd.DataFrame, h_df: pd.DataFrame) -> RaceInfo:
        """RaceInfoを作成する"""
        # 1. プロトタイプ（共通部分）の作成
        race_info_proto = self.create_race_info_prototype(race_id, df)

        # 2. 出馬表から馬のリスト作成
        # 馬のリスト作成を委譲
        horse_list = [
            self.horse_factory.create_horse_info(row, h_df) 
            for _, row in df.iterrows()
        ]

        # 3. プロトタイプに統合
        race_info = replace(race_info_proto, horses=horse_list)

        return race_info
    
    def create_race_info_prototype(self, race_id: str, race_df: pd.DataFrame) -> RaceInfo:
        """馬情報なしのRaceInfoのプロトタイプを作成"""
        # 全馬共通のため最初の1行を参照
        first_row = race_df.iloc[0]

        # セクション取得
        course_name = first_row[RaceCol.COURSE]
        distance = first_row[RaceCol.DISTANCE]
        surface = first_row[RaceCol.SURFACE]
        sections = TRACK_DATA.get(f"{self._get_track_name(course_name, distance, surface)}", DEFAULT_TRACK_DATA_KEY)

        # マスタからCourseSpec取得
        course_spec = NAME_TO_COURSE.get(course_name, DEFAULT_COURSE_SPEC_KEY)

        return RaceInfo(
            race_id=race_id,
            course_name=course_name,
            race_name=first_row[RaceCol.RACE_NAME],
            race_num=first_row[RaceCol.RACE_NUMBER],
            distance=distance,
            surface=surface,
            condition=TrackCondition.from_str(first_row[RaceCol.TRACK_CONDITION]),
            weather=TrackWeather.from_str(first_row[RaceCol.WEATHER]),
            track_width=course_spec.track_width,
            corner_penalty=course_spec.corner_penalty,
            surface_friction=course_spec.surface_friction,
            sections=sections,
            checkpoints=self._get_checkpoints_from_sections(sections),
            horses=[],
        )
    
    def create_initial_state(self, info: RaceInfo) -> RaceState:
        """RaceInfoからStateの初期値を作成"""
        horse_stetes = []
        for h_info in info.horses:
            h_id = h_info.horse_id
            h_state = self.horse_factory.reset_horse_state(h_info)
            horse_stetes.append(h_state)
        return RaceState(
            step_count=0.0,
            elapsed_time=0.0,
            horse_states=horse_stetes,
        )
    
    def _get_track_name(self, course_name: str, distance: int, surface: str) -> str:
        """コース構成用の名前取得"""
        suffix = "" if surface == "ダ" else "_芝"
        return f"{course_name}_{distance}{suffix}"

    def _get_checkpoints_from_sections(self, sections: list[TrackSection]) -> list[float]:
        """セクション情報から記録地点のリストを返す"""
        return [s.start_at for s in sections if s.start_at > 0]