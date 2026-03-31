"""
simulator.py の概要

1. 会場データの初期化
2. 各馬のエントリー
3. 実行管理：RaceEngine でゴールするまでループを回す
4. ログなどの記録
"""
from utils.logger import setup_logger
from constants.schema import RaceCol
from services.provider import RaceDataProvider
from services.factory import ContextFactory, HorseFactory

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
        for race_data in race_sets:
            entries_df = race_data[RaceCol.ENTRIES]
            
            horses = []
            for _, row in entries_df.iterrows():
                # インスタンス化済みのfactoryから馬を生成
                horse = self._entry_horse(horse_factory, row)
                horses.append(horse)
                self.logger.info(f"appended horse: {horse}")
            
            # 馬がいない場合は次のレースへ
            if not horses: continue
            
            # シミュレーション実行へ...

        self._save_logs()
        
    def _runn_simulation(self, race_context):
        """
        1回のレースのシミュレーションを行う
        """
        pass

    def _save_logs(self):
        """
        ログ情報の保存
        """
        pass

    def _entry_horses(self, factory, row):
        """
        馬インスタンスを作成
        """
        return factory.create_horse(row)

    def _get_horse_source(self, date: str) -> str:
        """馬の過去履歴のファイル"""
        return f"data/horse_history_{date}.csv"
