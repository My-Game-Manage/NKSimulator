"""
horse_factory.py の概要

馬の基本データ（HorseInfo）を作成する
"""
import pandas as pd
import logging

# ロガーの取得（__name__ はファイル名/モジュール名になる）
logger = logging.getLogger(__name__)

from src.constants.schema import RaceCol
from src.models.horse_info import HorseInfo, HorseParam, HorseState
from src.models.section import SectionType
from src.services.ability_analyzer import HorseAbilityAnalyzer
from src.models.strategy import StrategyEnum


class HorseFactory:
    def __init__(self):
        logger.info("初期化中...")
        self.analyzer = HorseAbilityAnalyzer()

    def create_horse_infos(self, entries: pd.DataFrame) -> dict:
        """1レースの出走全馬のHorseInfoの辞書（ID: Info）を作成する"""
        horse_ids = {}
        for _, row in entries.iterrows():
            horse_id = row[RaceCol.HORSE_ID]
            horse_ids[horse_id] = self.create_horse_info(row)
        return horse_ids

    def create_horse_info(self, row: pd.Series) -> HorseInfo:
        """HorseInfoを作成する"""
        return HorseInfo(
            horse_id=row[RaceCol.HORSE_ID],
            name=row[RaceCol.HORSE_NAME],
            bracket_num=row[RaceCol.BRACKET_NUM],
            horse_num=row[RaceCol.HORSE_NUM],
            # jockey
        )
    
    def create_horse_params(self, entries: pd.DataFrame, past_recoreds: pd.DataFrame, distance: int) -> dict:
        """1レースの出走全馬のHorseParamの辞書（ID: Param）を作成する"""
        horse_params = {}
        for _, row in entries.iterrows():
            horse_id = row[RaceCol.HORSE_ID]
            horse_params[horse_id] = self.create_horse_param(horse_id, past_recoreds, distance)
        return horse_params
    
    def create_horse_param(self, horse_id: str, past_records: pd.DataFrame, distance: int) -> HorseParam:
        """HorseParamを作成する"""
        analyzer = HorseAbilityAnalyzer()
        # 該当馬だけの履歴にする
        horse_hisotry = self.horse_history_by_id(past_records, horse_id)

        total_stamina, stamina_waste_rate = analyzer.calculate_stamina_params(horse_hisotry, distance)
        strategy = analyzer.determine_strategy(horse_hisotry)

        return HorseParam(
            horse_id=horse_id,
            max_speed=analyzer.calculate_max_speed(horse_hisotry),
            acceleration=analyzer.calculate_acceleration(horse_hisotry),
            total_stamina=total_stamina,
            stamina_waste_rate=stamina_waste_rate,
            cornering_ability=analyzer.calculate_cornering_ability(horse_hisotry),
            gate_reaction=analyzer.calculate_gate_reaction(horse_hisotry),
            strategy=strategy,
            target_spurt_dist=analyzer.calculate_spurt_dist(horse_hisotry, strategy),
        )
    
    def create_horse_states(self, h_infos: dict, h_params: dict) -> dict:
        """1レース全馬のHorseState（初期値）を作成する"""
        horse_states = {}
        for h_id in h_infos.keys():
            horse_states[h_id] = self.create_horse_state(h_infos[h_id], h_params[h_id])
        return horse_states
    
    def create_horse_state(self, h_info: HorseInfo, h_param: HorseParam) -> HorseState:
        """HorseStateの作成（初期化）"""
        return HorseState(
            horse_id=h_info.horse_id,
            step=0,
            elapsed_time=0.0,
            distance=0.0,
            velocity=0.0,
            target_velocity=h_param.max_speed,
            stamina=h_param.total_stamina,
            is_spurting=False,
            is_exhausted=False,
            section_name=SectionType.STRAIGHT,
            lane_p=float(h_info.horse_num),
            is_blocked=False,
            is_finished=False,
            finish_time=None,
        )
    
    def horse_history_by_id(self, df: pd.DataFrame, horse_id: str) -> pd.DataFrame:
        """該当する馬の履歴のみ抽出する"""
        try:
            history_df = df[df[RaceCol.HORSE_ID].astype(str) == str(horse_id)]
            return history_df
        except pd.errors.EmptyDataError:
            logger.warning(f"{horse_id}に該当する履歴がありません。")
            return pd.DataFrame()
        