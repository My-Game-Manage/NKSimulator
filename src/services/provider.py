"""
provider.py の概要

出馬表のCSVを読み込み、レース情報を作成する
"""
import pandas as pd

from constants.schema import RaceCol


class RaceDataProvider:
    def __init__(self, full_races_csv_path):
        """
        出走表CSVを読み込み、メモリに保持する
        """
        self.df = pd.read_csv(full_races_csv_path)
        self._preprocess()

    def _preprocess(self):
        """
        日付の型変換や、欠損値の補完など、抽出前の下準備を行う（中身は空でOK）
        """
        pass

    def get_race_entries(self, course: str, race_number: int):
        """
        指定された会場とレース番号に合致する行を抽出し、
        扱いやすい辞書のリスト形式で返す
        """
        # 条件に合致する行をフィルタリング
        race_df = self.df[
            (self.df[RaceCol.COURSE] == course) & 
            (self.df[RaceCol.RACE_NUMBER] == race_number)
        ]
        
        # エンジンやFactoryが扱いやすいように、1行＝1辞書のリストに変換
        return race_df.to_dict(orient='records')

    def get_race_info(self, course: str, race_number: int):
        """
        馬のリストではなく、レース全体の情報（距離、馬場状態など）を取得する
        """
        race_df = self.df[
            (self.df[RaceCol.COURSE] == course) & 
            (self.df[RaceCol.RACE_NUMBER] == race_number)
        ]
        
        if race_df.empty:
            return None
            
        # 最初の1行からレース共通情報を抽出
        first_row = race_df.iloc[0]
        return {
            RaceCol.DISTANCE: first_row[RaceCol.DISTANCE],
            RaceCol.SURFACE: first_row[RaceCol.SURFACE],
            RaceCol.TRACK_CONDITION: first_row[RaceCol.TRACK_CONDITION],
            RaceCol.NUM_HORSES: first_row[RaceCol.NUM_HORSES]
        }

    def get_all_race_numbers(self, course: str):
        """
        その会場でその日に行われる全レース番号を取得する（12レースあるか等の確認用）
        """
        return sorted(self.df[self.df[RaceCol.COURSE] == course][RaceCol.RACE_NUMBER].unique())
