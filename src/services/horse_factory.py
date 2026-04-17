"""
horse_factory.py の概要

馬の基本データ（HorseInfo）を作成する
"""
import pandas as pd
from dataclasses import dataclass
import logging

# ロガーの取得（__name__ はファイル名/モジュール名になる）
logger = logging.getLogger(__name__)

from src.constants.schema import RaceCol
from src.models.horse_data import HorseProfile, HorseState
from src.services.ability_analyzer import HorseAbilityAnalyzer
from src.models.strategy import StrategyEnum


@dataclass(frozen=True)
class _HorseBaseProf:
    """基本データ一時保存用のインナークラス"""
    # 基本情報
    horse_id: str
    name: str
    bracket_num: int
    horse_num: int
    jockey: str                 # ジョッキー名
    horse_weight: float         # 馬体重（未発表時は近走平均）
    weight_carried: float       # 斤量


@dataclass(frozen=True)
class _HorseParam:
    """能力データ一時保存用のインナークラス"""
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



class HorseFactory:
    def __init__(self):
        logger.info("初期化中...")
        self.analyzer = HorseAbilityAnalyzer()

    def create_all_horse_profiles(self, entries: pd.DataFrame, past_recoreds: pd.DataFrame, distance: int) -> dict:
        """1レースの出走全馬のHorseProfileの辞書（ID: Param）を作成する"""
        horse_profiles = {}
        for _, row in entries.iterrows():
            horse_id = row[RaceCol.HORSE_ID]
            horse_profiles[horse_id] = self.create_horse_profile(row, past_recoreds, distance)
        return horse_profiles

    def create_horse_profile(self, row: pd.Series, past_records: pd.DataFrame, distance: int) -> HorseProfile:
        """Profileを作成"""
        # 基本データ
        base_prof = self._horse_base_prof_from(row)
        horse_id = base_prof.horse_id
        # それぞれの能力値を算出する
        param = self._horse_abilities_from(horse_id, past_records, distance)
        return HorseProfile(
            horse_id=base_prof.horse_id,
            name=base_prof.name,
            bracket_num=base_prof.bracket_num,
            horse_num=base_prof.horse_num,
            jockey=base_prof.jockey,
            horse_weight=base_prof.horse_weight,
            weight_carried=base_prof.weight_carried,
            max_speed=param.max_speed,
            min_speed=param.min_speed,
            acceleration=param.acceleration,
            total_stamina=param.total_stamina,
            stamina_waste_rate=param.stamina_waste_rate,
            cornering_ability=param.cornering_ability,
            gate_reaction=param.gate_reaction,
            strategy=param.strategy,
            target_spurt_dist=param.target_spurt_dist,
        )
    
    def _horse_base_prof_from(self, row: pd.Series) -> _HorseBaseProf:
        """基本情報を取得して返す"""
        horse_id = row[RaceCol.HORSE_ID]
        name = row[RaceCol.HORSE_NAME]
        bracket_num = row[RaceCol.BRACKET_NUM]
        horse_num = row[RaceCol.HORSE_NUM]
        jockey = row[RaceCol.JOCKEY]
        horse_weight = row[RaceCol.HORSE_WEIGHT]
        weight_carried = row[RaceCol.WEIGHT_CARRIED]
        return _HorseBaseProf(
            horse_id=horse_id,
            name=name,
            bracket_num=bracket_num,
            horse_num=horse_num,
            jockey=jockey,
            horse_weight=horse_weight,
            weight_carried=weight_carried,
        )
    
    def _horse_abilities_from(self, horse_id: str, past_records: pd.DataFrame, distance: int) -> _HorseParam:
        """能力値を算出して返す"""
        analyzer = HorseAbilityAnalyzer()
        # 該当馬だけの履歴にする
        horse_hisotry = self.horse_history_by_id(past_records, horse_id)

        # スピード系
        max_speed, min_speed = analyzer.calculate_min_max_speed(horse_hisotry)
        acceleration=analyzer.calculate_acceleration(horse_hisotry)
        # スタミナ系
        total_stamina, stamina_waste_rate = analyzer.calculate_stamina_params(horse_hisotry, distance)
        # 適性・性格
        cornering_ability=analyzer.calculate_cornering_ability(horse_hisotry)
        gate_reaction=analyzer.calculate_gate_reaction(horse_hisotry)
        # 戦略
        strategy = analyzer.determine_strategy(horse_hisotry)
        target_spurt_dist=analyzer.calculate_spurt_dist(horse_hisotry, strategy)

        return _HorseParam(
            max_speed=max_speed,
            min_speed=min_speed,
            acceleration=acceleration,
            total_stamina=total_stamina,
            stamina_waste_rate=stamina_waste_rate,
            cornering_ability=cornering_ability,
            gate_reaction=gate_reaction,
            strategy=strategy,
            target_spurt_dist=target_spurt_dist,
        )

    def create_horse_states(self, h_profiles: dict[str, HorseProfile]) -> dict[str, HorseState]:
        """1レース全馬のHorseState（初期値）を作成する"""
        horse_states = {}
        for h_id in h_profiles.keys():
            horse_states[h_id] = self.create_horse_state(h_profiles[h_id])
        return horse_states
    
    def create_horse_state(self, profile: HorseProfile) -> HorseState:
        """HorseStateの作成（初期化）"""
        horse_id = profile.horse_id
        step = 0
        elapsed_time = 0.0
        current_velocity = 0.0
        current_distance = 0.0
        target_velocity = 0.0
        remaining_stamina = 0.0
        is_spurting = False
        is_exhausted = False
        current_lane = float(profile.horse_num)
        is_blocked = False
        is_finished = False
        finish_time = None
        return HorseState(
            horse_id=horse_id,
            step=step,
            elapsed_time=elapsed_time,
            current_velocity=current_velocity,
            current_distance=current_distance,
            target_velocity=target_velocity,
            remaining_stamina=remaining_stamina,
            is_spurting=is_spurting,
            is_exhausted=is_exhausted,
            current_lane=current_lane,
            is_blocked=is_blocked,
            is_finished=is_finished,
            finish_time=finish_time,
        )
    
    def horse_history_by_id(self, df: pd.DataFrame, horse_id: str) -> pd.DataFrame:
        """該当する馬の履歴のみ抽出する"""
        try:
            history_df = df[df[RaceCol.HORSE_ID].astype(str) == str(horse_id)]
            return history_df
        except pd.errors.EmptyDataError:
            logger.warning(f"{horse_id}に該当する履歴がありません。")
            return pd.DataFrame()
        