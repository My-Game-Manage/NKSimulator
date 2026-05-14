"""
result_comparer.py の概要

シミュレーション結果と現実の結果を比較する
"""
import pandas as pd
import numpy as np
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
            'course_sim', 'race_num',
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

    @staticmethod
    def calculate_hybrid_score(compared_csv: str) -> dict:
        # CSVからDataFrameに変換
        df = pd.read_csv(RaceResultComparer._RESULT_DIR / compared_csv)

        # 1. 順位相関 (Spearman's rank correlation)
        #   （相関）が低い場合: 馬の「基礎能力（スピード・スタミナの初期値）」の設定、
        #   または脚質による有利不利の計算が壊れています
        # 実際の着順とシミュレーション着順の相関を計算
        correlation = df['rank_actual'].corr(df['rank_sim'], method='spearman')
        # -1~1 を 0~40点に変換
        rank_correlation_score = ((correlation + 1) / 2) * 40

        # 2. 3着以内一致ボーナス
        #   ここだけが高い場合: 偶然の可能性もありますが、能力上位馬のピックアップはできている状態です
        top3_actual = set(df.nsmallest(3, 'rank_actual')['horse_id'])
        top3_sim = set(df.nsmallest(3, 'rank_sim')['horse_id'])
        match_count = len(top3_actual & top3_sim)
        betting_score = match_count * 10 # 最大30点

        # 3. タイム乖離ペナルティ (上位5頭の平均誤差で判定)
        #   （タイム）が低い場合: 物理エンジン（摩擦、スタミナ消費率、中だるみロジックの欠如）に問題があります。
        # 1秒のズレにつき5点減点（6秒ズレると0点）
        top5_time_diff = df.nsmallest(5, 'rank_actual')['time_diff'].abs().mean()
        time_penalty_score = max(0, 30 - (top5_time_diff * 5))

        total_score = rank_correlation_score + betting_score + time_penalty_score

        first_row = df.iloc[0]
    
        return {
            'race_id': Path(compared_csv).stem,
            'course': first_row['course_sim'],
            'race_num': first_row['race_num'],
            'total': round(total_score, 1),
            'rank_corr': round(rank_correlation_score, 1),
            'top3_match': betting_score,
            'time_validity': round(time_penalty_score, 1)
        }
    
    @staticmethod
    def save_compared_score_csv(output_csv: str, scores: list[dict]):
        """スコア結果をCSVで保存する"""
        score_df = pd.DataFrame(scores)

        # ファイル名作成
        save_path = RaceResultComparer._RESULT_DIR / output_csv

        score_df.to_csv(save_path, index=False, encoding='utf-8-sig')
        logger.info(f"比較スコアを {output_csv} に保存しました")
