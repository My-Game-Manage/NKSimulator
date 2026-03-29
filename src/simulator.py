"""
simulator.py の概要

1. レースをシミュレートするために動的にCSVデータからコース、騎手、馬のデータを構築する
2. RaceEngineを使い、1フレーム毎の挙動を計算して、馬を動かす
"""

import os
import time

from src.utils.logger import setup_logger

class RaceSimulator:
    def __init__(self):
        """
        初期化：
        """
        _CLASSNAME = "Simulator"
        # クラス名を名前としてロガーを作成
        self.logger = setup_logger(_CLASSNAME)

        self.logger.info("初期化しています...")
