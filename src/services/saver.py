"""
saver.py の概要

レースの結果などをCSVで保存する。
"""
import os
import pandas as pd
from pathlib import Path
import logging

# ロガーの取得（__name__ はファイル名/モジュール名になる）
logger = logging.getLogger(__name__)

from src.constants.schema import RaceCol
from src.models.horse_info import HorseInfo
from src.models.race_info import RaceInfo, RaceParam, RaceState, RaceDataSet
from src.utils.name_utils import get_save_file_name


class RaceResultSaver:
    def __init__(self, prepared_dir: str = "prepared", result_dir: str = "results"):
        logger.info("初期化中...")

        self.result_dir = Path(result_dir)
        self.prepared_dir = Path(prepared_dir)

        # ディレクトリがなければ作成する
        os.makedirs(self.result_dir, exist_ok=True)
        os.makedirs(self.prepared_dir, exist_ok=True)

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
                RaceCol.RANK: h_state.rank,
                RaceCol.TIME: round(h_state.finish_time, 2),
                "is_exhausted": h_state.is_exhausted,
            })
        return pd.DataFrame(summary_data)
    
    def export_horses_params(self, race_info: RaceInfo, horse_params: dict) -> pd.DataFrame:
        """レース前の各馬の能力値をDataFrameに整形する"""
        summary_data = []

        # HorseInfoのリストを受取り、馬番でソート
        sorted_horses = sorted(horse_params.keys(), key=lambda x: x)

        for h_id in sorted_horses:
            h_info = race_info.horses[h_id]
            h_param = horse_params[h_id]
            summary_data.append({
                RaceCol.COURSE: race_info.course_name,
                RaceCol.RACE_NUMBER: race_info.race_num,
                RaceCol.HORSE_ID: h_info.horse_id,
                RaceCol.BRACKET_NUM: h_info.bracket_num,
                RaceCol.HORSE_NUM: h_info.horse_num,
                RaceCol.HORSE_NAME: h_info.name,
                # 基本能力値
                "max_speed": h_param.max_speed,
                "acceleration": h_param.acceleration,
                "total_stamina": h_param.total_stamina,
                "stamina_waste_rate": h_param.stamina_waste_rate,
                "cornering_ability": h_param.cornering_ability,
                "gate_reaction": h_param.gate_reaction,
                "strategy": h_param.strategy.value,
                "target_spurt_dist": h_param.target_spurt_dist,
            })

        return pd.DataFrame(summary_data)

    def save_result_to_csv(self, date: str, course: str, distance: int, surface: str, history_df: pd.DataFrame):
        """1レースのデータをCSVで保存する"""
        fname = get_save_file_name(date, course,distance, surface)
        save_path = self.result_dir / fname
        history_df.to_csv(f"{save_path}.csv", index=False, encoding="utf-8-sig")
        logger.info(f"{save_path}に結果を保存しました。")

    def save_prepared_to_csv(self, date: str, course: str, distance: int, surface: str, params_df: pd.DataFrame):
        """1レースのレース前データをCSVで保存する"""
        fname = get_save_file_name(date, course,distance, surface)
        save_path = self.prepared_dir / fname
        params_df.to_csv(f"{save_path}.csv", index=False, encoding="utf-8-sig")
        logger.info(f"{save_path}に結果を保存しました。")
