"""
engine.py の概要

レースContextと各馬のインスタンスを使い、1フレームずつ時間を進める処理を行う
"""
import logging

# ロガーの取得（__name__ はファイル名/モジュール名になる）
logger = logging.getLogger(__name__)

from src.models.race_info import RaceInfo, RaceParam, RaceState, RaceDataSet
from src.models.horse_info import HorseInfo, HorseParam, HorseState, HorseTactics, HorseEnv, HorseFactors
from src.models.section import SectionType, TrackSection, SectionName
from src.constants.tactics_master import HorseMode, HorseMove
import src.core.physics as ph
import src.core.tactics as tac


class RaceEngine:
    def __init__(self):
        logger.info("初期化中...")
        
    def step(self, current_state: RaceState, race_param: RaceParam, dt: float) -> RaceState:
        """現在のStateからdt秒後のStateを生成して返す"""
        new_states = {}
        for h_id, h_state in current_state.horses.items():
            new_horse_state = self._update_horse(h_id, race_param, current_state.horses, dt)
            new_states[h_id] = new_horse_state

        return RaceState(
            race_id=current_state.race_id,
            step_count=self._calc_next_step(current_state.step_count),
            elapsed_time=self._calc_next_elapsed_time(current_state.elapsed_time, dt),
            horses=new_states,
        )
    
    def _calc_next_elapsed_time(self, elapsed_time: float, dt: float) -> float:
        """今の経過時間にdtを足して返す（次の経過時間）"""
        return round(elapsed_time + dt, 2) # 浮動小数点の誤差防止
    
    def _calc_next_step(self, current_step) -> int:
        """次のstepを計算して返す"""
        return current_step + 1
    
    def _update_horse(self, horse_id: str, race_param: RaceParam, horses: dict[str, HorseState], dt: float) -> HorseState:
        """馬の速度と距離の更新をし、次のStateを作成"""
        current_state = horses[horse_id]
        current_param = race_param.horses[horse_id]
        # 1. スキップ判定（すでにゴールしている馬はそのままStateを返す）
        if current_state.is_finished:
            return current_state.next_step()
        
        # 2. 環境認識フェーズ
        # - 他馬との位置関係
        # - コース情報
        horse_env = self._perceive_horse_position(current_state, race_param, horses)

        # 3. 意思決定フェーズ（目標速度算出）
        # - ベース速度
        # - 制限（衝突回避）
        # - スタミナ制限
        horse_tactics = self._decide_horse_tactics(horse_env)
        target_v = self._decide_horse_target_speed(current_param, horse_env, horse_tactics)
        accel = ph.calculate_acceleration(target_v, current_state.velocity, current_param.acceleration)

        # 4. 物理実行フェーズ（数値更新）
        velocity = current_state.velocity + accel * dt
        distance = current_state.distance + velocity * dt
        finish_time = None

        # 5. ゴール判定
        is_finished = False
        if ph.is_horse_finished(distance, race_param.distance):
            is_finished = True
            finish_time = ph.interpolate_goal_time(current_state.distance, distance,
                                                   current_state.elapsed_time, dt, race_param.distance)
        
        # TODO: 各要素を更新
        return HorseState(
            horse_id=current_state.horse_id,
            step=self._calc_next_step(current_state.step),
            elapsed_time=self._calc_next_elapsed_time(current_state.elapsed_time, dt),
            distance=distance,
            velocity=velocity,
            target_velocity=target_v,
            stamina=1,
            is_spurting=False,
            is_exhausted=False,
            section_name="",
            lane_p=1,
            is_blocked=False,
            is_finished=is_finished,
            finish_time=finish_time,
        )
    
    def _perceive_horse_position(self, current_state: HorseState, race_param: RaceParam, horses: dict[str, HorseState]) -> HorseEnv:
        """馬の環境認識フェーズ（位置関係やコース場所）"""
        # 現在のセクション
        section = ph.current_section_from(current_state.distance, race_param.sections)
        # 前の馬がいるか？その距離
        dist_to_front = self._distance_to_front_horse_from(current_state, horses)
        return HorseEnv(
            current_section=section,
            dist_to_front=dist_to_front,
        )

    def _section_factor_from(self, current_distance: float, sections: list[TrackSection], corner_penalty: float) -> float:
        """セクションによる補正値を返す"""
        section_type = ph.current_section_from(current_distance, sections)
        if section_type is SectionType.CURVE:
            return corner_penalty
        else:
            return 1.0 # Nothing
        
    def _distance_to_front_horse_from(self, current_state: HorseState, horses: dict[str, HorseState]) -> float:
        """前の馬との距離の更新"""
        min_dist = 999.0
        for h_id, other_state in horses.items():
            if current_state.horse_id == h_id: continue
            # 16レーンあるため、幅 0.5 程度を「同じ進路」とみなす
            if abs(current_state.lane_p - other_state.lane_p) < 0.5:
                dist = other_state.distance - current_state.distance
                if 0 < dist < min_dist:
                    min_dist = dist
        return min_dist
    
    def _surface_friction_factor_from(self, race_param: RaceParam) -> float:
        """馬場による補正を返す"""
        return race_param.surface_friction
    
    def _decide_horse_tactics(self, horse_env: HorseEnv) -> HorseTactics:
        """環境情報からTacticsを返す"""
        # この部分は本来はtacticsに投げる
        section = horse_env.current_section
        dist_to_front = horse_env.dist_to_front
        if section.type == SectionType.CURVE:
            # カーブはKEEP
            move = HorseMove.STAY
            mode = HorseMode.KEEP
        # 直線の場合は
        elif section.name == SectionName.STARTING:
            # スタート
            move = HorseMove.INSIDE
            mode = HorseMode.START
        elif section.name == SectionName.HOMESTRETCH:
            # ラストスパート
            move = HorseMove.STAY
            mode = HorseMode.SPURT
        elif dist_to_front < 5.0:
            # 前に馬がいる => 脚質により「外に出して抜く」or「後ろで追走」
            move = HorseMove.OUTSIDE
            mode = HorseMode.INCREASE
        else:
            # それ以外 => 巡航速度までは上げる
            move = HorseMove.STAY
            mode = HorseMode.INCREASE
        return HorseTactics(
            move=move,
            mode=mode,
        )

    def _decide_horse_target_speed(self, param: HorseParam, env: HorseEnv, tactics: HorseTactics) -> float:
        """馬の意思決定フェーズ（目標速度決定）"""
        # 目標速度の設定
        target_v = param.max_speed
        return target_v
    
    def _decide_horse_tactics_from(self) -> HorseTactics:
        """HorseTacticsを返す"""
        return HorseTactics(
            move=HorseMove.STAY,
            mode=HorseMode.KEEP,
        )

    def _update_horse_status(self):
        """馬の各数値を更新する"""
        pass

    def _update_horse_current_velocity(self):
        """馬の現在の速度を更新する"""
        pass

    def _update_horse_current_distance(self):
        """馬の現在の距離を更新する"""
        pass

    def _update_horse_remaining_stamina(self):
        """馬の残りのスタミナを更新する"""
        pass
    
    def _update_horse1(self, current_state: HorseState, h_info: HorseInfo, race_info: RaceInfo, dt: float) -> HorseState:
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
        # 最大速度までに制限
        target_v = ph.manage_limited_speed(target_v, h_info.param.max_speed)
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
    
    def _update_lane_position(self, h_state: HorseState) -> float:
        """進路（lane）の更新"""
        return 1.0
    