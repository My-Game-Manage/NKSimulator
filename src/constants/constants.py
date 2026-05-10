"""
constants.py の概要

各所で利用する定数を定義する。
"""
from src.constants.enums import TrackConditionType


# スタミナ消費調整用の定数
STAMINA_DRAIN_COEFFICIENT = 0.075

# 馬場コンディションの係数
TURF_CONDITION_ACCEL_FACTOR_MAP = {
    TrackConditionType.FIRM: 1.00,
    TrackConditionType.GOOD: 0.98,
    TrackConditionType.HEAVY: 0.95,
    TrackConditionType.MUDDY: 0.92,
}

DIRT_CONDITION_ACCEL_FACTOR_MAP = {
    TrackConditionType.FIRM: 1.00,
    TrackConditionType.GOOD: 1.02,
    TrackConditionType.HEAVY: 1.04,
    TrackConditionType.MUDDY: 1.06,
}

TURF_CONDITION_STAMINA_FACTOR_MAP = {
    TrackConditionType.FIRM: 1.00,
    TrackConditionType.GOOD: 1.05,
    TrackConditionType.HEAVY: 1.15,
    TrackConditionType.MUDDY: 1.25,
}

DIRT_CONDITION_STAMINA_FACTOR_MAP = {
    TrackConditionType.FIRM: 1.00,
    TrackConditionType.GOOD: 0.98,
    TrackConditionType.HEAVY: 0.96,
    TrackConditionType.MUDDY: 0.94,
}
