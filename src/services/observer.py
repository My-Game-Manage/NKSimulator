"""
observer.py の概要

Observerパターン用の基本クラス
"""
import logging

# ロガーの取得（__name__ はファイル名/モジュール名になる）
logger = logging.getLogger(__name__)

from abc import ABC, abstractmethod
from src.constants.enums import RaceEvent


class Subject:
    def __init__(self):
        self._observers = []

    def attach(self, observer: 'RaceObserver'):
        """通知先を登録する"""
        self._observers.append(observer)

    def notify(self, event_type: RaceEvent, data: dict):
        """登録されている全員に通知を送る"""
        for observer in self._observers:
            observer.update(event_type, data)


class RaceObserver(ABC):
    @abstractmethod
    def update(self, event_type: RaceEvent, data: dict):
        pass