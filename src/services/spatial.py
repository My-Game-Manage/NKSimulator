from dataclasses import dataclass
from typing import List, Optional, Tuple
from models.horse import Horse

@dataclass
class Surroundings:
    """
    ある馬から見た周囲の物理的状況をまとめたデータ構造。
    TacticsAIはこの値を参照して意思決定を行う。
    """
    dist_to_front: float = 999.0
    front_horse_velocity: Optional[float] = None
    # 将来的に「右斜め前に馬がいるか」などの拡張が可能
    is_left_blocked: bool = False
    is_right_blocked: bool = False

class SpatialService:
    """
    馬の空間認識を司るサービス。
    コース上の全馬の位置関係をスキャンし、特定の馬に必要な周辺情報を提供する。
    """

    def __init__(self, lane_threshold: float = 0.5):
        # 同じ進路（レーン）とみなす幅の閾値
        self.lane_threshold = lane_threshold

    def scan(self, observer: Horse, participants: List[Horse]) -> Surroundings:
        """
        指定した馬(observer)の周囲をスキャンし、Surroundingsオブジェクトを返す。
        """
        front_horse = self._get_front_horse(observer, participants)
        
        if front_horse:
            dist = front_horse.state.current_position - observer.state.current_position
            return Surroundings(
                dist_to_front=dist,
                front_horse_velocity=front_horse.state.current_velocity
            )
        
        # 前方に馬がいない場合
        return Surroundings()

    def _get_front_horse(self, observer: Horse, participants: List[Horse]) -> Optional[Horse]:
        """
        同一レーン上で最も近い前方の馬を探索する。
        """
        min_dist = 999.0
        target_horse = None
        
        obs_pos = observer.state.current_position
        obs_lane = observer.state.current_lane

        for other in participants:
            if observer.horse_id == other.horse_id:
                continue
            
            # 1. レーン判定（設定された閾値以内の横幅にいるか）
            if abs(obs_lane - other.state.current_lane) < self.lane_threshold:
                # 2. 前後判定
                dist = other.state.current_position - obs_pos
                if 0 < dist < min_dist:
                    min_dist = dist
                    target_horse = other
                    
        return target_horse