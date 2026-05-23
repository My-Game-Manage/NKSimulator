"""
finished.py

ゴール後状態での挙動の定義。
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
# 具象Stateクラス：ゴール後状態 (Finished)
# ---------------------------------------------------------
class FinishedState(HorseBehaviorState):
    """
    State：ゴール後の挙動。
    """
    def update(self, horse_id: str, race_prof: RaceProfile, race_snap: RaceSnapshot, dt: float) -> HorseSnapshot:
        # 基本情報
        horse_prof = race_prof.horses[horse_id]
        current_snap = race_snap.horses[horse_id]
        
        # stepを進めるだけにする

        return replace(race_snap,
                       step=logi.update_step(current_snap.step),
                       )
