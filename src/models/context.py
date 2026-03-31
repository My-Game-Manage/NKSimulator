"""
context.py の概要

レースの静的データを収めておくもの。dataclassを使い、Immutableにしている
"""
from dataclasses import dataclass
from typing import List, Dict

@dataclass(frozen=True)
class RaceContext:
    # CSVから取得する動的情報
    course_name: str
    race_number: int
    distance: int
    track_condition: str  # 良, 稍, 重, 不
    weather: str
    
    # 会場マスターデータから紐付ける静的情報
    track_width: float      # コース幅
    corner_radius: float    # コーナーのきつさ補正
    surface_friction: float # 馬場状態による摩擦係数

    # --- コースレイアウト (区間データ) ---
    # [{'type': 'straight', 'length': 300}, ...] のようなリスト
    segments: List[Dict]
