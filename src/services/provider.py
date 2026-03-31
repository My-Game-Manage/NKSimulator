"""
provider.py の概要

出馬表のCSVを読み込み、レース情報を作成する
"""
import pandas as pd
from pathlib import Path
from typing import List, Dict
from utils.logger import setup_logger

from constants.schema import RaceCol


class RaceDataProvider:
    def __init__(self, data_dir: str = "data"):
        """
        特定のファイルパスではなく、データが格納されているディレクトリを保持する
        """
        _CLASSNAME = "RaceDataProvider"
        # クラス名を名前としてロガーを作成
        self.logger = setup_logger(_CLASSNAME)
    
        self.data_dir = Path(data_dir)

    def get_race_data_sets(self, target_date: str, target_courses: List[str], target_race_nums: List[int]) -> List[Dict]:
        """
        【メイン機能】日付・コース・レース番号を指定して、該当するレースのリストを返す
        """
        file_path = self.data_dir / f"full_races_{target_date}.csv"
        self.logger.info(f"path: {file_path} - is exist? {file_path.exitst()}")
        
        if not file_path.exists():
            self.logger.warning(f"{file_path} does not exist.")
            return []

        # ここで読み込み（以前の __init__ でやっていた処理をここに移動）
        df = pd.read_csv(file_path)
        
        # 必要に応じて前処理（以前の _preprocess 相当）をここで呼ぶ
        df = self._preprocess(df)

        # フィルタリング
        filtered_df = df[
            (df[RaceCol.COURSE].isin(target_courses)) & 
            (df[RaceCol.RACE_NUMBER].isin(target_race_nums))
        ]

        # レース単位のリストにして返す
        race_sets = []
        grouped = filtered_df.groupby([RaceCol.COURSE, RaceCol.RACE_NUMBER])
        for (course, num), group in grouped:
            race_sets.append({
                RaceCol.COURSE: course,
                RaceCol.RACE_NUMBER: num,
                RaceCol.ENTRIES: group  # DataFrameのまま渡すとFactoryで扱いやすいです
            })
        return race_sets

    def _preprocess(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        型変換や欠損値処理など、読み込み直後の共通処理
        """
        # 例: race_number を確実に数値型にするなど
        df[RaceCol.RACE_NUMBER] = df[RaceCol.RACE_NUMBER].astype(int)
        return df
