"""
horse_info.py の概要

馬の情報を保持し、管理するデータクラス。
"""
import pandas as pd
from dataclasses import dataclass, field, replace

from src.models.strategy import StrategyEnum
from src.constants.tactics_master import HorseMove, HorseMode
from src.models.section import TrackSection, SectionName


@dataclass(frozen=True)
class HorseProfile:
    """馬の静的データ、能力値（固定値）を保持するデータクラス"""
    # 基本情報
    horse_id: str
    name: str
    bracket_num: int
    horse_num: int
    jockey: str                 # ジョッキー名
    horse_weight: float         # 馬体重（未発表時は近走平均）
    weight_carried: float       # 斤量
    # 能力値
    # スピード
    max_speed: float            # 最高速度
    min_speed: float            # 最低速度
    acceleration: float         # 加速力
    # スタミナ
    total_stamina: float        # 最大スタミナ
    stamina_waste_rate: float   # 消費効率
    # 適性・性格
    cornering_ability: float    # コーナー能力
    gate_reaction: float        # スタート反応
    # 戦略
    strategy: StrategyEnum      # 脚質
    target_spurt_dist: float    # スパート開始距離


@dataclass(frozen=True)
class HorseState:
    """レース中に変化する動的な馬のデータ（Engineに渡し、受け取る）"""
    # 認識用
    horse_id: str
    # --- 基本物理量 ---
    step: int                   # step数
    elapsed_time: float         # 経過時間
    current_velocity: float     # 現在の速度
    current_distance: float     # 進んだ距離
    # --- 内部状態・意思決定 ---
    target_velocity: float      # Engineが算出した理想速度
    remaining_stamina: float    # 残りスタミナ
    is_spurting: bool           # スパートモードか
    is_exhausted: bool          # 完全にバテたか
    # --- 環境・戦略 ---
    current_lane: float         # 横位置 (ゲート幅は0.9mで実質1.0mずつズレていく）
    is_blocked: bool            # 前が詰まっているか
    # --- 記録 ---
    is_finished: bool = False
    finish_time: float | None = None

    def next_step(self) -> 'HorseState':
        """ステップだけ更新した新しいStateを返す"""
        return replace(self, step=self.step + 1)


@dataclass(frozen=True)
class HorseEnv:
    """レース中の馬の環境情報を保持するデータクラス"""
    current_section: TrackSection   # 現在のセクション情報
    dist_to_front: float            # 前の馬までの距離


@dataclass(frozen=True)
class HorseTactics:
    """レース中の馬の戦術を保存するデータクラス"""
    move: HorseMove             # 次の行動
    mode: HorseMode             # 次の戦術モード


@dataclass
class HorseFactors:
    """State用の値に影響するFactorを保持するデータクラス"""
    section_factor: float       # セクションによる影響（コーナー補正
