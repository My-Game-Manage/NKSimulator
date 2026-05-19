"""
base.py の概要

Factoryクラスの基底クラスを記述する。
"""
import logging

# ロガーの取得（__name__ はファイル名/モジュール名になる）
logger = logging.getLogger(__name__)

from abc import ABC, abstractmethod

from src.models.race_data import RaceInfo, RaceProfile, RaceSnapshot
from src.models.horse_data import HorseProfile, HorseSnapshot


# ---------------------------------------------------------
# 基底クラス（RaceFactory）
# ---------------------------------------------------------
class RaceFactory(ABC):
    """
    レース用のデータセットを作成する
    """
    @abstractmethod
    def create_races(self, **kwargs) -> list[RaceInfo]:
        ...

    @abstractmethod
    def create_single_race(self, **kwargs) -> RaceInfo:
        ...

    @abstractmethod
    def create_race_profile(self, **kwargs) -> RaceProfile:
        ...

    def create_race_snapshot(self, race_id: str, horses: dict[str, HorseSnapshot]) -> RaceSnapshot:
        """Snapshot（初期値）作成"""
        return RaceSnapshot(
            race_id=race_id,
            step=0,
            elapsed_time=0.0,
            horses=horses,
            ranks=self._get_init_ranks(horses),
        )
    
    def _get_init_ranks(self, horses: dict[str, HorseSnapshot]) -> dict[str, int]:
        """ランクの初期値を返す"""
        return {h_id: 1 for h_id in horses.keys()}


# ---------------------------------------------------------
# 基底クラス（HorseFactory）
# ---------------------------------------------------------
class HorseFactory(ABC):
    """
    馬のデータを作成する
    """
    @abstractmethod
    def create_horse_profile(self, **kwargs) -> HorseProfile:
        ...

    def create_horse_snapshot(self, horse_id: str, horse_num: int, strategy: int) -> HorseSnapshot:
        """Snapshot（初期値）作成"""
        return HorseSnapshot(
            horse_id=horse_id,
            step=0,
            elapsed_time=0.0,
            accel_power=0.0,
            accel=0.0,
            target_velocity=0.0,
            velocity=0.0,
            distance=0.0,
            stamina=0.0,
            target_lane=0.0,
            lane=float(horse_num),
            dist_to_front=0.0,
            dist_to_front_left=0.0,
            dist_to_front_right=0.0,
            dist_to_side_left=0.0,
            dist_to_side_right=0.0,
            section=0,
            behavior=0,
            strategy=strategy,
            is_finished=False,
            finish_time=None,
            last_3f=None,
            time_at_600m=None,
        )
