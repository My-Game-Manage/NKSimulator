"""
race_logics.py の概要

レース中の馬の挙動についてのロジックを定義。
"""
import math
import logging

# ロガーの取得（__name__ はファイル名/モジュール名になる）
logger = logging.getLogger(__name__)

from src.models.race_data import RaceProfile
from src.models.track_data import TrackSection
from src.models.horse_data import HorseProfile, HorseSnapshot, HorseEnvironment, HorseTactics, HorseParam, DistContext
from src.constants.enums import RaceStrategyDecision, RaceSurfaceType, HorseStrategyType
from src.constants.fields import DistCtxField

from src.constants.constants import (
    HORSE_BASE_LENGTH,
    DIST_TO_FRONT_MAX, DIST_FRONT_RANGE, DIST_RIGHT_IN_FRONT, DIST_DIAGONALLY_IN_FRONT, DIST_BESIDE_RANGE, DIST_BESIDE_RANGE_MIN,
    RELEVANT_DIST_AREA, RELEVANT_DIST_JUST_FRONT, RELEVANT_DIST_AROUND_FRONT, RELEVANT_DIST_BESIDE,
    BASE_LANE_MOVE_SPEED,
)

import src.core.physics as ph


# ---------------------------------------------------------
# チェック系
# ---------------------------------------------------------
def is_out_gate(next_distance: float) -> bool:
    """ゲートを出たかどうかの判断"""
    return next_distance >= HORSE_BASE_LENGTH

def is_horse_finished(distance: float, course_length: float) -> bool:
    """ゴールしたか判定"""
    return distance >= course_length


# ---------------------------------------------------------
# 取得系
# ---------------------------------------------------------
def get_current_section(current_distance: float, sections: list[TrackSection]) -> TrackSection:
    """現在の距離から該当するセクション情報を返す"""
    for section in sections:
        if section.start_at <= current_distance < (section.start_at + section.distance):
            return section
    return sections[-1]

def get_dist_context(horse_id: str, horses: dict[HorseSnapshot]) -> DistContext:
    """周囲の馬との距離を返す"""
    current = horses[horse_id]
    context = {
        DistCtxField.DIST_TO_FRONT: DIST_TO_FRONT_MAX,
        DistCtxField.DIST_TO_FRONT_LEFT: DIST_TO_FRONT_MAX,
        DistCtxField.DIST_TO_FRONT_RIGHT: DIST_TO_FRONT_MAX,
        DistCtxField.DIST_TO_SIDE_LEFT: DIST_TO_FRONT_MAX,
        DistCtxField.DIST_TO_SIDE_RIGHT: DIST_TO_FRONT_MAX,
    }
    
    for h_id, other in horses.items():
        if horse_id == h_id: continue
        
        d_dist = other.distance - current.distance
        d_lane = other.lane - current.lane
        
        # 前方 (距離 10m 以内を対象にするなど)
        if 0 < d_dist < DIST_FRONT_RANGE:
            if abs(d_lane) < DIST_RIGHT_IN_FRONT: # 真前
                context[DistCtxField.DIST_TO_FRONT] = min(context[DistCtxField.DIST_TO_FRONT], d_dist)
            elif -DIST_DIAGONALLY_IN_FRONT < d_lane <= -DIST_RIGHT_IN_FRONT: # 左斜め前
                context[DistCtxField.DIST_TO_FRONT_LEFT] = min(context[DistCtxField.DIST_TO_FRONT_LEFT], d_dist)
            elif DIST_RIGHT_IN_FRONT <= d_lane < DIST_DIAGONALLY_IN_FRONT: # 右斜め前
                context[DistCtxField.DIST_TO_FRONT_RIGHT] = min(context[DistCtxField.DIST_TO_FRONT_RIGHT], d_dist)
        
        # 真横 (並走状態の検知)
        if abs(d_dist) < DIST_BESIDE_RANGE:
            if -DIST_BESIDE_RANGE < d_lane < DIST_BESIDE_RANGE_MIN: context[DistCtxField.DIST_TO_SIDE_LEFT] = min(context[DistCtxField.DIST_TO_SIDE_LEFT], abs(d_lane))
            if DIST_BESIDE_RANGE_MIN < d_lane < DIST_BESIDE_RANGE: context[DistCtxField.DIST_TO_SIDE_RIGHT] = min(context[DistCtxField.DIST_TO_SIDE_RIGHT], abs(d_lane))
            
    return DistContext(
        dist_to_front=context[DistCtxField.DIST_TO_FRONT],
        dist_to_front_left=context[DistCtxField.DIST_TO_FRONT_LEFT],
        dist_to_front_right=context[DistCtxField.DIST_TO_FRONT_RIGHT],
        dist_to_beside_left=context[DistCtxField.DIST_TO_SIDE_LEFT],
        dist_to_beside_right=context[DistCtxField.DIST_TO_SIDE_RIGHT],
    )

def get_friction_factor(race_prof: RaceProfile) -> float:
    """現在のコースのFriction係数を取得"""
    return race_prof.surface_friction if race_prof.surface == RaceSurfaceType.DIRT else race_prof.turf_friction

def get_target_lane(horse_prof: HorseProfile, horse_snap: HorseSnapshot, env: HorseEnvironment) -> float:
    """目標レーンの取得"""
    # 情報取得
    ctx = env.dist_context

    # スタートから5秒まではレーン移動しない
    if horse_snap.elapsed_time < 5.0: return horse_snap.lane
    
    # 候補となるレーン: [現在のレーン, 左に移動, 右に移動]
    # 0.5刻みなどで計算するとよりスムーズ
    options = [horse_snap.lane - 0.5, horse_snap.lane, horse_snap.lane + 0.5]
    lane_scores = {}

    for opt in options:
        if opt < 1.0 or opt > 18.0: continue # コース外
        
        score = 0.0
        
        # 1. 基本コスト: 内側ほどわずかに有利
        score += opt * 0.1
        
        # 2. 前方の詰まりによるペナルティ
        # そのレーンの「前方」に馬がいる場合
        d_lane_opt = opt - horse_snap.lane
        
        relevant_dist = 999.0
        if abs(d_lane_opt) < RELEVANT_DIST_AREA: relevant_dist = ctx.dist_to_front
        elif d_lane_opt < -RELEVANT_DIST_AREA:  relevant_dist = ctx.dist_to_front_left
        elif d_lane_opt > RELEVANT_DIST_AREA:   relevant_dist = ctx.dist_to_front_right
        
        if relevant_dist < RELEVANT_DIST_JUST_FRONT:
            score += 20.0 # 衝突回避（最優先）
        elif relevant_dist < RELEVANT_DIST_AROUND_FRONT:
            score += 5.0  # 少し詰まっている
            
        # 3. 横に馬がいる場合の移動制限
        if d_lane_opt < 0 and ctx.dist_to_beside_left < RELEVANT_DIST_BESIDE:
            score += 15.0 # 左に馬がいるので移動しにくい
        if d_lane_opt > 0 and ctx.dist_to_beside_right < RELEVANT_DIST_BESIDE:
            score += 15.0 # 右に馬がいるので移動しにくい
            
        # 4. 脚質(strategy)による補正 (ポンペルモ等の分析を反映)
        if horse_prof.strategy == HorseStrategyType.LEADER and opt > 2.0:
            score += 10.0 # 逃げ馬は外に行きたがらない
            
        lane_scores[opt] = score

    # 最もスコアの低い（快適な）レーンをターゲットにする
    target_lane = min(lane_scores, key=lane_scores.get)

    return target_lane

def get_race_strategy_decision(horse_prof: HorseProfile, current_snap: HorseSnapshot, env: HorseEnvironment) -> RaceStrategyDecision:
    """馬の行動戦略を返す"""
    return RaceStrategyDecision.KEEP_PACE

def get_target_velocity(horse_prof: HorseProfile, current_snap: HorseSnapshot, env: HorseEnvironment, tac: HorseTactics) -> float:
    """目標速度を取得"""
    # 情報取得
    base_v = tac.target_velocity

    # TODO: 状況によって目標速度を補正

    return base_v

def get_acceleration(target_v: float, horse_prof: HorseProfile, horse_snap: HorseSnapshot, env: HorseEnvironment, tac: HorseTactics) -> float:
    """加速力を取得"""
    # 情報取得
    accel_power = tac.accel_power

    return accel_power

def get_next_velocity(target_v: float, accel_power: float, horse_prof: HorseProfile, horse_snap: HorseSnapshot, env: HorseEnvironment, tac: HorseTactics, dt: float) -> float:
    """次のstepの速度を取得"""
    # 情報取得
    current_v = horse_snap.velocity

    # 加速、または減速
    if current_v < target_v:
        return min(current_v + accel_power * dt, target_v)
    elif current_v > target_v:
        # 減速時は今のところ一定、あるいは同様に減衰させても良い
        return max(current_v - accel_power * dt, target_v)
    else:
        # TODO: 速度維持の個体差をつける
        return current_v

def get_next_distance(next_velocity: float, horse_prof: HorseProfile, horse_snap: HorseSnapshot, env: HorseEnvironment, dt: float) -> float:
    """次のstepの距離を取得"""

    # 基本： v_avg = (current_v + next_v) / 2 ※台形近似式
    v_avg = (horse_snap.velocity + next_velocity) / 2
    next_distance = v_avg * dt

    return horse_snap.distance + next_distance

def get_next_stamina(next_velocity: float, horse_prof: HorseProfile, horse_snap: HorseSnapshot, env: HorseEnvironment, tac: HorseTactics, dt: float) -> float:
    """次のstepの体力を取得"""
    consumption = get_consumption_stamina(next_velocity, horse_prof, horse_snap, env, tac, dt)

    return max(0.0, horse_snap.stamina - consumption)

def get_consumption_stamina(next_velocity: float, horse_prof: HorseProfile, horse_snap: HorseSnapshot, env: HorseEnvironment, tac: HorseTactics, dt: float) -> float:
    """スタミナ消費量を取得"""
    # 速度の2乗をベースにする（空気抵抗や筋肉への負荷を表現）
    base_consumption = next_velocity ** 2
    
    # 1ステップあたりの消費量
    consumption = base_consumption * horse_prof.stamina_waste_rate

    return consumption

def get_next_lane(horse_prof: HorseProfile, horse_snap: HorseSnapshot, env: HorseEnvironment, tac: HorseTactics, dt: float) -> float:
    """次のstepのlaneを取得"""
    # 情報取得
    target_lane = tac.target_lane

    # 移動量の計算
    base_lane_speed = BASE_LANE_MOVE_SPEED * horse_prof.cornering_ability * horse_prof.base_agility
    max_move = base_lane_speed * dt

    # 目標と現在地の差
    diff = target_lane - horse_snap.lane

    # 移動可能量だけ移動
    if abs(diff) <= max_move:
        return target_lane
    else:
        move_dir = 1 if diff > 0 else -1
        return horse_snap.lane + (move_dir * max_move)

def get_actual_accel(next_velocity: float, current_velocity: float) -> float:
    """次のstep時の加速を算出して返す"""
    return ph.calculate_actual_acceleration(next_velocity, current_velocity)


# ---------------------------------------------------------
# 生成系
# ---------------------------------------------------------
def init_laptimes(race_prof: RaceProfile) -> list:
    return [0.0 for i in range(race_prof.distance // 200)]

def init_checkpoint_ranks(race_prof: RaceProfile) -> list:
    return [0 for i in range(len(race_prof.checkpoints))]


# ---------------------------------------------------------
# 更新系
# ---------------------------------------------------------
def update_step(current_step: int) -> int:
    """stepを更新する"""
    return current_step + 1

def update_elapsed_time(current_elapsed_time: float, dt: float) -> float:
    """elapsed_timeを更新する"""
    return round(current_elapsed_time + dt, 2) # 浮動小数点の誤差防止
