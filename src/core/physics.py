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

def calculate_interpolate_goal_time(pre_dist: float, post_dist: float, pre_time: float, dt: float, goal_dist: float) -> float:
    """
    ゴールラインを跨いだ瞬間の推定タイムを計算する。
    
    Args:
        pre_dist: ゴール直前の距離 (m)
        post_dist: ゴール直後の距離 (m)
        pre_time: ゴール直前の経過時間 (s)
        dt: タイムステップ (s)
        goal_dist: コース全長 (m)
    """
    # このステップで進んだ距離
    step_distance = post_dist - pre_dist
    
    # ゴールラインまでの距離
    distance_to_goal = goal_dist - pre_dist
    
    # 進んだ距離のうち、ゴールまでに費やした割合
    ratio = distance_to_goal / step_distance
    
    # 推定タイム
    return pre_time + (dt * ratio)


# ---------------------------------------------------------
# 速度系
# ---------------------------------------------------------
def calculate_actual_acceleration(next_velocity: float, current_velocity: float) -> float:
    """実際の加速度を算出"""
    return next_velocity - current_velocity
