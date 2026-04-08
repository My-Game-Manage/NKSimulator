"""
race_data.py の概要　- 出馬表と馬の過去履歴のデータクラス
"""
from dataclasses import dataclass
import pandas as pd


@dataclass(frozen=True)
class RaceRawData:
    """レースデータ（出馬表のDataFrameと馬の過去レースデータDataFrameを持つ）"""
    race_id: str
    course: str
    race_num: int
    entries: pd.DataFrame
    histories: pd.DataFrame
