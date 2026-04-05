"""
horse_info.py の概要

馬の情報を保持し、管理するデータクラス。
"""
import pandas as pd
from dataclasses import dataclass

from src.models.horse_param import HorseParam


@dataclass(frozen=True)
class HorseInfo:
    horse_id: str
    name: str
    bracket_num: int
    horse_num: int
    # 脳聴力
    param: HorseParam
    # 過去データ（辞書のリストではなくDataFrameで持つ）
    past_records: pd.DataFrame 
