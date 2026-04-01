"""
saver.py の概要

記録用
"""
import pandas as pd
from datetime import datetime
from pathlib import Path

from utils.logger import setup_logger
from constants.schema import RaceCol

class ResultSaver:
    def __init__(self, output_dir: str = "results"):
        _CLASSNAME = "ResultSaver"
        # クラス名を名前としてロガーを作成
        self.logger = setup_logger(_CLASSNAME)

        self.logger.info("初期化中...")
        
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.results = []

    def record_finish(self, horse, finish_time: float, context):
        """
        馬がゴールした瞬間のデータを記録する
        """
        # 上がり3Fの計算
        last_3f = 0.0
        if horse.state.time_at_600m > 0:
            last_3f = finish_time - horse.state.time_at_600m
        
        # リストをハイフン繋ぎの文字列に変換
        passing_order_str = "-".join(map(str, horse.state.passing_ranks))
            
        record = {
            RaceCol.COURSE: context.course_name,
            RaceCol.RACE_NUMBER: getattr(context, 'race_number', 0), # Contextに持たせておくと便利
            RaceCol.SURFACE: context.surface,
            RaceCol.DISTANCE: context.distance,
            RaceCol.HORSE_ID: horse.horse_id,
            RaceCol.BRACKET_NUM: horse.bracket_num,
            RaceCol.HORSE_NUM: horse.horse_num,
            RaceCol.HORSE_NAME: horse.name,
            RaceCol.TIME: round(finish_time, 2),
            "remaining_stamina": round(horse.state.current_stamina, 2),
            "stamina_capacity": horse.params.stamina_capacity,
            "avg_velocity": round(context.distance / finish_time, 2) if finish_time > 0 else 0,
            "max_velocity": round(horse.params.max_velocity, 2),
            RaceCol.LAST_3F: round(last_3f, 2), # schema.pyの定数を使用
            RaceCol.PASSING_ORDER: passing_order_str, # schema.py の定数を使用
            "strategy": horse.strategy,
            "spurt_dist": round(horse.state.spurt_dist, 2),
            "is_exhausted": horse.state.is_exhausted,
        }
        self.results.append(record)
        
    def save_to_csv(self, filename: str = None):
        """
        蓄積されたデータをレースごとにソートしてCSVとして保存
        """
        if not self.results:
            self.logger.info("保存するデータがありません。")
            return

        df = pd.DataFrame(self.results)
        
        # 1. レース番号(RACE_NUMBER)とタイム(TIME)で昇順ソート
        # これにより、同じレース内でのタイム順に並びます
        df = df.sort_values(by=[RaceCol.RACE_NUMBER, RaceCol.TIME])

        # 2. レースごとにグループ化し、その中で着順（Rank）を付与
        # groupby(RaceCol.RACE_NUMBER) を使うことで、レースごとに 1, 2, 3... と連番を振れます
        df[RaceCol.RANK] = df.groupby(RaceCol.RACE_NUMBER).cumcount() + 1

        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"sim_result_{timestamp}.csv"
        
        save_path = self.output_dir / filename
        df.to_csv(save_path, index=False, encoding="utf-8-sig")
        self.logger.info(f"結果を保存しました: {save_path}")
        return df
        
    def save_to_csv_old(self, filename: str = None):
        """
        蓄積されたデータをCSVとして保存
        """
        if not self.results:
            self.logger.info("保存するデータがありません。")
            return

        df = pd.DataFrame(self.results)
        
        # 着順（Rank）をタイム順に計算して付与
        df = df.sort_values(by=RaceCol.TIME)
        df[RaceCol.RANK] = range(1, len(df) + 1)

        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"sim_result_{timestamp}.csv"
        
        save_path = self.output_dir / filename
        df.to_csv(save_path, index=False, encoding="utf-8-sig")
        self.logger.info(f"結果を保存しました: {save_path}")
        return df
        
    def display_result(self, df: pd.DataFrame):
        """
        簡易結果表示
        """
        pd.set_option('display.float_format', '{:.2f}'.format)
        for _, r in df.iterrows():
            print(r)
