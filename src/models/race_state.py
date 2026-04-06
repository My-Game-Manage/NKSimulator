"""
race_state.py の概要

レースの状態（HorseState）を保持するデータクラス。
"""
from dataclasses import dataclass, field, replace

from src.models.horse_state import HorseState


@dataclass(frozen=True)
class RaceState:
    step_count: int
    elapsed_time: float
    horse_states: list[HorseState] = field(default_factory=list)
    
    @property
    def is_all_goal(self) -> bool:
        # 判定ロジックをプロパティとして持たせると便利
        return all(h_state.is_goal for h_state in self.horse_states)
    
    def update_ranks(self) -> 'RaceState':
        """現在の全馬の距離を比較し、順位を書き込んだ新しいRaceStateを返す"""
        sorted_states = self.get_sorted_horse_states()
        new_horse_states = []
        rank_count = 0
        for h_state in sorted_states:
            old_h_state = h_state
            rank_count += 1
            # dataclasses.replace を使って rank だけ書き換えたコピーを作成
            new_horse_states.append(replace(old_h_state, rank=rank_count))
        return replace(self, horse_states=new_horse_states)
    
    def get_sorted_horse_ids_as_simple(self) -> list[str]:
        """
        現在の走行距離に基づいて、馬IDを順位順（降順）に並べたリストを返す（簡略版）
        """
        # 距離(distance)で降順ソートし、IDのリストを抽出
        sorted_states = sorted(
            self.horse_states,
            key=lambda h: h.distance,
            reverse=True
        )
        return [h.horse_id for h in sorted_states]

    def get_rank_map(self) -> dict[str, int]:
        """
        {馬ID: 順位} の辞書を返す
        """
        sorted_ids = self.get_sorted_horse_ids()
        return {horse_id: rank + 1 for rank, horse_id in enumerate(sorted_ids)}
    
    def get_sorted_horse_ids(self) -> list[str]:
        """
        ゴール済みの馬はタイム順、走行中の馬は距離順でソートしてIDリストを返す（厳密版）
        """
        def sort_key(h: HorseState):
            if h.is_finished:
                # ゴール済みの場合: 
                # 第1優先: True (1) になり、未ゴールの馬 (0) より前に来る
                # 第2優先: タイムが小さいほど「大きい値」になるよう反転させる
                # (例: 99999 - 105.5s)
                return (1, 99999 - h.finish_time)
            else:
                # 未ゴールの場合:
                # 第1優先: False (0)
                # 第2優先: 走行距離そのもの
                return (0, h.distance)

        sorted_states = sorted(
            self.horse_states,
            key=sort_key,
            reverse=True
        )
        return [h.horse_id for h in sorted_states]
    
    def get_sorted_horse_states(self) -> list[HorseState]:
        """IDではなくHorseStatesの着順リストを返す"""
        def sort_key(h: HorseState):
            if h.is_finished:
                # ゴール済みの場合: 
                # 第1優先: True (1) になり、未ゴールの馬 (0) より前に来る
                # 第2優先: タイムが小さいほど「大きい値」になるよう反転させる
                # (例: 99999 - 105.5s)
                return (1, 99999 - h.finish_time)
            else:
                # 未ゴールの場合:
                # 第1優先: False (0)
                # 第2優先: 走行距離そのもの
                return (0, h.distance)

        sorted_states = sorted(
            self.horse_states,
            key=sort_key,
            reverse=True
        )
        return sorted_states
