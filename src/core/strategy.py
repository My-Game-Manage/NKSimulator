"""
strategy.py の概要

脚質に応じたStrategy（Protocol）を提供する特殊クラス群
"""
from typing import Protocol

import logging

# ロガーの取得（__name__ はファイル名/モジュール名になる）
logger = logging.getLogger(__name__)

from src.constants.enums import HorseStrategyType, SectionType, SectionName
from src.constants.fields import HorseEnvField, HorseTacField, HorseOvertake
from src.models.horse_data import HorseProfile, HorseSnapshot
from src.models.race_data import TrackSection
import src.core.physics as ph
from src.constants.constants import (
    CRUISE_SPEED_STYLE_FACTOR, START_SPEED_STYLE_FACTOR, SPURT_SPEED_STYLE_FACTOR,
)



# ---------------------------------------------------------
# Strategy（Protocol）パターンの基底クラス
# ---------------------------------------------------------
class RacingStrategy(Protocol):
    def get_start_speed(self, horse_prof: HorseProfile) -> float:
        ...

    def get_cruise_speed(self, horse_prof: HorseProfile) -> float:
        ...

    def get_spurt_speed(self, horse_prof: HorseProfile) -> float:
        ...

    def determinate_overtake(self, horse_prof: HorseProfile, horse_snap: HorseSnapshot, env: dict) -> bool:
        ...

# ---------------------------------------------------------
# 具象Strategyクラス：逃げ
# ---------------------------------------------------------
class LeaderStrategy:
    def get_start_speed(self, horse_prof: HorseProfile) -> float:
        return horse_prof.start_speed * START_SPEED_STYLE_FACTOR[HorseStrategyType.LEADER]
    
    def get_cruise_speed(self, horse_prof: HorseProfile) -> float:
        return horse_prof.cruise_speed * CRUISE_SPEED_STYLE_FACTOR[HorseStrategyType.LEADER]
    
    def get_spurt_speed(self, horse_prof: HorseProfile) -> float:
        return horse_prof.last_3f_speed * CRUISE_SPEED_STYLE_FACTOR[HorseStrategyType.LEADER]

    def determinate_overtake(self, horse_prof: HorseProfile, horse_snap: HorseSnapshot, env: dict) -> str:
        #環境情報
        race_distance = env[HorseEnvField.RACE_DISTANCE]
        current_distance = horse_snap.distance
        section = env[HorseEnvField.SECTION]
        rank = env[HorseEnvField.RANK]
        num_horses = env[HorseEnvField.NUM_HORSES]
        ctx = env[HorseEnvField.DIST_TO_CONTEXT]
        dist_to_front = ctx[HorseEnvField.DIST_TO_FRONT]
        front_left = ctx[HorseEnvField.DIST_TO_FRONT_LEFT]
        front_right = ctx[HorseEnvField.DIST_TO_FRONT_RIGHT]
        side_left = ctx[HorseEnvField.DIST_TO_SIDE_LEFT]
        side_right = ctx[HorseEnvField.DIST_TO_SIDE_RIGHT]

        score = 0.0

        # 囲まれているか判定
        relevant_dist = 999.0
        relevant_dist = min(dist_to_front, front_left, front_right)
        # 前に馬がいる
        if relevant_dist < 3.0:
            # 眼の前
            score += 1.0
            # 詰まってる場合は抜けない
            if side_left < 0.8 and side_right < 0.8:
                return HorseOvertake.SORROUNDED
        elif relevant_dist < 8.0:
            # 少し詰まっている
            score += 0.5
        # 横に馬がいる
        if side_left < 0.8: score += 0.5
        if side_right < 0.8: score += 0.5

        # 現在の距離はどのあたりか？
        if (current_distance / race_distance) < 0.5:
            score += 1.0
            # 順位はどのあたりか？
            if (rank / num_horses) > 0.5:
                score += 1.0

        # セクション判断
        if section.name is SectionName.HOMESTRETCH:
            score += 2.0
        
        return HorseOvertake.OVERTAKE if score >= 2.0 else HorseOvertake.STAY

# ---------------------------------------------------------
# 具象Strategyクラス：先行
# ---------------------------------------------------------
class StalkerStrategy:
    def get_start_speed(self, horse_prof: HorseProfile) -> float:
        return horse_prof.start_speed * START_SPEED_STYLE_FACTOR[HorseStrategyType.STALKER]
    
    def get_cruise_speed(self, horse_prof: HorseProfile) -> float:
        return horse_prof.cruise_speed * CRUISE_SPEED_STYLE_FACTOR[HorseStrategyType.STALKER]

    def get_spurt_speed(self, horse_prof: HorseProfile) -> float:
        return horse_prof.last_3f_speed * SPURT_SPEED_STYLE_FACTOR[HorseStrategyType.STALKER]

    def determinate_overtake(self, horse_prof: HorseProfile, horse_snap: HorseSnapshot, env: dict) -> str:
        #環境情報
        race_distance = env[HorseEnvField.RACE_DISTANCE]
        current_distance = horse_snap.distance
        section = env[HorseEnvField.SECTION]
        rank = env[HorseEnvField.RANK]
        num_horses = env[HorseEnvField.NUM_HORSES]
        ctx = env[HorseEnvField.DIST_TO_CONTEXT]
        dist_to_front = ctx[HorseEnvField.DIST_TO_FRONT]
        front_left = ctx[HorseEnvField.DIST_TO_FRONT_LEFT]
        front_right = ctx[HorseEnvField.DIST_TO_FRONT_RIGHT]
        side_left = ctx[HorseEnvField.DIST_TO_SIDE_LEFT]
        side_right = ctx[HorseEnvField.DIST_TO_SIDE_RIGHT]

        score = 0.0

        # 囲まれているか判定
        relevant_dist = 999.0
        relevant_dist = min(dist_to_front, front_left, front_right)
        # 前に馬がいる
        if relevant_dist < 3.0:
            # 眼の前
            score += 0.5
            # 詰まってる場合は抜けない
            if side_left < 0.8 and side_right < 0.8:
                return HorseOvertake.SORROUNDED
        elif relevant_dist < 8.0:
            # 少し詰まっている
            score += 0.2
        # 横に馬がいる
        if side_left < 0.8: score += 0.2
        if side_right < 0.8: score += 0.2

        # 現在の距離はどのあたりか？
        if (current_distance / race_distance) < 0.5:
            score += 1.0
            # 順位はどのあたりか？
            if (rank / num_horses) > 0.5:
                score += 1.0

        # セクション判断
        if section.name is SectionName.HOMESTRETCH:
            score += 2.0
        
        return HorseOvertake.OVERTAKE if score >= 2.0 else HorseOvertake.STAY

# ---------------------------------------------------------
# 具象Strategyクラス：差し
# ---------------------------------------------------------
class CloserStrategy:
    def get_start_speed(self, horse_prof: HorseProfile) -> float:
        return horse_prof.start_speed * START_SPEED_STYLE_FACTOR[HorseStrategyType.CLOSER]
    
    def get_cruise_speed(self, horse_prof: HorseProfile) -> float:
        return horse_prof.cruise_speed * CRUISE_SPEED_STYLE_FACTOR[HorseStrategyType.CLOSER]

    def get_spurt_speed(self, horse_prof: HorseProfile) -> float:
        return horse_prof.last_3f_speed * SPURT_SPEED_STYLE_FACTOR[HorseStrategyType.CLOSER]

    def determinate_overtake(self, horse_prof: HorseProfile, horse_snap: HorseSnapshot, env: dict) -> bool:
        #環境情報
        race_distance = env[HorseEnvField.RACE_DISTANCE]
        current_distance = horse_snap.distance
        section = env[HorseEnvField.SECTION]
        rank = env[HorseEnvField.RANK]
        num_horses = env[HorseEnvField.NUM_HORSES]
        ctx = env[HorseEnvField.DIST_TO_CONTEXT]
        dist_to_front = ctx[HorseEnvField.DIST_TO_FRONT]
        front_left = ctx[HorseEnvField.DIST_TO_FRONT_LEFT]
        front_right = ctx[HorseEnvField.DIST_TO_FRONT_RIGHT]
        side_left = ctx[HorseEnvField.DIST_TO_SIDE_LEFT]
        side_right = ctx[HorseEnvField.DIST_TO_SIDE_RIGHT]

        score = 0.0

        # 囲まれているか判定
        relevant_dist = 999.0
        relevant_dist = min(dist_to_front, front_left, front_right)
        # 前に馬がいる
        if relevant_dist < 3.0:
            # 眼の前
            score += 0.5
            # 詰まってる場合は抜けない
            if side_left < 0.8 and side_right < 0.8:
                return HorseOvertake.SORROUNDED
        elif relevant_dist < 8.0:
            # 少し詰まっている
            score += 0.2
        # 横に馬がいる
        if side_left < 0.8: score += 0.2
        if side_right < 0.8: score += 0.2

        # 現在の距離はどのあたりか？
        if (current_distance / race_distance) > 0.5:
            score += 1.0
            # 順位はどのあたりか？
            if (rank / num_horses) > 0.5:
                score += 1.0

        # セクション判断
        if section.name is SectionName.HOMESTRETCH:
            score += 2.0
        
        return HorseOvertake.OVERTAKE if score >= 2.0 else HorseOvertake.STAY

# ---------------------------------------------------------
# 具象Strategyクラス：追い込み
# ---------------------------------------------------------
class RearStrategy:
    def get_start_speed(self, horse_prof: HorseProfile) -> float:
        return horse_prof.start_speed * START_SPEED_STYLE_FACTOR[HorseStrategyType.REAR]
    
    def get_cruise_speed(self, horse_prof: HorseProfile) -> float:
        return horse_prof.cruise_speed * CRUISE_SPEED_STYLE_FACTOR[HorseStrategyType.REAR]

    def get_spurt_speed(self, horse_prof: HorseProfile) -> float:
        return horse_prof.last_3f_speed * SPURT_SPEED_STYLE_FACTOR[HorseStrategyType.REAR]

    def determinate_overtake(self, horse_prof: HorseProfile, horse_snap: HorseSnapshot, env: dict) -> bool:
        #環境情報
        race_distance = env[HorseEnvField.RACE_DISTANCE]
        current_distance = horse_snap.distance
        section = env[HorseEnvField.SECTION]
        rank = env[HorseEnvField.RANK]
        num_horses = env[HorseEnvField.NUM_HORSES]
        ctx = env[HorseEnvField.DIST_TO_CONTEXT]
        dist_to_front = ctx[HorseEnvField.DIST_TO_FRONT]
        front_left = ctx[HorseEnvField.DIST_TO_FRONT_LEFT]
        front_right = ctx[HorseEnvField.DIST_TO_FRONT_RIGHT]
        side_left = ctx[HorseEnvField.DIST_TO_SIDE_LEFT]
        side_right = ctx[HorseEnvField.DIST_TO_SIDE_RIGHT]

        score = 0.0

        # 囲まれているか判定
        relevant_dist = 999.0
        relevant_dist = min(dist_to_front, front_left, front_right)

        # 前に馬がいる
        if relevant_dist < 3.0:
            # 眼の前
            score += 0.5
            # 詰まってる場合は抜けない
            if side_left < 0.8 and side_right < 0.8:
                return HorseOvertake.SORROUNDED
        elif relevant_dist < 8.0:
            # 少し詰まっている
            score += 0.2
        # 横に馬がいる
        if side_left < 0.8: score += 0.2
        if side_right < 0.8: score += 0.2

        # 現在の距離はどのあたりか？
        if (current_distance / race_distance) > 0.7:
            score += 1.0
            # 順位はどのあたりか？
            if (rank / num_horses) > 0.5:
                score += 0.1

        # セクション判断
        if section.name is SectionName.HOMESTRETCH:
            score += 2.0
        
        return HorseOvertake.OVERTAKE if score >= 2.0 else HorseOvertake.STAY

# クラス取得用のMap
STRATEGY_MAP = {
    HorseStrategyType.LEADER: LeaderStrategy(),
    HorseStrategyType.STALKER: StalkerStrategy(),
    HorseStrategyType.CLOSER: CloserStrategy(),
    HorseStrategyType.REAR: RearStrategy(),
}
