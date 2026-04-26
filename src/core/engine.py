"""
engine.py の概要

レースContextと各馬のインスタンスを使い、1フレームずつ時間を進める処理を行う
"""
import logging

# ロガーの取得（__name__ はファイル名/モジュール名になる）
logger = logging.getLogger(__name__)

from src.models.race_data import RaceProfile, RaceSnapshot
from src.models.horse_data import HorseProfile, HorseSnapshot


class RaceEngine:
    def __init__(self):
        logger.info("初期化中...")
        
    def step(self, current_snap: RaceSnapshot, race_profile: RaceProfile, dt: float) -> RaceSnapshot:
        """現在のSnapshotからdt秒後のSnapshotを生成して返す"""
        new_snap = {}
        for h_id, h_snap in current_snap.horses.items():
            new_horse_state = self._update_horse(h_id, race_profile, current_state.horses, dt)
            new_states[h_id] = new_horse_state

        return RaceSnapshot(
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
    
    def _update_horse(self, horse_id: str, race_profile: RaceProfile, horses: dict[str, HorseSnapshot], dt: float) -> HorseSnapshot:
        """馬の速度と距離の更新をし、次のStateを作成"""
        current_state = horses[horse_id]
        h_prof = race_profile.horses[horse_id]
        # 1. スキップ判定（すでにゴールしている馬はそのままStateを返す）
        if current_state.is_finished:
            return current_state.next_step()
        
        # 2. 環境認識フェーズ
        # - 他馬との位置関係
        # - コース情報
        horse_env = self._perceive_horse_position(current_state, race_profile, horses)

        # 3. 意思決定フェーズ（目標速度算出）
        # - ベース速度
        # - 制限（衝突回避）
        # - スタミナ制限
        horse_tactics = self._decide_horse_tactics(horse_env)
        target_v = self._decide_horse_target_speed(h_prof, horse_env, horse_tactics)
        accel = ph.calculate_acceleration(target_v, current_state.current_velocity, h_prof.acceleration)

        # 4. 物理実行フェーズ（数値更新）
        velocity = current_state.current_velocity + accel * dt
        distance = current_state.current_distance + velocity * dt
        finish_time = None

        # 5. ゴール判定
        is_finished = False
        if ph.is_horse_finished(distance, race_profile.distance):
            is_finished = True
            finish_time = ph.interpolate_goal_time(current_state.current_distance, distance,
                                                   current_state.elapsed_time, dt, race_profile.distance)
        
        # TODO: 各要素を更新
        return HorseSnapshot(
            horse_id=current_state.horse_id,
            step=self._calc_next_step(current_state.step),
            elapsed_time=self._calc_next_elapsed_time(current_state.elapsed_time, dt),
            current_distance=distance,
            current_velocity=velocity,
            target_velocity=target_v,
            remaining_stamina=1,
            is_spurting=False,
            is_exhausted=False,
            current_lane=1,
            is_blocked=False,
            is_finished=is_finished,
            finish_time=finish_time,
        )
    
    def _perceive_horse_position(self, current_state: HorseSnapshot, race_profile: RaceProfile, horses: dict[str, HorseSnapshot]):
        """馬の環境認識フェーズ（位置関係やコース場所）"""
        # 現在のセクション
        section = ph.current_section_from(current_state.current_distance, race_profile.sections)
        # 前の馬がいるか？その距離
        dist_to_front = self._distance_to_front_horse_from(current_state, horses)
        return {
            'current_section': section,
            'dist_to_front':dist_to_front,
        }

    """def _section_factor_from(self, current_distance: float, sections: list[TrackSection], corner_penalty: float) -> float:
        セクションによる補正値を返す
        section_type = ph.current_section_from(current_distance, sections)
        if section_type is SectionType.CURVE:
            return corner_penalty
        else:
            return 1.0 # Nothing
    """    
    def _distance_to_front_horse_from(self, current_state: HorseSnapshot, horses: dict[str, HorseSnapshot]) -> float:
        """前の馬との距離の更新"""
        min_dist = 999.0
        for h_id, other_state in horses.items():
            if current_state.horse_id == h_id: continue
            # 16レーンあるため、幅 0.5 程度を「同じ進路」とみなす
            if abs(current_state.current_lane - other_state.current_lane) < 0.5:
                dist = other_state.current_distance - current_state.current_distance
                if 0 < dist < min_dist:
                    min_dist = dist
        return min_dist
    
    def _surface_friction_factor_from(self, race_param: RaceProfile) -> float:
        """馬場による補正を返す"""
        return race_param.surface_friction
    """
    def _decide_horse_tactics(self, horse_env: HorseEnv) -> HorseTactics:
        環境情報からTacticsを返す
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
        """

    def _decide_horse_target_speed(self, h_prof: HorseProfile, env: dict, tactics: str) -> float:
        """馬の意思決定フェーズ（目標速度決定）"""
        # 目標速度の設定
        target_v = h_prof.max_speed
        return target_v
    
    def _decide_horse_tactics_from(self) -> str:
        """HorseTacticsを返す"""
        #return HorseTactics(
        #    move=HorseMove.STAY,
        #    mode=HorseMode.KEEP,
        #)
        return ""

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
        
    def _update_lane_position(self, h_state: HorseSnapshot) -> float:
        """進路（lane）の更新"""
        return 1.0
    