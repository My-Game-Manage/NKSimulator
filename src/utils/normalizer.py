"""
normalizer.py の概要

正常化、正規化のための簡単なヘルパー関数群。
"""
import pandas as pd

from src.constants.schema import RaceCol


def valid_race_shutuba_df(df: pd.DataFrame) -> pd.DataFrame:
    """出馬表DFを正規化（レース番号）"""
    # レース番号を数値型に変換
    df[RaceCol.RACE_NUMBER] = df[RaceCol.RACE_NUMBER].astype(int)
    return df

