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
from src.constants.fields import RaceProfField, HorseProfField, HorseSnapField
from src.services.observer import RaceObserver
from src.models.horse_data import HorseProfile
from src.models.race_data import RaceInfo, RaceProfile, RaceSnapshot
from src.utils.utils import get_save_file_name


class RaceSaver(RaceObserver):
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
            self.save_prepare_race_info_list(data['data'])
        elif event_type is RaceEvent.FINISH:
            # レース終了時状態のセーブ
            self.save_result(data["data"], data["history"])

    def save_prepare_race_info_list(self, race_info_list: list[RaceInfo]):
        for race_info in race_info_list:
            self.save_prepare_race_info(race_info)

    def save_prepare_race_info(self, race_info: RaceInfo):
        # DataFrameに変換
        df = self.export_prepare_data(race_info)
        # レースからファイル名作成してCSVで保存する
        race_prof = race_info.profile
        file_name = get_save_file_name(race_prof.race_id, race_prof.course, race_prof.distance, race_prof.surface)
        save_path = self.prepared_dir / file_name
        df.to_csv(f"{save_path}.csv", index=False, encoding="utf-8-sig")
        logger.info(f"{save_path}に結果を保存しました。")

    def save_result(self, race_info: RaceInfo, history: list[RaceSnapshot]):
        # DataFrameに変換
        df = self.export_result_data(race_info, history)
        # レースからファイル名作成してCSVで保存する
        race_prof = race_info.profile
        file_name = get_save_file_name(race_prof.race_id, race_prof.course, race_prof.distance, race_prof.surface)
        save_path = self.result_dir / file_name
        df.to_csv(f"{save_path}.csv", index=False, encoding="utf-8-sig")
        logger.info(f"{save_path}に結果を保存しました。")

    def export_prepare_data(self, race_info: RaceInfo) -> pd.DataFrame:
        race_prof = race_info.profile
        summary_data = []
        for h_id, h_prof in race_prof.horses.items():
            summary_data.append({
                # レース基本情報
                RaceProfField.COURSE: race_prof.course,
                RaceProfField.RACE_NUM: race_prof.race_num,
                # 馬基本情報
                HorseProfField.HORSE_ID: h_prof.horse_id,
                HorseProfField.BRACKET_NUM: h_prof.bracket_num,
                HorseProfField.HORSE_NUM: h_prof.horse_num,
                HorseProfField.NAME: h_prof.name,
                HorseProfField.JOCKEY: h_prof.jockey,
                HorseProfField.HORSE_WEIGHT: h_prof.horse_weight,
                HorseProfField.WEIGHT_CARRIED: h_prof.weight_carried,
                # 基本能力値
                HorseProfField.BASE_SPEED: h_prof.base_speed,
                HorseProfField.BASE_SPURT_SPEED: h_prof.base_spurt_speed,
                HorseProfField.CRUISE_SPEED: h_prof.cruise_speed,
                HorseProfField.LAST_3F_SPEED: h_prof.last_3f_speed,
                HorseProfField.MIN_SPEED: h_prof.min_speed,
                HorseProfField.ACCELERATION: h_prof.acceleration,
                HorseProfField.TOTAL_STAMINA: h_prof.total_stamina,
                HorseProfField.STAMINA_WASTE_RATE: h_prof.stamina_waste_rate,
                HorseProfField.CORNER_ABILITY: h_prof.cornering_ability,
                HorseProfField.GATE_REACTION: h_prof.gate_reaction,
                HorseProfField.STABILITY_FACTOR: h_prof.stability_factor,
                HorseProfField.BASE_AGILITY: h_prof.base_agility,
                HorseProfField.LANE_CHANGE_FREQUENCY: h_prof.lane_change_frequency,
                HorseProfField.PREFERS_INSIDE: h_prof.prefers_inside,
                HorseProfField.STRATEGY: h_prof.strategy,
                HorseProfField.TARGET_SPURT_DIST: h_prof.target_spurt_dist,
            })
        # データをDataFrameに変換して返す
        return pd.DataFrame(summary_data)

    def export_result_data(self, race_info: RaceInfo, history: list[RaceSnapshot]) -> pd.DataFrame:
        race_prof = race_info.profile
        # 最後のSnapshotだけ取得
        race_snap = history[-1]
        summary_data = []
        for h_id, rank in race_snap.ranks.items():
            h_prof = race_prof.horses[h_id]
            h_snap = race_snap.horses[h_id]
            summary_data.append({
                # レース情報
                RaceProfField.COURSE: race_prof.course,
                RaceProfField.RACE_NUM: race_prof.race_num,
                # 馬情報
                HorseProfField.HORSE_ID: h_prof.horse_id,
                HorseProfField.BRACKET_NUM: h_prof.bracket_num,
                HorseProfField.HORSE_NUM: h_prof.horse_num,
                HorseProfField.NAME: h_prof.name,
                HorseProfField.STRATEGY: h_prof.strategy,
                # 結果情報
                'rank': rank,
                HorseSnapField.FINISH_TIME: round(h_snap.finish_time, 2) if h_snap.finish_time else 0.0,
                HorseSnapField.TIME_AT_600M: round(h_snap.time_at_600m, 2) if h_snap.time_at_600m else 0.0,
                HorseSnapField.STAMINA: round(h_snap.stamina, 2) if h_snap.stamina else 0.0,
                HorseSnapField.LANE: round(h_snap.lane, 2),
            })
        # DataFrameに変換して返す
        return pd.DataFrame(summary_data)
