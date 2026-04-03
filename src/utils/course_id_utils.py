"""
course_id_utils.py の概要

コースIDについての小さなヘルパー関数群。
"""
from typing import Dict, Optional

from constants.course_master import CourseSpec, COURSE_MASTER, NAME_TO_COURSE


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