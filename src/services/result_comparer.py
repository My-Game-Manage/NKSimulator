"""
result_comparer.py の概要

シミュレーション結果と現実の結果を比較する
"""
import pandas as pd
from pathlib import Path

import logging

# ロガーの取得（__name__ はファイル名/モジュール名になる）
logger = logging.getLogger(__name__)


class RaceResultComparer:

    _RESULT_DIR = Path("compared")

    @staticmethod
    def compare_race_results(actual_csv: str, sim_csv: str, output_csv: str, target_race_num: int):
        # 1. データの読み込み
        df_actual = pd.read_csv(actual_csv)
        df_sim = pd.read_csv(sim_csv)

        # 2. ターゲットレースの抽出と型調整
        # actualは race_number, simは race_num とカラム名が異なる点に注意
        actual_sub = df_actual[df_actual['race_number'] == target_race_num].copy()
        sim_sub = df_sim[df_sim['race_num'] == target_race_num].copy()

        actual_sub['horse_id'] = actual_sub['horse_id'].astype(str)
        sim_sub['horse_id'] = sim_sub['horse_id'].astype(str)

        # 3. horse_idをキーに結合 (suffixesで列名の重複を避ける)
        merged = pd.merge(
            actual_sub, 
            sim_sub, 
            on='horse_id', 
            suffixes=('_actual', '_sim')
        )

        # 4. 差異の計算
        # 着順の差 (正の値ならシミュレーションの方が着順が悪い)
        merged['rank_diff'] = merged['rank_sim'] - merged['rank_actual']
    
        # タイムの差 (実際のタイム 'time' は 105.3 のような形式、シミュレーションは 'finish_time')
        merged['time_diff'] = merged['finish_time'] - merged['time']

        # 上りタイム差
        merged['last3f_diff'] = merged['last_3f_sim'] - merged['last_3f_actual']

        # コーナー通過順位（比較）

        # 5. 必要なカラムだけ抽出して保存
        result_columns = [
            'horse_id', 'horse_name', 'strategy',
            'rank_actual', 'rank_sim', 'rank_diff',
            'time', 'finish_time', 'time_diff',
            'last_3f_actual', 'last_3f_sim', 'last3f_diff',
            'passing_order_actual', 'passing_order_sim',
        ]
        comparison_df = merged[result_columns]

        # ファイル名作成
        save_path = RaceResultComparer._RESULT_DIR / output_csv
    
        comparison_df.to_csv(save_path, index=False, encoding='utf-8-sig')
        logger.info(f"比較結果を {output_csv} に保存しました。")