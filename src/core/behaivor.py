"""
behaivor.py の概要

馬のレース中の動きをStateパターンで実装する
"""
from abc import ABC, abstractmethod
from dataclasses import replace
import logging

# ロガーの取得（__name__ はファイル名/モジュール名になる）
logger = logging.getLogger(__name__)

from src.models.race_data import RaceProfile, RaceSnapshot
from src.models.horse_data import HorseProfile, HorseSnapshot
from src.constants.fields import HorseSnapField, HorseEnvField, HorseTacField
from src.constants.enums import HorseBehaviorType
from src.core.strategy import RacingStrategy, STRATEGY_MAP
import src.core.physics as ph
from src.core.race_processor import RaceProcessor as proc


# ---------------------------------------------------------
# Stateパターンの基底クラス
# ---------------------------------------------------------
class HorseBehaviorState(ABC):
    @abstractmethod
    def update(self, horse_id: str, race_prof: RaceProfile, race_snap: RaceSnapshot, dt: float) -> HorseSnapshot:
        """
        この状態における馬の物理更新・ステータス更新ロジック。
        次のHorseSnapshotオブジェクトを返す。
        """
        ...

    def get_strategy(self, horse_prof: HorseProfile) -> RacingStrategy:
        """RacingStrategyを返す"""
        return STRATEGY_MAP[horse_prof.strategy]

# ---------------------------------------------------------
# 具象Stateクラス：スタート前 (InGate)
# ---------------------------------------------------------
class InGateState(HorseBehaviorState):
    def update(self, horse_id: str, race_prof: RaceProfile, race_snap: RaceSnapshot, dt: float) -> HorseSnapshot:
        h_prof = race_prof.horses[horse_id] 
        current_snap = race_snap.horses[horse_id]
        # ゲートを出る（laneはそのままで、加速と最初の距離だけ計算）
        # gate_reactionで距離に補正をかける。高いほど前を取りやすい
        # 環境情報の設定
        env = {}
        # 環境情報取得
        env[HorseEnvField.RACE_DISTANCE] = race_prof.distance
        env[HorseEnvField.SECTION] = ph.get_current_section(current_snap.distance, race_prof.sections)
        env[HorseEnvField.DIST_TO_CONTEXT] = ph.get_dist_to_front_context(horse_id, race_snap.horses)
        env[HorseEnvField.RANK] = race_snap.ranks[horse_id]
        env[HorseEnvField.FRICTION] = race_prof.surface_friction if race_prof.surface == "ダ" else race_prof.turf_friction
        env[HorseEnvField.CORNER_RADIUS] = race_prof.corner_radius
        env[HorseEnvField.NUM_HORSES] = len(race_snap.ranks)
        # 戦略情報決定
        tac = {}
        # 戦略情報取得
        tac[HorseTacField.TARGET_LANE] = proc.get_target_lane(h_prof, current_snap, env)
        # 各数値を算出
        base_velocity = h_prof.cruise_speed
        target_v = proc.get_target_velocity(base_velocity, h_prof, current_snap, env, tac)
        accel = proc.get_acceleration(h_prof, current_snap, env) * h_prof.gate_reaction
        next_velocity = proc.get_next_velocity(target_v, accel, h_prof, current_snap, env, dt)
        next_distance = proc.get_next_distance(next_velocity, h_prof, current_snap, env, dt)
        next_stamina = proc.consume_stamina(next_velocity, h_prof, current_snap, env, dt)
        next_lane = proc.get_next_lane(h_prof, current_snap, env, tac, dt)
        # StateをStartingに変更
        next_behavior = HorseBehaviorType.STARTING
        return replace(current_snap,
                       step=ph.calc_next_step(current_snap.step),
                       elapsed_time=ph.calc_next_elapsted_time(current_snap.elapsed_time, dt),
                       velocity=next_velocity,
                       distance=next_distance,
                       stamina=next_stamina,
                       lane=next_lane,
                       dist_to_front=env[HorseEnvField.DIST_TO_CONTEXT][HorseEnvField.DIST_TO_FRONT],
                       behavior=next_behavior,
                       )


# ---------------------------------------------------------
# 具象Stateクラス：スタート状態 (Starting)
# ---------------------------------------------------------
class StartingState(HorseBehaviorState):
    def update(self, horse_id: str, race_prof: RaceProfile, race_snap: RaceSnapshot, dt: float) -> HorseSnapshot:
        h_prof = race_prof.horses[horse_id] 
        current_snap = race_snap.horses[horse_id]
        # 環境情報の設定
        env = {}
        # 環境情報取得
        env[HorseEnvField.RACE_DISTANCE] = race_prof.distance
        env[HorseEnvField.SECTION] = ph.get_current_section(current_snap.distance, race_prof.sections)
        env[HorseEnvField.DIST_TO_CONTEXT] = ph.get_dist_to_front_context(horse_id, race_snap.horses)
        env[HorseEnvField.RANK] = race_snap.ranks[horse_id]
        env[HorseEnvField.FRICTION] = race_prof.surface_friction if race_prof.surface == "ダ" else race_prof.turf_friction
        env[HorseEnvField.CORNER_RADIUS] = race_prof.corner_radius
        env[HorseEnvField.NUM_HORSES] = len(race_snap.ranks)
        # 戦略情報決定
        tac = {}
        # 戦略情報取得
        tac[HorseTacField.TARGET_LANE] = proc.get_target_lane(h_prof, current_snap, env)
        # 各数値を算出
        base_velocity = h_prof.cruise_speed
        target_v = proc.get_target_velocity(base_velocity, h_prof, current_snap, env, tac)
        accel = proc.get_acceleration(h_prof, current_snap, env) * 1.2
        next_velocity = proc.get_next_velocity(target_v, accel, h_prof, current_snap, env, dt)
        next_distance = proc.get_next_distance(next_velocity, h_prof, current_snap, env, dt)
        next_stamina = proc.consume_stamina(next_velocity, h_prof, current_snap, env, dt)
        next_lane = proc.get_next_lane(h_prof, current_snap, env, tac, dt)

        next_behavior = current_snap.behavior

        # 巡航速度に近づく、スタート区間が終わる、100mを超える、とレース中に状態遷移
        if next_velocity >= base_velocity or ph.is_start_section(next_distance, race_prof.sections[1]):
            next_behavior = HorseBehaviorType.RACING
        return replace(current_snap,
                       step=ph.calc_next_step(current_snap.step),
                       elapsed_time=ph.calc_next_elapsted_time(current_snap.elapsed_time, dt),
                       velocity=next_velocity,
                       distance=next_distance,
                       stamina=next_stamina,
                       lane=next_lane,
                       dist_to_front=env[HorseEnvField.DIST_TO_CONTEXT][HorseEnvField.DIST_TO_FRONT],
                       behavior=next_behavior,
                       )


# ---------------------------------------------------------
# 具象Stateクラス：ゴール後 (Finished)
# ---------------------------------------------------------
class FinishedState(HorseBehaviorState):
    def update(self, horse_id: str, race_prof: RaceProfile, race_snap: RaceSnapshot, dt: float) -> HorseSnapshot:
        # ゴール済みの馬は、物理計算を行わず時間を進めるだけ
        current_snap = race_snap.horses[horse_id]
        return current_snap.next_step()


# ---------------------------------------------------------
# 具象Stateクラス：スパート状態 (Spurting)
# ---------------------------------------------------------
class SpurtingState(HorseBehaviorState):
    def update(self, horse_id: str, race_prof: RaceProfile, race_snap: RaceSnapshot, dt: float) -> HorseSnapshot:
        h_prof = race_prof.horses[horse_id] 
        current_snap = race_snap.horses[horse_id]
        # 環境情報の設定
        env = {}
        # 環境情報取得
        env[HorseEnvField.RACE_DISTANCE] = race_prof.distance
        env[HorseEnvField.SECTION] = ph.get_current_section(current_snap.distance, race_prof.sections)
        env[HorseEnvField.DIST_TO_CONTEXT] = ph.get_dist_to_front_context(horse_id, race_snap.horses)
        env[HorseEnvField.RANK] = race_snap.ranks[horse_id]
        env[HorseEnvField.FRICTION] = race_prof.surface_friction if race_prof.surface == "ダ" else race_prof.turf_friction
        env[HorseEnvField.CORNER_RADIUS] = race_prof.corner_radius
        env[HorseEnvField.NUM_HORSES] = len(race_snap.ranks)
        # 戦略情報決定
        tac = {}
        # 戦略情報取得
        tac[HorseTacField.TARGET_LANE] = proc.get_target_lane(h_prof, current_snap, env)
        # 各数値を算出
        base_velocity = h_prof.last_3f_speed
        target_v = proc.get_target_velocity(base_velocity, h_prof, current_snap, env, tac)
        accel = proc.get_acceleration(h_prof, current_snap, env) * 1.5
        next_velocity = proc.get_next_velocity(target_v, accel, h_prof, current_snap, env, dt)
        next_distance = proc.get_next_distance(next_velocity, h_prof, current_snap, env, dt)
        next_stamina = proc.consume_stamina(next_velocity, h_prof, current_snap, env, dt)
        next_lane = proc.get_next_lane(h_prof, current_snap, env, tac, dt)

        next_behavior = current_snap.behavior
        is_finished = False
        finish_time = None
        time_at_600m = current_snap.time_at_600m

        # ゴール判定　->　ゴールしていたらタイムを計測し状態遷移
        if ph.is_horse_finished(next_distance, race_prof.distance):
            # ゴールしていれば時間を記録
            finish_time = ph.interpolate_goal_time(current_snap.distance, next_distance,
                                                   current_snap.elapsed_time, dt, race_prof.distance)
            # 上り3Fを記録
            if current_snap.time_at_600m:
                time_at_600m = finish_time - current_snap.time_at_600m
            # フラグを調整
            is_finished = True
            next_behavior = HorseBehaviorType.FINISHED
        elif ph.is_exhausted(next_stamina, h_prof.total_stamina):
            # バテたので状態遷移
            next_behavior = HorseBehaviorType.EXHAUSTED
        return replace(current_snap,
                       step=ph.calc_next_step(current_snap.step),
                       elapsed_time=ph.calc_next_elapsted_time(current_snap.elapsed_time, dt),
                       velocity=next_velocity,
                       distance=next_distance,
                       stamina=next_stamina,
                       lane=next_lane,
                       dist_to_front=env[HorseEnvField.DIST_TO_CONTEXT][HorseEnvField.DIST_TO_FRONT],
                       behavior=next_behavior,
                       is_finished=is_finished,
                       finish_time=finish_time,
                       time_at_600m=time_at_600m,
                       )


# ---------------------------------------------------------
# 具象Stateクラス：走行中 (Racing)
# ---------------------------------------------------------
class RacingState(HorseBehaviorState):
    def update(self, horse_id: str, race_prof: RaceProfile, race_snap: RaceSnapshot, dt: float) -> HorseSnapshot:
        h_prof = race_prof.horses[horse_id] 
        current_snap = race_snap.horses[horse_id]
        # 環境情報の設定
        env = {}
        # 環境情報取得
        env[HorseEnvField.RACE_DISTANCE] = race_prof.distance
        env[HorseEnvField.SECTION] = ph.get_current_section(current_snap.distance, race_prof.sections)
        env[HorseEnvField.DIST_TO_CONTEXT] = ph.get_dist_to_front_context(horse_id, race_snap.horses)
        env[HorseEnvField.RANK] = race_snap.ranks[horse_id]
        env[HorseEnvField.FRICTION] = race_prof.surface_friction if race_prof.surface == "ダ" else race_prof.turf_friction
        env[HorseEnvField.CORNER_RADIUS] = race_prof.corner_radius
        env[HorseEnvField.NUM_HORSES] = len(race_snap.ranks)
        # 戦略情報決定
        tac = {}
        # 戦略情報取得
        tac[HorseTacField.TARGET_LANE] = proc.get_target_lane(h_prof, current_snap, env)
        # 各数値を算出
        base_velocity = h_prof.cruise_speed
        target_v = proc.get_target_velocity(base_velocity, h_prof, current_snap, env, tac)
        accel = proc.get_acceleration(h_prof, current_snap, env)
        next_velocity = proc.get_next_velocity(target_v, accel, h_prof, current_snap, env, dt)
        next_distance = proc.get_next_distance(next_velocity, h_prof, current_snap, env, dt)
        next_stamina = proc.consume_stamina(next_velocity, h_prof, current_snap, env, dt)
        next_lane = proc.get_next_lane(h_prof, current_snap, env, tac, dt)

        next_behavior = current_snap.behavior
        is_finished = False
        finish_time = None
        time_at_600m = current_snap.time_at_600m

        # 4. ゴール判定と状態遷移
        if ph.is_horse_finished(next_distance, race_prof.distance):
            # ゴールしていれば時間を記録
            finish_time = ph.interpolate_goal_time(current_snap.distance, next_distance,
                                                   current_snap.elapsed_time, dt, race_prof.distance)
            # 上り3Fを記録
            if current_snap.time_at_600m:
                time_at_600m = finish_time - current_snap.time_at_600m
            # フラグを調整
            is_finished = True
            next_behavior = HorseBehaviorType.FINISHED
        elif ph.is_spurt_distance(next_distance, h_prof.target_spurt_dist, race_prof.distance):
            # スパート開始
            next_behavior = HorseBehaviorType.SPURTING
        elif ph.is_exhausted(next_stamina, h_prof.total_stamina):
            # バテたので状態遷移
            next_behavior = HorseBehaviorType.EXHAUSTED

        # 走行を継続
        return replace(current_snap,
                       step=ph.calc_next_step(current_snap.step),
                       elapsed_time=ph.calc_next_elapsted_time(current_snap.elapsed_time, dt),
                       velocity=next_velocity,
                       distance=next_distance,
                       stamina=next_stamina,
                       lane=next_lane,
                       dist_to_front=env[HorseEnvField.DIST_TO_CONTEXT][HorseEnvField.DIST_TO_FRONT],
                       behavior=next_behavior,
                       is_finished=is_finished,
                       finish_time=finish_time,
                       time_at_600m=time_at_600m,
                       )


# ---------------------------------------------------------
# 具象Stateクラス：バテた状態 (Exhausted)
# ---------------------------------------------------------
class ExhaustedState(HorseBehaviorState):
    def update(self, horse_id: str, race_prof: RaceProfile, race_snap: RaceSnapshot, dt: float) -> HorseSnapshot:
        h_prof = race_prof.horses[horse_id] 
        current_snap = race_snap.horses[horse_id]
        # 環境情報の設定
        env = {}
        # 環境情報取得
        env[HorseEnvField.RACE_DISTANCE] = race_prof.distance
        env[HorseEnvField.SECTION] = ph.get_current_section(current_snap.distance, race_prof.sections)
        env[HorseEnvField.DIST_TO_CONTEXT] = ph.get_dist_to_front_context(horse_id, race_snap.horses)
        env[HorseEnvField.RANK] = race_snap.ranks[horse_id]
        env[HorseEnvField.FRICTION] = race_prof.surface_friction if race_prof.surface == "ダ" else race_prof.turf_friction
        env[HorseEnvField.CORNER_RADIUS] = race_prof.corner_radius
        env[HorseEnvField.NUM_HORSES] = len(race_snap.ranks)
        # 戦略情報決定
        tac = {}
        # 戦略情報取得
        tac[HorseTacField.TARGET_LANE] = proc.get_target_lane(h_prof, current_snap, env)
        # 各数値を算出
        base_velocity = h_prof.min_speed
        target_v = proc.get_target_velocity(base_velocity, h_prof, current_snap, env, tac)
        accel = proc.get_acceleration(h_prof, current_snap, env)
        next_velocity = proc.get_next_velocity(target_v, accel, h_prof, current_snap, env, dt)
        next_distance = proc.get_next_distance(next_velocity, h_prof, current_snap, env, dt)
        next_stamina = proc.consume_stamina(next_velocity, h_prof, current_snap, env, dt)
        next_lane = proc.get_next_lane(h_prof, current_snap, env, tac, dt)
        
        next_behavior = current_snap.behavior
        is_finished = False
        finish_time = None
        time_at_600m = current_snap.time_at_600m

        # 4. ゴール判定と状態遷移
        if ph.is_horse_finished(next_distance, race_prof.distance):
            # ゴールしていれば時間を記録
            finish_time = ph.interpolate_goal_time(current_snap.distance, next_distance,
                                                   current_snap.elapsed_time, dt, race_prof.distance)
            # 上り3Fを記録
            if current_snap.time_at_600m:
                time_at_600m = finish_time - current_snap.time_at_600m
            # フラグを調整
            is_finished = True
            next_behavior = HorseBehaviorType.FINISHED

        # 走行を継続
        return replace(current_snap,
                       step=ph.calc_next_step(current_snap.step),
                       elapsed_time=ph.calc_next_elapsted_time(current_snap.elapsed_time, dt),
                       velocity=next_velocity,
                       distance=next_distance,
                       stamina=next_stamina,
                       lane=next_lane,
                       dist_to_front=env[HorseEnvField.DIST_TO_CONTEXT][HorseEnvField.DIST_TO_FRONT],
                       behavior=next_behavior,
                       is_finished=is_finished,
                       finish_time=finish_time,
                       time_at_600m=time_at_600m,
                       )


HORSE_STATE_MAP = {
    HorseBehaviorType.IN_GATE: InGateState(),
    HorseBehaviorType.STARTING: StartingState(),
    HorseBehaviorType.RACING: RacingState(),
    HorseBehaviorType.SPURTING: SpurtingState(),
    HorseBehaviorType.FINISHED: FinishedState(),
    HorseBehaviorType.EXHAUSTED: ExhaustedState(),
}
