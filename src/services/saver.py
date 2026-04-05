"""
saver.py の概要

レースの結果などをCSVで保存する。
"""
import pandas as pd
from pathlib import Path
import logging

# ロガーの取得（__name__ はファイル名/モジュール名になる）
logger = logging.getLogger(__name__)

from src.constants.schema import RaceCol
from src.models.horse_info import HorseInfo
from src.models.race_info import RaceInfo
from src.models.race_state import RaceState
from src.utils.name_utils import get_save_file_name


class RaceResultSaver:
    def __init__(self, prepared_dir: str = "prepared", result_dir: str = "results"):
        logger.info("初期化中...")

        self.result_dir = Path(result_dir)
        self.prepared_dir = Path(prepared_dir)

    def export_results(self, race_info: RaceInfo, history: list[RaceState]) -> pd.DataFrame:
        """レース結果を記録用のDataFrameに整形する"""
        # 記録の最後のRaceStateを取得
        last_state = history[-1]

        summary_data = []

        for h_state in last_state.horse_states:
            h_info = race_info.get_horse(h_state.horse_id)

            summary_data.append({
                RaceCol.COURSE: race_info.course_name,
                RaceCol.RACE_NUMBER: race_info.race_num,
                RaceCol.HORSE_ID: h_state.horse_id,
                RaceCol.BRACKET_NUM: h_info.bracket_num,
                RaceCol.HORSE_NUM: h_info.horse_num,
                RaceCol.HORSE_NAME: h_info.name,
                RaceCol.TIME: round(h_state.finish_time, 2),
                "is_exhausted": h_state.is_exhausted,
            })
        return pd.DataFrame(summary_data)

    def save_result_to_csv(self, date: str, course: str, distance: int, surface: str, history_df: pd.DataFrame):
        """1レースのデータをCSVで保存する"""
        fname = get_save_file_name(date, course,distance, surface)
        save_path = self.result_dir / fname
        history_df.to_csv(f"{save_path}.csv", index=False, encoding="utf-8-sig")
        logger.info(f"{save_path}に結果を保存しました。")

    def save_prepared_to_csv(self, date: str, course: str, distance: int, surface: str, horses: list):
        """1レースのレース前データをCSVで保存する"""
        fname = get_save_file_name(date, course,distance, surface)
        file_path = self.prepared_dir / fname
