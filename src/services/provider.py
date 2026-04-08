"""
race_provider.py の概要

出馬表CSVから該当のレースと出走馬のデータを取得する。
"""
import pandas as pd
from pathlib import Path
import logging

# ロガーの取得（__name__ はファイル名/モジュール名になる）
logger = logging.getLogger(__name__)

from src.utils.name_utils import race_id_from, full_races_csv_filename_from, horse_history_csv_filename_from
from src.models.race_raw_data import RaceRawData
from src.constants.schema import RaceCol


class RaceDataProvider:
    """出馬表CSVから該当するレースの列を取得する"""
    def __init__(self, data_dir: str = "data"):
        logger.info("初期化中...")

        self.data_dir = Path(data_dir)

    def fetch_race_data(self, target_date: str) -> pd.DataFrame:
        """レースの出馬表データCSVを取得"""
        file_path = self.data_dir / full_races_csv_filename_from(target_date)
        try:
            race_df = pd.read_csv(file_path)
            return race_df
        except pd.errors.EmptyDataError:
            logger.warning(f"{file_path}はありません。")
            return pd.DataFrame()

    def fetch_horse_history(self, target_date: str) -> pd.DataFrame:
        """馬の過去データCSVをDataFrameで取得"""
        file_path = self.data_dir / horse_history_csv_filename_from(target_date)
        try:
            h_df = pd.read_csv(file_path)
            return h_df
        except pd.errors.EmptyDataError:
            logger.warning(f"{file_path}はありません。")
            return pd.DataFrame()
    
    def create_race_raw_data_list(self, target_date: str, target_courses: list[str], target_race_nums: list[int]) -> list[RaceRawData]:
        """出馬表など必要なデータのセット（RaceData）のリストを作成"""
        race_df = self.fetch_race_data(target_date)
        horse_df = self.fetch_horse_history(target_date)
        
        if race_df.empty or horse_df.empty:
            logger.warning("目的のレースデータが存在しません")
            return []
        
        cleared_race_df = self._preprocess(race_df)

        filtered_race_df = cleared_race_df[
            (cleared_race_df[RaceCol.COURSE].isin(target_courses)) & 
            (cleared_race_df[RaceCol.RACE_NUMBER].isin(target_race_nums))
        ]

        # レース単位のリストにして返す
        race_raw_data_list = []
        grouped = filtered_race_df.groupby([RaceCol.COURSE, RaceCol.RACE_NUMBER])
        for (course, num), group in grouped:
            race_raw_data_list.append(
                RaceRawData(
                    race_id=race_id_from(target_date, course, num),
                    course=course,
                    race_num=num,
                    entries=group,
                    histories=horse_df,
                )
            )
        return race_raw_data_list
    
    def _preprocess(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        型変換や欠損値処理など、読み込み直後の共通処理
        """
        # 例: race_number を確実に数値型にするなど
        df[RaceCol.RACE_NUMBER] = df[RaceCol.RACE_NUMBER].astype(int)
        return df