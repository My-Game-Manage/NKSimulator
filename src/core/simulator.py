"""
simulator.py の概要

1. 会場データの初期化
2. 各馬のエントリー
3. 実行管理：RaceEngine でゴールするまでループを回す
4. ログなどの記録
"""
from src.utils.logger import setup_logger

class RaceSimulator:
    def __init__(self):
        _CLASSNAME = "Simulator"
        # クラス名を名前としてロガーを作成
        self.logger = setup_logger(_CLASSNAME)

        self.logger.info("初期化中...")

    def run(self, target_date=None, course_filter=None, race_num_filter=None):
        """
        メインの実行メソッド
        """
        self.logger.info("実行中...")
        pass
        
