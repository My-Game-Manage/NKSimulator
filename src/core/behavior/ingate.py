"""
ingate.py

スタート前状態での挙動の定義。
"""
import logging
from dataclasses import replace

# ロガーの取得（__name__ はファイル名/モジュール名になる）
logger = logging.getLogger(__name__)

from src.core.behavior.base import HorseBehaviorState

from src.models.race_data import RaceProfile, RaceSnapshot
from src.models.horse_data import HorseProfile, HorseSnapshot

from src.constants.enums import HorseBehaviorType

import src.core.race_logics as logi


# ---------------------------------------------------------
# 具象Stateクラス：スタート前 (InGate)
# ---------------------------------------------------------
class InGateState(HorseBehaviorState):
    """
    State：スタート前の挙動。
    """
    def update(self, horse_id: str, race_prof: RaceProfile, race_snap: RaceSnapshot, dt: float) -> HorseSnapshot:
        # 基本情報
        horse_prof = race_prof.horses[horse_id]
        current_snap = race_snap.horses[horse_id]
        strategy = self.get_strategy(horse_prof)

        # 1. 認知（Perception）フェーズ
        env = self.get_horse_environment(horse_id, race_prof, race_snap)

        # 2. 判断 (Decision)フェーズ
        tac = self.determinate_tactics(horse_id, race_prof, race_snap, env)

        update_tac = replace(tac,
                      target_velocity=strategy.get_start_speed(horse_prof),
                      accel_power=strategy.get_start_acceleration(horse_prof),
                      )

        # 3. 実行 (Execution)フェーズ
        param = self.get_horse_parameter(horse_prof, current_snap, env, update_tac, dt)

        # 4. 状態遷移判定フェーズ
        behavior = current_snap.behavior
        if logi.is_out_gate(param.next_distance):
            behavior = HorseBehaviorType.STARTING

        # 5. 初期設定処理
        laptimes = logi.init_laptimes(race_prof) if not current_snap.laptimes else current_snap.laptimes
        checkpoint_ranks = logi.init_checkpoint_ranks(race_prof) if not current_snap.checkpoint_ranks else current_snap.checkpoint_ranks

        return replace(current_snap,
                       step=logi.update_step(current_snap.step),
                       elapsed_time=logi.update_elapsed_time(current_snap.elapsed_time, dt),
                       accel_power=param.accel_power,
                       accel=param.actual_accel,
                       target_velocity=param.target_velocity,
                       velocity=param.next_velocity,
                       distance=param.next_distance,
                       stamina=param.next_stamina,
                       lane=param.next_lane,
                       dist_to_front=env.dist_context.dist_to_front,
                       dist_to_front_left=env.dist_context.dist_to_front_left,
                       dist_to_front_right=env.dist_context.dist_to_front_right,
                       dist_to_side_left=env.dist_context.dist_to_side_left,
                       dist_to_side_right=env.dist_context.dist_to_side_right,
                       section=env.section,
                       behavior=behavior,
                       laptimes=laptimes,
                       checkpoint_ranks=checkpoint_ranks,
                       )
