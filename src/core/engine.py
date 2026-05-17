"""
engine.py の概要

レースContextと各馬のインスタンスを使い、1フレームずつ時間を進める処理を行う
"""
import logging

# ロガーの取得（__name__ はファイル名/モジュール名になる）
logger = logging.getLogger(__name__)

from src.models.race_data import RaceProfile, RaceSnapshot
from src.models.horse_data import HorseProfile, HorseSnapshot
from src.core.behaivor import HorseBehaviorState, HORSE_STATE_MAP
import src.core.physics as ph

class RaceEngine:
    def __init__(self):
        logger.info("初期化中...")
        
    def step(self, current_snap: RaceSnapshot, race_prof: RaceProfile, dt: float) -> RaceSnapshot:
        """現在のSnapshotからdt秒後のSnapshotを生成して返す"""
        new_horse_snaps = {}
        for h_id, h_snap in current_snap.horses.items():
            new_horse_snap = self._get_horse_behavior(h_snap).update(h_id, race_prof, current_snap, dt)
            new_horse_snaps[h_id] = new_horse_snap

        return RaceSnapshot(
            race_id=current_snap.race_id,
            step=ph.calc_next_step(current_snap.step),
            elapsed_time=ph.calc_next_elapsted_time(current_snap.elapsed_time, dt),
            horses=new_horse_snaps,
        )
    
    def _get_horse_behavior(self, horse_snap: HorseSnapshot) -> HorseBehaviorState:
        """BehaviorStateを返す"""
        return HORSE_STATE_MAP[horse_snap.behavior]