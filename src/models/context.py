"""
context.py の概要

レースの静的データを収めておくもの。dataclassを使い、Immutableにしている
"""
from dataclasses import dataclass

@dataclass(frozen=True)
class RaceContext:
    # CSVから取得する動的情報
    course_name: str
    distance: int
    track_condition: str  # 良, 稍重, 重, 不良
    weather: str
    
    # 会場マスターデータから紐付ける静的情報
    track_width: float      # コース幅
    corner_radius: float    # コーナーのきつさ補正
    surface_friction: float # 馬場状態による摩擦係数
    segment_data: list      # 前述した直線・コーナーの距離設定
