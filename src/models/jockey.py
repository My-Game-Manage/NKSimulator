"""
jockey.py について

騎手の静的データを保持するインスタンス作成
"""
from dataclasses import dataclass

@dataclass(frozen=True)
class Jockey:
    jockey_id: str
    name: str
    # 1. スタート技術（ゲートの出やすさ、二の脚の速さへの補正）
    start_skill: float  # 0.9 ~ 1.1
    # 2. 折り合い・スタミナ温存（道中のスタミナ消費効率への補正）
    pacing_skill: float
    # 3. 追い出し・剛腕（直線の最高速度や根性バフへの補正）
    drive_skill: float
    # 4. 戦略傾向（逃げ・先行などの脚質指示への忠実度や判断力）
    positioning_bias: str # 'aggressive', 'conservative', 'flexible'
