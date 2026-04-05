"""
engine.py の概要

レースContextと各馬のインスタンスを使い、1フレームずつ時間を進める処理を行う
"""
import logging

# ロガーの取得（__name__ はファイル名/モジュール名になる）
logger = logging.getLogger(__name__)

from src.models.race_info import RaceInfo
from src.models.race_state import RaceState
from src.models.horse_info import HorseInfo
from src.models.horse_param import HorseParam
from src.models.horse_state import HorseState
from src.models.section import SectionType, TrackSection
import src.core.physics as ph


class RaceEngine:
    def __init__(self):
        logger.info("初期化中...")
        
    def step(self, current_state: RaceState, race_info: RaceInfo, dt: float) -> RaceState:
        """
        現在の RaceState から、dt秒後の RaceState を計算して返す
        """
        new_horse_states = []
        # 時間の更新
        next_elapsed_time = round(current_state.elapsed_time + dt, 2) # 浮動小数点の誤差防止
        
        for h_state in current_state.horse_states:
            horse_id = h_state.horse_id
            # HorseInfo(固定パラ)を取得
            h_info = race_info.get_horse(horse_id)
            
            # 新しい状態を計算（ここで前述の速度・スタミナ計算を呼ぶ）
            new_h_state = self._update_horse(h_state, h_info, race_info, dt)
            new_horse_states.append(new_h_state)
            
        return RaceState(
            step_count=current_state.step_count + 1,
            elapsed_time=next_elapsed_time,
            horse_states=new_horse_states
            )

    def _update_horse(self, current_state: HorseState, h_info: HorseInfo, race_info: RaceInfo, dt: float) -> HorseState:
        """馬を1step動かして、新しいStateを生成する"""

        # 1. ゴール判定（すでにゴールしている馬はそのままStateを返す）
        if current_state.is_finished:
            return current_state.next_step()

        # 2. 環境認識フェーズ
        # - 他馬との位置関係
        # - コース情報

        # 3. 意思決定フェーズ（目標速度算出）
        # - ベース速度
        # - 制限（衝突回避）
        # - スタミナ制限

        # 4. 物理実行フェーズ（数値更新）
        # - 速度
        target_v = ph.calculate_simple_acceled_speed(current_state.velocity, h_info.param.acceleration, dt)
        # - 距離
        distance = ph.calculate_simple_target_position(target_v, current_state.distance, dt)
        # - スタミナ

        # 5. 状態確定フェーズ（ゴール判定とフラグ更新）
        # - ゴール判定
        is_finished = False
        finish_time = None
        if ph.check_goal(distance, race_info.distance):
            is_finished = True
            logger.info(f"{h_info.name} - Goal!")
            # ゴールした時はタイムを記録する
            finish_time = ph.interpolate_goal_time(current_state.distance, distance, current_state.elapsed_time, dt, race_info.distance)
        # - フラグ更新

        horse_id = current_state.horse_id
        step = current_state.step + 1
        elapsed_time = round(current_state.elapsed_time + dt, 2) # 浮動小数点の誤差防止
        velocity = target_v
        target_velocity = h_info.param.max_speed
        stamina = h_info.param.total_stamina
        is_spurting = False
        is_exhausted = False
        section_name = SectionType.STRAIGHT
        lane_p=0
        is_blocked = False

        return HorseState(
            horse_id=horse_id,
            step=step,
            elapsed_time=elapsed_time,
            distance=distance,
            velocity=velocity,
            target_velocity=target_velocity,
            stamina=stamina,
            is_spurting=is_spurting,
            is_exhausted=is_exhausted,
            section_name=section_name,
            lane_p=lane_p,
            is_blocked=is_blocked,
            is_finished=is_finished,
            finish_time=finish_time,
        )
    
    def _check_current_section(self, h_state: HorseState, section: TrackSection) -> SectionType:
        """現在のセクション判定"""
        # TODO: とりあえず直線
        return SectionType.STRAIGHT

    def _update_lane_position(self, h_state: HorseState) -> float:
        """進路（lane）の更新"""
        return 1.0
    