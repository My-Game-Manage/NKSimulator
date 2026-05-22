"""
demo_factory.py の概要

デモレース用のデータセットを作成する
"""
import logging

# ロガーの取得（__name__ はファイル名/モジュール名になる）
logger = logging.getLogger(__name__)


from src.services.factory.base import RaceFactory, HorseFactory

from src.constants.enums import RaceSurfaceType
from src.models.race_data import RaceInfo, RaceProfile, RaceSnapshot
from src.models.horse_data import HorseProfile, HorseSnapshot
from src.utils.utils import race_id_from


# ---------------------------------------------------------
# デモレース用の定数
# ---------------------------------------------------------
_DEMO_RACE_ID = race_id_from("10000101", "DEMO", 1)
_DEMO_RACE_NAME = "DEMO_RACE"

_DEMO_CORSES = {
    1600: "DEMO_1600",
}

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
        return RaceInfo()
    
    def create_race_profile(self, distance: int, surface: str, num_horses: int) -> RaceProfile:
        # デモコースの設定
        course = _DEMO_CORSES[1600]
        # 指定数だけHorseProfile（初期値）の作成
        horses = {}
        for i in num_horses:
            h_prof = self.horse_factory.create_horse_profile()
            horses[h_prof.horse_id] = h_prof
        return RaceProfile(
            race_id=_DEMO_RACE_ID,
            course=course,
            race_name=_DEMO_RACE_NAME,
            race_num=1,
            num_horses=num_horses,
            distance=distance,
            surface=RaceSurfaceType.from_str(surface),
            condition=0,
            weather=0,
            track_width=20.0,
            corner_penalty=1.0,
            corner_radius=100,
            turf_friction=1.0,
            surface_friction=1.0,
            sections=[],
            checkpoints=[],
            horses=horses,
        )

# ---------------------------------------------------------
# デモ馬作成クラス（DemoHorseFactory）
# ---------------------------------------------------------
class DemoHorseFactory(HorseFactory):
    """
    デモ馬作成用
    """
    # ダミー用のID
    _dummy_id_counter = 1

    def create_horse_profile(self, **kwargs) -> HorseProfile:
        horse_id = self.create_dummy_id()
        base_id = self._dummy_id_counter - 1
        return HorseProfile(
            horse_id=horse_id,
            name=f"dummy_horse_{base_id}",
            bracket_num=0,
            horse_num=base_id,
            jockey="",
            sex="",
            horse_weight=0,
            weight_carried=0,
            start_speed=1.0,
            cruise_speed=1.0,
            spurt_speed=1.0,
            start_acceleration=1.0,
            cruise_acceleration=1.0,
            spurt_acceleration=1.0,
            top_speed_potential=1.0,
            total_stamina=1600.0,
            stamina_waste_rate=1.0,
            heavy_track_aptitude=1.0,
            weight_tolerance=1.0,
            distance_flexibility=1.0,
            cornering_ability=1.0,
            gate_reaction=1.0,
            stability_factor=1.0,
            base_agility=1.0,
            lane_change_frequency=1.0,
            prefers_inside=1.0,
            pace_switching_agility=1.0,
            course_cornering_efficiency=1.0,
            strategy=0,
            pacing_strategy_bias=1.0,
            grit_factor=1.0,
            mental_stability=1.0,
        )

    def create_dummy_id(self) -> str:
        """シミュレーション用：'D'から始まる10桁の連番IDを生成"""
        new_id = f"D{str(self._dummy_id_counter).zfill(9)}"
        self._dummy_id_counter += 1
        return new_id
