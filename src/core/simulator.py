"""
simulator.py の概要

レースをシミュレートするための準備（会場データ、馬データ生成）と、Engineを使った実際のシミュレートを行う。
"""
from utils.logger import setup_logger

class RaceSimulator:
    def __init__(self):
        _CLASSNAME = "Simulator"
        # クラス名を名前としてロガーを作成
        self.logger = setup_logger(_CLASSNAME)

        self.logger.info("初期化中...")

        self._racing_contexts = []

    def run(self, date: str=None, courses: list[str] | None=None, race_numbers: list[int] | None=None):
        """
        メインの実行メソッド
        """
        self.logger.info("実行中...")

        self.logger.debug(f"{date}\n{courses}\n{race_numbers}")
