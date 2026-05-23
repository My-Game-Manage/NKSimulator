"""
physics.py の概要

物理演算を担う。
"""
import logging

# ロガーの取得（__name__ はファイル名/モジュール名になる）
logger = logging.getLogger(__name__)


# ---------------------------------------------------------
# タイム系
# ---------------------------------------------------------
def calculate_next_step(current_step: int) -> int:
    """stepを更新する"""
    return current_step + 1

def calculate_next_elapsed_time(current_elapsed_time: float, dt: float) -> float:
    """elapsed_timeを更新する"""
    return round(current_elapsed_time + dt, 2) # 浮動小数点の誤差防止


# ---------------------------------------------------------
# 速度系
# ---------------------------------------------------------
def calculate_actual_acceleration(next_velocity: float, current_velocity: float) -> float:
    """実際の加速度を算出"""
    return next_velocity - current_velocity
