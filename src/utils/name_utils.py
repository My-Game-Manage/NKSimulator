"""
name_utils.py の概要

名前に関するヘルパー関数群
"""
from src.constants.course_master import NAME_TO_CODE


def get_save_file_name(date: str, course: str, distance: str, surface: str) -> str:
    """保存用のファイル名作成"""
    return f"{date}_{course}_{surface}{distance}"

def race_id_from(date: str, course: str, race_num: int) -> str:
    """レースIDを、日付、開催会場、レース番号から作成する"""
    return f"{date}{NAME_TO_CODE[course]}{str(race_num).zfill(2)}"

def full_races_csv_filename_from(date: str) -> str:
    """目的の出馬表CSVのファイル名取得"""
    return f"full_races_{date}.csv"

def horse_history_csv_filename_from(date: str) -> str:
    """目的の馬過去履歴CSVのファイル名取得"""
    return f"horse_history_{date}.csv"
