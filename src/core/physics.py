"""
physics.py の概要

物理演算を担う。
"""
import logging

# ロガーの取得（__name__ はファイル名/モジュール名になる）
logger = logging.getLogger(__name__)



# ---------------------------------------------------------
# 速度系
# ---------------------------------------------------------
def calculate_actual_acceleration(next_velocity: float, current_velocity: float) -> float:
    """実際の加速度を算出"""
    return next_velocity - current_velocity
