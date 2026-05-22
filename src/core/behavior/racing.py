"""
racing.py

レース状態での挙動の定義。
"""
from abc import ABC, abstractmethod
import logging

# ロガーの取得（__name__ はファイル名/モジュール名になる）
logger = logging.getLogger(__name__)

from src.core.behavior.base import HorseBehaviorState



# ---------------------------------------------------------
# 具象Stateクラス：レース中の基本状態 (Racing)
# ---------------------------------------------------------
class RacingState(HorseBehaviorState):
    """
    State：レース中状態の基本挙動。
    """
    def update(self, horse_id):
        return super().update(horse_id)
