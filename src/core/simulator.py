"""
simulator.py の概要

レースをシミュレートするための準備（会場データ、馬データ生成）と、Engineを使った実際のシミュレートを行う。
"""
from src.utils.logger import setup_logger
from src.services.race_provider import RaceDataProvider
from src.services.factory import RaceInfoFactory
from src.models.race_state import RaceState

class RaceSimulator:
    def __init__(self):
        _CLASSNAME = "Simulator"
        # クラス名を名前としてロガーを作成
        self.logger = setup_logger(_CLASSNAME)

        self.logger.info("初期化中...")

        self.race_info_list = []
        # レースごとの結果（History）を格納する辞書
        # key: race_id, value: list[RaceState]
        self.results: dict[str, list[RaceState]] = {}

    def run(self, date: str=None, courses: list[str] | None=None, race_numbers: list[int] | None=None) -> bool:
        """
        メインの実行メソッド
        """
        self.logger.info("実行中...")
        self.logger.debug(f"{date}\n{courses}\n{race_numbers}")

        # 前準備
        self.race_info_list = self._prepare_races(date, courses, race_numbers)
        self.logger.debug(f"race_info_list: {self.race_info_list}")

        if not self.race_info_list:
            self.logger.warning(f"該当するレースがありません。: {self.race_info_list}")
            return False
        
        # 各レースのシミュレーション
        for info in self.race_info_list:
            history = self._run_single_race(info)
            self.results[info.race_id] = history
        
        # 事後処理
        self._post_races()

        return True
    
    def _prepare_races(self, date: str, courses, race_numbers) -> list:
        """レースの準備"""
        # 1. CSVデータの読み込み
        provider = RaceDataProvider(data_dir="data")
        race_data_sets = provider.get_race_data_sets(date, courses, race_numbers)
        #self.logger.debug(f"race_data_sets: {race_data_sets}")

        factory = RaceInfoFactory()
        race_info_list = factory.get_race_info_list(race_data_sets)

        return race_info_list

    def _run_single_race(self, info) -> list[RaceState]:
        """1レース分をEngineで動かして結果を返す"""
        return []
    
    def _post_races(self):
        """レースの事後処理"""
        pass