"""
analyzer.py の概要

1. JockeyAnalyzer - Jockeyインスタンスを作成する
"""
import pandas as pd

from constants.schema import RaceCol

class JockeyAnalyzer:
    def __init__(self, history_df):
        self.history_df = history_df
        # 騎手ごとの統計を計算
        self.stats = self._analyze_jockeys()

    def _analyze_jockeys(self):
        # 騎手ごとにグループ化して平均着順などを出す
        j_group = self.history_df.groupby(RaceCol.JOCKEY)
        
        # 簡易的な勝率計算
        win_rate = j_group.apply(lambda x: (x[RaceCol.RANK] == 1).mean())
        # 人気より着順が良かった回数（腕の良さ）
        skill_score = j_group.apply(lambda x: (x[RaceCol.POPULARITY] - x[RaceCol.RANK]).mean())
        
        return pd.DataFrame({'win_rate': win_rate, 'skill_score': skill_score})

    def get_jockey_model(self, name):
        """名前をキーに Jockey インスタンスを生成して返す"""
        row = self.stats.loc[name] if name in self.stats.index else None
        # ... ここで Jockey(jockey_id=..., start_skill=...) を作成
        pass
