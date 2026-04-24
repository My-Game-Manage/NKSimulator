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

from src.constants.enums import RaceEvent
from src.services.observer import RaceObserver
from src.constants.schema import RaceCol
from src.models.horse_data import HorseProfile
from src.models.race_data import RaceInfo, RaceProfile, RaceSnapshot
from src.utils.utils import get_save_file_name


class RaceResultSaver(RaceObserver):
    def __init__(self, prepared_dir: str = "prepared", result_dir: str = "results"):
        super().__init__()
        logger.info("初期化中...")

        self.result_dir = Path(result_dir)
        self.prepared_dir = Path(prepared_dir)

        # ディレクトリがなければ作成する
        os.makedirs(self.result_dir, exist_ok=True)
        os.makedirs(self.prepared_dir, exist_ok=True)

    def update(self, event_type: RaceEvent, data: dict):
        if event_type is RaceEvent.PREPARE:
            # 準備状態のセーブ（能力値部分）
            pass
        elif event_type is RaceEvent.FINISH:
            # レース終了時状態のセーブ
            pass

    def save_prepare_race_info_list(self, race_info_list: list[RaceInfo]):
        pass

    def save_prepare_race_info(self, race_info: RaceInfo):
        race_prof = race_info.profile
        summary_data = []
        for h_id, h_prof in race_prof.horses.items():
            summary_data.append({
                RaceCol.COURSE: race_prof.course_name,
                RaceCol.RACE_NUMBER: race_prof.race_num,
                RaceCol.HORSE_ID: h_prof.horse_id,
                RaceCol.BRACKET_NUM: h_prof.bracket_num,
                RaceCol.HORSE_NUM: h_prof.horse_num,
                RaceCol.HORSE_NAME: h_prof.name,
                RaceCol.JOCKEY: h_prof.jockey,
                RaceCol.HORSE_WEIGHT: h_prof.horse_weight,
                RaceCol.WEIGHT_CARRIED: h_prof.weight_carried,
                # 基本能力値
                "max_speed": h_prof.max_speed,
                "min_speed": h_prof.min_speed,
                "acceleration": h_prof.acceleration,
                "total_stamina": h_prof.total_stamina,
                "stamina_waste_rate": h_prof.stamina_waste_rate,
                "cornering_ability": h_prof.cornering_ability,
                "gate_reaction": h_prof.gate_reaction,
                "strategy": h_prof.strategy.value,
                "target_spurt_dist": h_prof.target_spurt_dist,
            })
        df = pd.DataFrame(summary_data)
        file_name = get_save_file_name(date, course,distance, surface)
        save_path = self.prepared_dir / file_name
        df.to_csv(f"{save_path}.csv", index=False, encoding="utf-8-sig")
        logger.info(f"{save_path}に結果を保存しました。")

    def save_result(self, race_info: RaceInfo, race_snap: RaceSnapshot):
        pass

    def export_prepare_data(self, race_prof: RaceProfile):
        pass

    def export_result_data(self, race_prof: RaceProfile, race_snap: RaceSnapshot):
        pass

    def export_results(self, race_profile: RaceProfile, history: list[RaceState]) -> pd.DataFrame:
        """レース結果を記録用のDataFrameに整形する"""
        # 記録の最後のRaceStateを取得
        last_state = history[-1]

        summary_data = []

        for h_id, rank in last_state.ranks.items():
            h_prof = race_profile.horses[h_id]
            h_state = last_state.horses[h_id]
            summary_data.append({
                RaceCol.COURSE: race_profile.course_name,
                RaceCol.RACE_NUMBER: race_profile.race_num,
                RaceCol.HORSE_ID: h_id,
                RaceCol.BRACKET_NUM: h_prof.bracket_num,
                RaceCol.HORSE_NUM: h_prof.horse_num,
                RaceCol.HORSE_NAME: h_prof.name,
                RaceCol.RANK: rank,
                RaceCol.TIME: round(h_state.finish_time, 2),
                "is_exhausted": h_state.is_exhausted,
            })

        return pd.DataFrame(summary_data)
    
    def export_horses_params(self, race_profile: RaceProfile) -> pd.DataFrame:
        """レース前の各馬の能力値をDataFrameに整形する"""
        summary_data = []

        for h_id, h_prof in race_profile.horses.items():
            summary_data.append({
                RaceCol.COURSE: race_profile.course_name,
                RaceCol.RACE_NUMBER: race_profile.race_num,
                RaceCol.HORSE_ID: h_prof.horse_id,
                RaceCol.BRACKET_NUM: h_prof.bracket_num,
                RaceCol.HORSE_NUM: h_prof.horse_num,
                RaceCol.HORSE_NAME: h_prof.name,
                RaceCol.JOCKEY: h_prof.jockey,
                RaceCol.HORSE_WEIGHT: h_prof.horse_weight,
                RaceCol.WEIGHT_CARRIED: h_prof.weight_carried,
                # 基本能力値
                "max_speed": h_prof.max_speed,
                "min_speed": h_prof.min_speed,
                "acceleration": h_prof.acceleration,
                "total_stamina": h_prof.total_stamina,
                "stamina_waste_rate": h_prof.stamina_waste_rate,
                "cornering_ability": h_prof.cornering_ability,
                "gate_reaction": h_prof.gate_reaction,
                "strategy": h_prof.strategy.value,
                "target_spurt_dist": h_prof.target_spurt_dist,
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
