"""
path_utils.py の概要

ファイルのパス関連のヘルパー関数群。
"""


def get_race_cards_csv_filename(date: str) -> str:
    """目的の出馬表CSVのファイル名取得"""
    return f"full_races_{date}.csv"

def get_horse_history_csv_filename(date: str) -> str:
    """目的の馬過去履歴CSVのファイル名取得"""
    return f"horse_history_{date}.csv"
