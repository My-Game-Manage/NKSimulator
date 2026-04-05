"""
horse_state.py の概要

馬のレース中の状態（動的データ）を保持しておくデータクラス。
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class HorseState:
    velocity: float
    distance: float