"""
strategy.py の概要

脚質に応じたStrategy（Protocol）を提供する特殊クラス群
"""
from typing import Protocol

from src.constants.enums import HorseStrategyType
from src.models.horse_data import HorseProfile, HorseSnapshot


# ---------------------------------------------------------
# Strategy（Protocol）パターンの基底クラス
# ---------------------------------------------------------
class RacingStrategy(Protocol):
    def get_target_velocity(self, horse_prof: HorseProfile, horse_snap: HorseSnapshot) -> float:
        ...

    def get_acceleration(self, target_v: float, horse_prof: HorseProfile, horse_snap: HorseSnapshot) -> float:
        ...


# ---------------------------------------------------------
# 具象Strategyクラス：逃げ
# ---------------------------------------------------------
class LeaderStrategy:
    def get_target_velocity(self, horse_prof: HorseProfile, horse_snap: HorseSnapshot) -> float:
        target_v = horse_prof.max_speed
        return target_v

    def get_acceleration(self, target_v: float, horse_prof: HorseProfile, horse_snap: HorseSnapshot) -> float:
        diff_v = target_v - horse_snap.velocity
        return diff_v * horse_prof.acceleration

# ---------------------------------------------------------
# 具象Strategyクラス：先行
# ---------------------------------------------------------
class StalkerStrategy:
    def get_target_velocity(self, horse_prof: HorseProfile, horse_snap: HorseSnapshot) -> float:
        target_v = horse_prof.max_speed
        return target_v
    
    def get_acceleration(self, target_v: float, horse_prof: HorseProfile, horse_snap: HorseSnapshot) -> float:
        diff_v = target_v - horse_snap.velocity
        return diff_v * horse_prof.acceleration


# ---------------------------------------------------------
# 具象Strategyクラス：差し
# ---------------------------------------------------------
class CloserStrategy:
    def get_target_velocity(self, horse_prof: HorseProfile, horse_snap: HorseSnapshot) -> float:
        target_v = horse_prof.max_speed
        return target_v
    
    def get_acceleration(self, target_v: float, horse_prof: HorseProfile, horse_snap: HorseSnapshot) -> float:
        diff_v = target_v - horse_snap.velocity
        return diff_v * horse_prof.acceleration


# ---------------------------------------------------------
# 具象Strategyクラス：追い込み
# ---------------------------------------------------------
class RearStrategy:
    def get_target_velocity(self, horse_prof: HorseProfile, horse_snap: HorseSnapshot) -> float:
        target_v = horse_prof.max_speed
        return target_v
    
    def get_acceleration(self, target_v: float, horse_prof: HorseProfile, horse_snap: HorseSnapshot) -> float:
        diff_v = target_v - horse_snap.velocity
        return diff_v * horse_prof.acceleration


# クラス取得用のMap
STRATEGY_MAP = {
    HorseStrategyType.LEADER: LeaderStrategy(),
    HorseStrategyType.STALKER: StalkerStrategy(),
    HorseStrategyType.CLOSER: CloserStrategy(),
    HorseStrategyType.REAR: RearStrategy(),
}
