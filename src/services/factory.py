"""
factory.py の概要

1. ContextFactory　- RaceContextインスタンスの作成
"""
import pandas as pd
from pathlib import Path

from utils.logger import setup_logger
from constants.schema import RaceCol
from models.context import RaceContext
from models.horse import Horse
from models.params import StaticParams

class ContextFactory:
    # 会場ごとの定数を定義
    COURSE_MASTER = {
        "大井": {"width": 25, "radius_factor": 1.0, "base_friction": 0.05},
        "笠松": {"width": 20, "radius_factor": 1.2, "base_friction": 0.07}, # 笠松は砂が深くコーナーが急
    }

    @staticmethod
    def create_from_df(race_df):
        """
        抽出されたDataFrame（1レース分）からContextを1つ生成
        """
        if race_df.empty:
            return None

        # 最初の1行から基本情報を取得
        base = race_df.iloc[0]
        course = base[RaceCol.COURSE]
        
        # 会場マスターから設定を取得（なければデフォルト値）
        master = ContextFactory.COURSE_MASTER.get(course, {"width": 20, "radius_factor": 1.0, "base_friction": 0.05})

        # 馬場状態による摩擦の微調整ロジック（Normalizerの一部）
        condition_multiplier = {
            "良": 1.0, "稍": 0.98, "重": 0.95, "不良": 0.92
        }.get(base[RaceCol.TRACK_CONDITION], 1.0)

        return RaceContext(
            course_name=course,
            distance=int(base[RaceCol.DISTANCE]),
            track_condition=base[RaceCol.TRACK_CONDITION],
            weather=base[RaceCol.WEATHER],
            track_width=master['width'],
            corner_radius=master['radius_factor'],
            surface_friction=master['base_friction'] * condition_multiplier,
            segment_data=[] # ここに前回計算した大井1600mの分割データなどを入れる
        )


class HorseFactory:
    def __init__(self):
        _CLASSNAME = "HorseFactory"
        # クラス名を名前としてロガーを作成
        self.logger = setup_logger(_CLASSNAME)

        self.logger.info("初期化中...")
        
        self.history_df = None
        self._current_path = None

    def set_history_source(self, csv_path: str):
        """
        必要なタイミングで履歴CSVのパスを指定し、メモリにロードする
        """
        path = Path(csv_path)
        if not path.exists():
            raise FileNotFoundError(f"History file not found: {csv_path}")
        
        # すでに同じファイルがロードされている場合はスキップ（効率化）
        if self._current_path == str(path):
            return

        self.logger.info(f"Loading history data from: {path.name}...")
        self.history_df = pd.read_csv(path)
        self._current_path = str(path)

    def create_horse(self, entry_row: pd.Series) -> Horse:
        """
        現在の履歴データを使用してHorseインスタンスを生成
        """
        self.logger.info("create horse processing...")
        if self.history_df is None:
            raise ValueError("History data is not loaded. Call set_history_source() first.")

        horse_id = entry_row[RaceCol.HORSE_ID]
        name = entry_row[RaceCol.HORSE_NAME]
        
        # 過去データの抽出
        past_performances = self.history_df[self.history_df[RaceCol.HORSE_ID] == horse_id]

        # 能力計算
        params = self._calculate_params(past_performances, entry_row)
        
        return Horse(horse_id=horse_id, name=name, params=params)

    def _calculate_params(self, past_df: pd.DataFrame, entry_row: pd.Series) -> StaticParams:
        # --- ロジックの例 ---
        
        # A. 最高速度の推定 (上がり3Fの平均から算出)
        # 例: 38.0秒なら 600/38 = 15.78 m/s。これに個体差を加味
        self.logger.info("最高速度の推定...")
        if not past_df.empty:
            avg_last_3f = past_df[RaceCol.LAST_3F].mean(numeric_only=True)
            max_v = (600.0 / avg_last_3f) * 1.05  # スパート時は平均より速いと仮定
        else:
            max_v = 15.5  # データがない場合のデフォルト値

        # B. スタミナの推定 (距離実績から算出)
        # 過去に走った最長距離などをベースにスタミナ総量を決める
        stamina = entry_row[RaceCol.DISTANCE] * 1.2 

        # C. パワー (馬場状態適性)
        # 過去、track_conditionが「重・不良」の時の着順が良いなら高めに設定
        self.logger.info("パワー推定...")
        power_val = 1.0
        heavy_cond_df = past_df[past_df[RaceCol.TRACK_CONDITION].isin(['重', '不'])]
        self.logger.info(f"heavy: {heavy_cond_df[RaceCol.RANK]}")
        bad_track_performance = heavy_cond_df[RaceCol.RANK].mean(numeric_only=True)
        if bad_track_performance < 5.0: # 掲示板によく載っているなら
            power_val = 1.1

        return StaticParams(
            max_velocity=max_v,
            base_acceleration=0.8, # 加速度
            stamina_capacity=stamina,
            power=power_val,
            intelligence=1.0,
            grit=1.0
        )
