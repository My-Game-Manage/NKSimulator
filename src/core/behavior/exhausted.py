"""
exhausted.py

バテた状態での挙動の定義。
"""
from abc import ABC, abstractmethod
import logging

# ロガーの取得（__name__ はファイル名/モジュール名になる）
logger = logging.getLogger(__name__)

from src.core.behavior.base import HorseBehaviorState

from src.models.race_data import RaceProfile, RaceSnapshot
from src.models.horse_data import HorseProfile, HorseSnapshot



# ---------------------------------------------------------
# 具象Stateクラス：バテた状態 (Exhausted)
# ---------------------------------------------------------
class ExhaustedState(HorseBehaviorState):
    """
    State：バテた状態での挙動。
    """
    def update(self, horse_id: str, race_prof: RaceProfile, current_snapshot: RaceSnapshot, dt: float) -> HorseSnapshot:
        return current_snapshot.horses[horse_id]
