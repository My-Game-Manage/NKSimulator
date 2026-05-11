"""
research_helper.py 概要

検証用のヘルパー関数、クラス群
"""
import os
import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib

import logging
# ロガーの取得（__name__ はファイル名/モジュール名になる）
logger = logging.getLogger(__name__)

from src.services.observer import RaceObserver
from src.constants.enums import RaceEvent, SectionType
from src.constants.fields import RaceProfField, RaceSnapField, HorseProfField, HorseSnapField
from src.models.race_data import RaceInfo, RaceProfile, RaceSnapshot
from src.models.horse_data import HorseProfile, HorseSnapshot
from src.utils.utils import get_save_file_name


class ResearchResultSaver(RaceObserver):
    def __init__(self, result_dir: str = "researchs"):
        super().__init__()
        logger.info("初期化中...")

        self.result_dir = Path(result_dir)

        # ディレクトリがなければ作成する
        os.makedirs(self.result_dir, exist_ok=True)

    def update(self, event_type: RaceEvent, data: dict):
        if event_type is RaceEvent.FINISH:
            # レース終了後に全部の履歴をCSV保存する
            self.save_all_history(data['data'], data['history'])

    def save_all_history(self, race_info: RaceInfo, history: list[RaceSnapshot]):
        """履歴から1レースの仔細データを全てCSVとして保存する"""
        # DataFrameに変換
        df = self.export_result_all(race_info, history)
        # レースからファイル名作成してCSVで保存する
        race_prof = race_info.profile
        file_name = get_save_file_name(race_prof.race_id, race_prof.course, race_prof.distance, race_prof.surface)
        save_path = self.result_dir / file_name
        df.to_csv(f"{save_path}.csv", index=False, encoding="utf-8-sig")
        logger.info(f"{save_path}に結果を保存しました。")

    def export_result_all(self, race_info: RaceInfo, history: list[RaceSnapshot]) -> pd.DataFrame:
        """レース履歴データをDataFrame形式に変換"""
        race_prof = race_info.profile
        summary_data = []
        # 結果Snapshotを取得
        result_snapshot = history[-1]
        # 結果Rankの馬ID順で、全ての履歴を変換
        for h_id, rank in result_snapshot.ranks.items():
            h_prof = race_prof.horses[h_id]
            for race_snap in history:
                h_snap = race_snap.horses[h_id]
                current_rank = race_snap.ranks[h_id]
                summary_data.append({
                    # レース情報
                    RaceProfField.COURSE: race_prof.course,
                    RaceProfField.RACE_NUM: race_prof.race_num,
                    # 馬情報
                    HorseProfField.HORSE_ID: h_prof.horse_id,
                    HorseProfField.BRACKET_NUM: h_prof.bracket_num,
                    HorseProfField.HORSE_NUM: h_prof.horse_num,
                    HorseProfField.NAME: h_prof.name,
                    HorseProfField.STRATEGY: h_prof.strategy,
                    # 道中情報
                    HorseSnapField.STEP: h_snap.step,
                    HorseSnapField.ELAPSED_TIME: round(h_snap.elapsed_time, 2),
                    HorseSnapField.ACCEL: round(h_snap.accel, 2),
                    HorseSnapField.TARGET_VELOCITY: round(h_snap.target_velocity, 2),
                    HorseSnapField.VELOCITY: round(h_snap.velocity, 2),
                    HorseSnapField.DISTANCE: round(h_snap.distance, 2),
                    HorseSnapField.LANE: round(h_snap.lane, 2),
                    HorseSnapField.DIST_TO_FRONT: round(h_snap.dist_to_front, 2),
                    HorseSnapField.SECTION: h_snap.section,
                    HorseSnapField.BEHAVIOR: h_snap.behavior,
                    # 結果情報
                    'rank': current_rank,
                    HorseSnapField.FINISH_TIME: round(h_snap.finish_time, 2) if h_snap.finish_time else 0.0,
                    HorseSnapField.TIME_AT_600M: round(h_snap.time_at_600m, 2) if h_snap.time_at_600m else 0.0,
                    HorseSnapField.STAMINA: round(h_snap.stamina, 2) if h_snap.stamina else 0.0,
                })
        # DataFrameに変換して返す
        return pd.DataFrame(summary_data)


# --- Matplot用の日本語フォントの設定 ---
# 環境に合わせてフォントを選択してください
# Windows: 'MS Gothic', Mac: 'AppleGothic' or 'Hiragino Sans GB', Linux: 'Japan00' など
matplotlib.rcParams['font.family'] = 'MS Gothic' # Windowsの場合の例


class RaceResultPlotter():
    @staticmethod
    def plot_race_analysis(history: list[RaceSnapshot], profile: RaceProfile, target_field: str = "velocity"):
        """
        指定した項目（velocity, stamina, elapsed_time等）を縦軸に表示する

        Args:
            history: RaceSnapshotのリスト
            profile: レースの固定データ
            target_field: HorseSnapshot内の表示したいフィールド名（文字列）
        """
        # 1. 馬ごとのデータ抽出
        horse_data = {}
        for snapshot in history:
            for horse_id, h_state in snapshot.horses.items():
                if horse_id not in horse_data:
                    horse_data[horse_id] = {"distances": [], "values": []}
            
                # 指定されたフィールドの値を動的に取得
                val = getattr(h_state, target_field, None)
            
                horse_data[horse_id]["distances"].append(h_state.distance)
                horse_data[horse_id]["values"].append(val)

        # 2. グラフ描画
        fig, ax = plt.subplots(figsize=(14, 7))

        # --- セクション背景の描画 ---
        for section in profile.sections:
            color = 'lavender' if section.type == SectionType.STRAIGHT else 'honeydew'
            start = section.start_at
            end = start + section.distance
        
            ax.axvspan(start, end, color=color, alpha=0.2)
            ax.axvline(x=start, color='gray', linestyle='--', linewidth=0.8, alpha=0.5)
        
            mid_point = start + (section.distance / 2)
            ax.text(mid_point, ax.get_ylim()[1], section.name.value, 
                    rotation=45, ha='center', va='bottom', fontsize=9)

        # --- 各馬のプロット ---
        ranks = history[-1].ranks
        for horse_id in ranks.keys():
            data = horse_data[horse_id]
            label_name = profile.horses[horse_id].name if horse_id in profile.horses else horse_id
            ax.plot(data["distances"], data["values"], label=label_name, linewidth=1.5)

        # 3. 装飾
        ax.set_title(f"Race Analysis: {target_field.capitalize()} over Distance", fontsize=14)
        ax.set_xlabel("Distance (m)")
        ax.set_ylabel(target_field)
        ax.grid(True, linestyle=':', alpha=0.5)
        ax.legend(bbox_to_anchor=(1.02, 1), loc='upper left')
    
        plt.tight_layout()
        plt.show()

    @staticmethod
    def plot_race_rank_history(history: list[RaceSnapshot], profile: RaceProfile):
        """
        RaceSnapshotのranksデータを使用して、各馬の順位推移をグラフ化する
        """
        # 1. 馬ごとの順位データを抽出
        horse_ranks = {}
        for snapshot in history:
            # snapshot.ranks は {horse_id: rank} の辞書
            for horse_id, rank in snapshot.ranks.items():
                if horse_id not in horse_ranks:
                    horse_ranks[horse_id] = {"distances": [], "ranks": []}
            
                # 各馬の現在の走行距離を取得するために snapshot.horses を参照[cite: 2]
                if horse_id in snapshot.horses:
                    dist = snapshot.horses[horse_id].distance
                    horse_ranks[horse_id]["distances"].append(dist)
                    horse_ranks[horse_id]["ranks"].append(rank)

        # 2. グラフ描画設定
        fig, ax = plt.subplots(figsize=(14, 7))

        # --- セクション背景の描画 ---
        for section in profile.sections:
            color = 'lavender' if section.type == SectionType.STRAIGHT else 'honeydew'
            start = section.start_at
            end = start + section.distance
        
            ax.axvspan(start, end, color=color, alpha=0.2)
            ax.axvline(x=start, color='gray', linestyle='--', linewidth=0.8, alpha=0.5)
        
            mid_point = start + (section.distance / 2)
            ax.text(mid_point, ax.get_ylim()[1], section.name.value, 
                    rotation=45, ha='center', va='bottom', fontsize=9)

        # --- 各馬のプロット ---
        ranks = history[-1].ranks
        for horse_id in ranks.keys():
            data = horse_ranks[horse_id]
            label_name = profile.horses[horse_id].name if horse_id in profile.horses else horse_id
            ax.plot(data["distances"], data["ranks"], label=label_name, linewidth=1.5, marker='o', markersize=2, alpha=0.8)

        # 3. 順位グラフ用の装飾（ここがポイント）
        ax.set_title(f"Rank History: {profile.race_name}", fontsize=14)
        ax.set_xlabel("Distance (m)")
        ax.set_ylabel("Rank")
    
        # 順位なので1位が一番上に来るように軸を反転させる
        ax.set_ylim(profile.num_horses + 0.5, 0.5) 
        # y軸のメモリを整数（1位から頭数分）に固定
        ax.set_yticks(range(1, profile.num_horses + 1))
    
        ax.grid(True, axis='y', linestyle=':', alpha=0.7)
        ax.legend(bbox_to_anchor=(1.02, 1), loc='upper left')
    
        plt.tight_layout()
        plt.show()