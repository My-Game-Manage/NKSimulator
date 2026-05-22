"""
finished.py

ゴール後状態での挙動の定義。
"""
from abc import ABC, abstractmethod
import logging

# ロガーの取得（__name__ はファイル名/モジュール名になる）
logger = logging.getLogger(__name__)

from src.core.behavior.base import HorseBehaviorState



# ---------------------------------------------------------
# 具象Stateクラス：ゴール後状態 (Finished)
# ---------------------------------------------------------
class FinishedState(HorseBehaviorState):
    """
    State：ゴール後の挙動。
    """
    def update(self, horse_id):
        return super().update(horse_id)
