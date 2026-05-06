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
from dataclasses import replace
import random

from src.constants.enums import HorseBehaviorType, HorseStrategyType
from src.constants.fields import RaceProfField, HorseProfField, HorseSnapField
from src.constants.schema import RaceCol
from src.models.race_data import RaceInfo, RaceRawData, RaceProfile, RaceSnapshot
from src.models.horse_data import HorseProfile, HorseSnapshot
from src.utils.utils import full_races_csv_filename_from, horse_history_csv_filename_from, race_id_from, track_name_from, checkpoints_from_sections
from src.utils.normalizer import valid_race_shutuba_df
from src.constants.course_master import NAME_TO_COURSE, DEFAULT_COURSE_SPEC_KEY, TRACK_DATA, DEFAULT_TRACK_DATA_KEY, TrackSection
import src.services.ability_analyzer as abi


_DATA_DIR = "data"


# ---------------------------------------------------------
# 基底クラス
# ---------------------------------------------------------
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

    def create_race_snapshot(self, race_id: str, horses: dict[str, HorseSnapshot]) -> RaceSnapshot:
        """Snapshot（初期値）作成"""
        ranks = {h_id: 1 for h_id in horses.keys()}
        return RaceSnapshot(
            race_id=race_id,
            step=0,
            elapsed_time=0.0,
            horses=horses,
            ranks=ranks,
        )


class HorseFactory(ABC):
    """馬用データを作成する基底クラス"""
    @abstractmethod
    def create_horse_profile(self, **kwargs) -> HorseProfile:
        pass

    def create_horse_snapshot(self, horse_id: str, horse_num: int, stamina: float, stragety: str) -> HorseSnapshot:
        """Snapshot（初期値）作成"""
        return HorseSnapshot(
            horse_id=horse_id,
            step=0,
            elapsed_time=0.0,
            velocity=0.0,
            distance=0.0,
            stamina=stamina,
            lane=float(horse_num),
            dist_to_front=0.0,
            behavior=HorseBehaviorType.IN_GATE.value,
            strategy=stragety,
            is_finished=False,
            finish_time=None,
        )


# ---------------------------------------------------------
# Race data (CSV)
# ---------------------------------------------------------
class CSVRaceFactory(RaceFactory):
    """CSVデータからレース用データを作成する"""
    def __init__(self):
        super().__init__()
        self.horse_factory = CSVHorseFactory()

    def create_races(self, date: str, course: str, race_nums: list[int]) -> list[RaceInfo]:
        """目的のレース群のRaceInfoリストを作成して取得"""
        return [self.create_race(date, course, num) for num in race_nums]
    
    def create_race(self, date: str, course: str, race_num: int) -> RaceInfo:
        """CSVデータを取得し、Profileを作成する（Snapshotはレース直前に作成するのでここは空）"""
        raw_data = CSVProvider.get_target_race_raw_data(date, course, race_num)
        profile = self.create_race_profile(raw_data)
        h_snaps = {}
        for h_id, h_prof in profile.horses.items():
            h_snaps[h_id] = self.horse_factory.create_horse_snapshot(h_id, h_prof.horse_num, h_prof.total_stamina, h_prof.strategy)
        snapshot = self.create_race_snapshot(raw_data.race_id, h_snaps)
        return RaceInfo(
            race_id=raw_data.race_id,
            profile=profile,
            snapshot=snapshot,
        )
    
    def create_race_profile(self, raw_data: RaceRawData) -> RaceProfile:
        """RaceProfileの作成"""
        base_prof = self._create_base_profile(raw_data)
        logger.info(f"base_prof: {base_prof}")
        prof_param = self._create_profile_param(base_prof[RaceProfField.COURSE.value],
                                                base_prof[RaceProfField.DISTANCE.value],
                                                base_prof[RaceProfField.SURFACE.value])
        distance = base_prof[RaceProfField.DISTANCE.value]
        horses = {}
        for _, row in raw_data.entries.iterrows():
            horse_id = row[RaceCol.HORSE_ID]
            history_df = raw_data.histories[raw_data.histories[RaceCol.HORSE_ID].astype(str) == str(horse_id)]
            horses[horse_id] = self.horse_factory.create_horse_profile(distance, row, history_df)
        # 辞書型なので**base_profでフィールド自動入力される
        prof = {**base_prof, **prof_param}
        return RaceProfile(horses=horses, **prof)
    
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
    
    def _create_base_prof(self, row: pd.Series) -> dict:
        """馬の基本データ部分作成"""
        return {
            HorseProfField.HORSE_ID: row[RaceCol.HORSE_ID],
            HorseProfField.NAME: row[RaceCol.HORSE_NAME],
            HorseProfField.BRACKET_NUM: row[RaceCol.BRACKET_NUM],
            HorseProfField.HORSE_NUM: row[RaceCol.HORSE_NUM],
            HorseProfField.JOCKEY: row[RaceCol.JOCKEY],
            HorseProfField.HORSE_WEIGHT: row[RaceCol.HORSE_WEIGHT],
            HorseProfField.WEIGHT_CARRIED: row[RaceCol.WEIGHT_CARRIED],
        }
    
    def _create_horse_ability(self, distance: int, history: pd.DataFrame) -> dict:
        """馬の能力値算出"""
        base_speed = abi.calculate_normalized_speed(history)
        stability_factor = abi.calculate_stability_factor(history)
        base_spurt_speed = abi.calculate_normalized_spurt_speed(history)
        cruise_speed = abi.get_race_cruise_speed(base_speed, distance)
        last_3f_speed = abi.get_race_spurt_speed(base_spurt_speed, distance)
        min_speed = base_speed * stability_factor
        total_stamina, stamina_waste_rate = abi.calculate_stamina_params(history)
        strategy = abi.determine_strategy(history)
        return {
            HorseProfField.BASE_SPEED: base_speed,
            HorseProfField.BASE_SPURT_SPEED: base_spurt_speed,
            HorseProfField.CRUISE_SPEED: cruise_speed,
            HorseProfField.LAST_3F_SPEED: last_3f_speed,
            HorseProfField.MIN_SPEED: min_speed,
            HorseProfField.ACCELERATION: abi.calculate_acceleration(history),
            HorseProfField.TOTAL_STAMINA: total_stamina,
            HorseProfField.STAMINA_WASTE_RATE: stamina_waste_rate,
            HorseProfField.CORNER_ABILITY: abi.calculate_cornering_ability(history),
            HorseProfField.GATE_REACTION: abi.calculate_gate_reaction(history),
            HorseProfField.STABILITY_FACTOR: stability_factor,
            HorseProfField.STRATEGY: strategy,
            HorseProfField.TARGET_SPURT_DIST: abi.calculate_spurt_dist(strategy, history),
        }    
    
# ---------------------------------------------------------
# Race data (debug)
# ---------------------------------------------------------
DEBUG_DEFAULTS = {
    RaceProfField.RACE_ID.value: race_id_from("10000101", "大井", 1),
    RaceProfField.COURSE.value: "DEMO",
    RaceProfField.RACE_NAME.value: "DEBUG",
    RaceProfField.RACE_NUM.value: 1,
    RaceProfField.NUM_HORSES.value: 8,
    RaceProfField.DISTANCE.value: 1600,
    RaceProfField.SURFACE.value: "ダ",
    RaceProfField.CONDITION.value: "良",
    RaceProfField.WEATHER.value: "晴",
}

class DebugRaceFactory(RaceFactory):
    """デバッグ用のレースデータを作成する"""
    def __init__(self):
        super().__init__()
        self.horse_factory = DebugHorseFactory()

    def create_races(self, **kwargs) -> list[RaceInfo]:
        """DEMOの時はこちらは使わないでおく"""
        logger.warning("DEBUG時は create_race のみ使って下さい")
        return []
    
    def create_race(self,
                    course=DEBUG_DEFAULTS[RaceProfField.COURSE.value],
                    num_horses: int=DEBUG_DEFAULTS[RaceProfField.NUM_HORSES.value],
                    distance: int=DEBUG_DEFAULTS[RaceProfField.DISTANCE.value],
                    surface: str=DEBUG_DEFAULTS[RaceProfField.SURFACE.value],
                    condition: str=DEBUG_DEFAULTS[RaceProfField.CONDITION.value],
                    weather: str=DEBUG_DEFAULTS[RaceProfField.WEATHER.value],
                ) -> RaceInfo:
        """DEMO用のデータ作成"""
        race_id = DEBUG_DEFAULTS[RaceProfField.RACE_ID.value]
        profile = self.create_race_profile(race_id, course, num_horses, distance, surface, condition, weather)
        snapshot = self.create_race_snapshot(race_id, {})
        return RaceInfo(
            race_id=race_id,
            profile=profile,
            snapshot=snapshot,
        )
    
    def create_race_profile(self, race_id: str, course: str, num_horses: int, distance: int,
                            surface: str, condition: str, weather: str) -> RaceProfile:
        """DEMO用のProfile作成（馬はなし）"""
        course_spec = NAME_TO_COURSE.get(course, DEFAULT_COURSE_SPEC_KEY)
        sections = TRACK_DATA.get(f"{track_name_from(course, distance, surface)}", DEFAULT_TRACK_DATA_KEY)
        checkpoints = checkpoints_from_sections(sections)
        return RaceProfile(
            race_id=race_id,
            course=course,
            race_name=DEBUG_DEFAULTS[RaceProfField.RACE_NAME.value],
            race_num=DEBUG_DEFAULTS[RaceProfField.RACE_NUM.value],
            num_horses=num_horses,
            distance=distance,
            surface=surface,
            condition=condition,
            weather=weather,
            track_width=course_spec.track_width,
            corner_penalty=course_spec.corner_penalty,
            turf_friction=course_spec.turf_friction,
            surface_friction=course_spec.surface_friction,
            sections=sections,
            checkpoints=checkpoints,
            horses={},
        )
        
    def update_race_prof_status(self, race_info: RaceInfo, **kwargs) -> RaceInfo:
        """テスト用の数値に書き換える（Profile用）"""
        new_prof = replace(race_info.profile, **kwargs)
        return replace(race_info, profile=new_prof)
    
    def entry_horse(self, race_info: RaceInfo, horse_prof: HorseProfile) -> RaceInfo:
        """RaceInfoに馬をエントリーする"""
        # 既存のHorseProfileの最後に追加する
        new_h_profs = {**race_info.profile.horses, **{horse_prof.horse_id: horse_prof}}
        new_prof = replace(race_info.profile, horses=new_h_profs)
        h_snaps = race_info.snapshot.horses
        h_snaps[horse_prof.horse_id] = self.horse_factory.create_horse_snapshot(
            horse_prof.horse_id, horse_prof.horse_num, horse_prof.total_stamina, horse_prof.strategy
        )
        ranks = race_info.snapshot.ranks
        ranks[horse_prof.horse_id] = 1
        new_snap = replace(race_info.snapshot, horses=h_snaps, ranks=ranks)
        return replace(race_info, profile=new_prof, snapshot=new_snap)

    def entry_horses(self, race_info: RaceInfo, horses: dict[str, HorseProfile]) -> RaceInfo:
        """RaceInfoに馬をまとめてエントリーする"""
        new_h_profs = {**race_info.profile.horses, **horses}
        # 新規のHorseProfile群として追加する
        new_prof = replace(race_info.profile, horses=new_h_profs)
        h_snaps = {}
        ranks = {}
        for h_id, h_prof in new_h_profs.items():
            h_snaps[h_id] = self.horse_factory.create_horse_snapshot(h_id, h_prof.horse_num, h_prof.total_stamina, h_prof.strategy)
            ranks[h_id] = 1
        new_snap = replace(race_info.snapshot, horses=h_snaps, ranks=ranks)
        return replace(race_info, profile=new_prof, snapshot=new_snap)

# ---------------------------------------------------------
# Horse data (debug)
# ---------------------------------------------------------
DEBUG_HORSE_DEFAULTS = {
    HorseProfField.HORSE_ID.value: 1,
    HorseProfField.NAME.value: "ダミー",
    HorseProfField.BRACKET_NUM.value: 1,
    HorseProfField.HORSE_NUM.value: 1,
    HorseProfField.JOCKEY.value: "ダミー騎手",
    HorseProfField.HORSE_WEIGHT.value: 450,
    HorseProfField.WEIGHT_CARRIED.value: 55.0,
    HorseProfField.BASE_SPEED: 15.0,
    HorseProfField.BASE_SPURT_SPEED: 17.0,
    HorseProfField.CRUISE_SPEED.value: 15.0,
    HorseProfField.LAST_3F_SPEED.value: 17.0,
    HorseProfField.MIN_SPEED.value: 13.0,
    HorseProfField.ACCELERATION.value: 1.2,
    HorseProfField.TOTAL_STAMINA.value: 1800,
    HorseProfField.STAMINA_WASTE_RATE.value: 1.0,
    HorseProfField.CORNER_ABILITY.value: 1.0,
    HorseProfField.GATE_REACTION.value: 1.0,
    HorseProfField.STABILITY_FACTOR: 0.9,
    HorseProfField.STRATEGY.value: HorseStrategyType.CLOSER.value,
    HorseProfField.TARGET_SPURT_DIST.value: 600.0,
}

DEBUG_HORSE_ABILITY_MIN_MAX = {
    HorseProfField.HORSE_WEIGHT.value: (350.0, 550.0),
    HorseProfField.BASE_SPEED: (15.0, 17.0),
    HorseProfField.BASE_SPURT_SPEED: (17.0, 18.5),
    HorseProfField.CRUISE_SPEED.value: (15.0, 17.0),
    HorseProfField.LAST_3F_SPEED.value: (17.0, 18.5),
    HorseProfField.MIN_SPEED.value: (13.5, 15.0),
    HorseProfField.ACCELERATION.value: (0.8, 1.2),
    HorseProfField.TOTAL_STAMINA.value: (1800, 2600),
    HorseProfField.STAMINA_WASTE_RATE.value: (0.95, 1.05),
    HorseProfField.CORNER_ABILITY.value: (0.4, 0.6),
    HorseProfField.GATE_REACTION.value: (0.3, 1.0),
    HorseProfField.STABILITY_FACTOR: (0.8, 0.95),
    HorseProfField.TARGET_SPURT_DIST.value: (500.0, 700.0),
}

class DebugHorseFactory(HorseFactory):
    """デバッグ用の馬データを作成する"""
    # ダミー用のID
    _dummy_id_counter = 1

    def create_horse_profile(self,
                             horse_weight: int=DEBUG_HORSE_DEFAULTS[HorseProfField.HORSE_WEIGHT.value],
                             weight_carried: float=DEBUG_HORSE_DEFAULTS[HorseProfField.WEIGHT_CARRIED.value],
                             base_speed: float=DEBUG_HORSE_DEFAULTS[HorseProfField.BASE_SPEED],
                             base_spurt_speed: float=DEBUG_HORSE_DEFAULTS[HorseProfField.BASE_SPURT_SPEED],
                             cruise_speed: float=DEBUG_HORSE_DEFAULTS[HorseProfField.CRUISE_SPEED.value],
                             last_3f_speed: float=DEBUG_HORSE_DEFAULTS[HorseProfField.LAST_3F_SPEED.value],
                             min_speed: float=DEBUG_HORSE_DEFAULTS[HorseProfField.MIN_SPEED.value],
                             acceleration: float=DEBUG_HORSE_DEFAULTS[HorseProfField.ACCELERATION.value],
                             total_stamina: float=DEBUG_HORSE_DEFAULTS[HorseProfField.TOTAL_STAMINA.value],
                             stamina_waste_rate: float=DEBUG_HORSE_DEFAULTS[HorseProfField.STAMINA_WASTE_RATE.value],
                             corner_ability: float=DEBUG_HORSE_DEFAULTS[HorseProfField.CORNER_ABILITY.value],
                             gate_reaction: float=DEBUG_HORSE_DEFAULTS[HorseProfField.GATE_REACTION.value],
                             stability_factor: float=DEBUG_HORSE_DEFAULTS[HorseProfField.STABILITY_FACTOR],
                             strategy: str=DEBUG_HORSE_DEFAULTS[HorseProfField.STRATEGY.value],
                             target_spurt_dist: float=DEBUG_HORSE_DEFAULTS[HorseProfField.TARGET_SPURT_DIST.value]) -> HorseProfile:
        return HorseProfile(
            horse_id=self.create_dummy_id(),
            name=self.create_dummy_name(),
            bracket_num=1,
            horse_num=self._dummy_id_counter,
            jockey=self.create_dummy_jockey(),
            horse_weight=horse_weight,
            weight_carried=weight_carried,
            base_speed=base_speed,
            base_spurt_speed=base_spurt_speed,
            cruise_speed=cruise_speed,
            last_3f_speed=last_3f_speed,
            min_speed=min_speed,
            acceleration=acceleration,
            total_stamina=total_stamina,
            stamina_waste_rate=stamina_waste_rate,
            cornering_ability=corner_ability,
            gate_reaction=gate_reaction,
            stability_factor=stability_factor,
            strategy=strategy,
            target_spurt_dist=target_spurt_dist,
        )
    
    def create_horse_profile_as_random(self) -> HorseProfile:
        """Profile作成（ランダムで）"""
        return HorseProfile(
            horse_id=self.create_dummy_id(),
            name=self.create_dummy_name(),
            bracket_num=1,
            horse_num=self._dummy_id_counter,
            jockey=self.create_dummy_jockey(),
            horse_weight=self.create_random_horse_weight(),
            weight_carried=self.create_random_weight_carried(),
            base_speed=self.create_random_base_speed(),
            base_min_speed=self.create_random_base_min_speed(),
            cruise_speed=self.create_random_cruise_speed(),
            last_3f_speed=self.create_random_last_3f_speed(),
            min_speed=self.create_random_min_speed(),
            acceleration=self.create_random_acceleration(),
            total_stamina=self.create_random_total_stamina(),
            stamina_waste_rate=self.create_random_stamina_waste_rate(),
            cornering_ability=self.create_random_corner_ability(),
            gate_reaction=self.create_random_gate_reaction(),
            stability_factor=self.create_random_stability_factor(),
            strategy=self.create_random_strategy(),
            target_spurt_dist=self.create_random_target_spurt_dist(),
        )
        
    def create_dummy_id(self) -> str:
        """シミュレーション用：'D'から始まる10桁の連番IDを生成"""
        new_id = f"D{str(self._dummy_id_counter).zfill(9)}"
        self._dummy_id_counter += 1
        return new_id
    
    def create_dummy_name(self) -> str:
        """ダミーネームを生成"""
        return f"ダミー馬{str(self._dummy_id_counter - 1).zfill(2)}"
    
    def create_dummy_jockey(self) -> str:
        """ダミージョッキー生成"""
        return f"ダミー機種{str(self._dummy_id_counter - 1).zfill(2)}"
    
    def create_random_horse_weight(self) -> float:
        return random.uniform(DEBUG_HORSE_ABILITY_MIN_MAX[HorseProfField.HORSE_WEIGHT.value][0],
                              DEBUG_HORSE_ABILITY_MIN_MAX[HorseProfField.HORSE_WEIGHT.value][1])
    
    def create_random_weight_carried(self) -> float:
        weights = [51.0, 52.0, 53.0, 54.0, 55.0, 56.0, 57.0, 58.0]
        return weights[random.randint(0, len(weights) - 1)]
    
    def create_random_base_speed(self) -> float:
        return random.uniform(DEBUG_HORSE_ABILITY_MIN_MAX[HorseProfField.BASE_SPEED][0],
                              DEBUG_HORSE_ABILITY_MIN_MAX[HorseProfField.BASE_SPEED][1])

    def create_random_stability_factor(self) -> float:
        return random.uniform(DEBUG_HORSE_ABILITY_MIN_MAX[HorseProfField.STABILITY_FACTOR][0],
                              DEBUG_HORSE_ABILITY_MIN_MAX[HorseProfField.STABILITY_FACTOR][1])

    def create_random_base_spurt_speed(self) -> float:
        return random.uniform(DEBUG_HORSE_ABILITY_MIN_MAX[HorseProfField.BASE_SPURT_SPEED][0],
                              DEBUG_HORSE_ABILITY_MIN_MAX[HorseProfField.BASE_SPURT_SPEED][1])

    def create_random_cruise_speed(self) -> float:
        return random.uniform(DEBUG_HORSE_ABILITY_MIN_MAX[HorseProfField.CRUISE_SPEED][0],
                              DEBUG_HORSE_ABILITY_MIN_MAX[HorseProfField.CRUISE_SPEED][1])

    def create_random_last_3f_speed(self) -> float:
        return random.uniform(DEBUG_HORSE_ABILITY_MIN_MAX[HorseProfField.LAST_3F_SPEED][0],
                              DEBUG_HORSE_ABILITY_MIN_MAX[HorseProfField.LAST_3F_SPEED][1])

    def create_random_min_speed(self) -> float:
        return random.uniform(DEBUG_HORSE_ABILITY_MIN_MAX[HorseProfField.MIN_SPEED.value][0],
                              DEBUG_HORSE_ABILITY_MIN_MAX[HorseProfField.MIN_SPEED.value][1])

    def create_random_acceleration(self) -> float:
        return random.uniform(DEBUG_HORSE_ABILITY_MIN_MAX[HorseProfField.ACCELERATION.value][0],
                              DEBUG_HORSE_ABILITY_MIN_MAX[HorseProfField.ACCELERATION.value][1])

    def create_random_total_stamina(self) -> float:
        return random.uniform(DEBUG_HORSE_ABILITY_MIN_MAX[HorseProfField.TOTAL_STAMINA.value][0],
                              DEBUG_HORSE_ABILITY_MIN_MAX[HorseProfField.TOTAL_STAMINA.value][1])

    def create_random_stamina_waste_rate(self) -> float:
        return random.uniform(DEBUG_HORSE_ABILITY_MIN_MAX[HorseProfField.STAMINA_WASTE_RATE.value][0],
                              DEBUG_HORSE_ABILITY_MIN_MAX[HorseProfField.STAMINA_WASTE_RATE.value][1])

    def create_random_corner_ability(self) -> float:
        return random.uniform(DEBUG_HORSE_ABILITY_MIN_MAX[HorseProfField.CORNER_ABILITY.value][0],
                              DEBUG_HORSE_ABILITY_MIN_MAX[HorseProfField.CORNER_ABILITY.value][1])

    def create_random_gate_reaction(self) -> float:
        return random.uniform(DEBUG_HORSE_ABILITY_MIN_MAX[HorseProfField.GATE_REACTION.value][0],
                              DEBUG_HORSE_ABILITY_MIN_MAX[HorseProfField.GATE_REACTION.value][1])

    def create_random_strategy(self) -> str:
        strategy_num = random.randint(0, 4)
        if strategy_num == 0:
            return HorseStrategyType.LEADER.value
        elif strategy_num == 1:
            return HorseStrategyType.STALKER.value
        elif strategy_num == 2:
            return HorseStrategyType.CLOSER.value
        else:
            return HorseStrategyType.REAR.value
    
    def create_random_target_spurt_dist(self) -> float:
        return random.uniform(DEBUG_HORSE_ABILITY_MIN_MAX[HorseProfField.TARGET_SPURT_DIST.value][0],
                              DEBUG_HORSE_ABILITY_MIN_MAX[HorseProfField.TARGET_SPURT_DIST.value][1])
