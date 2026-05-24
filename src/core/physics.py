"""
physics.py の概要

物理演算を担う。
"""
import logging
import math

# ロガーの取得（__name__ はファイル名/モジュール名になる）
logger = logging.getLogger(__name__)

from src.constants.constants import (
    LANE_WIDTH, RESIST_CORNER_GRAVITY, CORNER_SLOWDOWN_PERCENT,
)

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

def calculate_target_velocity_at_corner(target_v: float, radius: float, lane: float, agility: float) -> float:
    # laneが外に行くほど半径が大きくなる = 遠心力が弱まる
    effective_radius = radius + (lane * LANE_WIDTH) # 1レーン1mと仮定
    
    # 馬の器用さ(agility)に基づいた、耐えられる最大横G
    # 例: agility 1.0 の馬は 3.0 m/s^2 まで耐えられるとする
    max_lateral_accel = RESIST_CORNER_GRAVITY * agility 
    
    # 遠心力に耐えられる限界速度を算出 (v = sqrt(a * r))
    limit_velocity = math.sqrt(max_lateral_accel * effective_radius)
    
    # 現在の target_velocity が限界を超えていれば制限する
    # 一気に下げず、現在の速度から徐々に近づける（慣性の表現）
    if target_v > limit_velocity:
        target_v = max(limit_velocity, target_v * CORNER_SLOWDOWN_PERCENT)

    return target_v
