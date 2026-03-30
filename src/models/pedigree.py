"""
pedigree.py の概要

馬の血統の補正についてのデータクラス
"""
from dataclasses import dataclass

@dataclass(frozen=True)
class PedigreeEffect:
    father_name: str
    # 1.0を基準とした補正係数
    mud_aptitude: float      # 道悪（重・不良）適性
    distance_flexibility: float # 距離延長への耐性
    speed_bonus: float       # 純粋なスピードへの加点
    grit_inheritance: float  # 根性の遺伝力
