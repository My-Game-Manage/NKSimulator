"""
horse_info.py の概要

馬の情報を保持し、管理するデータクラス。
"""
import pandas as pd
from dataclasses import dataclass, field

from src.models.strategy import StrategyEnum


@dataclass(frozen=True)
class HorseInfo:
    """IDや名前などの馬の基本情報（準備時だけ使う）"""
    horse_id: str
    name: str
    bracket_num: int
    horse_num: int
    # 過去データ（辞書のリストではなくDataFrameで持つ）
    past_records: pd.DataFrame 


@dataclass(frozen=True)
class HorseParam:
    """過去データ等から算出した馬の基礎能力値（Engineに渡す）"""
    horse_id: str
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


@dataclass(frozen=True)
class HorseState:
    """レース中に変化する動的な馬のデータ（Engineに渡し、受け取る）"""
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
    rank: int = 99
    passing_rank: list[int] = field(default_factory=list)
