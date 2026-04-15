"""
strategy.py の概要

戦術（脚質）の定義。
"""
from enum import Enum
from dataclasses import dataclass

class StrategyEnum(Enum):
    ESCAPE = "逃げ"
    LEADING = "先行"
    BETWEEN = "差し"
    PUSHING = "追込"
