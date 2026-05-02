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
                    HorseSnapField.VELOCITY: round(h_snap.velocity, 2),
                    HorseSnapField.DISTANCE: round(h_snap.distance, 2),
                    HorseSnapField.LANE: round(h_snap.lane, 2),
                    HorseSnapField.BEHAVIOR: h_snap.behavior,
                    # 結果情報
                    'rank': current_rank,
                    HorseSnapField.FINISH_TIME: round(h_snap.finish_time, 2) if h_snap.finish_time else 0.0,
                    HorseSnapField.STAMINA: round(h_snap.stamina, 2) if h_snap.stamina else 0.0,
                })
        # DataFrameに変換して返す
        return pd.DataFrame(summary_data)


# --- Matplot用の日本語フォントの設定 ---
# 環境に合わせてフォントを選択してください
# Windows: 'MS Gothic', Mac: 'AppleGothic' or 'Hiragino Sans GB', Linux: 'Japan00' など
matplotlib.rcParams['font.family'] = 'MS Gothic' # Windowsの場合の例


class RaceResultPlotter():
    def __init__(self, race_profile: RaceProfile, history: list[RaceSnapshot]):
        self.race_prof = race_profile
        self.history = history

    def plot_race_distance(self):
        # 1. 履歴リストを、Pandasが扱いやすい「辞書のリスト」に変換
        data_log = []
        for snapshot in self.history:
            # 各ステップのデータを抽出
            # ここで「距離」を選択
            row = {h_id: h_s.distance for h_id, h_s in snapshot.horses.items()}
            row[RaceSnapField.STEP] = snapshot.step
            data_log.append(row)

        # 2. DataFrameを作成し、stepをインデックス（横軸）にする
        df = pd.DataFrame(data_log).set_index(RaceSnapField.STEP)

        title = "Distance"
        elm_title = "Distance (m)"

        # 3. グラフの描画
        self.show_plot(title, elm_title, df)

    def plot_race_velocity(self):
        # 1. 履歴リストを、Pandasが扱いやすい「辞書のリスト」に変換
        data_log = []
        for snapshot in self.history:
            # 各ステップのデータを抽出
            # ここで「距離」を選択
            row = {h_id: h_s.velocity for h_id, h_s in snapshot.horses.items()}
            row[RaceSnapField.STEP] = snapshot.step
            data_log.append(row)

        # 2. DataFrameを作成し、stepをインデックス（横軸）にする
        df = pd.DataFrame(data_log).set_index(RaceSnapField.STEP)

        title = "Velocity"
        elm_title = "Velocity (m/s)"

        # 3. グラフの描画
        self.show_plot(title, elm_title, df)

    def plot_race_stamina(self):
        # 1. 履歴リストを、Pandasが扱いやすい「辞書のリスト」に変換
        data_log = []
        for snapshot in self.history:
            # 各ステップのデータを抽出
            # ここで「距離」を選択
            row = {h_id: h_s.stamina for h_id, h_s in snapshot.horses.items()}
            row[RaceSnapField.STEP] = snapshot.step
            data_log.append(row)

        # 2. DataFrameを作成し、stepをインデックス（横軸）にする
        df = pd.DataFrame(data_log).set_index(RaceSnapField.STEP)

        title = "Stamina"
        elm_title = "Stamina (hp)"

        # 3. グラフの描画
        self.show_plot(title, elm_title, df)

    def plot_race_lane(self):
        # 1. 履歴リストを、Pandasが扱いやすい「辞書のリスト」に変換
        data_log = []
        for snapshot in self.history:
            # 各ステップのデータを抽出
            # ここで「距離」を選択
            row = {h_id: h_s.lane for h_id, h_s in snapshot.horses.items()}
            row[RaceSnapField.STEP] = snapshot.step
            data_log.append(row)

        # 2. DataFrameを作成し、stepをインデックス（横軸）にする
        df = pd.DataFrame(data_log).set_index(RaceSnapField.STEP)

        title = "Lane"
        elm_title = "Lane (m)"

        # 3. グラフの描画
        self.show_plot(title, elm_title, df)

    def show_plot(self, title: str, elem_title: str, df: pd.DataFrame):
        """グラフを描画する"""
        # 馬名辞書取得
        horse_names = self.get_horse_names()

        # グラフ描写
        plt.figure(figsize=(15, 8))
        ranks = self.history[-1].ranks
        for horse_id in ranks.keys():
            plt.plot(df.index, df[horse_id], label=f"H: {horse_names[horse_id]}")
        
        plt.title(f"Race Progress ({title})")
        plt.xlabel("Time Step (dt=0.1)")
        plt.ylabel(f"{elem_title}")
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left') # 凡例を外側に
        plt.show()
    
    def get_horse_names(self) -> dict:
        return {h_id: h_prof.name for h_id, h_prof in self.race_prof.horses.items()}

    def plot_race_analysis(self, history: list[RaceSnapshot], profile: RaceProfile, target_field: str = "velocity"):
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