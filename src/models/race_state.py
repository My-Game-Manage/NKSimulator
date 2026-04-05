"""
race_state.py の概要

レースの状態（HorseState）を保持するデータクラス。
"""
from dataclasses import dataclass, field

from src.models.horse_state import HorseState


@dataclass(frozen=True)
class RaceState:
    step_count: int
    elapsed_time: float
    horse_states: list[HorseState] = field(default_factory=list)
    
    @property
    def is_all_goal(self) -> bool:
        # 判定ロジックをプロパティとして持たせると便利
        return all(h_state.is_goal for h_state in self.horse_states)
    