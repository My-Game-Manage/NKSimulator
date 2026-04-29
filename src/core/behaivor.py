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
from src.constants.fields import HorseSnapField
from src.constants.enums import HorseBehaviorType
from src.core.strategy import RacingStrategy, STRATEGY_MAP
import src.core.physics as ph


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
        strategy = self.get_strategy(h_prof)
        target_v = strategy.get_target_velocity(h_prof, current_snap)
        accel = strategy.get_acceleration(target_v, h_prof, current_snap)
        next_velocity = strategy.get_next_velocity(current_snap, accel, dt)
        next_distance = strategy.get_next_distance(current_snap, next_velocity, dt)
        next_stamina = strategy.consume_stamina(h_prof.total_stamina, next_velocity, current_snap, race_prof.distance, dt)
        next_lane = current_snap.lane
        # StateをStartingに変更
        next_behavior = HorseBehaviorType.STARTING
        return replace(current_snap,
                       step=ph.calc_next_step(current_snap.step),
                       elapsed_time=ph.calc_next_elapsted_time(current_snap.elapsed_time, dt),
                       velocity=next_velocity,
                       distance=next_distance,
                       stamina=next_stamina,
                       lane=next_lane,
                       behavior=next_behavior,
                       )


# ---------------------------------------------------------
# 具象Stateクラス：スタート状態 (Starting)
# ---------------------------------------------------------
class StartingState(HorseBehaviorState):
    def update(self, horse_id: str, race_prof: RaceProfile, race_snap: RaceSnapshot, dt: float) -> HorseSnapshot:
        h_prof = race_prof.horses[horse_id] 
        current_snap = race_snap.horses[horse_id]
        # 脚質に応じて各値を算出
        strategy = self.get_strategy(h_prof)
        target_v = strategy.get_target_velocity(h_prof, current_snap)
        accel = strategy.get_acceleration(target_v, h_prof, current_snap)
        next_velocity = strategy.get_next_velocity(current_snap, accel, dt)
        next_distance = strategy.get_next_distance(current_snap, next_velocity, dt)
        next_stamina = strategy.consume_stamina(h_prof.total_stamina, next_velocity, current_snap, race_prof.distance, dt)
        next_lane = current_snap.lane
        # スタート区間が終わっていればレース中状態に移行
        next_behavior = HorseBehaviorType.RACING if ph.is_start_section(next_distance, race_prof.sections[0]) else current_snap.behavior
        return replace(current_snap,
                       step=ph.calc_next_step(current_snap.step),
                       elapsed_time=ph.calc_next_elapsted_time(current_snap.elapsed_time, dt),
                       velocity=next_velocity,
                       distance=next_distance,
                       stamina=next_stamina,
                       lane=next_lane,
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
        # 脚質に応じて各値を算出
        strategy = self.get_strategy(h_prof)
        target_v = strategy.get_target_velocity(h_prof, current_snap)
        accel = strategy.get_acceleration(target_v, h_prof, current_snap) * 1.2
        next_velocity = strategy.get_next_velocity(current_snap, accel, dt)
        next_distance = strategy.get_next_distance(current_snap, next_velocity, dt)
        next_stamina = strategy.consume_stamina(h_prof.total_stamina, next_velocity, current_snap, race_prof.distance, dt)
        next_lane = current_snap.lane
        next_behavior = current_snap.behavior
        is_finished = False
        finish_time = None
        # ゴール判定　->　ゴールしていたらタイムを計測し状態遷移
        if ph.is_horse_finished(next_distance, race_prof.distance):
            # ゴールしていれば時間を記録
            finish_time = ph.interpolate_goal_time(current_snap.distance, next_distance,
                                                   current_snap.elapsed_time, dt, race_prof.distance)
            is_finished = True
            next_behavior = HorseBehaviorType.FINISHED
        return replace(current_snap,
                       step=ph.calc_next_step(current_snap.step),
                       elapsed_time=ph.calc_next_elapsted_time(current_snap.elapsed_time, dt),
                       velocity=next_velocity,
                       distance=next_distance,
                       stamina=next_stamina,
                       lane=next_lane,
                       behavior=next_behavior,
                       is_finished=is_finished,
                       finish_time=finish_time,
                       )


# ---------------------------------------------------------
# 具象Stateクラス：走行中 (Racing)
# ---------------------------------------------------------
class RacingState(HorseBehaviorState):
    def update(self, horse_id: str, race_prof: RaceProfile, race_snap: RaceSnapshot, dt: float) -> HorseSnapshot:
        h_prof = race_prof.horses[horse_id] 
        current_snap = race_snap.horses[horse_id]
        # Strategyの取得
        strategy = self.get_strategy(h_prof)
        # 1. 環境認識
        dist_to_front = ph.get_dist_to_front(horse_id, race_snap.horses)
        # TODO: 環境情報の取得をとりあえず整備
        current_section = ""
        # 各数値を算出
        target_v = strategy.get_target_velocity(h_prof, current_snap)
        accel = strategy.get_acceleration(target_v, h_prof, current_snap)
        next_velocity = strategy.get_next_velocity(current_snap, accel, dt)
        next_distance = strategy.get_next_distance(current_snap, next_velocity, dt)
        next_stamina = strategy.consume_stamina(h_prof.total_stamina, next_velocity, current_snap, race_prof.distance, dt)
        next_lane = current_snap.lane
        next_behavior = current_snap.behavior
        is_finished = False
        finish_time = None

        # 1. 環境認識 (Engineのメソッドを利用)
        #horse_env = engine._perceive_horse_position(current_state, race_profile, horses)

        # 2. 意思決定 (Strategyパターンと組み合わせるのが理想的)
        #horse_tactics = engine._decide_horse_tactics(horse_env)
        #target_v = engine._decide_horse_target_speed(h_prof, horse_env, horse_tactics)
        
        # 3. 物理計算 (physicsモジュールを利用)
        #accel = ph.calculate_acceleration(target_v, current_state.current_velocity, h_prof.acceleration)
        #velocity = current_state.current_velocity + accel * dt
        #distance = current_state.current_distance + velocity * dt

        # 4. ゴール判定と状態遷移
        if ph.is_horse_finished(next_distance, race_prof.distance):
            # ゴールしていれば時間を記録
            finish_time = ph.interpolate_goal_time(current_snap.distance, next_distance,
                                                   current_snap.elapsed_time, dt, race_prof.distance)
            is_finished = True
            next_behavior = HorseBehaviorType.FINISHED
        elif ph.is_spurt_distance(next_distance, h_prof.target_spurt_dist):
            # スパート開始
            next_behavior = HorseBehaviorType.SPURTING

        # 走行を継続
        return replace(current_snap,
                       step=ph.calc_next_step(current_snap.step),
                       elapsed_time=ph.calc_next_elapsted_time(current_snap.elapsed_time, dt),
                       velocity=next_velocity,
                       distance=next_distance,
                       stamina=next_stamina,
                       lane=next_lane,
                       behavior=next_behavior,
                       is_finished=is_finished,
                       finish_time=finish_time,
                       )


# ---------------------------------------------------------
# 具象Stateクラス：バテた状態 (Exhausted)
# ---------------------------------------------------------
class ExhaustedState(HorseBehaviorState):
    def update(self, horse_id: str, race_prof: RaceProfile, race_snap: RaceSnapshot, dt: float) -> HorseSnapshot:
        h_prof = race_prof.horses[horse_id] 
        current_snap = race_snap.horses[horse_id]
        # 脚質に応じて各値を算出
        strategy = self.get_strategy(h_prof)
        target_v = strategy.get_target_velocity(h_prof, current_snap)
        accel = strategy.get_acceleration(target_v, h_prof, current_snap)
        next_velocity = strategy.get_next_velocity(current_snap, accel, dt) * 0.8
        next_distance = strategy.get_next_distance(current_snap, next_velocity, dt)
        next_stamina = strategy.consume_stamina(h_prof.total_stamina, next_velocity, current_snap, race_prof.distance, dt)
        next_lane = current_snap.lane
        next_behavior = current_snap.behavior
        is_finished = False
        finish_time = None
        # 4. ゴール判定と状態遷移
        if ph.is_horse_finished(next_distance, race_prof.distance):
            # ゴールしていれば時間を記録
            finish_time = ph.interpolate_goal_time(current_snap.distance, next_distance,
                                                   current_snap.elapsed_time, dt, race_prof.distance)
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
                       behavior=next_behavior,
                       is_finished=is_finished,
                       finish_time=finish_time,
                       )


HORSE_STATE_MAP = {
    HorseBehaviorType.IN_GATE: InGateState(),
    HorseBehaviorType.STARTING: StartingState(),
    HorseBehaviorType.RACING: RacingState(),
    HorseBehaviorType.SPURTING: SpurtingState(),
    HorseBehaviorType.FINISHED: FinishedState(),
    HorseBehaviorType.EXHAUSTED: ExhaustedState(),
}
