"""
utils.py の概要

個別ファイルにするまでもない小さなヘルパー関数群。
"""
from typing import Dict, Optional
import pandas as pd
from datetime import datetime, timedelta, timezone

from src.constants.course_master import CourseSpec, COURSE_MASTER, NAME_TO_COURSE
from src.constants.course_master import NAME_TO_CODE


# ---------------------------------------------------------
# Date and Time
# ---------------------------------------------------------
def normalize_date_format(date_val) -> str:
    """
    あらゆる日付形式を 8桁の文字列ID 'YYYYMMDD' に変換する
    """
    if not date_val:
        return ""

    # すでに 20260327 形式の文字列ならそのまま返す
    if isinstance(date_val, str) and len(date_val) == 8 and date_val.isdigit():
        return date_val

    # datetimeオブジェクトの場合
    if isinstance(date_val, datetime):
        return date_val.strftime('%Y%m%d')

    # それ以外（ハイフンあり文字列など）
    date_str = str(date_val).strip()
    # 数字だけを抽出
    normalized = "".join(filter(str.isdigit, date_str))
    
    return normalized
    
def get_today_jst() -> str:
    """
    現在の日本時間を 'YYYYMMDD' 形式で返す
    """
    # UTC+9時間（日本時間）のタイムゾーンを定義
    # 現在時刻をJSTで取得
    return datetime.now(timezone(timedelta(hours=9), 'JST')).strftime('%Y%m%d')

def time_to_seconds(time_str):
    """'1:25.2' -> 85.2, '59.9' -> 59.9 への変換"""
    if pd.isna(time_str) or not isinstance(time_str, str) or time_str == "**":
        return None
    try:
        if ':' in time_str:
            m, s = time_str.split(':')
            return int(m) * 60 + float(s)
        return float(time_str)
    except: return None


# ---------------------------------------------------------
# File name
# ---------------------------------------------------------

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

# ---------------------------------------------------------
# List
# ---------------------------------------------------------
def convert_to_int_list(data_list) -> list:
    """リスト内の要素をすべてint型に変換する関数"""
    return [int(x) for x in data_list]

def fill_list_if_empty(data_list, start_num: int=1, end_range: int=13) -> list:
    """リストが空なら1から12までの数字のリストに置き換える関数"""
    if not data_list:
        return list(range(start_num, end_range))
    return data_list

def parse_list_from_args_with_comma(arg) -> list:
    """カンマ区切りの文字列をリストに変換する汎用関数"""
    if not arg:
        return []
    return [item.strip() for item in arg.split(',')]

# ---------------------------------------------------------
# Race data
# ---------------------------------------------------------
def get_course_from_race_id(race_id: str) -> Optional[CourseSpec]:
    """
    レースIDから会場コードを抽出し、対応するCourseSpecを返す。
    不正なIDや未登録の会場の場合はNoneを返す。
    """
    # 1. 型チェックと長さの検証（標準的な12桁を想定）
    if not isinstance(race_id, str) or len(race_id) != 12:
        print(f"Error: Invalid RaceID format ({race_id})")
        return None

    # 2. 会場コードの抽出 (5-6桁目)
    course_code = race_id[4:6]

    # 3. マスタデータとの照合
    course = COURSE_MASTER.get(course_code)

    if course:
        print(f"Success: {course.name}競馬場を特定しました。")
        return course
    else:
        print(f"Error: 会場コード '{course_code}' はマスタに存在しません。")
        return None

def is_valid_race_id(race_id: str) -> bool:
    """レースIDが正しい会場コードを含んでいるかチェックする"""
    return get_course_from_race_id(race_id) is not None

def get_course_by_name(name_input: str) -> Optional[CourseSpec]:
    """
    入力された文字列（会場名）がマスタに含まれるかチェックする。
    存在すれば CourseSpec オブジェクトを、なければ None を返す。
    """
    # 完全一致でチェック
    course = NAME_TO_COURSE.get(name_input)
    
    if course:
        return course
    
    # 失敗時：少し柔軟に「競馬場」という後ろ文字を消して再試行（任意）
    clean_name = name_input.replace("競馬場", "")
    return NAME_TO_COURSE.get(clean_name)

def is_valid_course_name(name_input: str) -> bool:
    """会場名が有効かどうかのみを判定する"""
    return get_course_by_name(name_input) is not None