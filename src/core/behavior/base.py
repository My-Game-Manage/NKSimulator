"""
base.py の概要

レース中の馬の状態による挙動の違いを表現するStateパターンのための基底クラスの定義。
"""
from abc import ABC, abstractmethod
import logging

# ロガーの取得（__name__ はファイル名/モジュール名になる）
logger = logging.getLogger(__name__)

from src.models.race_data import RaceProfile, RaceSnapshot
from src.models.horse_data import HorseProfile, HorseSnapshot, HorseEnvironment, HorseTactics, HorseParam, DistContext

from src.core.strategy import RacingStrategy, STRATEGY_MAP

import src.core.race_logics as logi


# ---------------------------------------------------------
# 基底クラス（HorseBehaviorState）
# ---------------------------------------------------------
class HorseBehaviorState(ABC):
    """
    レース中の馬のデータ更新のためのStateパターンのための基底クラス
    """
    @abstractmethod
    def update(self, horse_id: str, race_prof: RaceProfile, race_snap: RaceSnapshot, dt: float) -> HorseSnapshot:
        ...

    def get_strategy(self, horse_prof: HorseProfile) -> RacingStrategy:
        """RacingStrategyを返す"""
        return STRATEGY_MAP[horse_prof.strategy]

    def get_horse_environment(self, horse_id: str, race_prof: RaceProfile, race_snap: RaceSnapshot) -> HorseEnvironment:
        """環境情報の取得"""
        current_snap = race_snap.horses[horse_id]

        # 情報取得
        race_distance = race_prof.distance
        surface = race_prof.surface
        condition = race_prof.condition
        section = logi.get_current_section(current_snap.distance, race_prof.sections)
        dist_ctx = logi.get_dist_context(horse_id, race_snap.horses)
        rank = race_snap.ranks[horse_id]
        friction = logi.get_friction_factor(race_prof)
        corner_radius = race_prof.corner_radius
        num_horses = len(race_snap.ranks)

        return HorseEnvironment(
            race_distance=race_distance,
            surface=surface,
            condition=condition,
            friction=friction,
            corner_radius=corner_radius,
            num_horses=num_horses,
            rank=rank,
            dist_context=dist_ctx,
            section=section,
        )

    def determinate_tactics(self, horse_id: str, race_prof: RaceProfile, race_snap: RaceSnapshot, env: HorseEnvironment) -> HorseTactics:
        """戦略情報の決定"""
        # 情報取得
        horse_prof = race_prof.horses[horse_id]
        current_snap = race_snap.horses[horse_id]

        target_velocity = horse_prof.cruise_speed
        accel_power = horse_prof.cruise_acceleration
        target_lane = logi.get_target_lane(horse_prof, current_snap, env)
        race_decision = logi.get_race_strategy_decision(horse_prof, current_snap, env)

        return HorseTactics(
            target_velocity=target_velocity,
            accel_power=accel_power,
            target_lane=target_lane,
            race_decision=race_decision,
        )

    def get_horse_parameter(self, horse_prof: HorseProfile, horse_snap: HorseSnapshot, env: HorseEnvironment, tac: HorseTactics, dt: float) -> HorseParam:
        """パラメータの取得"""
        # 情報取得
        
        # 値の計算
        target_v = logi.get_target_velocity(horse_prof, horse_snap, env, tac)
        accel_power = logi.get_acceleration(target_v, horse_prof, horse_snap, env, tac)
        next_velocity = logi.get_next_velocity(target_v, accel_power, horse_prof, horse_snap, env, tac, dt)
        next_distance = logi.get_next_distance(next_velocity, horse_prof, horse_snap, env, dt)
        next_stamina = logi.get_next_stamina(next_velocity, horse_prof, horse_snap, env, tac, dt)
        next_lane = logi.get_next_lane(horse_prof, horse_snap, env, tac, dt)
        actual_accel = logi.get_actual_accel(next_velocity, horse_snap.velocity)

        return HorseParam(
            target_velocity=target_v,
            accel_power=accel_power,
            actual_accel=actual_accel,
            next_velocity=next_velocity,
            next_distance=next_distance,
            next_stamina=next_stamina,
            next_lane=next_lane,
        )
