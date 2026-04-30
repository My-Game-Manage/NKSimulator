"""
strategy.py の概要

脚質に応じたStrategy（Protocol）を提供する特殊クラス群
"""
from typing import Protocol

from src.constants.enums import HorseStrategyType, SectionType
from src.models.horse_data import HorseProfile, HorseSnapshot
from src.models.race_data import TrackSection
import src.core.physics as ph


# ---------------------------------------------------------
# Strategy（Protocol）パターンの基底クラス
# ---------------------------------------------------------
class RacingStrategy(Protocol):
    def get_target_velocity(self, horse_prof: HorseProfile, horse_snap: HorseSnapshot, section: TrackSection, corner_penalty: float) -> float:
        ...

    def get_acceleration(self, target_v: float, horse_prof: HorseProfile, horse_snap: HorseSnapshot, friction: float) -> float:
        ...

    def get_next_velocity(self, horse_snap: HorseSnapshot, accel: float, dt: float) -> float:
        ...

    def get_next_distance(self, horse_snap: HorseSnapshot, next_velocity: float, dt: float) -> float:
        ...

    def consume_stamina(self, total_stamina: float, next_velocity: float, horse_snap: HorseSnapshot, distance: float, dt: float) -> float:
        ...


# ---------------------------------------------------------
# 具象Strategyクラス：逃げ
# ---------------------------------------------------------
class LeaderStrategy:
    def get_target_velocity(self, horse_prof: HorseProfile, horse_snap: HorseSnapshot, section: TrackSection, corner_penalty: float) -> float:
        # 基本はmax_speed（ベストな巡航速度）を目指す
        target_v = horse_prof.max_speed
        if section.type is SectionType.CURVE:
            # コーナーでは係数の分だけ目標速度を減らす->減れば自然と減速
            target_v *= (1.0 - corner_penalty)
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
        return horse_snap.distance + next_velocity * dt

    def consume_stamina(self, total_stamina: float, next_velocity: float, horse_snap: HorseSnapshot, distance: float, dt: float) -> float:
        base_consumption = ph.calculate_stamina_consumption(next_velocity, distance, total_stamina, dt)
        current_stamina = horse_snap.stamina
        return current_stamina - base_consumption

# ---------------------------------------------------------
# 具象Strategyクラス：先行
# ---------------------------------------------------------
class StalkerStrategy:
    def get_target_velocity(self, horse_prof: HorseProfile, horse_snap: HorseSnapshot, section: TrackSection, corner_penalty: float) -> float:
        # 基本はmax_speed（ベストな巡航速度）を目指す
        target_v = horse_prof.max_speed
        if section.type is SectionType.CURVE:
            # コーナーでは係数の分だけ目標速度を減らす->減れば自然と減速
            target_v *= (1.0 - corner_penalty)
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
        return horse_snap.distance + next_velocity * dt

    def consume_stamina(self, total_stamina: float, next_velocity: float, horse_snap: HorseSnapshot, distance: float, dt: float) -> float:
        base_consumption = ph.calculate_stamina_consumption(next_velocity, distance, total_stamina, dt)
        current_stamina = horse_snap.stamina
        return current_stamina - base_consumption

# ---------------------------------------------------------
# 具象Strategyクラス：差し
# ---------------------------------------------------------
class CloserStrategy:
    def get_target_velocity(self, horse_prof: HorseProfile, horse_snap: HorseSnapshot, section: TrackSection, corner_penalty: float) -> float:
        # 基本はmax_speed（ベストな巡航速度）を目指す
        target_v = horse_prof.max_speed
        if section.type is SectionType.CURVE:
            # コーナーでは係数の分だけ目標速度を減らす->減れば自然と減速
            target_v *= (1.0 - corner_penalty)
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
        return horse_snap.distance + next_velocity * dt

    def consume_stamina(self, total_stamina: float, next_velocity: float, horse_snap: HorseSnapshot, distance: float, dt: float) -> float:
        base_consumption = ph.calculate_stamina_consumption(next_velocity, distance, total_stamina, dt)
        current_stamina = horse_snap.stamina
        return current_stamina - base_consumption

# ---------------------------------------------------------
# 具象Strategyクラス：追い込み
# ---------------------------------------------------------
class RearStrategy:
    def get_target_velocity(self, horse_prof: HorseProfile, horse_snap: HorseSnapshot, section: TrackSection, corner_penalty: float) -> float:
        # 基本はmax_speed（ベストな巡航速度）を目指す
        target_v = horse_prof.max_speed
        if section.type is SectionType.CURVE:
            # コーナーでは係数の分だけ目標速度を減らす->減れば自然と減速
            target_v *= (1.0 - corner_penalty)
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
        return horse_snap.distance + next_velocity * dt

    def consume_stamina(self, total_stamina: float, next_velocity: float, horse_snap: HorseSnapshot, distance: float, dt: float) -> float:
        base_consumption = ph.calculate_stamina_consumption(next_velocity, distance, total_stamina, dt)
        current_stamina = horse_snap.stamina
        return current_stamina - base_consumption

# クラス取得用のMap
STRATEGY_MAP = {
    HorseStrategyType.LEADER: LeaderStrategy(),
    HorseStrategyType.STALKER: StalkerStrategy(),
    HorseStrategyType.CLOSER: CloserStrategy(),
    HorseStrategyType.REAR: RearStrategy(),
}
