"""
physics.py の概要

レースのシミュレートに関する物理演算を行う関数群。
"""
import math

from src.models.horse_data import HorseProfile, HorseSnapshot
from src.constants.enums import SectionName, RaceSurfaceType
from src.models.race_data import TrackSection
from src.constants.fields import HorseEnvField

from src.constants.constants import (
    EXHAUSTED_LIMIT_PERCENT,
    SAME_LANE_WIDTH, LANE_WIDTH,
    DIST_TO_FRONT_MAX, DIST_FRONT_RANGE, DIST_RIGHT_IN_FRONT, DIST_DIAGONALLY_IN_FRONT, DIST_BESIDE_RANGE,
    RESIST_CORNER_GRAVITY, CORNER_SLOWDOWN_PERCENT,
    RACE_TIME_AVERAGE_MAP, TURF_TIME_ADJUST, DIRT_TIME_ADJUST,
)


# チェック系
def is_horse_finished(distance: float, course_length: float) -> bool:
    """コースの距離と現在の距離を比較してゴールしたかどうかを返す"""
    return distance >= course_length

def is_spurt_distance(distance: float, spurt_dist: float, race_distance: float) -> bool:
    """スパート開始距離かどうかの判定"""
    return distance >= (race_distance - spurt_dist)

def is_start_section(distance: float, section: TrackSection) -> bool:
    """スタートセクションかどうか"""
    return distance >= section.distance

def is_exhausted(remain_stamina: float, total_stamina: float) -> bool:
    """バテ状態かどうか判定する"""
    # 95%をバテの閾値とする
    return remain_stamina < total_stamina * EXHAUSTED_LIMIT_PERCENT


# 要素取得系
def get_dist_to_front(horse_id: str, horses: dict[str, HorseSnapshot]) -> float:
    """前の馬との距離を返す"""
    min_dist = DIST_TO_FRONT_MAX
    current_snap = horses[horse_id]
    for h_id, other_snap in horses.items():
        if horse_id == h_id: continue
        # 16レーンあるため、幅 0.5 程度を「同じ進路」とみなす
        if abs(current_snap.lane - other_snap.lane) < SAME_LANE_WIDTH:
            dist = other_snap.distance - current_snap.distance
            if 0 < dist < min_dist:
                min_dist = dist
    return min_dist

def get_dist_to_front_context(horse_id: str, horses: dict[str, HorseSnapshot]) -> dict:
    """周囲の馬との距離を返す"""
    current = horses[horse_id]
    context = {
        HorseEnvField.DIST_TO_FRONT: DIST_TO_FRONT_MAX,
        HorseEnvField.DIST_TO_FRONT_LEFT: DIST_TO_FRONT_MAX,
        HorseEnvField.DIST_TO_FRONT_RIGHT: DIST_TO_FRONT_MAX,
        HorseEnvField.DIST_TO_SIDE_LEFT: DIST_TO_FRONT_MAX,
        HorseEnvField.DIST_TO_SIDE_RIGHT: DIST_TO_FRONT_MAX,
    }
    
    for h_id, other in horses.items():
        if horse_id == h_id: continue
        
        d_dist = other.distance - current.distance
        d_lane = other.lane - current.lane
        
        # 前方 (距離 10m 以内を対象にするなど)
        if 0 < d_dist < DIST_FRONT_RANGE:
            if abs(d_lane) < DIST_RIGHT_IN_FRONT: # 真前
                context[HorseEnvField.DIST_TO_FRONT] = min(context[HorseEnvField.DIST_TO_FRONT], d_dist)
            elif -DIST_DIAGONALLY_IN_FRONT < d_lane <= -DIST_RIGHT_IN_FRONT: # 左斜め前
                context[HorseEnvField.DIST_TO_FRONT_LEFT] = min(context[HorseEnvField.DIST_TO_FRONT_LEFT], d_dist)
            elif DIST_RIGHT_IN_FRONT <= d_lane < DIST_DIAGONALLY_IN_FRONT: # 右斜め前
                context[HorseEnvField.DIST_TO_FRONT_RIGHT] = min(context[HorseEnvField.DIST_TO_FRONT_RIGHT], d_dist)
        
        # 真横 (並走状態の検知)
        if abs(d_dist) < DIST_BESIDE_RANGE:
            if -DIST_BESIDE_RANGE < d_lane < 0: context[HorseEnvField.DIST_TO_SIDE_LEFT] = min(context[HorseEnvField.DIST_TO_SIDE_LEFT], abs(d_lane))
            if 0 < d_lane < DIST_BESIDE_RANGE: context[HorseEnvField.DIST_TO_SIDE_RIGHT] = min(context[HorseEnvField.DIST_TO_SIDE_RIGHT], abs(d_lane))
            
    return context

def get_current_section(distance: float, sections: list[TrackSection]) -> TrackSection:
    """現在の距離からセクションを取得"""
    for section in sections:
        if section.start_at <= distance < (section.start_at + section.distance):
            return section
    return sections[-1]

# 時計計算系
def calc_next_step(current_step: int) -> int:
    """stepを足して返す"""
    return current_step + 1

def calc_next_elapsted_time(current_time: float, dt: float) -> float:
    """elapsted_timeをdt分だけ経過させる"""
    return round(current_time + dt, 2) # 浮動小数点の誤差防止

# 物理演算系
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

def calculate_stamina_consumption(current_speed: float, race_distance: float, surface: str, total_stamina: float, dt: float) -> float:
    """レース距離からスタミナ消費量を算出"""
    # 1. 基準となる「1秒あたりの消費量」を算出
    # 完走にかかる想定時間 = 距離 / 想定平均速度
    # 1秒あたりの消費 = 最大スタミナ / 想定時間
    target_avg_speed = get_target_avg_speed(race_distance, surface)
    base_consumption_per_sec = total_stamina / (race_distance / target_avg_speed)
    
    # 2. 速度による消費倍率（速度の2乗に比例させるのが一般的）
    # 巡航速度(target_avg_speed)で走っている時は倍率1.0
    speed_ratio = current_speed / target_avg_speed
    speed_factor = math.pow(speed_ratio)
    
    # 3. 基本消費量を返す（ここにFactorをかける）
    consumption = base_consumption_per_sec * speed_factor * dt
    
    return consumption

def get_target_avg_speed(race_distance: float, surface: str):
    """
    レース距離に基づき、基準となる平均速度を取得する
    TODO: これは今は使われていないが基準平均速度を何かに利用するよう調整
    """

    # 芝かダートで補正
    surface_adjust = DIRT_TIME_ADJUST if surface == RaceSurfaceType.DIRT else TURF_TIME_ADJUST

    # 1. 辞書にピッタリの距離がある場合はそれを返す
    if race_distance in RACE_TIME_AVERAGE_MAP:
        return RACE_TIME_AVERAGE_MAP[race_distance] + surface_adjust

    # 2. ピッタリがない場合、最も近い距離の設定を探す
    # (例: 1400mなら1600mの設定を採用)
    closest_distance = min(RACE_TIME_AVERAGE_MAP.keys(), key=lambda x: abs(x - race_distance))
    
    return RACE_TIME_AVERAGE_MAP[closest_distance] + surface_adjust

def calculate_acceleration(target_v: float, current_v: float, accel_power: float) -> float:
    """速度と加速能力から加速度を算出"""
    v_diff = target_v - current_v
    return v_diff * accel_power

def check_goal(distance: float, course_length: float) -> bool:
    """コースの距離と進んだ距離を比較し、ゴールしたかどうか判定する"""
    return distance >= course_length

def manage_limited_speed(target_speed: float, max_speed: float) -> float:
    """限界速度までしか出せないようにする"""
    return target_speed if target_speed <= max_speed else max_speed

def calculate_simple_acceled_speed(current_velocity: float, accel: float, dt: float) -> float:
    """加速度から次の速度を求めるシンプルな数式"""
    return current_velocity + accel * dt

def calculate_simple_target_position(new_velocity: float, current_distance: float, dt: float) -> float:
    """新しい速度から次の距離を求めるシンプルな数式"""
    return current_distance + new_velocity * dt

def interpolate_goal_time(pre_dist: float, post_dist: float, pre_time: float, dt: float, goal_dist: float) -> float:
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

def get_condition_modifier(condition) -> float:
    """コンディションによる補正数値を返す"""
    # TODO：とりあえず現状は1.0を返す
    return 1.0

def calculate_next_velocity(current_v: float, target_v: float, horse_prof: HorseProfile, has_stamina: bool, dt: float) -> float:
    """
    TODO: これは古いロジックで今は使われていない。これも取り込むように修正
    加速・減速ロジック
    1. 加速時: 目標速度より遅い場合、acceleration パラメータを使って速度を上げます
    2. 減速時: 目標速度より速い場合（オーバーペースやコーナー進入）、自然減速またはブレーキをかけます
    3. スタミナ影響: スタミナが切れている場合、加速力が大幅に落ち、目標速度自体も強制的に下方修正されます
    """
    diff = target_v - current_v
    
    if diff > 0:
        # 加速プロセス
        accel = horse_prof.acceleration
        if not has_stamina:
            accel *= 0.3  # スタミナ切れなら加速力激減
        next_v = current_v + (accel * dt)
        return min(next_v, target_v) # 目標は超えない
    else:
        # 減速プロセス（自然減速は加速より速いのが一般的）
        decel = 2.0  # 固定値またはパラメータ
        next_v = current_v - (decel * dt)
        return max(next_v, target_v) # 目標よりは下がらない