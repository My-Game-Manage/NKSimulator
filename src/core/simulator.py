"""
simulator.py の概要

レースをシミュレートするための準備（会場データ、馬データ生成）と、Engineを使った実際のシミュレートを行う。
"""
import logging

# ロガーの取得（__name__ はファイル名/モジュール名になる）
logger = logging.getLogger(__name__)

from src.services.provider import RaceDataProvider
from src.services.race_factory import RaceInfoFactory
from src.models.race_info import RaceInfo, RaceProfile, RaceState
from src.core.engine import RaceEngine
from src.services.saver import RaceResultSaver
from src.services.race_analyzer import RaceAnalyer


class RaceSimulator:
    DT = 0.1
    MAX_STEPS = 2000
    def __init__(self):
        logger.info("初期化中...")

        self.engine = RaceEngine()
        self.saver = RaceResultSaver()

        self.race_data_set_list: list[RaceInfo] = []

        # レースごとの結果（History）を格納する辞書
        # key: race_id, value: list[RaceState]
        self.results: dict[str, list[RaceState]] = {}

    def run(self, date: str=None, courses: list[str] | None=None, race_numbers: list[int] | None=None) -> bool:
        """
        メインの実行メソッド
        """
        logger.info("実行中...")

        # 前準備
        self.race_data_set_list = self.prepare_races(date, courses, race_numbers)

        if not self.race_data_set_list:
            logger.warning(f"該当するレースがありません。: {self.race_data_set_list}")
            return False
        
        # 各レースのシミュレーション
        for race_data_set in self.race_data_set_list:
            history = self._run_single_race(race_data_set)
            self.results[race_data_set.race_id] = history
        
        # 事後処理
        self._post_races(date)

        return True
    
    def prepare_races(self, date: str, courses, race_numbers) -> list:
        """レースの準備"""
        # レースのデータセットのリスト作成
        race_info_list = self._create_race_info_list(date, courses, race_numbers)
        # 事前能力値のセーブ
        self._save_prepared_data(date, race_info_list)

        return race_info_list
    
    def _create_race_info_list(self, date: str, courses: list, race_numbers: list) -> list[RaceInfo]:
        """レースに必要な情報セットのリストを返す"""
        # 1. CSVデータ読み込み
        provider = RaceDataProvider(data_dir="data")
        race_raw_data_list = provider.create_race_raw_data_list(date, courses, race_numbers)

        # 2. レース毎にRaceInfoを作成
        factory = RaceInfoFactory()
        race_info_list = []
        for raw_data in race_raw_data_list:
            # Profile作成
            profile = factory.create_race_profile(raw_data)
            # State作成
            state = factory.create_race_state(profile.race_id, profile.horses)
            # リストに追加
            race_info_list.append(RaceInfo(
                race_id=profile.race_id,
                profile=profile,
                state=state,
            ))
        return race_info_list
    
    def _save_prepared_data(self, date: str, race_info_list: list[RaceInfo]):
        """能力値セーブ処理"""
        for race_info in race_info_list:
            profile = race_info.profile
            param_df = self.saver.export_horses_params(profile)
            self.saver.save_prepared_to_csv(date, profile.course_name, profile.distance, profile.surface, param_df)

    def _run_single_race(self, race_data_set: RaceInfo) -> list[RaceState]:
        """1レースのシミュレーションを実行し、全ステップの履歴を返す"""
        logger.info(f"レース開始: {race_data_set.race_id}")

        analyzer = RaceAnalyer()

        # 1. 初期状態（0ステップ目）の生成
        # info 内の各 HorseInfo から初期位置などを設定した RaceState を作る
        current_state = race_data_set.state
        history = [current_state]
        
        dt = self.DT  # 0.1秒きざみ
        max_steps = self.MAX_STEPS # 安全のための最大ステップ数
        
        # 2. 全馬がゴールするまでループ
        for _ in range(max_steps):
            # Engine に 「現在の状態」 と 「レースの固定情報」 を渡して 「次の状態」 を得る
            # Engine自体に状態を持たせない（Stateless）のがコツです
            next_state = self.engine.step(current_state, race_data_set.param, dt)
            
            # 2. Simulatorによる順位の確定（刻印）
            # ここで全馬の距離を比較して正しい rank を入れる
            next_state = analyzer.update_ranks(next_state)

            # 3. 履歴への追加と更新
            history.append(next_state)
            current_state = next_state
            
            # 全頭ゴールしたか判定
            if analyzer.is_all_goal(current_state):
                break
                
        return history
    
    def _post_races(self, date: str):
        """レースの事後処理"""
        for race_data_set in self.race_data_set_list:
            race_info = race_data_set.info
            race_param = race_data_set.param
            history = self.results[race_info.race_id]
            result_df = self.saver.export_results(race_info, history)
            self.saver.save_result_to_csv(date, race_info.course_name, race_param.distance, race_param.surface, result_df)

    def _save_result_as_single_race(self, date: str, race_data_set, history: list):
        """テスト用：1レース分の結果をcsvにセーブする"""
        race_info = race_data_set.info
        race_param = race_data_set.param
        result_df = self.saver.export_results(race_info, history)
        self.saver.save_result_to_csv(date, race_info.course_name, race_param.distance, race_param.surface, result_df)