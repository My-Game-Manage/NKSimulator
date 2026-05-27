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
from src.constants.enums import RaceStrategyDecision, RaceSurfaceType, HorseStrategyType, SectionType, SectionName
from src.constants.fields import DistCtxField

from src.constants.constants import (
    HORSE_BASE_LENGTH,
    DIST_TO_FRONT_MAX, DIST_FRONT_RANGE, DIST_JUST_FRONT, DIST_DIAGONALLY_IN_FRONT, DIST_BESIDE_RANGE, DIST_BESIDE_RANGE_MIN,
    RELEVANT_DIST_AREA, RELEVANT_DIST_JUST_FRONT, RELEVANT_DIST_AROUND_FRONT, RELEVANT_DIST_BESIDE,
    BASE_LANE_MOVE_SPEED,
    STAMINA_DRAIN_COEFFICIENT,
    TARGET_V_IN_CORNER_FACTOR,
    DIRT_CONDITION_ACCEL_FACTOR_MAP, TURF_CONDITION_ACCEL_FACTOR_MAP,
    DISTANCE_LANE_FACTOR,
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

def is_horse_exhausted(total_stamina: float, next_stamina: float) -> bool:
    """バテたかどうか判定"""
    # 最大値の99%に設定
    return next_stamina <= (total_stamina * 0.01)

def is_start_section(distance: float, first_section: TrackSection) -> bool:
    """スタートセクションかどうか"""
    return distance <= first_section.distance

def is_readed_cruise_speed(current_v: float, cruise_speed: float) -> bool:
    """巡航速度に達したかどうか"""
    return current_v >= cruise_speed

def is_sorrounded_horses(dist_context: DistContext) -> bool:
    """囲まれているかどうか"""
    relevant_dist = min(dist_context.dist_to_front, dist_context.dist_to_front_left, dist_context.dist_to_front_right)
    if relevant_dist < 3.0:
        # 前方（左右合わせて）が塞がっている
        if dist_context.dist_to_side_left < 1.0 and dist_context.dist_to_side_right < 1.0:
            return True
    return False

def is_head_of_lane(dist_context: DistContext) -> bool:
    """レーンの先頭かどうか"""
    return dist_context.dist_to_front >= DIST_TO_FRONT_MAX

def is_second_of_lanes(dist_context: DistContext) -> bool:
    """レーン（前方少し広く取る）の番手かどうか"""
    relevant_dist = min(dist_context.dist_to_front, dist_context.dist_to_front_left, dist_context.dist_to_front_right)
    return relevant_dist < 3.0 

# ---------------------------------------------------------
# 取得系
# ---------------------------------------------------------
def get_current_section(current_distance: float, sections: list[TrackSection]) -> int:
    """現在の距離から該当するセクション情報を返す"""
    index = 0
    for section in sections:
        if section.start_at <= current_distance < (section.start_at + section.distance):
            return index
        index += 1
    return len(sections) - 1

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
            if abs(d_lane) < DIST_JUST_FRONT: # 真前
                context[DistCtxField.DIST_TO_FRONT] = min(context[DistCtxField.DIST_TO_FRONT], d_dist)
            elif -DIST_DIAGONALLY_IN_FRONT < d_lane <= -DIST_JUST_FRONT: # 左斜め前
                context[DistCtxField.DIST_TO_FRONT_LEFT] = min(context[DistCtxField.DIST_TO_FRONT_LEFT], d_dist)
            elif DIST_JUST_FRONT <= d_lane < DIST_DIAGONALLY_IN_FRONT: # 右斜め前
                context[DistCtxField.DIST_TO_FRONT_RIGHT] = min(context[DistCtxField.DIST_TO_FRONT_RIGHT], d_dist)
        
        # 真横 (並走状態の検知)
        if abs(d_dist) < DIST_BESIDE_RANGE:
            if -DIST_BESIDE_RANGE < d_lane < DIST_BESIDE_RANGE_MIN: context[DistCtxField.DIST_TO_SIDE_LEFT] = min(context[DistCtxField.DIST_TO_SIDE_LEFT], abs(d_lane))
            if DIST_BESIDE_RANGE_MIN < d_lane < DIST_BESIDE_RANGE: context[DistCtxField.DIST_TO_SIDE_RIGHT] = min(context[DistCtxField.DIST_TO_SIDE_RIGHT], abs(d_lane))
            
    return DistContext(
        dist_to_front=context[DistCtxField.DIST_TO_FRONT],
        dist_to_front_left=context[DistCtxField.DIST_TO_FRONT_LEFT],
        dist_to_front_right=context[DistCtxField.DIST_TO_FRONT_RIGHT],
        dist_to_side_left=context[DistCtxField.DIST_TO_SIDE_LEFT],
        dist_to_side_right=context[DistCtxField.DIST_TO_SIDE_RIGHT],
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
        if d_lane_opt < 0 and ctx.dist_to_side_left < RELEVANT_DIST_BESIDE:
            score += 15.0 # 左に馬がいるので移動しにくい
        if d_lane_opt > 0 and ctx.dist_to_side_right < RELEVANT_DIST_BESIDE:
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
    # TODO: スコアにより戦略を変える。共通スコアと、脚質による個別スコアで構成
    # 自分の位置はどれくらいか？
    # 前に馬がいる？
    # 左右に馬がいる？
    # 囲まれている？
    return RaceStrategyDecision.KEEP_PACE

def get_target_velocity(horse_prof: HorseProfile, current_snap: HorseSnapshot, race_prof: RaceProfile, env: HorseEnvironment, tac: HorseTactics) -> float:
    """目標速度を取得"""
    # 情報取得
    base_v = tac.target_velocity
    section = race_prof.sections[env.section]

    # TODO: 状況によって目標速度を補正

    # コーナー補正
    if section.type == SectionType.CURVE:
        base_v *= TARGET_V_IN_CORNER_FACTOR
        base_v = ph.calculate_target_velocity_at_corner(base_v, race_prof.corner_radius, current_snap.lane, horse_prof.base_agility)

    return base_v

def get_acceleration(target_v: float, horse_prof: HorseProfile, horse_snap: HorseSnapshot, env: HorseEnvironment, tac: HorseTactics) -> float:
    """加速力を取得"""
    # 情報取得
    accel_power = tac.accel_power
    surface = env.surface
    condition = env.condition
    current_v = horse_snap.velocity
    start_speed = horse_prof.start_speed

    # 種別による補正
    friction_factor = 1.0 - env.friction

    # 馬場状態による補正
    condition_factor = DIRT_CONDITION_ACCEL_FACTOR_MAP[condition] if surface == RaceSurfaceType.DIRT else TURF_CONDITION_ACCEL_FACTOR_MAP[condition]

    # 速度差による加速減衰（スタート速度までは減衰なし）
    adjusted_ratio = ph.get_dumping_accel_rate(target_v, current_v) if target_v >= start_speed else 1.0

    # 斤量補正
    weight_penalty_raito = ph.get_accel_weight_carried_factor(horse_prof.weight_carried)

    # 補正をまとめる
    correction_factors = (
        friction_factor * condition_factor * weight_penalty_raito
    )

    # 補正係数による加速
    accel = accel_power * correction_factors

    # 実際の加速度を算出
    actual_accel = accel * max(0.2, adjusted_ratio)

    return actual_accel

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
    # 情報取得

    # レーン補正（5秒までは補正しない）
    lane_factor = 0.0
    if horse_snap.elapsed_time >= 5.0:
        lane_factor = horse_snap.lane * DISTANCE_LANE_FACTOR
    
    actual_next_v = next_velocity - lane_factor
    # 基本： v_avg = (current_v + next_v) / 2 ※台形近似式
    v_avg = ph.get_trapezoidal_approximate_value(horse_snap.velocity, actual_next_v)

    # 移動距離
    move_distance = v_avg * dt

    return horse_snap.distance + move_distance

def get_next_stamina(next_velocity: float, horse_prof: HorseProfile, horse_snap: HorseSnapshot, env: HorseEnvironment, tac: HorseTactics, dt: float) -> float:
    """次のstepの体力を取得"""
    consumption = get_consumption_stamina(next_velocity, horse_prof, horse_snap, env, tac, dt)

    return max(0.0, horse_snap.stamina - consumption)

def get_consumption_stamina(next_velocity: float, horse_prof: HorseProfile, horse_snap: HorseSnapshot, env: HorseEnvironment, tac: HorseTactics, dt: float) -> float:
    """スタミナ消費量を取得"""
    # 速度の2乗をベースにする（空気抵抗や筋肉への負荷を表現）
    base_consumption = next_velocity ** 2

    # 斤量補正（50kgを基準とした補正）
    weight_factor = ph.get_stamina_weight_carried_factor(horse_prof.weight_carried)

    # 囲まれている（前にいても左右もいる時）場合、消費が増える
    sorrounded_factor = 1.05 if is_sorrounded_horses(env.dist_context) else 1.0

    # 列の先頭の場合、消費が増える
    wind_factor = 1.1 if is_head_of_lane(env.dist_context) else 1.0
    # 前に馬がいると消費が抑えられる
    if is_second_of_lanes(env.dist_context):
        wind_factor = 0.9
    
    # 補正をまとめる
    correction_factors = (
        weight_factor * sorrounded_factor * wind_factor
    )

    # 1ステップあたりの消費量
    consumption = base_consumption * horse_prof.stamina_waste_rate * STAMINA_DRAIN_COEFFICIENT * correction_factors * dt

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

def get_finish_time(next_distance: float, race_distance: float, horse_snap: HorseSnapshot, dt: float) -> float:
    """ゴールしたタイムを返す"""
    return ph.calculate_interpolate_goal_time(horse_snap.distance, next_distance, horse_snap.elapsed_time, dt, race_distance)


# ---------------------------------------------------------
# 判定系
# ---------------------------------------------------------
def should_start_spurting(next_distance: float, race_prof: RaceProfile, horse_prof: HorseProfile, horse_snap: HorseSnapshot, env: HorseEnvironment) -> bool:
    """スパート判定"""
    # 情報取得
    total_distance = race_prof.distance
    section = race_prof.sections[horse_snap.section]

    # 残り距離
    remaining_dist = total_distance - next_distance

    # セクション判定：最後の直線ならスパート開始
    if section.name == SectionName.HOMESTRETCH: return True

    return remaining_dist <= horse_prof.spurt_trigger_distance


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
    return ph.calculate_next_step(current_step)

def update_elapsed_time(current_elapsed_time: float, dt: float) -> float:
    """elapsed_timeを更新する"""
    return ph.calculate_next_elapsed_time(current_elapsed_time, dt)
