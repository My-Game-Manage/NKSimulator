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
from src.models.horse_info import HorseInfo
from src.models.strategy import StrategyEnum
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
    
