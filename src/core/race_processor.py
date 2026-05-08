"""
race_processor.py の概要

レース中の各馬の値の処理を行う。
"""
import logging

# ロガーの取得（__name__ はファイル名/モジュール名になる）
logger = logging.getLogger(__name__)

from src.constants.enums import HorseStrategyType, SectionType, SectionName
from src.constants.fields import HorseEnvField, HorseTacField
from src.models.horse_data import HorseProfile, HorseSnapshot
from src.models.race_data import TrackSection
import src.core.physics as ph
from src.constants.constants import STAMINA_DRAIN_COEFFICIENT


class RaceProcessor:
    @staticmethod
    def get_target_velocity(base_velocity: float, horse_prof: HorseProfile, horse_snap: HorseSnapshot, env: dict, tac: dict) -> float:
        # 必要な環境情報取得
        section = env[HorseEnvField.SECTION]
        dist_to_context = env[HorseEnvField.DIST_TO_CONTEXT]
        dist_to_front = dist_to_context[HorseEnvField.DIST_TO_FRONT]
        corner_radius = env[HorseEnvField.CORNER_RADIUS]
        rank = env[HorseEnvField.RANK]
        num_horses = env[HorseEnvField.NUM_HORSES]
        # 必要な戦略情報取得
        target_lane = tac[HorseTacField.TARGET_LANE]
        # 基本はmax_speed（ベストな巡航速度）を目指す
        target_v = base_velocity
        if target_lane == horse_snap.lane:
            # レーン移動しない場合は前の馬に馬がいれば維持
            if dist_to_front <= 0.5:
                target_v = horse_snap.velocity
        if section.type is SectionType.CURVE:
            # コーナーでは係数の分だけ目標速度を減らす->減れば自然と減速
            target_v = ph.calculate_target_velocity_at_corner(target_v, corner_radius, horse_snap.lane, horse_prof.cornering_ability)
        return target_v

    @staticmethod
    def get_spurt_velocity(horse_prof: HorseProfile, horse_snap: HorseSnapshot, env: dict) -> float:
        # 基本： spurt_v = spurt_speed * factor
        # 必要な環境情報取得
        section = env[HorseEnvField.SECTION]
        dist_to_context = env[HorseEnvField.DIST_TO_CONTEXT]
        dist_to_front = dist_to_context[HorseEnvField.DIST_TO_FRONT]
        corner_radius = env[HorseEnvField.CORNER_RADIUS]
        spurt_v = horse_prof.last_3f_speed
        if section.type is SectionType.CURVE:
            # コーナーでは係数の分だけ目標速度を減らす->減れば自然と減速
            spurt_v = ph.calculate_target_velocity_at_corner(spurt_v, corner_radius, horse_snap.lane, horse_prof.cornering_ability)
        return spurt_v

    @staticmethod
    def get_acceleration(horse_prof: HorseProfile, horse_snap: HorseSnapshot, env: dict) -> float:
        # 基本： accel = acceleration * factor
        friction = env[HorseEnvField.FRICTION]
        # 斤量補正：50kgを基準とし、1kgあたり 0.5% 加速度を低下させる
        penalty_rate = (horse_prof.weight_carried - 50) * 0.005
        # 芝やダートの上を走る分の係数を引く
        accel = horse_prof.acceleration * (1.0 - penalty_rate) - friction
        # 加速力が低くなりすぎないよう下限を設定
        return max(0.5, accel)

    @staticmethod
    def get_next_velocity(target_v: float, accel: float, horse_prof: HorseProfile, horse_snap: HorseSnapshot, env: dict, dt: float) -> float:
        # 基本： current_v と target_v の差で加速／減速になる 
        #   if current_v < target_v: return min(current_v + accel * dt, target_v)
        #   elif current_v > target_v: return max(current_v - accel * dt, target_v)
        #   else: return target_v
        if horse_snap.velocity < target_v:
            return min(horse_snap.velocity + accel * dt, target_v)
        elif horse_snap.velocity > target_v:
            return max(horse_snap.velocity - accel * dt, target_v)
        else:
            return target_v

    @staticmethod
    def get_next_distance(next_velocity: float, horse_prof: HorseProfile, horse_snap: HorseSnapshot, env: dict, dt: float) -> float:
        # 基本： v_avg = (current_v + next_v) / 2 ※台形近似式
        #   next_dist = v_avg * dt
        v_avg = (horse_snap.velocity + next_velocity) / 2
        next_distance = v_avg * dt
        return horse_snap.distance + next_distance

    @staticmethod
    def consume_stamina(next_velocity: float, horse_prof: HorseProfile, horse_snap: HorseSnapshot, env: dict, dt: float) -> float:
        # 基本： base_consumption = v_next ** 2 ※速度の2乗にするとリアリティが出る
        #   cons_stamina = base_compumption * waste_rate * (weight / 50.0) * dt
        #環境情報
        ctx = env[HorseEnvField.DIST_TO_CONTEXT]
        dist_to_front = ctx[HorseEnvField.DIST_TO_FRONT]
        side_left = ctx[HorseEnvField.DIST_TO_SIDE_LEFT]
        side_right = ctx[HorseEnvField.DIST_TO_SIDE_RIGHT]
        # 速度の2乗をベースにする（空気抵抗や筋肉への負荷を表現）
        base_consumption = next_velocity ** 2
        # 斤量による負荷補正（例: 50kgを基準とする）
        weight_load = horse_prof.weight_carried / 50.0
        # 加速中なら消費量を増やす
        accel_factor = 1.5 if next_velocity < horse_snap.velocity else 1.0
        # レーンの先頭なら風圧で消費量を増やす
        wind_factor = 1.0
        if dist_to_front >= 999:
            wind_factor = 1.1
        elif 2.0 < dist_to_front < 5.0:
            wind_factor = 0.9
        elif side_left < 0.5 or side_right < 0.5:
            wind_factor = 1.1
        # ステップあたりの消費量
        consumption = base_consumption * horse_prof.stamina_waste_rate * STAMINA_DRAIN_COEFFICIENT * weight_load * accel_factor *  wind_factor * dt
        return max(0.0, horse_snap.stamina - consumption)

    @staticmethod
    def get_target_lane(horse_prof: HorseProfile, horse_snap: HorseSnapshot, env: dict) -> float:
        # 環境情報
        section = env[HorseEnvField.SECTION]
        dist_to_context = env[HorseEnvField.DIST_TO_CONTEXT]
        rank = env[HorseEnvField.RANK]
        num_horses = env[HorseEnvField.NUM_HORSES]
        ctx = dist_to_context
    
        # 候補となるレーン: [現在のレーン, 左に移動, 右に移動]
        # 0.5刻みなどで計算するとよりスムーズ
        options = [horse_snap.lane - 0.5, horse_snap.lane, horse_snap.lane + 0.5]
        lane_scores = {}

        for opt in options:
            if opt < 1.0 or opt > 16.0: continue # コース外
        
            score = 0.0
        
            # 1. 基本コスト: 内側ほどわずかに有利
            score += opt * 0.1
        
            # 2. 前方の詰まりによるペナルティ
            # そのレーンの「前方」に馬がいる場合
            d_lane_opt = opt - horse_snap.lane
        
            relevant_dist = 999.0
            if abs(d_lane_opt) < 0.2: relevant_dist = ctx[HorseEnvField.DIST_TO_FRONT]
            elif d_lane_opt < -0.2:  relevant_dist = ctx[HorseEnvField.DIST_TO_FRONT_LEFT]
            elif d_lane_opt > 0.2:   relevant_dist = ctx[HorseEnvField.DIST_TO_FRONT_RIGHT]
        
            if relevant_dist < 3.0:
                score += 20.0 # 衝突回避（最優先）
            elif relevant_dist < 8.0:
                score += 5.0  # 少し詰まっている
            
            # 3. 横に馬がいる場合の移動制限
            if d_lane_opt < 0 and ctx[HorseEnvField.DIST_TO_SIDE_LEFT] < 0.8:
                score += 15.0 # 左に馬がいるので移動しにくい
            if d_lane_opt > 0 and ctx[HorseEnvField.DIST_TO_SIDE_RIGHT] < 0.8:
                score += 15.0 # 右に馬がいるので移動しにくい
            
            # 4. 脚質(strategy)による補正 (ポンペルモ等の分析を反映)
            if horse_prof.strategy == HorseStrategyType.LEADER and opt > 2.0:
                score += 10.0 # 逃げ馬は外に行きたがらない
            
            lane_scores[opt] = score

        # 最もスコアの低い（快適な）レーンをターゲットにする
        target_lane = min(lane_scores, key=lane_scores.get)

        return target_lane

    @staticmethod
    def get_next_lane(horse_prof: HorseProfile, horse_snap: HorseSnapshot, env: dict, tac: dict, dt: float) -> float:
        # 基本： base_lane_speed = 2.0 * corner_ability
        #   max_move = base_lane_speed * dt
        #   diff = target_lane - current_lane
        #   if abs(diff) <= max_move: return target_lane
        #   else:
        #       move_dir = 1 if diff > 0 else -1
        #       return current_lane + (move_dir * max_move)
        target_lane = tac[HorseTacField.TARGET_LANE]
        base_lane_speed = 2.0 * horse_prof.cornering_ability * horse_prof.base_agility
        max_move = base_lane_speed * dt
        diff = target_lane - horse_snap.lane
        if abs(diff) <= max_move:
            return target_lane
        else:
            move_dir = 1 if diff > 0 else -1
            return horse_snap.lane + (move_dir * max_move)
