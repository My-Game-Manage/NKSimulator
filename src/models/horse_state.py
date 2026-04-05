"""
horse_state.py の概要

馬のレース中の状態（動的データ）を保持しておくデータクラス。
"""
from dataclasses import dataclass, replace


@dataclass(frozen=True)
class HorseState:
    # 認識用
    horse_id: str
    # --- 基本物理量 ---
    step: int                   # step数
    elapsed_time: float         # 経過時間
    distance: float             # 進んだ距離
    velocity: float             # 現在の速度
    
    # --- 内部状態・意思決定 ---
    target_velocity: float      # Engineが算出した理想速度
    stamina: float              # 残りスタミナ
    is_spurting: bool           # スパートモードか
    is_exhausted: bool          # 完全にバテたか
    
    # --- 環境・戦略 ---
    section_name: str           # "3コーナー" など
    lane_p: float               # 横位置 (0.0=最内, 1.0=大外)
    is_blocked: bool            # 前が詰まっているか
    
    # --- 記録 ---
    is_finished: bool = False
    finish_time: float | None = None

    def next_step(self):
        return replace(self, step=self.step + 1)
    
    @property
    def is_goal(self):
        return self.is_finished