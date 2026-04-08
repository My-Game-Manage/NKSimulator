"""
simulator.py の概要

レースをシミュレートするための準備（会場データ、馬データ生成）と、Engineを使った実際のシミュレートを行う。
"""
import logging

# ロガーの取得（__name__ はファイル名/モジュール名になる）
logger = logging.getLogger(__name__)

from src.services.provider import RaceDataProvider
from src.services.race_factory import RaceInfoFactory
from src.services.horse_factory import HorseFactory
from src.models.race_info import RaceInfo, RaceParam, RaceState, RaceDataSet
from src.models.horse_info import HorseInfo, HorseParam, HorseState
from src.core.engine import RaceEngine
from src.services.saver import RaceResultSaver


class RaceSimulator:
    DT = 0.1
    MAX_STEPS = 2000
    def __init__(self):
        logger.info("初期化中...")

        self.engine = RaceEngine()
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
        # 1. CSVデータの読み込み -> [RaceRawData...]
        provider = RaceDataProvider(data_dir="data")
        race_raw_data_list = provider.create_race_raw_data_list(date, courses, race_numbers)

        # 2. レース毎にRaceInfo等の基本データを作成
        factory = RaceInfoFactory()
        race_data_set_list = []
        for raw_data in race_raw_data_list:
            # Info作成
            race_info = factory.create_race_info_with_horse_infos(raw_data)
            # Param作成
            race_param = factory.create_race_param_with_horse_params(raw_data)
            # State作成
            racec_state = factory.create_race_state_with_horse_states(
                raw_data.race_id, race_info.horses, race_param.horses,
                )
            race_data_set_list.append(RaceDataSet(
                race_id=race_info.race_id,
                info=race_info,
                param=race_param,
                state=racec_state,
            ))

        if race_data_set_list:
            # 能力値セーブ処理
            for race_data_set in race_data_set_list:
                race_info = race_data_set.info
                race_param = race_data_set.param
                param_df = self.saver.export_horses_params(race_data_set.info, race_data_set.param.horses)
                self.saver.save_prepared_to_csv(date, race_info.course_name, race_param.distance, race_param.surface, param_df)

        return race_data_set_list

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