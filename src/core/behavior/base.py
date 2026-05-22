"""
base.py の概要

レース中の馬の状態による挙動の違いを表現するStateパターンのための基底クラスの定義。
"""
from abc import ABC, abstractmethod
import logging

# ロガーの取得（__name__ はファイル名/モジュール名になる）
logger = logging.getLogger(__name__)

from src.models.race_data import RaceProfile, RaceSnapshot
from src.models.horse_data import HorseProfile, HorseSnapshot


# ---------------------------------------------------------
# 基底クラス（HorseBehaviorState）
# ---------------------------------------------------------
class HorseBehaviorState(ABC):
    """
    レース中の馬のデータ更新のためのStateパターンのための基底クラス
    """
    @abstractmethod
    def update(self, horse_id: str) -> HorseSnapshot:
        ...
