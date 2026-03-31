"""
simulator.py の概要

1. 会場データの初期化
2. 各馬のエントリー
3. 実行管理：RaceEngine でゴールするまでループを回す
4. ログなどの記録
"""
from utils.logger import setup_logger
from constants.schema import RaceCol
from models.context import RaceContext
from services.provider import RaceDataProvider
from services.factory import ContextFactory, HorseFactory
from core.engine import RaceEngine
from services.saver import ResultSaver

class RaceSimulator:
    def __init__(self):
        _CLASSNAME = "Simulator"
        # クラス名を名前としてロガーを作成
        self.logger = setup_logger(_CLASSNAME)

        self.logger.info("初期化中...")

        self._racing_contexts = []

    def run(self, target_date=None, course_filter=None, race_num_filter=None):
        """
        メインの実行メソッド
        """
        self.logger.info("実行中...")

        self.logger.debug(f"{target_date}\n{course_filter}\n{race_num_filter}")

        # 記録の起動
        saver = ResultSaver()

        # 1. データの取得
        provider = RaceDataProvider(data_dir="data")
        
        # 前述のロジックで [ {RaceCol.COURSE: "大井", RaceCol.ENTRIES: df}, ... ] が返る
        race_data_sets = provider.get_race_data_sets(target_date, course_filter, race_num_filter)

        self.logger.debug(f"race_data_sets: {race_data_sets}")
        
        # 2. 過去データ（履歴）の読み込み (HorseFactory用)
        # 実際にはこれもProvider経由で取得するのが望ましいです
        horse_factory = HorseFactory()
        horse_factory.set_history_source(self._get_horse_source(target_date))

        # 3. レースエントリー毎の処理
        for race_data in race_data_sets:
            entries_df = race_data[RaceCol.ENTRIES]
            
            # 1. コンテキストの作成（レース全体の環境）
            context = ContextFactory.create_from_df(entries_df)

            # 2. 馬たちの作成（個体ごとの能力）
            horses = [horse_factory.create_horse(row) for _, row in entries_df.iterrows()]

            # 馬がいない場合は次のレースへ
            if not horses: continue
                    
            # シミュレーション実行へ...
            self._run_simulation(context, horses, saver)

        self._save_logs(saver, target_date)
        
    def _run_simulation(self, context: RaceContext, horses: list, saver: ResultSaver):
        """
        1回のレースのシミュレーションを行う
        """
        self.logger.info("シミュレーション開始...")
        # エンジン起動
        engine = RaceEngine(context, horses, saver=saver)
        self.logger.info(f"Setup complete for {context.course_name} {context.distance}m")
        engine.run_race()
        
        # 結果の確認
        for h in horses:
            self.logger.info(f"{h.name}: {engine.elapsed_time:.1f}秒 (残スタミナ: {h.state.current_stamina:.1f})")

    def _save_logs(self, saver: ResultSaver, date: str):
        """
        ログ情報の保存
        """
        # 全レース終了後にまとめて保存
        save_file = f"simulation_{date}.csv"
        final_df = saver.save_to_csv(save_file)

    def _entry_horse(self, factory: HorseFactory, row):
        """
        馬インスタンスを作成
        """
        return factory.create_horse(row)

    def _get_horse_source(self, date: str) -> str:
        """馬の過去履歴のファイル"""
        return f"data/horse_history_{date}.csv"
