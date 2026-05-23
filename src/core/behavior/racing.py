"""
racing.py

レース状態での挙動の定義。
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
# 具象Stateクラス：レース中の基本状態 (Racing)
# ---------------------------------------------------------
class RacingState(HorseBehaviorState):
    """
    State：レース中状態の基本挙動。
    """
    def update(self, horse_id: str, race_prof: RaceProfile, race_snap: RaceSnapshot, dt: float) -> HorseSnapshot:
        # 基本情報
        horse_prof = race_prof.horses[horse_id]
        current_snap = race_snap.horses[horse_id]
        
        # 1. 認知（Perception）フェーズ
        env = self.get_horse_environment(horse_id, race_prof, race_snap)

        # 2. 判断 (Decision)フェーズ
        tac = self.determinate_tactics(horse_id, race_prof, race_snap, env)

        # 3. 実行 (Execution)フェーズ
        param = self.get_horse_parameter()

        # 4. 状態遷移判定フェーズ
        behavior = current_snap.behavior
        if logi.is_horse_finished(param.next_distance, race_prof.distance):
            behavior = HorseBehaviorType.FINISHED

        return replace(race_snap,
                       step=logi.update_step(current_snap.step),
                       elapsed_time=logi.update_elapsed_time(current_snap.elapsed_time),
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
                       dist_to_beside_left=env.dist_context.dist_to_beside_left,
                       dist_to_beside_right=env.dist_context.dist_to_beside_right,
                       section=env.section,
                       behavior=behavior,
                       )
