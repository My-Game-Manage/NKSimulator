"""
demo_factory.py の概要

デモレース用のデータセットを作成する
"""
import logging
from dataclasses import replace

# ロガーの取得（__name__ はファイル名/モジュール名になる）
logger = logging.getLogger(__name__)


from src.services.factory.base import RaceFactory, HorseFactory

from src.constants.enums import RaceSurfaceType
from src.models.race_data import RaceInfo, RaceProfile, RaceSnapshot
from src.models.horse_data import HorseProfile, HorseSnapshot
from src.utils.utils import race_id_from, get_waku_ban, checkpoints_from_sections

from src.constants.course_master import TRACK_DATA


# ---------------------------------------------------------
# デモレース用の定数
# ---------------------------------------------------------
_DEMO_RACE_ID = race_id_from("10000101", "DEMO", 1)
_DEMO_RACE_NAME = "DEMO_RACE"
_DEMO_RACE_COURSE = "DEMO"
_DEMO_RACE_CONDITION = "良"
_DEMO_RACE_WEATHER = "晴"
_DEMO_RACE_TRACK_WIDTH = 20.0
_DEMO_RACE_CORNER_PENALTY = 0.5
_DEMO_RACE_CORNER_RADIUS = 100
_DEMO_RACE_TURF_FRICTION = 1.0
_DEMO_RACE_SURFACE_FRICTION = 1.0

_DEMO_COURSE_KEYS = {
    1600: "DEMO_1600",
}


# ---------------------------------------------------------
# デモ馬用の定数
# ---------------------------------------------------------
_DEMOHORSE_SEX = 0                      # 牡馬
_DEMOHORSE_AGE = 4                      # 年齢
_DEMOHORSE_WEIGHT = 450
_DEMOHORSE_WEIGHT_CARRIED = 55
_DEMOHORSE_START_SPEED = 13.0
_DEMOHORSE_CRUISE_SPEED = 15.5
_DEMOHORSE_SPURT_SPEED = 18.0
_DEMOHORSE_START_ACCEL = 2.8
_DEMOHORSE_CRUISE_ACCEL = 0.5
_DEMOHORSE_SPURT_ACCEL = 1.0
_DEMOHORSE_TOP_SPEED_POTENTIAL = 18.0
_DEMOHORSE_TOTAL_STAMINA = 1600.0
_DEMOHORSE_STAMINA_WASTE_RATE = 1.0
_DEMOHORSE_HEAVY_TRACK_APTITUDE = 1.0
_DEMOHORSE_WEIGHT_TOLERANCE = 1.0
_DEMOHORSE_DISTANCE_FLEXIBILITY = 0.9
_DEMOHORSE_CORNER_ABILITY = 0.9
_DEMOHORSE_GATE_REACTION = 0.1
_DEMOHORSE_STABILITY_FACTOR = 0.03
_DEMOHORSE_BASE_AGILITY = 1.5
_DEMOHORSE_LANE_CHANGE_FREQUENCY = 0.1
_DEMOHORSE_PREFERS_INSIDE = 0.5
_DEMOHORSE_PACE_SWITCHING_AGILITY = 1.0
_DEMOHORSE_COURSE_CORNERING_EFFICIENCY = 1.0
_DEMOHORSE_STRATEGY = 1
_DEMOHORSE_PACING_STRATEGY_BIAS = 0.2
_DEMOHORSE_GRIT_FACTOR = 1.0
_DEMOHORSE_MENTAL_STABILITY = 1.0
_DEMOHORSE_SPURT_TRIGGER_DISTANCE = 400
_DEMOHORSE_SPURT_TRIGGER_TYPE = 0


# ---------------------------------------------------------
# デモレース作成クラス（DemoRaceFactory）
# ---------------------------------------------------------
class DemoRaceFactory(RaceFactory):
    """
    デモレース作成用
    """
    def __init__(self):
        super().__init__()
        # 馬作成用
        self.horse_factory = DemoHorseFactory()

    def create_races(self, **kwargs) -> list[RaceInfo]:
        logger.warning(f"デモレースでは1レースのみ作成できます")
        return [self.create_single_race(**kwargs)]
    
    def create_single_race(self, distance: int, surface: str, num_horses: int) -> RaceInfo:
        race_prof = self.create_race_profile(distance, surface, num_horses)
        horse_snaps = {h_id: self.horse_factory.create_horse_snapshot(h_id, h_prof.horse_num, h_prof.total_stamina, h_prof.strategy) for h_id, h_prof in race_prof.horses.items()}
        race_snap = self.create_race_snapshot(race_prof.race_id, horse_snaps)
        return RaceInfo(
            race_id=race_prof.race_id,
            profile=race_prof,
            snapshot=race_snap,
        )
    
    def create_race_profile(self, distance: int, surface: str, num_horses: int) -> RaceProfile:
        # デモコースの設定
        course = _DEMO_RACE_COURSE
        course_key = _DEMO_COURSE_KEYS[1600]
        sections = TRACK_DATA[course_key]
        # 指定数だけHorseProfile（初期値）の作成
        horses = {}
        for i in range(num_horses):
            h_prof = self.horse_factory.create_horse_profile(num_horses)
            horses[h_prof.horse_id] = h_prof
        return RaceProfile(
            race_id=_DEMO_RACE_ID,
            course=course,
            race_name=_DEMO_RACE_NAME,
            race_num=1,
            num_horses=num_horses,
            distance=distance,
            surface=RaceSurfaceType.from_str(surface),
            condition=_DEMO_RACE_CONDITION,
            weather=_DEMO_RACE_WEATHER,
            track_width=_DEMO_RACE_TRACK_WIDTH,
            corner_penalty=_DEMO_RACE_CORNER_PENALTY,
            corner_radius=_DEMO_RACE_CORNER_RADIUS,
            turf_friction=_DEMO_RACE_TURF_FRICTION,
            surface_friction=_DEMO_RACE_SURFACE_FRICTION,
            sections=sections,
            checkpoints=checkpoints_from_sections(sections),
            horses=horses,
        )
    
    def setup_race_profile(self, race_prof: RaceProfile, **kwargs) -> RaceProfile:
        """DEMOレース用に値を設定する"""
        # TODO: 設定する値やKeyが正しいかどうかチェックする
        logger.info(f"レース {race_prof.race_name} の値を次のように設定しました >> {kwargs}")
        return replace(race_prof, **kwargs)
    
    def update_race_info(self, race_info: RaceInfo, race_prof: RaceProfile) -> RaceInfo:
        """設定したProfileでInfoをUpdateする"""
        return replace(race_info, profile=race_prof)


# ---------------------------------------------------------
# デモ馬作成クラス（DemoHorseFactory）
# ---------------------------------------------------------
class DemoHorseFactory(HorseFactory):
    """
    デモ馬作成用
    """
    # ダミー用のID
    _dummy_id_counter = 1

    def create_horse_profile(self, num_horses: int) -> HorseProfile:
        horse_id = self._create_dummy_id()
        # 現在の馬番は self._dummy_id_counter - 1 になる
        current_num = self._dummy_id_counter - 1
        return HorseProfile(
            horse_id=horse_id,
            name=f"dummy_horse_{current_num}",
            bracket_num=get_waku_ban(current_num, num_horses),
            horse_num=current_num,
            jockey=f"dummy_jockey_{current_num}",
            sex=_DEMOHORSE_SEX,
            age=_DEMOHORSE_AGE,
            horse_weight=_DEMOHORSE_WEIGHT,
            weight_carried=_DEMOHORSE_WEIGHT_CARRIED,
            start_speed=_DEMOHORSE_START_SPEED,
            cruise_speed=_DEMOHORSE_CRUISE_SPEED,
            spurt_speed=_DEMOHORSE_SPURT_SPEED,
            start_acceleration=_DEMOHORSE_START_ACCEL,
            cruise_acceleration=_DEMOHORSE_CRUISE_ACCEL,
            spurt_acceleration=_DEMOHORSE_SPURT_ACCEL,
            top_speed_potential=_DEMOHORSE_TOP_SPEED_POTENTIAL,
            total_stamina=_DEMOHORSE_TOTAL_STAMINA,
            stamina_waste_rate=_DEMOHORSE_STAMINA_WASTE_RATE,
            heavy_track_aptitude=_DEMOHORSE_HEAVY_TRACK_APTITUDE,
            weight_tolerance=_DEMOHORSE_WEIGHT_TOLERANCE,
            distance_flexibility=_DEMOHORSE_DISTANCE_FLEXIBILITY,
            cornering_ability=_DEMOHORSE_CORNER_ABILITY,
            gate_reaction=_DEMOHORSE_GATE_REACTION,
            stability_factor=_DEMOHORSE_STABILITY_FACTOR,
            base_agility=_DEMOHORSE_BASE_AGILITY,
            lane_change_frequency=_DEMOHORSE_LANE_CHANGE_FREQUENCY,
            prefers_inside=_DEMOHORSE_PREFERS_INSIDE,
            pace_switching_agility=_DEMOHORSE_PACE_SWITCHING_AGILITY,
            course_cornering_efficiency=_DEMOHORSE_COURSE_CORNERING_EFFICIENCY,
            strategy=_DEMOHORSE_STRATEGY,
            pacing_strategy_bias=_DEMOHORSE_PACING_STRATEGY_BIAS,
            grit_factor=_DEMOHORSE_GRIT_FACTOR,
            mental_stability=_DEMOHORSE_MENTAL_STABILITY,
            spurt_trigger_distance=_DEMOHORSE_SPURT_TRIGGER_DISTANCE,
            spurt_trigger_type=_DEMOHORSE_SPURT_TRIGGER_TYPE,
        )
    
    def setup_horse_profile(self, horse_prof: HorseProfile, **kwargs) -> HorseProfile:
        """DEMO用に馬の能力値を設定する"""
        # TODO: 能力が範囲内かどうかチェックする機構を追加
        logger.info(f"馬 {horse_prof.name} の能力値を設定しました >> {kwargs}")
        return replace(horse_prof, **kwargs)

    def _create_dummy_id(self) -> str:
        """シミュレーション用：'D'から始まる10桁の連番IDを生成"""
        new_id = f"D{str(self._dummy_id_counter).zfill(9)}"
        self._dummy_id_counter += 1
        return new_id
