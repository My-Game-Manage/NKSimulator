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
import src.core.physics as ph

# スタミナ消費調整用の定数
STAMINA_DRAIN_COEFFICIENT = 0.075

# ---------------------------------------------------------
# Strategy（Protocol）パターンの基底クラス
# ---------------------------------------------------------
class RacingStrategy(Protocol):
    def get_cruise_speed(self, horse_prof: HorseProfile) -> float:
        ...

    def get_spurt_speed(self, horse_prof: HorseProfile) -> float:
        ...

# ---------------------------------------------------------
# 具象Strategyクラス：逃げ
# ---------------------------------------------------------
class LeaderStrategy:
    def get_cruise_speed(self, horse_prof: HorseProfile) -> float:
        return horse_prof.cruise_speed * 1.02
    
    def get_spurt_speed(self, horse_prof: HorseProfile) -> float:
        return horse_prof.last_3f_speed * 0.96

# ---------------------------------------------------------
# 具象Strategyクラス：先行
# ---------------------------------------------------------
class StalkerStrategy:
    def get_cruise_speed(self, horse_prof: HorseProfile) -> float:
        return horse_prof.cruise_speed * 1.0

    def get_spurt_speed(self, horse_prof: HorseProfile) -> float:
        return horse_prof.last_3f_speed * 0.98

# ---------------------------------------------------------
# 具象Strategyクラス：差し
# ---------------------------------------------------------
class CloserStrategy:
    def get_cruise_speed(self, horse_prof: HorseProfile) -> float:
        return horse_prof.cruise_speed * 0.98

    def get_spurt_speed(self, horse_prof: HorseProfile) -> float:
        return horse_prof.last_3f_speed * 1.02

# ---------------------------------------------------------
# 具象Strategyクラス：追い込み
# ---------------------------------------------------------
class RearStrategy:
    def get_cruise_speed(self, horse_prof: HorseProfile) -> float:
        return horse_prof.cruise_speed * 0.97

    def get_spurt_speed(self, horse_prof: HorseProfile) -> float:
        return horse_prof.last_3f_speed * 1.05

# クラス取得用のMap
STRATEGY_MAP = {
    HorseStrategyType.LEADER: LeaderStrategy(),
    HorseStrategyType.STALKER: StalkerStrategy(),
    HorseStrategyType.CLOSER: CloserStrategy(),
    HorseStrategyType.REAR: RearStrategy(),
}
