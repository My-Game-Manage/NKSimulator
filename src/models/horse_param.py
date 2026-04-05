"""
horse_param.py の概要

馬の能力値を保持するデータクラス。
"""
from dataclasses import dataclass
from src.models.strategy import StrategyEnum

@dataclass(frozen=True)
class HorseParam:
    """レース中に変化しない、その馬固有の能力値セット"""
    # 速度系
    max_speed: float            # 最高速度
    acceleration: float         # 加速力
    
    # スタミナ系
    total_stamina: float        # 最大スタミナ
    stamina_waste_rate: float   # 消費効率
    
    # 適性・性格
    cornering_ability: float    # 0.0 ~ 1.0
    gate_reaction: float        # スタートの反応
    
    # 戦略
    strategy: StrategyEnum      # 逃げ/先行など
    target_spurt_dist: float    # 何m地点からスパートするか