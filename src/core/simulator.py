"""
simulator.py の概要

レースをシミュレートするための準備（会場データ、馬データ生成）と、Engineを使った実際のシミュレートを行う。
"""
import logging

# ロガーの取得（__name__ はファイル名/モジュール名になる）
logger = logging.getLogger(__name__)

from src.services.provider import RaceDataProvider
from src.services.race_factory import RaceInfoFactory
from src.models.race_state import RaceState
from src.models.race_info import RaceInfo
from src.core.engine import RaceEngine
from src.services.saver import RaceResultSaver


class RaceSimulator:
    DT = 0.1
    MAX_STEPS = 2000
    def __init__(self):
        logger.info("初期化中...")

        self.engine = RaceEngine()
        self.factory = RaceInfoFactory()
        self.saver = RaceResultSaver()

        self.race_info_list = []
        # レースごとの結果（History）を格納する辞書
        # key: race_id, value: list[RaceState]
        self.results: dict[str, list[RaceState]] = {}

    def run(self, date: str=None, courses: list[str] | None=None, race_numbers: list[int] | None=None) -> bool:
        """
        メインの実行メソッド
        """
        logger.info("実行中...")

        # 前準備
        self.race_info_list = self._prepare_races(date, courses, race_numbers)

        if not self.race_info_list:
            logger.warning(f"該当するレースがありません。: {self.race_info_list}")
            return False
        
        # 各レースのシミュレーション
        for info in self.race_info_list:
            history = self._run_single_race(info)
            self.results[info.race_id] = history
        
        # 事後処理
        self._post_races(date)

        return True
    
    def _prepare_races(self, date: str, courses, race_numbers) -> list:
        """レースの準備"""
        # 1. CSVデータの読み込み
        provider = RaceDataProvider(data_dir="data")
        race_data_sets = provider.get_race_data_sets(date, courses, race_numbers)

        race_info_list = self.factory.get_race_info_list(race_data_sets)

        if race_info_list:
            # 能力値セーブ処理
            for race_info in race_info_list:
                param_df = self.saver.export_horses_params(race_info)
                self.saver.save_prepared_to_csv(date, race_info.course_name, race_info.distance, race_info.surface, param_df)

        return race_info_list

    def _run_single_race(self, info: RaceInfo) -> list[RaceState]:
        """1レースのシミュレーションを実行し、全ステップの履歴を返す"""
        logger.info(f"レース開始: {info.race_id}")
        # 1. 初期状態（0ステップ目）の生成
        # info 内の各 HorseInfo から初期位置などを設定した RaceState を作る
        current_state = self.factory.create_initial_state(info)
        history = [current_state]
        
        dt = self.DT  # 0.1秒きざみ
        max_steps = self.MAX_STEPS # 安全のための最大ステップ数
        
        # 2. 全馬がゴールするまでループ
        for _ in range(max_steps):
            # Engine に 「現在の状態」 と 「レースの固定情報」 を渡して 「次の状態」 を得る
            # Engine自体に状態を持たせない（Stateless）のがコツです
            next_state = self.engine.step(current_state, info, dt)
            
            # 2. Simulatorによる順位の確定（刻印）
            # ここで全馬の距離を比較して正しい rank を入れる
            next_state = next_state.update_ranks()

            # 3. 履歴への追加と更新
            history.append(next_state)
            current_state = next_state
            
            # 全頭ゴールしたか判定
            if current_state.is_all_goal:
                break
                
        return history
    
    def _post_races(self, date: str):
        """レースの事後処理"""
        for race_info in self.race_info_list:
            history = self.results[race_info.race_id]
            result_df = self.saver.export_results(race_info, history)
            self.saver.save_result_to_csv(date, race_info.course_name, race_info.distance, race_info.surface, result_df)