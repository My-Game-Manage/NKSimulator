"""
race_processor.py の概要

レース中の各馬の値の処理を行う。
"""
import logging

# ロガーの取得（__name__ はファイル名/モジュール名になる）
logger = logging.getLogger(__name__)

from src.constants.enums import HorseStrategyType, SectionType, SectionName, RaceSurfaceType
from src.constants.fields import HorseEnvField, HorseTacField, HorseOvertake
from src.models.horse_data import HorseProfile, HorseSnapshot
from src.models.race_data import TrackSection, RaceProfile
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
        overtake = tac[HorseTacField.OVERTAKE_DECISION]
        # 基本はmax_speed（ベストな巡航速度）を目指す
        target_v = base_velocity
        if overtake is HorseOvertake.OVERTAKE:
            target_v *= 1.02
        elif overtake is HorseOvertake.SORROUNDED:
            target_v *= 0.98
        if section.type is SectionType.CURVE:
            # コーナーでは係数の分だけ目標速度を減らす->減れば自然と減速
            # コーナー時は95%にtarget_vを95%にダウン
            target_v *= 0.95
            target_v = ph.calculate_target_velocity_at_corner(target_v, corner_radius, horse_snap.lane, horse_prof.cornering_ability)
        return target_v

    @staticmethod
    def get_acceleration(target_v: float, horse_prof: HorseProfile, horse_snap: HorseSnapshot, env: dict, tac: dict) -> float:
        # 基本： accel = acceleration * factor
        # 環境変数を取得
        accel_boost = tac[HorseTacField.ACCEL_BOOST]
        friction = env[HorseEnvField.FRICTION]
        current_v = horse_snap.velocity

        # 2. 速度域によるブースト（低速時は強く）
        boost = 1.0
        if accel_boost > 1.0:
            boost = min(10.0, accel_boost * horse_snap.accel)

        # 1. 速度差による加速減衰（目標に近いほど加速を鈍くする）
        diff_ratio = max(0, (target_v - current_v) / (target_v * 0.5)) if target_v > 0 else 0
        # 0.5乗することで、速度差が小さくなっても比率が大きく保たれる
        adjusted_ratio = diff_ratio ** 0.5

        # 斤量補正：50kgを基準とし、1kgあたり 0.5% 加速度を低下させる
        penalty_rate = (horse_prof.weight_carried - 50) * 0.005
        # 芝やダートの上を走る分の係数を引く
        accel = horse_prof.acceleration * (1.0 - penalty_rate) * (1.0 - friction)

        # 実際の加速度を算出
        actual_acc = accel * max(0.2, adjusted_ratio) * boost

        # 加速力が低くなりすぎないよう下限を設定
        return min(10.0, max(0.2, actual_acc))

    @staticmethod
    def get_next_velocity(target_v: float, accel: float, horse_prof: HorseProfile, horse_snap: HorseSnapshot, env: dict, tac: dict, dt: float) -> float:
        # 基本： current_v と target_v の差で加速／減速になる 
        #   if current_v < target_v: return min(current_v + accel * dt, target_v)
        #   elif current_v > target_v: return max(current_v - accel * dt, target_v)
        #   else: return target_v
        # 環境変数を取得
        current_v = horse_snap.velocity

        if current_v < target_v:
            return min(current_v + accel * dt, target_v)
        elif current_v > target_v:
            # 減速時は今のところ一定、あるいは同様に減衰させても良い
            return max(current_v - accel * dt, target_v)
        else:
            # TODO: 速度維持の個体差をつける
            return current_v

    @staticmethod
    def get_accel_boost(horse_snap: HorseSnapshot) -> float:
        """ブーストするかどうか"""
        if horse_snap.velocity < 3.0:
            return 1.5
        elif horse_snap.velocity < 7.5:
            return 2.0
        elif horse_snap.velocity < 12.0:
            return 1.2
        else:
            return 1.0

    @staticmethod
    def get_spurt_boost(horse_snap: HorseSnapshot) -> float:
        """残り体力からスパート用のブーストを算出"""
        # TODO: 残り体力から算出。最大値を設定しておくこと
        if horse_snap.velocity < 3.0:
            return 1.5
        elif horse_snap.velocity < 7.5:
            return 2.0
        elif horse_snap.velocity < 12.0:
            return 1.2
        else:
            return 1.0

    @staticmethod
    def get_start_accel_boost(horse_snap: HorseSnapshot) -> float:
        """ブーストするかどうか"""
        if horse_snap.velocity < 3.0:
            return 1.5
        elif horse_snap.velocity < 7.5:
            return 2.0
        elif horse_snap.velocity < 12.0:
            return 1.2
        else:
            return 1.0

    @staticmethod
    def get_next_distance(next_velocity: float, horse_prof: HorseProfile, horse_snap: HorseSnapshot, env: dict, dt: float) -> float:
        # 基本： v_avg = (current_v + next_v) / 2 ※台形近似式
        #   next_dist = v_avg * dt
        v_avg = (horse_snap.velocity + next_velocity) / 2
        next_distance = v_avg * dt
        return horse_snap.distance + next_distance

    @staticmethod
    def consume_stamina(next_velocity: float, horse_prof: HorseProfile, horse_snap: HorseSnapshot, env: dict, tac: dict, dt: float) -> float:
        # 基本： base_consumption = v_next ** 2 ※速度の2乗にするとリアリティが出る
        #   cons_stamina = base_compumption * waste_rate * (weight / 50.0) * dt
        consumption = RaceProcessor.get_consumption_stamina(next_velocity, horse_prof, horse_snap, env, tac, dt)
        return max(0.0, horse_snap.stamina - consumption)
    
    @staticmethod
    def get_consumption_stamina(next_velocity: float, horse_prof: HorseProfile, horse_snap: HorseSnapshot, env: dict, tac: dict, dt: float) -> float:
        # 基本： base_consumption = v_next ** 2 ※速度の2乗にするとリアリティが出る
        #   cons_stamina = base_compumption * waste_rate * (weight / 50.0) * dt
        # 環境情報
        ctx = env[HorseEnvField.DIST_TO_CONTEXT]
        dist_to_front = ctx[HorseEnvField.DIST_TO_FRONT]
        front_left = ctx[HorseEnvField.DIST_TO_FRONT_LEFT]
        front_right = ctx[HorseEnvField.DIST_TO_FRONT_RIGHT]
        side_left = ctx[HorseEnvField.DIST_TO_SIDE_LEFT]
        side_right = ctx[HorseEnvField.DIST_TO_SIDE_RIGHT]
        friction = env[HorseEnvField.FRICTION]
        # 戦略情報
        overtake = tac[HorseTacField.OVERTAKE_DECISION]
        # 速度の2乗をベースにする（空気抵抗や筋肉への負荷を表現）
        base_consumption = next_velocity ** 2
        # 斤量による負荷補正（例: 50kgを基準とする）
        weight_load = horse_prof.weight_carried / 50.0
        # 加速中なら消費量を増やす
        accel_factor = 1.3 if next_velocity < horse_snap.velocity else 1.0
        # 囲まれていれば消費量を増やす
        sorrounded_factor = 1.1 if overtake is HorseOvertake.SORROUNDED else 1.0
        # レーンの先頭なら風圧で消費量を増やす
        wind_factor = 1.0
        relevant_dist = min(dist_to_front, front_left, front_right)
        if relevant_dist >= 999:
            wind_factor = 1.1
        elif 2.0 < relevant_dist < 5.0:
            wind_factor = 0.9
        elif side_left < 0.5 or side_right < 0.5:
            wind_factor = 1.1
        # ステップあたりの消費量
        consumption = base_consumption * horse_prof.stamina_waste_rate * STAMINA_DRAIN_COEFFICIENT * (1.0 + friction) * weight_load * accel_factor *  sorrounded_factor * wind_factor * dt
        return consumption

    @staticmethod
    def get_target_lane(horse_prof: HorseProfile, horse_snap: HorseSnapshot, env: dict) -> float:
        # 環境情報
        section = env[HorseEnvField.SECTION]
        dist_to_context = env[HorseEnvField.DIST_TO_CONTEXT]
        rank = env[HorseEnvField.RANK]
        num_horses = env[HorseEnvField.NUM_HORSES]
        ctx = dist_to_context

        # スタートから5秒まではレーン移動しない
        if horse_snap.elapsed_time < 5.0: return horse_snap.lane
    
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
        
    @staticmethod
    def should_start_spurt(next_distance: float, next_velocity: float, horse_prof: HorseProfile, horse_snap: HorseSnapshot, env: dict, tac: dict, dt: float) -> bool:
        # 環境情報
        total_dist = env[HorseEnvField.RACE_DISTANCE]
        remaining_dist = total_dist - next_distance
    
        # 物理的な限界点（このままの速度でゴールまでスタミナが持つか？）を計算
        estimated_consumtion_at_spurt = RaceProcessor.get_consumption_stamina(next_velocity, horse_prof, horse_snap, env, tac, dt)
        can_run_dist = horse_snap.stamina / (estimated_consumtion_at_spurt / horse_prof.last_3f_speed)
    
        # 残り距離が「全力で走れる距離」以下になったら強制スパート
        #if remaining_dist <= can_run_dist:
        #    return True
        
        # それ以外は、脚質ごとの理想地点まで待機
        return remaining_dist <= horse_prof.target_spurt_dist

    @staticmethod
    def get_friction_factor(race_prof: RaceProfile) -> float:
        """馬場の基本係数を取得"""
        return race_prof.surface_friction if race_prof.surface == RaceSurfaceType.DIRT else race_prof.turf_friction
