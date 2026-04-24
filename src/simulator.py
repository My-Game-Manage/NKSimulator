"""
simulator.py の概要

レースをシミュレートするための準備（会場データ、馬データ生成）と、Engineを使った実際のシミュレートを行う。
"""
import logging

# ロガーの取得（__name__ はファイル名/モジュール名になる）
logger = logging.getLogger(__name__)

from src.constants.enums import RaceEvent
from src.services.observer import Subject
from src.services.factory import RaceFactory
from src.core.engine import RaceEngine
from src.models.race_data import RaceInfo, RaceSnapshot


class RaceSimulator(Subject):
    DT = 0.1
    MAX_STEPS = 2000
    def __init__(self, factory: RaceFactory):
        super().__init__()
        logger.info("初期化中...")

        # Factoryを外部から注入 (DI)
        self.factory = factory
        self.engine = RaceEngine()

        self.race_info_list: list[RaceInfo] = []

        # レースごとの結果（History）を格納する辞書
        # key: race_id, value: list[RaceState]
        self.results: dict[str, list[RaceSnapshot]] = {}

        # Observerのアタッチ

    def run(self, **kwargs) -> bool:
        logger.info("実行中...")

        # レース準備
        race_info_list = self.prepare(**kwargs)

        self.notify(RaceEvent.PREPARE, {'data': race_info_list})
        
        # １レースずつシミュレーションを行う
        for race_info in race_info_list:
            history = self._run_single_race(race_info)
            self.results[race_info.race_id] = history

        return True
    
    def _run_single_race(self, race_info: RaceInfo) -> list[RaceSnapshot]:
        """1レースだけ実行"""
        return []
    
    def prepare(self, **kwargs) -> list[RaceInfo]:
        """レースの準備"""
        # Factoryでレース情報を生成
        race_info_list = self.factory.create_races(**kwargs)

        if not race_info_list:
            logger.warning(f"該当するレースがありません。: {race_info_list}")
            return []
        
        return race_info_list
