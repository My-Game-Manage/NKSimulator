"""
factory.py の概要
- 出走馬の初期設定を行う
"""

class HorseFactory:
    def __init__(self, history_df):
        """
        過去走CSV(horse_history)を読み込み、
        馬ごとの能力分析（AbilityAnalyzerの役割）を事前に行っておく
        """
        self.history_df = history_df
        self.ability_dict = self._analyze_all_abilities()

    def _analyze_all_abilities(self):
        """
        全馬の過去データから、スピード・スタミナ等の静的パラメータを算出し
        {horse_id: StaticParams} の辞書を作る
        """
        # ここで前回議論した「5角形チャート」の算出ロジックを回す
        abilities = {}
        # 例: for horse_id in self.history_df['馬ID'].unique(): ...
        return abilities

    def create_horse(self, race_row):
        """
        DataProviderから渡された「今日の1行」を元にHorseを生成する
        race_row: {'horse_id': '2023...', 'weight_carried': 56.0, 'horse_number': 1, ...}
        """
        horse_id = race_row['horse_id']
        
        # 1. 過去データからベース能力（静的パラメータ）を取得
        # 過去データがない新馬などの場合はデフォルト値を設定するロジックが必要
        base_ability = self.ability_dict.get(horse_id, self._get_default_ability())
        
        # 2. 今日の条件（斤量、枠番など）による微調整
        # 例：斤量が重ければスタミナ消費係数を増やすなど
        adjusted_params = self._apply_today_bias(base_ability, race_row)
        
        # 3. Horseインスタンスの組み立て
        return Horse(
            name=race_row['horse_name'],
            gate_number=race_row['horse_number'],
            static_params=adjusted_params
        )

    def _apply_today_bias(self, ability, race_row):
        """今日特有の変数（斤量・馬体重・枠番）を能力値に反映させる"""
        # ロジック実装（空でOK）
        return ability

    def _get_default_ability(self):
        """過去データがない馬（初出走など）向けの平均的な能力値を返す"""
        pass
