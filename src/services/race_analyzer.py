"""
race_analyzer.py の概要

レースの分析をして結果等を追加するヘルパー
"""
import logging

# ロガーの取得（__name__ はファイル名/モジュール名になる）
logger = logging.getLogger(__name__)

from src.models.race_info import RaceState
from src.models.horse_info import HorseState


class RaceAnalyer:
    @staticmethod
    def update_ranks(race_state: RaceState) -> RaceState:
        """現在の距離に基づき、全馬の順位を更新した新しいStateを生成する"""
        # 既にゴールしている馬がいた場合の対処
        def sort_key(h: HorseState):
            if h.is_finished:
                return (1, 99999 - h.finish_time)
            return (0, h.distance)

        # 1. ソートしてゴール済の馬の順位を確定
        sorted_horses = sorted(race_state.horses.values(), key=sort_key, reverse=True)
        
        # 2. rankを書き換えた新しいHorseStateのリストを作成
        new_ranks = {}
        for i, h_state in enumerate(sorted_horses):
            new_ranks[h_state.horse_id] = i + 1
            
        # 3. 順位が更新された新しいRaceStateを返す
        return race_state.update_ranks(new_ranks)

    @staticmethod
    def is_all_goal(race_state: RaceState) -> bool:
        """全馬ゴールしたか判定する"""
        for h_id in race_state.horses.keys():
            if not race_state.horses[h_id].is_finished:
                return False
        return True