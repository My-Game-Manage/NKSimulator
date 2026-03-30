"""
名前に関するヘルパー関数
"""
from src.constants.master_data import JYO_NAME_MAP

def course_name_from_course_id(course_id) -> str:
    """コースIDからコース名に変換する"""
    return JYO_NAME_MAP.get(course_id, "不明")
