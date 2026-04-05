"""
horse_factory.py の概要

馬の基本データ（HorseInfo）を作成する
"""
import pandas as pd
import logging

# ロガーの取得（__name__ はファイル名/モジュール名になる）
logger = logging.getLogger(__name__)

from src.constants.schema import RaceCol
from src.models.horse_param import HorseParam
from src.models.horse_state import HorseState
from src.models.horse_info import HorseInfo
from src.models.section import SectionType
from src.services.ability_analyzer import HorseAbilityAnalyzer


class HorseFactory:
    def __init__(self):
        logger.info("初期化中...")
        self.analyzer = HorseAbilityAnalyzer()

    def create_horse_info(self, row: pd.Series, df: pd.DataFrame) -> HorseInfo:
        """HorseInfoを作成する"""
        distance = row[RaceCol.DISTANCE]
        # historyは自分のものだけ持たせる
        horse_id = row[RaceCol.HORSE_ID]
        horse_history_df = self._get_horse_history_by_id(df, horse_id)
        # TODO: historyがない場合（新馬など）の対策をどうするか？

        # 能力値の作成は委譲
        param = self.analyzer.analyze(horse_history_df, distance)

        return HorseInfo(
            horse_id=row[RaceCol.HORSE_ID],
            name=row[RaceCol.HORSE_NAME],
            bracket_num=row[RaceCol.BRACKET_NUM],
            horse_num=row[RaceCol.HORSE_NUM],
            past_records=horse_history_df,
            param=param,
        )
    
    def reset_horse_state(self, h_info: HorseInfo) -> HorseState:
        """HorseStateの初期化"""
        horse_id = h_info.horse_id
        max_velocity = h_info.param.max_speed
        total_stamina = h_info.param.total_stamina
        horse_num = h_info.horse_num
        return HorseState(
            horse_id=horse_id,
            step=0,
            elapsed_time=0.0,
            distance=0,
            velocity=0.0,
            target_velocity=max_velocity,
            stamina=total_stamina,
            is_spurting=False,
            is_exhausted=False,
            section_name=SectionType.STRAIGHT,
            lane_p=float(horse_num),
            is_blocked=False,
            is_finished=False,
            finish_time=None,
        )
    
    def _get_horse_history_by_id(self, df: pd.DataFrame, horse_id: str) -> pd.DataFrame:
        """
        指定された馬IDの過去レース記録のみを抽出して返す。
    
        Args:
            df (pd.DataFrame): 過去データの全レコードが入ったDataFrame
            horse_id (str): 抽出したい馬のID (例: '2020106948')
        Returns:
            pd.DataFrame: 該当する馬のレコードのみを含むDataFrame
        """
        # ID列が数値型か文字列型か不明な場合を考慮し、文字列に変換して比較
        # アップロードされたCSVの列名に合わせて 'horse_id' を指定
        target_df = df[df[RaceCol.HORSE_ID].astype(str) == str(horse_id)].copy()
    
        if target_df.empty:
            logger.warning(f"警告: ID {horse_id} に該当するデータは見つかりませんでした。")
        else:
            # 時系列順に並べ替えておくとシミュレーションの分析に便利
            # 'date' 列がある場合はソート（必要に応じて有効化してください）
            # target_df = target_df.sort_values('date')
            pass
        
        return target_df
    
