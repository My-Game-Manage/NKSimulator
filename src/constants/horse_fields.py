"""
fields.py の概要

辞書のKeyに利用するWordのEnum
"""
from enum import Enum


class SnapshotField(Enum):
    """Snapshotのフィールド"""
    ID = "horse_id"
    # --- 基本物理量 ---
    STEP = "step"
    TIME = "elapsed_time"
    VELOCITY = "current_velocity"
    DISTANCE = "current_distance"
    # --- 内部状態・意思決定 ---
    TARGET_V = "target_velocity"
    STAMINA = "remaining_stamina"
    IS_SPURTING = "is_spurting"
    IS_EXHAUSTED = "is_exhausted"
    # --- 環境・戦略 ---
    LANE = "current_lane"
    IS_BLOCKED = "is_blocked"
    # --- 記録 ---
    IS_FINISHED = "is_finished"
    FINISH_TIME = "finish_time"
