"""
engine.py の概要

レースContextと各馬のインスタンスを使い、1フレームずつ時間を進める処理を行う
"""
import logging

# ロガーの取得（__name__ はファイル名/モジュール名になる）
logger = logging.getLogger(__name__)

from src.models.race_data import RaceProfile, RaceSnapshot
from src.models.horse_data import HorseProfile, HorseSnapshot
import src.core.physics as ph

from src.constants.enums import HorseBehaviorType

from src.core.behavior.base import HorseBehaviorState
from src.core.behavior.exhausted import ExhaustedState
from src.core.behavior.finished import FinishedState
from src.core.behavior.ingate import InGateState
from src.core.behavior.racing import RacingState
from src.core.behavior.spurting import SpurtingState
from src.core.behavior.starting import StartingState


_HORSE_STATES = {
    HorseBehaviorType.IN_GATE: InGateState(),
    HorseBehaviorType.STARTING: StartingState(),
    HorseBehaviorType.SPURTING: SpurtingState(),
    HorseBehaviorType.FINISHED: FinishedState(),
    HorseBehaviorType.RACING: RacingState(),
    HorseBehaviorType.EXHAUSTED: ExhaustedState(),
}

class RaceEngine:
    """
    レースを1stepだけ動かす
    """
    def __init__(self):
        logger.info("初期化中...")
        
    def step(self, current_snap: RaceSnapshot, race_prof: RaceProfile, dt: float) -> RaceSnapshot:
        """現在のSnapshotからdt秒後のSnapshotを生成して返す"""
        new_horse_snaps = {h_id: self._get_behavior(h_snap).update(
            h_id, race_prof, current_snap, dt) for h_id, h_snap in current_snap.horses.items()}

        return RaceSnapshot(
            race_id=current_snap.race_id,
            step=ph.calculate_next_step(current_snap.step),
            elapsed_time=ph.calculate_next_elapsed_time(current_snap.elapsed_time, dt),
            horses=new_horse_snaps,
        )
    
    def _get_behavior(self, horse_snap: HorseSnapshot) -> HorseBehaviorState:
        """BehaviorStateを返す"""
        return _HORSE_STATES[horse_snap.behavior]