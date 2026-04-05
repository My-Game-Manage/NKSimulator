"""
factory.py の概要

レースと出走馬の情報を取得し、RaceInfoのリストを返す。
"""
import pandas as pd
import numpy as np
import logging

# ロガーの取得（__name__ はファイル名/モジュール名になる）
logger = logging.getLogger(__name__)


from dataclasses import dataclass, replace

from src.constants.schema import RaceCol
from src.models.race_info import RaceInfo
from src.models.horse_info import HorseInfo
from src.models.horse_param import HorseParam
from src.models.strategy import StrategyEnum
from src.constants.race_master import TrackCondition, TrackWeather
from src.constants.course_master import CourseSpec, NAME_TO_COURSE, DEFAULT_COURSE_SPEC_KEY
from src.constants.track_master import TRACK_DATA, DEFAULT_TRACK_DATA_KEY


class RaceInfoFactory:
    _CLASSNAME = "RaceInfoFactory"
    def __init__(self):
        logger.info("初期化中...")

    def get_race_info_list(self, race_data_sets: list[dict]) -> list[RaceInfo]:
        """レース情報のリストを返す"""
        race_info_list = []

        for race_data in race_data_sets:
            entries_df = race_data[RaceCol.ENTRIES]
            histories_df = race_data[RaceCol.HISTORIES]
            race_info = self.create_race_info_from_df(entries_df, histories_df)
            race_info_list.append(race_info)

        return race_info_list
    
    def create_race_info_from_df(self, df: pd.DataFrame, h_df: pd.DataFrame) -> RaceInfo:
        """RaceInfoを作成する"""
        # 1. プロトタイプ（共通部分）の作成
        race_info_proto = self.create_race_info_prototype(df)

        # 2. 出馬表から馬のリスト作成
        horse_list = []
        for _, row in df.iterrows():
            horse_info = self.create_horse_info(row, h_df)
            horse_list.append(horse_info)

        # 3. プロトタイプに統合
        race_info = replace(race_info_proto, horses=horse_list)

        return race_info
    
    def _get_track_name(self, course_name: str, distance: int, surface: str) -> str:
        """コース構成用の名前取得"""
        suffix = "" if surface == "ダ" else "_芝"
        return f"{course_name}_{distance}{suffix}"

    def create_race_info_prototype(self, race_df: pd.DataFrame) -> RaceInfo:
        """馬情報なしのRaceInfoのプロトタイプを作成"""
        # 全馬共通のため最初の1行を参照
        first_row = race_df.iloc[0]

        # セクション取得
        course_name = first_row[RaceCol.COURSE]
        distance = first_row[RaceCol.DISTANCE]
        surface = first_row[RaceCol.SURFACE]
        sections = TRACK_DATA.get(f"{self._get_track_name(course_name, distance, surface)}", DEFAULT_TRACK_DATA_KEY)

        # マスタからCourseSpec取得
        course_spec = NAME_TO_COURSE.get(course_name, DEFAULT_COURSE_SPEC_KEY)

        return RaceInfo(
            course_name=course_name,
            race_name=first_row[RaceCol.RACE_NAME],
            race_num=first_row[RaceCol.RACE_NUMBER],
            distance=distance,
            surface=surface,
            condition=TrackCondition.from_str(first_row[RaceCol.TRACK_CONDITION]),
            weather=TrackWeather.from_str(first_row[RaceCol.WEATHER]),
            track_width=course_spec.track_width,
            corner_penalty=course_spec.corner_penalty,
            surface_friction=course_spec.surface_friction,
            sections=sections,
            horses=[],
        )
    
    def create_horse_info(self, row: pd.Series, df: pd.DataFrame) -> HorseInfo:
        """HorseInfoを作成する"""
        distance = row[RaceCol.DISTANCE]
        # historyは自分のものだけ持たせる
        horse_id = row[RaceCol.HORSE_ID]
        horse_history_df = df[df[RaceCol.HORSE_ID] == horse_id]

        return HorseInfo(
            horse_id=row[RaceCol.HORSE_ID],
            name=row[RaceCol.HORSE_NAME],
            bracket_num=row[RaceCol.BRACKET_NUM],
            horse_num=row[RaceCol.HORSE_NUM],
            past_records=horse_history_df,
            param=self.create_horse_param(distance, df)
        )
    
    def create_horse_param(self, distance: int, df: pd.DataFrame) -> HorseParam:
        """HorseParamを算出して作成"""
        strategy = StrategyEnum.PUSHING #self._determine_strategy(df)
        total_stamina, stamina_waste_rate = self._calculate_stamina_params(df, distance)

        return HorseParam(
            max_speed=self._calculate_max_speed(df),
            acceleration=self._calculate_acceleration(df),
            total_stamina=total_stamina,
            stamina_waste_rate=stamina_waste_rate,
            cornering_ability=self._calculate_cornering_ability(df),
            gate_reaction=self._calculate_gate_reaction(df),
            strategy=strategy,
            target_spurt_dist=self._calculate_spurt_dist(df, strategy),
        )

    def get_horse_history_by_id(self, df: pd.DataFrame, horse_id: str) -> pd.DataFrame:
        """
        指定された馬IDの過去レース記録のみを抽出して返す。
    
        Args:
            df (pd.DataFrame): 過去データの全レコードが入ったDataFrame
            horse_id (str): 抽出したい馬のID (例: '2020106948')
        Returns:
            pd.DataFrame: 該当する馬のレコードのみを含むDataFrame
        """
        # ID列が数値型か文字列型か不明な場合を考慮し、文字列に変換して比較
        # アップロードされたCSVの列名に合わせて 'horse_id' を指定
        target_df = df[df[RaceCol.HORSE_ID].astype(str) == str(horse_id)].copy()
    
        if target_df.empty:
            logger.warning(f"警告: ID {horse_id} に該当するデータは見つかりませんでした。")
        else:
            # 時系列順に並べ替えておくとシミュレーションの分析に便利
            # 'date' 列がある場合はソート（必要に応じて有効化してください）
            # target_df = target_df.sort_values('date')
            pass
        
        return target_df
    
    def _calculate_max_speed(self, past_records: pd.DataFrame) -> float:
        # 1. 走破タイム(s)を算出 (タイムが '107.6' などの形式の場合)
        # 2. 全レースの時速(m/s)を計算
        speeds = past_records[RaceCol.DISTANCE] / past_records[RaceCol.TIME]
    
        # 3. 上位3件の平均をとる（1回きりのラッキーパンチを防ぐため）
        top_3_avg = speeds.nlargest(3).mean()
    
        # 大井の平均的なC3クラスなら 15.0 ~ 16.5 m/s 程度に収束するはずです
        return top_3_avg

    def _calculate_acceleration(self, past_records: pd.DataFrame) -> float:
        # 上がり3F (last_3f) が速いほど高い値を返す
        # 例：平均的な上がりタイムより1秒速ければ +0.1 m/s^2
        avg_last_3f = past_records[RaceCol.LAST_3F].mean()
    
        # 標準的な加速力を 1.0 とした相対評価
        accel_factor = 1.0 + (39.0 - avg_last_3f) * 0.05 
        return max(0.5, accel_factor)

    def _calculate_stamina_params(self, past_records: pd.DataFrame, current_race_dist: float) -> tuple:
        # 1. 過去の最長距離をベースにする
        max_dist_history = past_records[RaceCol.DISTANCE].max()
        avg_weight = past_records[RaceCol.HORSE_WEIGHT].mean()
    
        # 総スタミナ: 距離適性が高いほど余裕が出るように算出
        total_stamina = max_dist_history * 1.2 + (avg_weight * 0.5)
    
        # 2. 燃費: 過去の上がり3F(last_3f)と走破タイムのバランスを見る
        # 終盤にバテている（上がりタイムが極端に遅い）馬は燃費を悪く設定
        stamina_efficiency = self._estimate_efficiency(past_records)
    
        return total_stamina, stamina_efficiency
    
    def _calculate_gate_reaction(self, past_records: pd.DataFrame) -> float:
        # 各レースの最初の通過順位を取り出す
        # 例: "5-4-3-2" -> 5
        valid_records = past_records.dropna(subset=RaceCol.PASSING_ORDER)
        first_pos = valid_records[RaceCol.PASSING_ORDER].str.split('-').str[0].astype(float)
        # 頭数に対する比率にする（14頭立ての5位と、8頭立ての5位は意味が違うため）
        pos_ratio = first_pos / past_records[RaceCol.NUM_HORSES]

        # 比率が小さい（＝前の方にいる）ほど高い値を返す
        # 標準を1.0とし、逃げ・先行馬なら1.2〜、出遅れがちな馬なら0.8〜
        return 1.2 - pos_ratio.mean()
    
    def _calculate_cornering_ability(self, past_records: pd.DataFrame) -> float:
        # 3角と4角の順位差の平均を見る
        # "2-2-3-4" のような馬はコーナーで置かれている（適性低め）
        # "8-7-5-3" のような馬はコーナーで加速している（適性高め）
        diffs = []
        valid_records = past_records.dropna(subset=RaceCol.PASSING_ORDER)
        for order in valid_records[RaceCol.PASSING_ORDER]:
            pts = order.split('-')
            if len(pts) >= 3:
                # 後半2つのセクションの差分（例: 4角順位 - 3角順位）
                diffs.append(int(pts[-2]) - int(pts[-1])) 

        # 順位が上がっている（差が正）ほど高評価
        ability = 0.5 + (sum(diffs) / len(diffs) if diffs else 0) * 0.1
        return max(0.2, min(1.0, ability))

    def _determine_strategy(self, past_records: pd.DataFrame) -> StrategyEnum:
        # 最初のコーナー順位の平均比率を算出
        first_pos_ratios = []
        # TODO: cleaning df
        for _, row in past_records.iterrows():
            first_pos = int(row[RaceCol.PASSING_ORDER].split('-')[0])
            first_pos_ratios.append(first_pos / row[RaceCol.NUM_HORSES])

        avg_ratio = sum(first_pos_ratios) / len(first_pos_ratios)

        # 比率による判定しきい値
        if avg_ratio <= 0.15: return StrategyEnum.ESCAPE   # 逃げ (最前列)
        if avg_ratio <= 0.40: return StrategyEnum.LEADING  # 先行 (前め)
        if avg_ratio <= 0.70: return StrategyEnum.BETWEEN  # 差し (中団)
        return StrategyEnum.PUSHING                         # 追込 (後方)
    
    def _calculate_spurt_dist(self, past_records: pd.DataFrame, strategy: StrategyEnum) -> float:
        # 基本値は 600m (上がり3F)
        base_dist = 600.0

        # 脚質による調整
        # 逃げ・先行は早めに踏ん張る必要があるため長めにする傾向
        if strategy == StrategyEnum.ESCAPE: base_dist += 100.0

        # 過去の「マクリ」傾向（コーナーでの順位押し上げ）があれば加算
        # （前の回答の cornering_ability と連動させると効果的）

        return base_dist
    
    def _estimate_efficiency(self, past_records: pd.DataFrame) -> float:
        """
        過去データからスタミナ消費効率（燃費）を推定する。
        1.0 を標準とし、値が小さいほど燃費が良い（スタミナが減りにくい）と定義する。
        """
        # 1. 「上がり」の失速度合いをチェック
        # 全体の平均時速に対して、最後の600m(上がり3F)でどれだけ失速しているか
        avg_speed = (past_records[RaceCol.DISTANCE] / past_records[RaceCol.TIME]).mean()
        last_3f_speed = (600.0 / past_records[RaceCol.LAST_3F]).mean()
    
        # 失速率 (値が大きいほど、最後の方でバテている)
        # 通常、ダートでは最後は少し遅くなるので 1.05 くらいが標準
        decline_ratio = avg_speed / last_3f_speed
    
        # 2. 人気と着順の相関（精神的なムラ・掛かり癖の推測）
        # 人気より着順が大幅に悪いレースが多い馬は、道中で体力をロスしていると見なす
        # 数値に変換し、変換できなかった（NaNになった）行を削除
        valid_data = (pd.to_numeric(past_records[RaceCol.RANK], errors='coerce') - 
              pd.to_numeric(past_records[RaceCol.POPULARITY], errors='coerce')).dropna()
        pop_rank_diff = valid_data.mean()

        # 3. 燃費係数の計算
        # ベースを 1.0 とし、失速しやすさとムラを加味
        efficiency = 1.0
    
        # 最後までバテない馬（decline_ratioが低い）は燃費を良くする
        efficiency += (decline_ratio - 1.05) * 0.5
    
        # 人気裏切りが多い馬は、道中の「掛かり」を想定して燃費を悪くする
        if pop_rank_diff > 2.0:
            efficiency += 0.05
        
        # 0.8 (超省エネ) 〜 1.2 (ガス欠しやすい) の範囲に収める
        return max(0.8, min(1.2, efficiency))