"""
name_utils.py の概要

名前に関するヘルパー関数群
"""


def get_save_file_name(date: str, course: str, distance: str, surface: str) -> str:
    """保存用のファイル名作成"""
    return f"{date}_{course}_{surface}{distance}"