"""
starting.py の概要

スタート状態の挙動の定義。
"""
from abc import ABC, abstractmethod
import logging

# ロガーの取得（__name__ はファイル名/モジュール名になる）
logger = logging.getLogger(__name__)

from src.core.behavior.base import HorseBehaviorState


# ---------------------------------------------------------
# 具象Stateクラス：スタート (Starting)
# ---------------------------------------------------------
class StartingState(HorseBehaviorState):
    """
    State: スタート状態の挙動。
    """
    def update(self, horse_id):
        return super().update(horse_id)