"""
race_state.py の概要

レースの状態（HorseState）を保持するデータクラス。
"""
from dataclasses import dataclass

from src.models.horse_state import HorseState

@dataclass(frozen=True)
class RaceState:
    step_count: int
    elapsed_time: float
    horse_states: tuple[HorseState]
    
    @property
    def is_all_goal(self) -> bool:
        # 判定ロジックをプロパティとして持たせると便利
        return all(h.is_goal for h in self.horse_states)