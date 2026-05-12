"""
race_analyzer.py の概要

レースの分析をして結果等を追加するヘルパー
"""
from dataclasses import replace
import logging

# ロガーの取得（__name__ はファイル名/モジュール名になる）
logger = logging.getLogger(__name__)

from src.models.race_data import RaceSnapshot
from src.models.horse_data import HorseSnapshot


class RaceAnalyer:
    @staticmethod
    def update_ranks(race_snap: RaceSnapshot) -> RaceSnapshot:
        """現在の距離に基づき、全馬の順位を更新した新しいStateを生成する"""
        # 既にゴールしている馬がいた場合の対処
        def sort_key(h: HorseSnapshot):
            if h.is_finished:
                return (1, 99999 - h.finish_time)
            return (0, h.distance)

        # 1. ソートしてゴール済の馬の順位を確定
        sorted_horses = sorted(race_snap.horses.values(), key=sort_key, reverse=True)
        
        # 2. rankを書き換えた新しいHorseStateのリストを作成
        new_ranks = {}
        for i, h_state in enumerate(sorted_horses):
            new_ranks[h_state.horse_id] = i + 1
            
        # 3. 順位が更新された新しいRaceStateを返す
        return race_snap.update_ranks(new_ranks)

    @staticmethod
    def is_all_goal(race_snap: RaceSnapshot) -> bool:
        """全馬ゴールしたか判定する"""
        for h_id in race_snap.horses.keys():
            if not race_snap.horses[h_id].is_finished:
                return False
        return True
    
    @staticmethod
    def update_time_at_600m(distance: float, race_snap: RaceSnapshot) -> RaceSnapshot:
        """残り600mを切ったところで時間を記録する"""
        horses = race_snap.horses
        is_updated = False
        for h_id, h_snap in horses.items():
            if h_snap.distance >= (distance - 600) and h_snap.time_at_600m is None:
                # ゴール前600m地点のタイムを記録しておく
                update_snap = replace(h_snap, time_at_600m=h_snap.elapsed_time)
                horses[h_id] = update_snap
                is_updated = True
        if is_updated:
            return replace(race_snap, horses=horses)
        else:
            return race_snap

    @staticmethod
    def update_laptime_at_furlong(race_snap :RaceSnapshot) -> RaceSnapshot:
        """1F（200m）毎のラップタイムを記録する"""
        horses = race_snap.horses
        is_updated = False
        for h_id, h_snap in horses.items():
            current_distance = int(h_snap.distance // 200)
            if current_distance <= 0: continue
            if h_snap.distance >= current_distance * 200 and h_snap.laptimes[current_distance - 1] <= 0.0:
                # その地点のラップライムを記録する
                laptimes = h_snap.laptimes
                laptimes[current_distance - 1] = h_snap.elapsed_time
                update_snap = replace(h_snap, laptimes=laptimes)
                horses[h_id] = update_snap
                is_updated = True
        if is_updated:
            return replace(race_snap, horses=horses)
        else:
            return race_snap
        
    @staticmethod
    def update_checkpoint_rank(checkpoints: list, race_snap: RaceSnapshot) -> RaceSnapshot:
        """チェックポイント（コーナー）での順位を記録する"""
        horses = race_snap.horses
        is_updated = True
        for h_id, h_snap in horses.items():
            for idx in range(len(checkpoints)):
                check_dist = checkpoints[idx]
                if h_snap.distance >= check_dist and h_snap.checkpoint_ranks[idx] <= 0:
                    # その地点での順位を記録する
                    checkpoint_ranks = h_snap.checkpoint_ranks
                    checkpoint_ranks[idx] = race_snap.ranks[h_id]
                    update_snap = replace(h_snap, checkpoint_ranks=checkpoint_ranks)
                    horses[h_id] = update_snap
                    is_updated = True
        if is_updated:
            return replace(race_snap, horses=horses)
        else:
            return race_snap


