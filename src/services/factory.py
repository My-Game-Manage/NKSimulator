"""
factory.py の概要

1. ContextFactory　- RaceContextインスタンスの作成
"""
import pandas as pd
from pathlib import Path

from utils.logger import setup_logger
from constants.schema import RaceCol
from constants.config import SimConfig
from constants.strategy import StrategyType, STRATEGY_STAMINA_MAP, STRATEGY_LANE_MAP
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
            ],
            "layout_1200": [
                {"type": "straight", "length": 480}, # スタートから3角まで（非常に長い）
                {"type": "curve",    "length": 334}, # 3-4角（外回りの大きなカーブ）
                {"type": "straight", "length": 386}, # 最後の直線
            ],
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
        distance = entry_row[RaceCol.DISTANCE] # 距離を取得
        
        # 過去データの抽出
        past_performances = self.history_df[self.history_df[RaceCol.HORSE_ID] == horse_id]

        # 前処理
        past_df = self._preprocess(past_performances)

        # 脚質を判定
        strategy = self._determine_strategy(past_df)
        self.logger.debug(f"strategy: {strategy}")

        # 能力計算（distanceを渡すように変更）
        params = self._calculate_params(past_df, entry_row, distance, strategy)
        
        return Horse(
            horse_id=horse_id,
            name=name,
            bracket_num=bracket_num,
            horse_num=horse_num,
            params=params,
            strategy=strategy,
            lane=STRATEGY_LANE_MAP.get(strategy, 0),
        )

    def _calculate_params(self, past_df: pd.DataFrame, entry_row: pd.Series, distance: int, strategy: StrategyType) -> StaticParams:
        """
        馬の基本能力値を算出する
        """
        # 過去の上がり3Fの平均を取得
        avg_last_3f = past_df[RaceCol.LAST_3F].mean(numeric_only=True) if not past_df.empty else SimConfig.DEFAULT_LAST_3F
        
        # 距離に応じた動的係数を取得
        dist_coeff = self._get_distance_velocity_coeff(distance)
        
        # 最終的な max_v の算出
        # SimConfig.MAX_VELOCITY_COEFF (0.98等) に距離補正を掛ける
        final_coeff = SimConfig.MAX_VELOCITY_COEFF * dist_coeff
        max_v = (600.0 / avg_last_3f) * final_coeff

        # --- 脚質によるスタミナ容量の補正 ---
        # 逃げは消費が激しいため実質的な容量を少なめに、後方は温存が得意なため多めに設定
        
        # スタミナ初期値も距離に比例させる（例: 距離 * 1.2）
        # これにより1200mでも1600mでも「同じような枯渇感」を再現しやすくなります
        stamina = self._calc_stamina(entry_row, strategy)

        return StaticParams(
            max_velocity=max_v,
            base_acceleration=SimConfig.DEFAULT_ACCEL, # 加速度
            stamina_capacity=stamina,
            power=self._calc_power(past_df),
            intelligence=1.0,
            grit=1.0,
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

    def _calc_stamina(self, entry_row: pd.Series, strategy: StrategyType) -> float:
        # B. スタミナの推定 (距離実績から算出)
        # 過去に走った最長距離などをベースにスタミナ総量を決める
        base_stamina = entry_row[RaceCol.DISTANCE] * 1.2
        stamina_cap = base_stamina * STRATEGY_STAMINA_MAP.get(strategy, 1.0)
        return stamina_cap

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
        
    def _determine_strategy(self, past_df: pd.DataFrame) -> str:
        """
        過去の通過順位から脚質を判定する
        """
        if past_df.empty:
            return StrategyType.FRONT  # データがない場合は標準的な「先行」をデフォルトに

        ratios = []
        for _, row in past_df.iterrows():
            passing_order = str(row.get(RaceCol.PASSING_ORDER, ""))
            num_horses = row.get(RaceCol.NUM_HORSES, 10)
            
            if not passing_order or passing_order == "nan":
                continue
            
            # "9-9-9-7" -> [9, 9, 9, 7] に分解して最後のコーナー付近の順位を取得
            try:
                ranks = [int(r) for r in passing_order.split("-") if r.isdigit()]
                self.logger.debug(f"strategy: {ranks}")
                if not ranks:
                    continue
                
                # 平均的な位置取りを頭数に対する比率で計算 (1位/10頭 = 0.1)
                avg_rank = sum(ranks) / len(ranks)
                ratios.append(avg_rank / num_horses)
            except ValueError:
                continue

        if not ratios:
            return StrategyType.FRONT

        # 全レースの平均ポジション指数を算出
        mean_ratio = sum(ratios) / len(ratios)

        # 指数に基づいて脚質を割り当て
        if mean_ratio <= 0.2:
            return StrategyType.LEAD    # 逃げ
        elif mean_ratio <= 0.45:
            return StrategyType.FRONT   # 先行
        elif mean_ratio <= 0.75:
            return StrategyType.SUSTAINED # 差し
        else:
            return StrategyType.REAR    # 追込
            
    def _get_distance_velocity_coeff(self, distance: int) -> float:
        """
        距離に応じて max_velocity の計算係数を動的に返す
        基準: 1600m = 1.0 (SimConfig.MAX_VELOCITY_COEFF をそのまま使用)
        """
        # 1600mを基準とし、400m短くなるごとに係数を約0.07(7%)増加させる
        # 1200mの場合: 1.0 + (400 / 400 * 0.07) = 1.07
        # 0.07 -> 0.12 に引き上げ
        # 1200m時に係数が 1.12 になり、よりスプリントらしい速度が出ます
        base_dist = 1600
        diff = (base_dist - distance) / 400
        dist_coeff = 1.0 + (diff * SimConfig.DISTANCE_DYNAMIC_COEFF)
        
        # 急激な変化を防ぐためのガード（0.9 ~ 1.15 の範囲に収める）
        #return max(0.9, min(1.15, dist_coeff))
        return max(0.85, min(1.20, dist_coeff))
