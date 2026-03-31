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
        record = {
            RaceCol.COURSE: context.course_name,
            RaceCol.RACE_NUMBER: getattr(context, 'race_number', 0), # Contextに持たせておくと便利
            RaceCol.SURFACE: context.surface,
            RaceCol.DISTANCE: context.distance,
            RaceCol.HORSE_ID: horse.horse_id,
            RaceCol.HORSE_NAME: horse.name,
            RaceCol.TIME: round(finish_time, 2),
            "remaining_stamina": round(horse.state.current_stamina, 2),
            "avg_velocity": round(context.distance / finish_time, 2) if finish_time > 0 else 0
        }
        self.results.append(record)

    def save_to_csv(self, filename: str = None):
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
        for row in df.columns:
            self.logger.info(f"{row[RaceCol.RANK]} | {row[RaceCol.HORSE_NAME]} | {row[RaceCol.TIME]} | {row['remaining_stamina']} | {row['ave_velocity']}")
