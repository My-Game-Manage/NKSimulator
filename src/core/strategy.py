"""
strategy.py の概要

脚質に応じたStrategy（Protocol）を提供する特殊クラス群
"""
from typing import Protocol

import logging

# ロガーの取得（__name__ はファイル名/モジュール名になる）
logger = logging.getLogger(__name__)

from src.constants.enums import HorseStrategyType, SectionType, SectionName
from src.models.horse_data import HorseProfile, HorseSnapshot
from src.models.race_data import TrackSection
import src.core.physics as ph


# ---------------------------------------------------------
# Strategy（Protocol）パターンの基底クラス
# ---------------------------------------------------------
class RacingStrategy(Protocol):
    def get_target_velocity(self, velocity: float, horse_prof: HorseProfile, horse_snap: HorseSnapshot, section: TrackSection, dist_to_front: float, corner_penalty: float) -> float:
        ...

    def get_spurt_velocity(self, horse_prof: HorseProfile, horse_snap: HorseSnapshot, section: TrackSection, corner_penalty: float) -> float:
        ...

    def get_acceleration(self, target_v: float, horse_prof: HorseProfile, horse_snap: HorseSnapshot, friction: float) -> float:
        ...

    def get_next_velocity(self, horse_snap: HorseSnapshot, accel: float, dt: float) -> float:
        ...

    def get_next_distance(self, horse_snap: HorseSnapshot, next_velocity: float, dt: float) -> float:
        ...

    def consume_stamina(self, total_stamina: float, next_velocity: float, horse_snap: HorseSnapshot, section: TrackSection, distance: float, dist_to_front: float, friction: float, is_spurt: bool, dt: float) -> float:
        ...

    def get_next_lane(self, horse_snap: HorseSnapshot, section: TrackSection, dist_to_front: float, rank: int) -> float:
        ...


# ---------------------------------------------------------
# 具象Strategyクラス：逃げ
# ---------------------------------------------------------
class LeaderStrategy:
    def get_target_velocity(self, velocity: float, horse_prof: HorseProfile, horse_snap: HorseSnapshot, section: TrackSection, dist_to_front: float, corner_penalty: float) -> float:
        # 基本はmax_speed（ベストな巡航速度）を目指す
        target_v = velocity
        if section.type is SectionType.CURVE:
            # コーナーでは係数の分だけ目標速度を減らす->減れば自然と減速
            target_v *= (1.0 - corner_penalty * horse_prof.cornering_ability)
        elif dist_to_front <= 0.5:
            # 前にいる場合は維持
            return horse_snap.velocity
        return target_v

    def get_acceleration(self, target_v: float, horse_prof: HorseProfile, horse_snap: HorseSnapshot, friction: float) -> float:
        # 芝やダートの上を走る分の係数を引く
        accel = horse_prof.acceleration - friction
        if target_v < horse_snap.velocity:
            # 減速処理: 加速より負荷がかかる
            return -(accel * 1.1 + friction)
        else:
            # 加速処理
            diff_v = target_v - horse_snap.velocity
            return diff_v * accel

    def get_next_velocity(self, horse_snap: HorseSnapshot, accel: float, dt: float) -> float:
        return horse_snap.velocity + accel * dt

    def get_next_distance(self, horse_snap: HorseSnapshot, next_velocity: float, dt: float) -> float:
        lane_mod = horse_snap.lane * 0.01
        return horse_snap.distance - lane_mod + next_velocity * dt

    def consume_stamina(self, total_stamina: float, next_velocity: float, horse_snap: HorseSnapshot, section: TrackSection, distance: float, dist_to_front: float, friction: float, is_spurt: bool, dt: float) -> float:
        base_consumption = ph.calculate_stamina_consumption(next_velocity, distance, total_stamina, dt)
        current_stamina = horse_snap.stamina
        factor = 1.2 if is_spurt else 1.0
        if section.type is SectionType.CURVE:
            # カーブは負荷がかかる
            factor += 0.1
        if dist_to_front <= 0.5:
            # 前にいる場合は温存
            factor -= 0.1
        return max(0.0, current_stamina - (base_consumption + friction) * factor)

    def get_next_lane(self, horse_snap: HorseSnapshot, section: TrackSection, dist_to_front: float, rank: int) -> float:
        current_lane = horse_snap.lane
        if dist_to_front > 0.5:
            # 前にいない判定
            if current_lane <= 1.0:
                return horse_snap.lane
            else:
                return current_lane - 0.1
        else:
            # 前にいる場合
            if rank < 6:
                # 先団ならそのまま
                return current_lane
            else:
                # 違うなら追い抜く
                return current_lane + 0.1

# ---------------------------------------------------------
# 具象Strategyクラス：先行
# ---------------------------------------------------------
class StalkerStrategy:
    def get_target_velocity(self, velocity: float, horse_prof: HorseProfile, horse_snap: HorseSnapshot, section: TrackSection, dist_to_front: float, corner_penalty: float) -> float:
        # 基本はmax_speed（ベストな巡航速度）を目指す
        target_v = velocity
        if section.type is SectionType.CURVE:
            # コーナーでは係数の分だけ目標速度を減らす->減れば自然と減速
            target_v *= (1.0 - corner_penalty * horse_prof.cornering_ability)
        elif dist_to_front <= 0.5:
            # 前にいる場合は維持
            return horse_snap.velocity
        return target_v
    
    def get_acceleration(self, target_v: float, horse_prof: HorseProfile, horse_snap: HorseSnapshot, friction: float) -> float:
        # 芝やダートの上を走る分の係数を引く
        accel = horse_prof.acceleration - friction
        if target_v < horse_snap.velocity:
            # 減速処理: 加速より負荷がかかる
            return -(accel * 1.1 + friction)
        else:
            # 加速処理
            diff_v = target_v - horse_snap.velocity
            return diff_v * accel

    def get_next_velocity(self, horse_snap: HorseSnapshot, accel: float, dt: float) -> float:
        return horse_snap.velocity + accel * dt

    def get_next_distance(self, horse_snap: HorseSnapshot, next_velocity: float, dt: float) -> float:
        lane_mod = horse_snap.lane * 0.01
        return horse_snap.distance - lane_mod + next_velocity * dt

    def consume_stamina(self, total_stamina: float, next_velocity: float, horse_snap: HorseSnapshot, section: TrackSection, distance: float, dist_to_front: float, friction: float, is_spurt: bool, dt: float) -> float:
        base_consumption = ph.calculate_stamina_consumption(next_velocity, distance, total_stamina, dt)
        current_stamina = horse_snap.stamina
        factor = 1.2 if is_spurt else 1.0
        if section.type is SectionType.CURVE:
            # カーブは負荷がかかる
            factor += 0.1
        if dist_to_front <= 0.5:
            # 前にいる場合は温存
            factor -= 0.1
        return max(0.0, current_stamina - (base_consumption + friction) * factor)

    def get_next_lane(self, horse_snap: HorseSnapshot, section: TrackSection, dist_to_front: float, rank: int) -> float:
        current_lane = horse_snap.lane
        if dist_to_front > 0.5:
            # 前にいない判定
            if current_lane <= 3.0:
                return horse_snap.lane
            else:
                return current_lane - 0.1
        else:
            # 前にいる場合
            if rank < 6:
                # 先団ならそのまま
                return current_lane
            else:
                # 違うなら追い抜く
                return current_lane + 0.1

# ---------------------------------------------------------
# 具象Strategyクラス：差し
# ---------------------------------------------------------
class CloserStrategy:
    def get_target_velocity(self, velocity: float, horse_prof: HorseProfile, horse_snap: HorseSnapshot, section: TrackSection, dist_to_front: float, corner_penalty: float) -> float:
        # 基本はmax_speed（ベストな巡航速度）を目指す
        target_v = velocity
        if section.type is SectionType.CURVE:
            # コーナーでは係数の分だけ目標速度を減らす->減れば自然と減速
            target_v *= (1.0 - corner_penalty * horse_prof.cornering_ability)
        elif dist_to_front <= 0.5:
            # 前にいる場合は維持
            return horse_snap.velocity
        return target_v
    
    def get_acceleration(self, target_v: float, horse_prof: HorseProfile, horse_snap: HorseSnapshot, friction: float) -> float:
        # 芝やダートの上を走る分の係数を引く
        accel = horse_prof.acceleration - friction
        if target_v < horse_snap.velocity:
            # 減速処理: 加速より負荷がかかる
            return -(accel * 1.1 + friction)
        else:
            # 加速処理
            diff_v = target_v - horse_snap.velocity
            return diff_v * accel

    def get_next_velocity(self, horse_snap: HorseSnapshot, accel: float, dt: float) -> float:
        return horse_snap.velocity + accel * dt

    def get_next_distance(self, horse_snap: HorseSnapshot, next_velocity: float, dt: float) -> float:
        lane_mod = horse_snap.lane * 0.01
        return horse_snap.distance - lane_mod + next_velocity * dt

    def consume_stamina(self, total_stamina: float, next_velocity: float, horse_snap: HorseSnapshot, section: TrackSection, distance: float, dist_to_front: float, friction: float, is_spurt: bool, dt: float) -> float:
        base_consumption = ph.calculate_stamina_consumption(next_velocity, distance, total_stamina, dt)
        current_stamina = horse_snap.stamina
        factor = 1.2 if is_spurt else 0.9
        if section.type is SectionType.CURVE:
            # カーブは負荷がかかる
            factor += 0.1
        if dist_to_front <= 0.5:
            # 前にいる場合は温存
            factor -= 0.1
        return max(0.0, current_stamina - (base_consumption + friction) * factor)

    def get_next_lane(self, horse_snap: HorseSnapshot, section: TrackSection, dist_to_front: float, rank: int) -> float:
        current_lane = horse_snap.lane
        if dist_to_front > 0.5:
            # 前にいない判定
            if current_lane <= 5.0:
                return horse_snap.lane
            else:
                return current_lane - 0.1
        else:
            # 前にいる場合
            if rank < 10:
                # 中団までならそのまま
                return current_lane
            else:
                # 違うなら追い抜く
                return current_lane + 0.1

# ---------------------------------------------------------
# 具象Strategyクラス：追い込み
# ---------------------------------------------------------
class RearStrategy:
    def get_target_velocity(self, velocity: float, horse_prof: HorseProfile, horse_snap: HorseSnapshot, section: TrackSection, dist_to_front: float, corner_penalty: float) -> float:
        # 基本はmax_speed（ベストな巡航速度）を目指す
        target_v = velocity
        if section.type is SectionType.CURVE:
            # コーナーでは係数の分だけ目標速度を減らす->減れば自然と減速
            target_v *= (1.0 - corner_penalty * horse_prof.cornering_ability)
        elif dist_to_front <= 0.5:
            # 前にいる場合は維持
            return horse_snap.velocity
        return target_v
    
    def get_acceleration(self, target_v: float, horse_prof: HorseProfile, horse_snap: HorseSnapshot, friction: float) -> float:
        # 芝やダートの上を走る分の係数を引く
        accel = horse_prof.acceleration - friction
        if target_v < horse_snap.velocity:
            # 減速処理: 加速より負荷がかかる
            return -(accel * 1.1 + friction)
        else:
            # 加速処理
            diff_v = target_v - horse_snap.velocity
            return diff_v * accel

    def get_next_velocity(self, horse_snap: HorseSnapshot, accel: float, dt: float) -> float:
        return horse_snap.velocity + accel * dt

    def get_next_distance(self, horse_snap: HorseSnapshot, next_velocity: float, dt: float) -> float:
        lane_mod = horse_snap.lane * 0.01
        return horse_snap.distance - lane_mod + next_velocity * dt

    def consume_stamina(self, total_stamina: float, next_velocity: float, horse_snap: HorseSnapshot, section: TrackSection, distance: float, dist_to_front: float, friction: float, is_spurt: bool, dt: float) -> float:
        base_consumption = ph.calculate_stamina_consumption(next_velocity, distance, total_stamina, dt)
        current_stamina = horse_snap.stamina
        factor = 1.2 if is_spurt else 0.9
        if section.type is SectionType.CURVE:
            # カーブは負荷がかかる
            factor += 0.1
        if dist_to_front <= 0.5:
            # 前にいる場合は温存
            factor -= 0.1
        return max(0.0, current_stamina - (base_consumption + friction) * factor)

    def get_next_lane(self, horse_snap: HorseSnapshot, section: TrackSection, dist_to_front: float, rank: int) -> float:
        current_lane = horse_snap.lane
        if dist_to_front > 0.5:
            # 前にいない判定
            if current_lane <= 3.0:
                return horse_snap.lane
            else:
                return current_lane - 0.1
        else:
            # 前にいる場合
            if section.name is SectionName.HOMESTRETCH:
                # 最後の直線なら抜くために移動
                return current_lane + 0.5
            else:
                # 違うならそのまま
                return current_lane

# クラス取得用のMap
STRATEGY_MAP = {
    HorseStrategyType.LEADER: LeaderStrategy(),
    HorseStrategyType.STALKER: StalkerStrategy(),
    HorseStrategyType.CLOSER: CloserStrategy(),
    HorseStrategyType.REAR: RearStrategy(),
}
