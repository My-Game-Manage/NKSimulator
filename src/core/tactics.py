"""
tactics.py の概要

意思決定部分の関数の集合。
"""
from src.models.horse_info import HorseProfile, HorseState
from src.constants.tactics_master import HorseMode, HorseMove

def determinate_target_speed_from(param: HorseProfile, state: HorseState) -> float:
    """馬の速度に関する戦略を返す"""
    # 距離と位置関係、体力から、目的の速度を返す
    return 0.0

def determinate_horse_move() -> HorseMove:
    """馬の動き戦略を返す"""
    return HorseMove.STAY

def determinate_horse_mode() -> HorseMode:
    """馬のモード戦略を返す"""
    return HorseMode.KEEP