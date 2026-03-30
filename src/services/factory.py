"""
factory.py の概要

1. ContextFactory　- RaceContextインスタンスの作成
"""

from src.constants.schema import RaceCol
from src.models.context import RaceContext

class ContextFactory:
    # 会場ごとの定数を定義
    COURSE_MASTER = {
        "大井": {"width": 25, "radius_factor": 1.0, "base_friction": 0.05},
        "笠松": {"width": 20, "radius_factor": 1.2, "base_friction": 0.07}, # 笠松は砂が深くコーナーが急
    }

    @staticmethod
    def create_from_df(race_df):
        """
        抽出されたDataFrame（1レース分）からContextを1つ生成
        """
        if race_df.empty:
            return None

        # 最初の1行から基本情報を取得
        base = race_df.iloc[0]
        course = base[RaceCol.COURSE]
        
        # 会場マスターから設定を取得（なければデフォルト値）
        master = ContextFactory.COURSE_MASTER.get(course, {"width": 20, "radius_factor": 1.0, "base_friction": 0.05})

        # 馬場状態による摩擦の微調整ロジック（Normalizerの一部）
        condition_multiplier = {
            "良": 1.0, "稍": 0.98, "重": 0.95, "不良": 0.92
        }.get(base[RaceCol.TRACK_CONDITION], 1.0)

        return RaceContext(
            course_name=course,
            distance=int(base[RaceCol.DISTANCE]),
            track_condition=base[RaceCol.TRACK_CONDITION],
            weather=base[RaceCol.WEATHER],
            track_width=master['width'],
            corner_radius=master['radius_factor'],
            surface_friction=master['base_friction'] * condition_multiplier,
            segment_data=[] # ここに前回計算した大井1600mの分割データなどを入れる
        )
