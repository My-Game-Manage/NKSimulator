from typing import List, Tuple, Optional
from constants.strategy import StrategyConfig, StrategyParamKey, STRATEGY_LANE_MAP, StrategyType
from models.horse import Horse

class TacticsAI:
    """
    馬の意思決定（戦術）を司るクラス。
    物理演算（Engine）から切り離し、進路取りやペース配分の判断のみを行う。
    """

    def __init__(self, horse: Horse):
        self.horse = horse

    def decide_next_move(self, surroundings, segment_type: str) -> Tuple[float, float]:
        """
        次のフレームでの目標速度と目標レーンを決定する。
        """
        # 1. 基礎となる目標速度の算出
        target_v = self._calculate_base_target_velocity(segment_type)

        # 2. 前方の状況に応じた速度調整（同期・ブレーキ）
        target_v = self._adjust_velocity_by_surroundings(target_v, surroundings)

        # 3. 進路（レーン）の決定
        target_lane = self._decide_target_lane(surroundings, segment_type, target_v)

        return target_v, target_lane

    def _calculate_base_target_velocity(self, segment_type: str) -> float:
        """
        他馬の影響を考慮しない、現在のスタミナや区間に基づいた理想的な目標速度。
        """
        strat_params = StrategyConfig.get(self.horse.strategy)
        pos = self.horse.state.current_position
        
        # スタートダッシュ(300m以内)
        if pos < 300.0:
            if self.horse.strategy in [StrategyType.LEAD, StrategyType.FRONT]:
                return self.horse.params.max_velocity * 1.05
            return self.horse.params.max_velocity * 1.00
        
        # バテ状態
        if self.horse.state.is_exhausted:
            return self.horse.params.max_velocity * strat_params[StrategyParamKey.EXHAUST_SPEED_COEFF]
        
        # スパート状態
        if self.horse.state.is_spurt:
            return self.horse.params.max_velocity
        
        # 巡航状態
        return self.horse.params.max_velocity * strat_params[StrategyParamKey.CRUISING_COEFF]

    def _adjust_velocity_by_surroundings(self, base_target_v: float, surroundings) -> float:
        """
        前方馬との距離(dist)と速度(front_v)に基づき、追走・ブレーキの調整を行う。
        """
        dist = surroundings.dist_to_front
        front_v = surroundings.front_horse_velocity
        pos = self.horse.state.current_position

        # 100m以内は密集を許容して加速優先
        if pos < 100.0:
            return base_target_v

        if dist < 5.0 and front_v is not None:
            if dist < 1.5:
                # ブレーキ：前の馬に合わせつつ、わずかに減速して車間を保つ
                return min(base_target_v, front_v * 0.98)
            else:
                # 同期：前の馬のペースに吸い付く
                return min(base_target_v, front_v + 0.1)
        
        return base_target_v

    def _decide_target_lane(self, surroundings, segment_type: str, current_target_v: float) -> float:
        """
        「壁」の判定を行い、追い越しが必要か、内ラチに戻るべきかを判断する。
        """
        ideal_lane = STRATEGY_LANE_MAP.get(self.horse.strategy, 1)
        dist = surroundings.dist_to_front
        front_v = surroundings.front_horse_velocity
        current_lane = self.horse.state.current_lane
        pos = self.horse.state.current_position

        # 1. 基本方針：直線終盤以外は理想レーンを目指す
        if segment_type == "straight" and pos > 800:
            target_lane = current_lane
        else:
            target_lane = ideal_lane

        # 2. 追い越し判定（壁判定）
        if dist < 5.0 and front_v is not None:
            base_v = self._calculate_base_target_velocity(segment_type)
            # 自分のポテンシャルが前の馬より高い（追い抜きたい）場合
            if base_v > (front_v + 0.05):
                # 外に持ち出す
                target_lane = current_lane + 2.0
            else:
                # 前が速いなら今のレーンで追走
                target_lane = current_lane
        
        # 3. 復帰判定
        elif current_lane > ideal_lane:
            # 前が空いていれば理想レーンに戻る
            target_lane = ideal_lane

        return max(0.0, min(target_lane, 15.0))