"""
behaivor.py の概要

馬のレース中の動きをStateパターンで実装する
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, replace

import src.core.physics as ph


# ---------------------------------------------------------
# Stateパターンの基底クラス
# ---------------------------------------------------------
class HorseBehaviorState(ABC):
    @abstractmethod
    def update(self, horse_id: str, engine, race_profile, horses, dt: float):
        """
        この状態における馬の物理更新・ステータス更新ロジック。
        次のHorseStateオブジェクトを返す。
        """
        pass

# ---------------------------------------------------------
# 具象Stateクラス：走行中 (Racing)
# ---------------------------------------------------------
class RacingState(HorseBehaviorState):
    def update(self, horse_id, engine, race_profile, horses, dt):
        current_state = horses[horse_id]
        h_prof = race_profile.horses[horse_id]

        # 1. 環境認識 (Engineのメソッドを利用)
        horse_env = engine._perceive_horse_position(current_state, race_profile, horses)

        # 2. 意思決定 (Strategyパターンと組み合わせるのが理想的)
        horse_tactics = engine._decide_horse_tactics(horse_env)
        target_v = engine._decide_horse_target_speed(h_prof, horse_env, horse_tactics)
        
        # 3. 物理計算 (physicsモジュールを利用)
        accel = ph.calculate_acceleration(target_v, current_state.current_velocity, h_prof.acceleration)
        velocity = current_state.current_velocity + accel * dt
        distance = current_state.current_distance + velocity * dt

        # 4. ゴール判定と状態遷移
        is_finished = ph.is_horse_finished(distance, race_profile.distance)
        if is_finished:
            finish_time = ph.interpolate_goal_time(current_state.current_distance, distance,
                                                   current_state.elapsed_time, dt, race_profile.distance)
            # 次のステップからは FinishedState に切り替える
            new_behavior = FinishedState()
            return replace(current_state, 
                           current_distance=distance, current_velocity=0, 
                           is_finished=True, finish_time=finish_time,
                           behavior=new_behavior) # 状態を遷移

        # 走行を継続
        return replace(current_state, 
                       current_distance=distance, current_velocity=velocity,
                       target_velocity=target_v, behavior=self)

# ---------------------------------------------------------
# 具象Stateクラス：バテた状態 (Exhausted)
# ---------------------------------------------------------
class ExhaustedState(HorseBehaviorState):
    def update(self, horse_id, engine, race_profile, horses, dt):
        current_state = horses[horse_id]
        return current_state.next_step()

# ---------------------------------------------------------
# 具象Stateクラス：スタート時 (InGate)
# ---------------------------------------------------------
class InGateState(HorseBehaviorState):
    def update(self, horse_id, engine, race_profile, horses, dt):
        current_state = horses[horse_id]
        return current_state.next_step()

# ---------------------------------------------------------
# 具象Stateクラス：ゴール後 (Finished)
# ---------------------------------------------------------
class FinishedState(HorseBehaviorState):
    def update(self, horse_id, engine, race_profile, horses, dt):
        # ゴール済みの馬は、物理計算を行わず時間を進めるだけ
        current_state = horses[horse_id]
        return current_state.next_step()