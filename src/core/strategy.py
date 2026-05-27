"""
strategy.py の概要

脚質に応じたStrategy（Protocol）を提供する特殊クラス群
"""
from typing import Protocol

import logging

# ロガーの取得（__name__ はファイル名/モジュール名になる）
logger = logging.getLogger(__name__)

from src.constants.enums import HorseStrategyType, SectionType, SectionName
from src.constants.fields import HorseEnvField, HorseTacField
from src.models.horse_data import HorseProfile, HorseSnapshot
from src.models.race_data import TrackSection
from src.constants.constants import (
    CRUISE_SPEED_STYLE_FACTOR, START_SPEED_STYLE_FACTOR, SPURT_SPEED_STYLE_FACTOR,
)



# ---------------------------------------------------------
# Strategy（Protocol）パターンの基底クラス
# ---------------------------------------------------------
class RacingStrategy(Protocol):
    def get_start_speed(self, horse_prof: HorseProfile) -> float:
        ...

    def get_cruise_speed(self, horse_prof: HorseProfile) -> float:
        ...

    def get_spurt_speed(self, horse_prof: HorseProfile) -> float:
        ...

    def get_start_acceleration(self, horse_prof: HorseProfile) -> float:
        ...

    def get_spurt_acceleration(self, horse_prof: HorseProfile) -> float:
        ...

    def get_cruise_acceleration(self, horse_prof: HorseProfile) -> float:
        ...


# ---------------------------------------------------------
# 具象Strategyクラス：逃げ
# ---------------------------------------------------------
class LeaderStrategy:
    def get_start_speed(self, horse_prof: HorseProfile) -> float:
        return horse_prof.start_speed * START_SPEED_STYLE_FACTOR[HorseStrategyType.LEADER]
    
    def get_cruise_speed(self, horse_prof: HorseProfile) -> float:
        return horse_prof.cruise_speed * CRUISE_SPEED_STYLE_FACTOR[HorseStrategyType.LEADER]
    
    def get_spurt_speed(self, horse_prof: HorseProfile) -> float:
        return horse_prof.spurt_speed * CRUISE_SPEED_STYLE_FACTOR[HorseStrategyType.LEADER]

    def get_start_acceleration(self, horse_prof: HorseProfile) -> float:
        return horse_prof.start_acceleration
    
    def get_spurt_acceleration(self, horse_prof: HorseProfile) -> float:
        return horse_prof.spurt_acceleration
    
    def get_cruise_acceleration(self, horse_prof: HorseProfile) -> float:
        return horse_prof.cruise_acceleration


# ---------------------------------------------------------
# 具象Strategyクラス：先行
# ---------------------------------------------------------
class StalkerStrategy:
    def get_start_speed(self, horse_prof: HorseProfile) -> float:
        return horse_prof.start_speed * START_SPEED_STYLE_FACTOR[HorseStrategyType.STALKER]
    
    def get_cruise_speed(self, horse_prof: HorseProfile) -> float:
        return horse_prof.cruise_speed * CRUISE_SPEED_STYLE_FACTOR[HorseStrategyType.STALKER]

    def get_spurt_speed(self, horse_prof: HorseProfile) -> float:
        return horse_prof.spurt_speed * SPURT_SPEED_STYLE_FACTOR[HorseStrategyType.STALKER]

    def get_start_acceleration(self, horse_prof: HorseProfile) -> float:
        return horse_prof.start_acceleration
    
    def get_spurt_acceleration(self, horse_prof: HorseProfile) -> float:
        return horse_prof.spurt_acceleration
    
    def get_cruise_acceleration(self, horse_prof: HorseProfile) -> float:
        return horse_prof.cruise_acceleration


# ---------------------------------------------------------
# 具象Strategyクラス：差し
# ---------------------------------------------------------
class CloserStrategy:
    def get_start_speed(self, horse_prof: HorseProfile) -> float:
        return horse_prof.start_speed * START_SPEED_STYLE_FACTOR[HorseStrategyType.CLOSER]
    
    def get_cruise_speed(self, horse_prof: HorseProfile) -> float:
        return horse_prof.cruise_speed * CRUISE_SPEED_STYLE_FACTOR[HorseStrategyType.CLOSER]

    def get_spurt_speed(self, horse_prof: HorseProfile) -> float:
        return horse_prof.spurt_speed * SPURT_SPEED_STYLE_FACTOR[HorseStrategyType.CLOSER]

    def get_start_acceleration(self, horse_prof: HorseProfile) -> float:
        return horse_prof.start_acceleration
    
    def get_spurt_acceleration(self, horse_prof: HorseProfile) -> float:
        return horse_prof.spurt_acceleration
    
    def get_cruise_acceleration(self, horse_prof: HorseProfile) -> float:
        return horse_prof.cruise_acceleration


# ---------------------------------------------------------
# 具象Strategyクラス：追い込み
# ---------------------------------------------------------
class RearStrategy:
    def get_start_speed(self, horse_prof: HorseProfile) -> float:
        return horse_prof.start_speed * START_SPEED_STYLE_FACTOR[HorseStrategyType.REAR]
    
    def get_cruise_speed(self, horse_prof: HorseProfile) -> float:
        return horse_prof.cruise_speed * CRUISE_SPEED_STYLE_FACTOR[HorseStrategyType.REAR]

    def get_spurt_speed(self, horse_prof: HorseProfile) -> float:
        return horse_prof.spurt_speed * SPURT_SPEED_STYLE_FACTOR[HorseStrategyType.REAR]

    def get_start_acceleration(self, horse_prof: HorseProfile) -> float:
        return horse_prof.start_acceleration
    
    def get_spurt_acceleration(self, horse_prof: HorseProfile) -> float:
        return horse_prof.spurt_acceleration
    
    def get_cruise_acceleration(self, horse_prof: HorseProfile) -> float:
        return horse_prof.cruise_acceleration


# クラス取得用のMap
STRATEGY_MAP = {
    HorseStrategyType.LEADER: LeaderStrategy(),
    HorseStrategyType.STALKER: StalkerStrategy(),
    HorseStrategyType.CLOSER: CloserStrategy(),
    HorseStrategyType.REAR: RearStrategy(),
}
