"""
factory.py の概要

1. ContextFactory　- RaceContextインスタンスの作成
"""
import pandas as pd
from pathlib import Path

from utils.logger import setup_logger
from constants.schema import RaceCol
from constants.config import SimConfig
from models.context import RaceContext
from models.horse import Horse
from models.params import StaticParams

class ContextFactory:
    # 会場ごとの物理定数マスタ
    COURSE_MASTER = {
        "大井": {
            "base_friction": 0.05,
            "track_width": 25,
            "corner_penalty": 0.15,
            # 前述した大井1600mの構成例（距離に応じて動的に変えるのが理想）
            "layout_1600": [
                {"type": "straight", "length": 300}, # スタート
                {"type": "curve",    "length": 250}, # 1-2角
                {"type": "straight", "length": 350}, # 向こう正面
                {"type": "curve",    "length": 414}, # 3-4角
                {"type": "straight", "length": 286}, # 直線
            ]
        },
        "笠松": {
            "base_friction": 0.07, # 砂が深い想定
            "track_width": 20,
            "corner_penalty": 0.20, # コーナーが急な想定
            "layout_1400": [...] 
        }
    }

    @staticmethod
    def create_from_df(race_df) -> RaceContext:
        # 全馬共通の情報なので、最初の1行を参照
        first_row = race_df.iloc[0]
        course = first_row[RaceCol.COURSE]
        race_num = first_row[RaceCol.RACE_NUMBER]
        condition = first_row[RaceCol.TRACK_CONDITION]
        dist = int(first_row[RaceCol.DISTANCE])
        surface = first_row[RaceCol.SURFACE]
        weather = first_row[RaceCol.WEATHER]

        # マスタから基本設定を取得
        master = ContextFactory.COURSE_MASTER.get(course, {
            "track_width": 25, "base_friction": 0.05, "corner_penalty": SimConfig.CORNER_PENALTY_BASE, "layout_1600": []
        })

        # --- 馬場状態による摩擦の補正 (Normalizing) ---
        # 重馬場なら摩擦係数を上げるなどの処理
        condition_map = {"良": 1.0, "稍": 1.05, "重": 1.15, "不": 1.25}
        friction = master["base_friction"] * condition_map.get(condition, 1.0)

        return RaceContext(
            course_name=course,
            race_number=race_num,
            distance=dist,
            surface=surface,
            track_condition=condition,
            track_width=master['track_width'],
            weather=weather,
            surface_friction=friction,
            corner_penalty=master["corner_penalty"],
            segments=master.get(f"layout_{dist}", []) # 距離に応じたレイアウトを取得
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
        bracket_num =  entry_row[RaceCol.BRACKET_NUM]
        horse_num =  entry_row[RaceCol.HORSE_NUM]
        
        # 過去データの抽出
        past_performances = self.history_df[self.history_df[RaceCol.HORSE_ID] == horse_id]

        # 前処理
        past_df = self._preprocess(past_performances)

        # 能力計算
        params = self._calculate_params(past_df, entry_row)
        
        return Horse(horse_id=horse_id, name=name, bracket_num=bracket_num, horse_num=hores_num, params=params)

    def _calculate_params(self, past_df: pd.DataFrame, entry_row: pd.Series) -> StaticParams:
        # --- ロジックの例 ---
        # TODO：加速度
        # TODO：知能
        # TODO：根性
        return StaticParams(
            max_velocity=self._calc_max_speed(past_df),
            base_acceleration=SimConfig.DEFAULT_ACCEL, # 加速度
            stamina_capacity=self._calc_stamina(entry_row),
            power=self._calc_power(past_df),
            intelligence=1.0,
            grit=1.0
        )

    def _calc_max_speed(self, df: pd.DataFrame) -> float:
        # A. 最高速度の推定 (上がり3Fの平均から算出)
        # 例: 38.0秒なら 600/38 = 15.78 m/s。これに個体差を加味
        self.logger.debug("最高速度の推定...")
        if not df.empty:
            avg_last_3f = df[RaceCol.LAST_3F].mean(numeric_only=True)
            max_v = (SimConfig.SPURT_DISTANCE / avg_last_3f) * SimConfig.MAX_VELOCITY_COEFF  # スパート時は平均より速いと仮定
        else:
            max_v = SimConfig.DEFAULT_MAX_VELOCITY  # データがない場合のデフォルト値
        return max_v

    def _calc_stamina(self, entry_row: pd.Series) -> float:
        # B. スタミナの推定 (距離実績から算出)
        # 過去に走った最長距離などをベースにスタミナ総量を決める
        stamina = entry_row[RaceCol.DISTANCE] * 1.2
        return stamina

    def _calc_power(self, past_df: pd.DataFrame) -> float:
        # C. パワー (馬場状態適性)
        # 過去、track_conditionが「重・不良」の時の着順が良いなら高めに設定
        self.logger.debug("パワー推定...")
        power_val = 1.0
        # 完走した（着順が1以上の）レースだけを抽出して計算
        heavy_cond_df = past_df[past_df[RaceCol.TRACK_CONDITION].isin(['重', '不'])]
        finished_races = heavy_cond_df[heavy_cond_df[RaceCol.RANK] > 0]
        bad_track_performance = finished_races[RaceCol.RANK].mean(numeric_only=True)
        if bad_track_performance < 5.0: # 掲示板によく載っているなら
            power_val = 1.1
        return power_val

    def _preprocess(self, df: pd.DataFrame) -> pd.DataFrame:
        # 'rank' カラムの「取」「中」などを強制的に NaN に変換
        df[RaceCol.RANK] = pd.to_numeric(df[RaceCol.RANK], errors='coerce')
        return df
