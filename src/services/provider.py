"""
race_provider.py の概要

出馬表CSVから該当のレースと出走馬のデータを取得する。
"""
import pandas as pd
from pathlib import Path
import logging

# ロガーの取得（__name__ はファイル名/モジュール名になる）
logger = logging.getLogger(__name__)

from src.constants.schema import RaceCol
from src.constants.course_master import NAME_TO_CODE
from src.utils.path_utils import get_race_cards_csv_filename, get_horse_history_csv_filename

class RaceDataProvider:
    _CLASSNAME = "RaceDataProvider"
    def __init__(self, data_dir: str = "data"):
        logger.info("初期化中...")

        self.data_dir = Path(data_dir)

    def get_race_data_sets(self, target_date: str, target_courses: list[str], target_race_nums: list[int]) -> list[dict]:
        """
        【メイン機能】日付・コース・レース番号を指定して、該当するレースのリストを返す
        """
        file_path = self.data_dir / get_race_cards_csv_filename(target_date)
        h_file_path = self.data_dir / get_horse_history_csv_filename(target_date)
        
        if not file_path.exists():
            logger.warning(f"{file_path} does not exist.")
            return []

        # ここで読み込み
        df = pd.read_csv(file_path)
        h_df = pd.read_csv(h_file_path)
        
        # 必要に応じて前処理
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
            race_id = f"{target_date}{NAME_TO_CODE[course]}{str(num).zfill(2)}"
            race_sets.append({
                RaceCol.RACE_ID: race_id,
                RaceCol.COURSE: course,
                RaceCol.RACE_NUMBER: num,
                RaceCol.ENTRIES: group,  # DataFrameのまま渡すとFactoryで扱いやすいです
                RaceCol.HISTORIES: h_df,
            })
        return race_sets

    def _preprocess(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        型変換や欠損値処理など、読み込み直後の共通処理
        """
        # 例: race_number を確実に数値型にするなど
        df[RaceCol.RACE_NUMBER] = df[RaceCol.RACE_NUMBER].astype(int)
        return df