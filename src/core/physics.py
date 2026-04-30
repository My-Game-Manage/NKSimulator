"""
physics.py の概要

レースのシミュレートに関する物理演算を行う関数群。
"""
from src.models.horse_data import HorseProfile, HorseSnapshot
from src.constants.enums import SectionName
from src.models.race_data import TrackSection


# チェック系
def is_horse_finished(distance: float, course_length: float) -> bool:
    """コースの距離と現在の距離を比較してゴールしたかどうかを返す"""
    return distance >= course_length

def is_spurt_distance(distance: float, spurt_dist: float) -> bool:
    """スパート開始距離かどうかの判定"""
    return distance >= spurt_dist

def is_start_section(distance: float, section: TrackSection) -> bool:
    """スタートセクションかどうか"""
    return distance >= section.distance

# 要素取得系
#def current_section_from(position: float, sections: list[TrackSection]) -> TrackSection:
    """距離から現在のセクションを返す"""
    """accumulated_dist = 0
    for section in sections:
        accumulated_dist +=section.distance
        if position <= accumulated_dist:
            return section
    return TrackSection(SectionType.STRAIGHT, 9999, 9999, SectionName.HOME_STRAIGHT) # 予備
"""
def get_dist_to_front(horse_id: str, horses: dict[str, HorseSnapshot]) -> float:
    """前の馬との距離を返す"""
    min_dist = 999.0
    current_snap = horses[horse_id]
    for h_id, other_snap in horses.items():
        if horse_id == h_id: continue
        # 16レーンあるため、幅 0.5 程度を「同じ進路」とみなす
        if abs(current_snap.lane - other_snap.lane) < 0.5:
            dist = other_snap.distance - current_snap.distance
            if 0 < dist < min_dist:
                min_dist = dist
    return min_dist

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
def calculate_stamina_consumption(current_speed: float, race_distance: float, total_stamina: float, dt: float) -> float:
    """レース距離からスタミナ消費量を算出"""
    # 1. 基準となる「1秒あたりの消費量」を算出
    # 完走にかかる想定時間 = 距離 / 想定平均速度
    # 1秒あたりの消費 = 最大スタミナ / 想定時間
    target_avg_speed = get_target_avg_speed(race_distance)
    base_consumption_per_sec = total_stamina / (race_distance / target_avg_speed)
    
    # 2. 速度による消費倍率（速度の2乗に比例させるのが一般的）
    # 巡航速度(target_avg_speed)で走っている時は倍率1.0
    speed_ratio = current_speed / target_avg_speed
    speed_factor = speed_ratio ** 2 
    
    # 3. 基本消費量を返す（ここにFactorをかける）
    consumption = base_consumption_per_sec * speed_factor * dt
    
    return consumption

def get_target_avg_speed(race_distance):
    """
    レース距離に基づき、基準となる平均速度を取得する
    """
    # 距離ごとの基準速度テーブル
    # 距離(m): 速度(m/s)
    race_settings = {
        800: 17.8,
        1600: 16.8,
        2400: 16.0,
        3000: 15.5
    }

    # 1. 辞書にピッタリの距離がある場合はそれを返す
    if race_distance in race_settings:
        return race_settings[race_distance]

    # 2. ピッタリがない場合、最も近い距離の設定を探す
    # (例: 1400mなら1600mの設定を採用)
    closest_distance = min(race_settings.keys(), key=lambda x: abs(x - race_distance))
    
    return race_settings[closest_distance]

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

#def get_current_section(distance: float, sections: list[TrackSection]) -> TrackSection:
#    """現在位置から該当するセクションを返す"""
#    for section in sections:
#        if section.start_at <= distance < (section.start_at + section.distance):
#            return section
#    return sections[-1] # ゴール後は最後の直線扱い

def get_condition_modifier(condition) -> float:
    """コンディションによる補正数値を返す"""
    # TODO：とりあえず現状は1.0を返す
    return 1.0

#def calculate_target_speed(param: HorseProfile, state: HorseState, section: TrackSection, condition: TrackCondition) -> float:
    """
    目標速度の決定ロジック
    1. ベース速度: max_speed（基本能力）に、馬場状態（TrackCondition）の補正を掛けます
    2. フェーズ補正: レース序盤・中盤・終盤（スパート）で倍率を変えます
    3. セクション補正: コーナー（CURVE）では、遠心力による減速（cornering_ability）を適用します
    
    # 1. 馬場による基本速度の減衰 (良=1.0, 不良=0.95 など)
    condition_mod = get_condition_modifier(condition)
    base_speed = param.max_speed * condition_mod
    
    # 2. セクションによる補正 (コーナーなら能力に応じて減速)
    section_mod = 1.0
    if section.type == SectionType.CURVE:
        # コーナー適性が高いほど減速しにくい
        section_mod = 0.9 + (param.cornering_ability * 0.1)
    
    # 3. フェーズによる戦略的目標速度
    # スパート距離に入っていれば100%、そうでなければスタミナ温存で90%など
    phase_mod = 1.0 if state.is_spurting else 0.9
    
    return base_speed * section_mod * phase_mod
    """

def calculate_next_velocity(current_v: float, target_v: float, param: HorseProfile, has_stamina: bool, dt: float) -> float:
    """
    加速・減速ロジック
    1. 加速時: 目標速度より遅い場合、acceleration パラメータを使って速度を上げます
    2. 減速時: 目標速度より速い場合（オーバーペースやコーナー進入）、自然減速またはブレーキをかけます
    3. スタミナ影響: スタミナが切れている場合、加速力が大幅に落ち、目標速度自体も強制的に下方修正されます
    """
    diff = target_v - current_v
    
    if diff > 0:
        # 加速プロセス
        accel = param.acceleration
        if not has_stamina:
            accel *= 0.3  # スタミナ切れなら加速力激減
        next_v = current_v + (accel * dt)
        return min(next_v, target_v) # 目標は超えない
    else:
        # 減速プロセス（自然減速は加速より速いのが一般的）
        decel = 2.0  # 固定値またはパラメータ
        next_v = current_v - (decel * dt)
        return max(next_v, target_v) # 目標よりは下がらない