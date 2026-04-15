"""
tactics_master.py の概要

レース中の馬の選択や戦術のEnum等
"""
from enum import Enum


class HorseMove(Enum):
    """馬の移動の選択肢"""
    STAY = "移動なし"
    OUTSIDE = "外へ"
    INSIDE = "内へ"


class HorseMode(Enum):
    """馬の走行モード"""
    KEEP = "速度維持"
    INCREASE = "速度アップ"
    DECREASE = "速度ダウン"
    START = "スタートダッシュ"
    SPURT = "スパート"
    BRAKE = "ブレーキ"
