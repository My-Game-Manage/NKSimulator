"""
strategy.py の概要

脚質に応じたStrategy（Protocol）を提供する特殊クラス群
"""
from typing import Protocol

import logging

# ロガーの取得（__name__ はファイル名/モジュール名になる）
logger = logging.getLogger(__name__)

from src.constants.enums import HorseStrategyType, SectionType, SectionName
from src.constants.fields import HorseEnvField, HorseTacField
from src.models.horse_data import HorseProfile, HorseSnapshot
from src.models.race_data import TrackSection
import src.core.physics as ph

# スタミナ消費調整用の定数
STAMINA_DRAIN_COEFFICIENT = 0.075

# ---------------------------------------------------------
# Strategy（Protocol）パターンの基底クラス
# ---------------------------------------------------------
class RacingStrategy(Protocol):
    def get_target_velocity(self, horse_prof: HorseProfile, horse_snap: HorseSnapshot, env: dict, tac: dict) -> float:
        # 基本： target_v = cruise_speed * factor
        ...

    def get_spurt_velocity(self, horse_prof: HorseProfile, horse_snap: HorseSnapshot, env: dict) -> float:
        # 基本： spurt_v = spurt_speed * factor
        ...

    def get_acceleration(self, horse_prof: HorseProfile, horse_snap: HorseSnapshot, env: dict) -> float:
        # 基本： accel = acceleration * factor
        ...

    def get_next_velocity(self, target_v: float, accel: float, horse_prof: HorseProfile, horse_snap: HorseSnapshot, env: dict, dt: float) -> float:
        # 基本： current_v と target_v の差で加速／減速になる 
        #   if current_v < target_v:
        #       v_next = v_current + (acceleration * dt)
        #       return min(v_next, v_target)
        #   elif current_v > target_v:
        #       v_next = v_current - (acceleration * dt)
        #       return max(v_next, v_target)
        #   else: return target_v
        ...

    def get_next_distance(self, next_velocity: float, horse_prof: HorseProfile, horse_snap: HorseSnapshot, env: dict, dt: float) -> float:
        # 基本： v_avg = (current_v + next_v) / 2 ※台形近似式
        #   next_dist = v_avg * dt
        ...

    def consume_stamina(self, next_velocity: float, horse_prof: HorseProfile, horse_snap: HorseSnapshot, env: dict, dt: float) -> float:
        # 基本： base_consumption = v_next ** 2 ※速度の2乗にするとリアリティが出る
        #   cons_stamina = base_compumption * waste_rate * (weight / 50.0) * dt
        ...

    def get_target_lane(self, horse_prof: HorseProfile, horse_snap: HorseSnapshot, env: dict) -> float:
        ...

    def get_next_lane(self, horse_prof: HorseProfile, horse_snap: HorseSnapshot, env: dict, tac: dict, dt: float) -> float:
        # 基本： base_lane_speed = 2.0 * corner_ability
        #   max_move = base_lane_speed * dt
        #   diff = target_lane - current_lane
        #   if abs(diff) <= max_move: return target_lane
        #   else:
        #       move_dir = 1 if diff > 0 else -1
        #       return current_lane + (move_dir * max_move)
        ...


# ---------------------------------------------------------
# 具象Strategyクラス：逃げ
# ---------------------------------------------------------
class LeaderStrategy:
    def get_target_velocity(self, horse_prof: HorseProfile, horse_snap: HorseSnapshot, env: dict, tac: dict) -> float:
        # 必要な環境情報取得
        section = env[HorseEnvField.SECTION]
        dist_to_context = env[HorseEnvField.DIST_TO_CONTEXT]
        dist_to_front = dist_to_context[HorseEnvField.DIST_TO_FRONT]
        corner_penalty = env[HorseEnvField.CORNER_PENALTY]
        race_distance = env[HorseEnvField.RACE_DISTANCE]
        # 必要な戦略情報取得
        target_lane = tac[HorseTacField.TARGET_LANE]
        # 基本はmax_speed（ベストな巡航速度）を目指す
        target_v = horse_prof.cruise_speed
        if target_lane == horse_snap.lane:
            # レーン移動しない場合は前の馬に馬がいれば維持
            if dist_to_front <= 0.5:
                target_v = horse_snap.velocity
        if dist_to_front <= 0.5:
            # 前にいる場合はー＞追い抜こうとする
            return target_v
        return target_v

    def get_spurt_velocity(self, horse_prof: HorseProfile, horse_snap: HorseSnapshot, env: dict) -> float:
        # 基本： spurt_v = spurt_speed * factor
        # 必要な環境情報取得
        section = env[HorseEnvField.SECTION]
        dist_to_context = env[HorseEnvField.DIST_TO_CONTEXT]
        dist_to_front = dist_to_context[HorseEnvField.DIST_TO_FRONT]
        corner_penalty = env[HorseEnvField.CORNER_PENALTY]
        spurt_v = horse_prof.last_3f_speed
        if section.type is SectionType.CURVE:
            # コーナーでは係数の分だけ目標速度を減らす->減れば自然と減速
            spurt_v *= (1.0 - corner_penalty)
        return spurt_v

    def get_acceleration(self, horse_prof: HorseProfile, horse_snap: HorseSnapshot, env: dict) -> float:
        # 基本： accel = acceleration * factor
        friction = env[HorseEnvField.FRICTION]
        # 斤量補正：50kgを基準とし、1kgあたり 0.5% 加速度を低下させる
        penalty_rate = (horse_prof.weight_carried - 50) * 0.005
        # 芝やダートの上を走る分の係数を引く
        accel = horse_prof.acceleration * (1.0 - penalty_rate) - friction
        # 加速力が低くなりすぎないよう下限を設定
        return max(0.5, accel)

    def get_next_velocity(self, target_v: float, accel: float, horse_prof: HorseProfile, horse_snap: HorseSnapshot, env: dict, dt: float) -> float:
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

    def get_next_distance(self, next_velocity: float, horse_prof: HorseProfile, horse_snap: HorseSnapshot, env: dict, dt: float) -> float:
        # 基本： v_avg = (current_v + next_v) / 2 ※台形近似式
        #   next_dist = v_avg * dt
        v_avg = (horse_snap.velocity + next_velocity) / 2
        next_distance = v_avg * dt
        return horse_snap.distance + next_distance

    def consume_stamina(self, next_velocity: float, horse_prof: HorseProfile, horse_snap: HorseSnapshot, env: dict, dt: float) -> float:
        # 基本： base_consumption = v_next ** 2 ※速度の2乗にするとリアリティが出る
        #   cons_stamina = base_compumption * waste_rate * (weight / 50.0) * dt
        #環境情報
        dist_to_context = env[HorseEnvField.DIST_TO_CONTEXT]
        dist_to_front = dist_to_context[HorseEnvField.DIST_TO_FRONT]
        # 速度の2乗をベースにする（空気抵抗や筋肉への負荷を表現）
        base_consumption = next_velocity ** 2
        # 斤量による負荷補正（例: 50kgを基準とする）
        weight_load = horse_prof.weight_carried / 50.0
        # 加速中なら消費量を増やす
        accel_factor = 1.5 if next_velocity < horse_snap.velocity else 1.0
        # レーンの先頭なら風圧で消費量を増やす
        wind_factor = 1.1 if dist_to_front >= 999 else 1.0
        # ステップあたりの消費量
        consumption = base_consumption * horse_prof.stamina_waste_rate * STAMINA_DRAIN_COEFFICIENT * weight_load * accel_factor *  wind_factor * dt
        return max(0.0, horse_snap.stamina - consumption)

    def get_target_lane(self, horse_prof: HorseProfile, horse_snap: HorseSnapshot, env: dict) -> float:
        # 環境情報
        section = env[HorseEnvField.SECTION]
        dist_to_context = env[HorseEnvField.DIST_TO_CONTEXT]
        dist_to_front = dist_to_context[HorseEnvField.DIST_TO_FRONT]
        rank = env[HorseEnvField.RANK]
        num_horses = env[HorseEnvField.NUM_HORSES]
        # 評価スコア：低いほど良い（走りやすい）
        lane_scores = {}
        current_lane = horse_snap.lane
        for lane in [current_lane - 1.0, current_lane, current_lane + 1.0]:
            if lane < 1.0: continue # ラチより内側は除外
            score = 0
            # 1. 内側ほど基本スコアが良い（最短距離）
            score += lane * 0.5
            # 2. 前方に馬がいるか？
            if dist_to_front < 2.0:# 非常に近い
                score += 10.0 # 衝突リスク大
            elif dist_to_front < 5.0: # ドラフティング圏内
                # 逃げ馬なら「邪魔」なので避ける、差し馬なら「温存」のため残る
                score -= horse_prof.lane_change_frequency
            lane_scores[lane] = score
        # 最もスコアの低い（有利な）レーンをターゲットにする
        target_lane = min(lane_scores, key=lane_scores.get)
        return target_lane

    def get_next_lane(self, horse_prof: HorseProfile, horse_snap: HorseSnapshot, env: dict, tac: dict, dt: float) -> float:
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

# ---------------------------------------------------------
# 具象Strategyクラス：先行
# ---------------------------------------------------------
class StalkerStrategy:
    def get_target_velocity(self, horse_prof: HorseProfile, horse_snap: HorseSnapshot, env: dict, tac: dict) -> float:
        # 必要な環境情報取得
        section = env[HorseEnvField.SECTION]
        dist_to_context = env[HorseEnvField.DIST_TO_CONTEXT]
        dist_to_front = dist_to_context[HorseEnvField.DIST_TO_FRONT]
        corner_penalty = env[HorseEnvField.CORNER_PENALTY]
        rank = env[HorseEnvField.RANK]
        num_horses = env[HorseEnvField.NUM_HORSES]
        # 必要な戦略情報取得
        target_lane = tac[HorseTacField.TARGET_LANE]
        # 基本はmax_speed（ベストな巡航速度）を目指す
        target_v = horse_prof.cruise_speed
        if target_lane == horse_snap.lane:
            # レーン移動しない場合は前の馬に馬がいれば維持
            if dist_to_front <= 0.5:
                target_v = horse_snap.velocity
        if section.type is SectionType.CURVE:
            # コーナーでは係数の分だけ目標速度を減らす->減れば自然と減速
            target_v *= (1.0 - corner_penalty)
        return target_v
    
    def get_spurt_velocity(self, horse_prof: HorseProfile, horse_snap: HorseSnapshot, env: dict) -> float:
        # 基本： spurt_v = spurt_speed * factor
        # 必要な環境情報取得
        section = env[HorseEnvField.SECTION]
        dist_to_context = env[HorseEnvField.DIST_TO_CONTEXT]
        dist_to_front = dist_to_context[HorseEnvField.DIST_TO_FRONT]
        corner_penalty = env[HorseEnvField.CORNER_PENALTY]
        spurt_v = horse_prof.last_3f_speed
        if section.type is SectionType.CURVE:
            # コーナーでは係数の分だけ目標速度を減らす->減れば自然と減速
            spurt_v *= (1.0 - corner_penalty)
        return spurt_v
    
    def get_acceleration(self, horse_prof: HorseProfile, horse_snap: HorseSnapshot, env: dict) -> float:
        # 基本： accel = acceleration * factor
        friction = env[HorseEnvField.FRICTION]
        # 斤量補正：50kgを基準とし、1kgあたり 0.5% 加速度を低下させる
        penalty_rate = (horse_prof.weight_carried - 50) * 0.005
        # 芝やダートの上を走る分の係数を引く
        accel = horse_prof.acceleration * (1.0 - penalty_rate) - friction
        # 加速力が低くなりすぎないよう下限を設定
        return max(0.5, accel)

    def get_next_velocity(self, target_v: float, accel: float, horse_prof: HorseProfile, horse_snap: HorseSnapshot, env: dict, dt: float) -> float:
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

    def get_next_distance(self, next_velocity: float, horse_prof: HorseProfile, horse_snap: HorseSnapshot, env: dict, dt: float) -> float:
        # 基本： v_avg = (current_v + next_v) / 2 ※台形近似式
        #   next_dist = v_avg * dt
        v_avg = (horse_snap.velocity + next_velocity) / 2
        next_distance = v_avg * dt
        return horse_snap.distance + next_distance

    def consume_stamina(self, next_velocity: float, horse_prof: HorseProfile, horse_snap: HorseSnapshot, env: dict, dt: float) -> float:
        # 基本： base_consumption = v_next ** 2 ※速度の2乗にするとリアリティが出る
        #   cons_stamina = base_compumption * waste_rate * (weight / 50.0) * dt
        dist_to_context = env[HorseEnvField.DIST_TO_CONTEXT]
        dist_to_front = dist_to_context[HorseEnvField.DIST_TO_FRONT]
        # 速度の2乗をベースにする（空気抵抗や筋肉への負荷を表現）
        base_consumption = next_velocity ** 2
        # 斤量による負荷補正（例: 50kgを基準とする）
        weight_load = horse_prof.weight_carried / 50.0
        # 加速中なら消費量を増やす
        accel_factor = 1.5 if next_velocity < horse_snap.velocity else 1.0
        # レーンの先頭なら風圧で消費量を増やす
        wind_factor = 1.1 if dist_to_front >= 999 else 1.0
        # ステップあたりの消費量
        consumption = base_consumption * horse_prof.stamina_waste_rate * STAMINA_DRAIN_COEFFICIENT * weight_load * accel_factor *  wind_factor * dt
        return max(0.0, horse_snap.stamina - consumption)
    
    def get_target_lane(self, horse_prof: HorseProfile, horse_snap: HorseSnapshot, env: dict) -> float:
        # 環境情報
        section = env[HorseEnvField.SECTION]
        dist_to_context = env[HorseEnvField.DIST_TO_CONTEXT]
        dist_to_front = dist_to_context[HorseEnvField.DIST_TO_FRONT]
        rank = env[HorseEnvField.RANK]
        num_horses = env[HorseEnvField.NUM_HORSES]
        # 評価スコア：低いほど良い（走りやすい）
        lane_scores = {}
        current_lane = horse_snap.lane
        for lane in [current_lane - 1.0, current_lane, current_lane + 1.0]:
            if lane < 1.0: continue # ラチより内側は除外
            score = 0
            # 1. 内側ほど基本スコアが良い（最短距離）
            score += lane * 0.5
            # 2. 前方に馬がいるか？
            if dist_to_front < 2.0:# 非常に近い
                score += 10.0 # 衝突リスク大
            elif dist_to_front < 5.0: # ドラフティング圏内
                # 逃げ馬なら「邪魔」なので避ける、差し馬なら「温存」のため残る
                score -= horse_prof.lane_change_frequency
            lane_scores[lane] = score
        # 最もスコアの低い（有利な）レーンをターゲットにする
        target_lane = min(lane_scores, key=lane_scores.get)
        return target_lane

    def get_next_lane(self, horse_prof: HorseProfile, horse_snap: HorseSnapshot, env: dict, tac: dict, dt: float) -> float:
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

# ---------------------------------------------------------
# 具象Strategyクラス：差し
# ---------------------------------------------------------
class CloserStrategy:
    def get_target_velocity(self, horse_prof: HorseProfile, horse_snap: HorseSnapshot, env: dict, tac: dict) -> float:
        # 必要な環境情報取得
        section = env[HorseEnvField.SECTION]
        dist_to_context = env[HorseEnvField.DIST_TO_CONTEXT]
        dist_to_front = dist_to_context[HorseEnvField.DIST_TO_FRONT]
        corner_penalty = env[HorseEnvField.CORNER_PENALTY]
        rank = env[HorseEnvField.RANK]
        num_horses = env[HorseEnvField.NUM_HORSES]
        # 必要な戦略情報取得
        target_lane = tac[HorseTacField.TARGET_LANE]
        # 基本はmax_speed（ベストな巡航速度）を目指す
        target_v = horse_prof.cruise_speed
        if target_lane == horse_snap.lane:
            # レーン移動しない場合は前の馬に馬がいれば維持
            if dist_to_front <= 0.5:
                target_v = horse_snap.velocity
        if section.type is SectionType.CURVE:
            # コーナーでは係数の分だけ目標速度を減らす->減れば自然と減速
            target_v *= (1.0 - corner_penalty)
        return target_v
    
    def get_spurt_velocity(self, horse_prof: HorseProfile, horse_snap: HorseSnapshot, env: dict) -> float:
        # 基本： spurt_v = spurt_speed * factor
        # 必要な環境情報取得
        section = env[HorseEnvField.SECTION]
        dist_to_context = env[HorseEnvField.DIST_TO_CONTEXT]
        dist_to_front = dist_to_context[HorseEnvField.DIST_TO_FRONT]
        corner_penalty = env[HorseEnvField.CORNER_PENALTY]
        spurt_v = horse_prof.last_3f_speed
        if section.type is SectionType.CURVE:
            # コーナーでは係数の分だけ目標速度を減らす->減れば自然と減速
            spurt_v *= (1.0 - corner_penalty)
        return spurt_v

    def get_acceleration(self, horse_prof: HorseProfile, horse_snap: HorseSnapshot, env: dict) -> float:
        # 基本： accel = acceleration * factor
        friction = env[HorseEnvField.FRICTION]
        # 斤量補正：50kgを基準とし、1kgあたり 0.5% 加速度を低下させる
        penalty_rate = (horse_prof.weight_carried - 50) * 0.005
        # 芝やダートの上を走る分の係数を引く
        accel = horse_prof.acceleration * (1.0 - penalty_rate) - friction
        # 加速力が低くなりすぎないよう下限を設定
        return max(0.5, accel)

    def get_next_velocity(self, target_v: float, accel: float, horse_prof: HorseProfile, horse_snap: HorseSnapshot, env: dict, dt: float) -> float:
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

    def get_next_distance(self, next_velocity: float, horse_prof: HorseProfile, horse_snap: HorseSnapshot, env: dict, dt: float) -> float:
        # 基本： v_avg = (current_v + next_v) / 2 ※台形近似式
        #   next_dist = v_avg * dt
        v_avg = (horse_snap.velocity + next_velocity) / 2
        next_distance = v_avg * dt
        return horse_snap.distance + next_distance

    def consume_stamina(self, next_velocity: float, horse_prof: HorseProfile, horse_snap: HorseSnapshot, env: dict, dt: float) -> float:
        # 基本： base_consumption = v_next ** 2 ※速度の2乗にするとリアリティが出る
        #   cons_stamina = base_compumption * waste_rate * (weight / 50.0) * dt
        # 環境情報
        dist_to_context = env[HorseEnvField.DIST_TO_CONTEXT]
        dist_to_front = dist_to_context[HorseEnvField.DIST_TO_FRONT]
        # 速度の2乗をベースにする（空気抵抗や筋肉への負荷を表現）
        base_consumption = next_velocity ** 2
        # 斤量による負荷補正（例: 50kgを基準とする）
        weight_load = horse_prof.weight_carried / 50.0
        # 加速中なら消費量を増やす
        accel_factor = 1.5 if next_velocity < horse_snap.velocity else 1.0
        # レーンの先頭なら風圧で消費量を増やす
        wind_factor = 1.1 if dist_to_front >= 999 else 1.0
        # ステップあたりの消費量
        consumption = base_consumption * horse_prof.stamina_waste_rate * STAMINA_DRAIN_COEFFICIENT * weight_load * accel_factor *  wind_factor * dt
        return max(0.0, horse_snap.stamina - consumption)
    
    def get_target_lane(self, horse_prof: HorseProfile, horse_snap: HorseSnapshot, env: dict) -> float:
        # 環境情報
        section = env[HorseEnvField.SECTION]
        dist_to_context = env[HorseEnvField.DIST_TO_CONTEXT]
        dist_to_front = dist_to_context[HorseEnvField.DIST_TO_FRONT]
        rank = env[HorseEnvField.RANK]
        num_horses = env[HorseEnvField.NUM_HORSES]
        # 評価スコア：低いほど良い（走りやすい）
        lane_scores = {}
        current_lane = horse_snap.lane
        for lane in [current_lane - 1.0, current_lane, current_lane + 1.0]:
            if lane < 1.0: continue # ラチより内側は除外
            score = 0
            # 1. 内側ほど基本スコアが良い（最短距離）
            score += lane * 0.5
            # 2. 前方に馬がいるか？
            if dist_to_front < 2.0:# 非常に近い
                score += 10.0 # 衝突リスク大
            elif dist_to_front < 5.0: # ドラフティング圏内
                # 逃げ馬なら「邪魔」なので避ける、差し馬なら「温存」のため残る
                score -= horse_prof.lane_change_frequency
            lane_scores[lane] = score
        # 最もスコアの低い（有利な）レーンをターゲットにする
        target_lane = min(lane_scores, key=lane_scores.get)
        return target_lane

    def get_next_lane(self, horse_prof: HorseProfile, horse_snap: HorseSnapshot, env: dict, tac: dict, dt: float) -> float:
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

# ---------------------------------------------------------
# 具象Strategyクラス：追い込み
# ---------------------------------------------------------
class RearStrategy:
    def get_target_velocity(self, horse_prof: HorseProfile, horse_snap: HorseSnapshot, env: dict, tac: dict) -> float:
        # 必要な環境情報取得
        section = env[HorseEnvField.SECTION]
        dist_to_context = env[HorseEnvField.DIST_TO_CONTEXT]
        dist_to_front = dist_to_context[HorseEnvField.DIST_TO_FRONT]
        corner_penalty = env[HorseEnvField.CORNER_PENALTY]
        # 必要な戦略情報取得
        target_lane = tac[HorseTacField.TARGET_LANE]
        # 基本はmax_speed（ベストな巡航速度）を目指す
        target_v = horse_prof.cruise_speed
        if target_lane == horse_snap.lane:
            # レーン移動しない場合は前の馬に馬がいれば維持
            if dist_to_front <= 0.5:
                target_v = horse_snap.velocity
        if section.type is SectionType.CURVE:
            # コーナーでは係数の分だけ目標速度を減らす->減れば自然と減速
            target_v *= (1.0 - corner_penalty)
        return target_v
    
    def get_spurt_velocity(self, horse_prof: HorseProfile, horse_snap: HorseSnapshot, env: dict) -> float:
        # 基本： spurt_v = spurt_speed * factor
        # 必要な環境情報取得
        section = env[HorseEnvField.SECTION]
        dist_to_context = env[HorseEnvField.DIST_TO_CONTEXT]
        dist_to_front = dist_to_context[HorseEnvField.DIST_TO_FRONT]
        corner_penalty = env[HorseEnvField.CORNER_PENALTY]
        spurt_v = horse_prof.last_3f_speed
        if section.type is SectionType.CURVE:
            # コーナーでは係数の分だけ目標速度を減らす->減れば自然と減速
            spurt_v *= (1.0 - corner_penalty)
        return spurt_v

    def get_acceleration(self, horse_prof: HorseProfile, horse_snap: HorseSnapshot, env: dict) -> float:
        # 基本： accel = acceleration * factor
        friction = env[HorseEnvField.FRICTION]
        # 斤量補正：50kgを基準とし、1kgあたり 0.5% 加速度を低下させる
        penalty_rate = (horse_prof.weight_carried - 50) * 0.005
        # 芝やダートの上を走る分の係数を引く
        accel = horse_prof.acceleration * (1.0 - penalty_rate) - friction
        # 加速力が低くなりすぎないよう下限を設定
        return max(0.5, accel)

    def get_next_velocity(self, target_v: float, accel: float, horse_prof: HorseProfile, horse_snap: HorseSnapshot, env: dict, dt: float) -> float:
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

    def get_next_distance(self, next_velocity: float, horse_prof: HorseProfile, horse_snap: HorseSnapshot, env: dict, dt: float) -> float:
        # 基本： v_avg = (current_v + next_v) / 2 ※台形近似式
        #   next_dist = v_avg * dt
        v_avg = (horse_snap.velocity + next_velocity) / 2
        next_distance = v_avg * dt
        return horse_snap.distance + next_distance

    def consume_stamina(self, next_velocity: float, horse_prof: HorseProfile, horse_snap: HorseSnapshot, env: dict, dt: float) -> float:
        # 基本： base_consumption = v_next ** 2 ※速度の2乗にするとリアリティが出る
        #   cons_stamina = base_compumption * waste_rate * (weight / 50.0) * dt
        # 環境情報
        dist_to_context = env[HorseEnvField.DIST_TO_CONTEXT]
        dist_to_front = dist_to_context[HorseEnvField.DIST_TO_FRONT]
        # 速度の2乗をベースにする（空気抵抗や筋肉への負荷を表現）
        base_consumption = next_velocity ** 2
        # 斤量による負荷補正（例: 50kgを基準とする）
        weight_load = horse_prof.weight_carried / 50.0
        # 加速中なら消費量を増やす
        accel_factor = 1.5 if next_velocity < horse_snap.velocity else 1.0
        # レーンの先頭なら風圧で消費量を増やす
        wind_factor = 1.1 if dist_to_front >= 999 else 1.0
        # ステップあたりの消費量
        consumption = base_consumption * horse_prof.stamina_waste_rate * STAMINA_DRAIN_COEFFICIENT * weight_load * accel_factor *  wind_factor * dt
        return max(0.0, horse_snap.stamina - consumption)
    
    def get_target_lane(self, horse_prof: HorseProfile, horse_snap: HorseSnapshot, env: dict) -> float:
        # 環境情報
        section = env[HorseEnvField.SECTION]
        dist_to_context = env[HorseEnvField.DIST_TO_CONTEXT]
        dist_to_front = dist_to_context[HorseEnvField.DIST_TO_FRONT]
        rank = env[HorseEnvField.RANK]
        num_horses = env[HorseEnvField.NUM_HORSES]
        # 評価スコア：低いほど良い（走りやすい）
        lane_scores = {}
        current_lane = horse_snap.lane
        for lane in [current_lane - 1.0, current_lane, current_lane + 1.0]:
            if lane < 1.0: continue # ラチより内側は除外
            score = 0
            # 1. 内側ほど基本スコアが良い（最短距離）
            score += lane * 0.5
            # 2. 前方に馬がいるか？
            if dist_to_front < 2.0:# 非常に近い
                score += 10.0 # 衝突リスク大
            elif dist_to_front < 5.0: # ドラフティング圏内
                # 逃げ馬なら「邪魔」なので避ける、差し馬なら「温存」のため残る
                score -= horse_prof.lane_change_frequency
            lane_scores[lane] = score
        # 最もスコアの低い（有利な）レーンをターゲットにする
        target_lane = min(lane_scores, key=lane_scores.get)
        return target_lane

    def get_next_lane(self, horse_prof: HorseProfile, horse_snap: HorseSnapshot, env: dict, tac: dict, dt: float) -> float:
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

# クラス取得用のMap
STRATEGY_MAP = {
    HorseStrategyType.LEADER: LeaderStrategy(),
    HorseStrategyType.STALKER: StalkerStrategy(),
    HorseStrategyType.CLOSER: CloserStrategy(),
    HorseStrategyType.REAR: RearStrategy(),
}
