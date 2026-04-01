"""
strategy.py の概要

1. 脚質タイプの定義
2. 脚質ごとのパラメータ補正設定
"""

class StrategyType:
    LEAD = "Lead"           # 逃げ
    FRONT = "Front"         # 先行
    SUSTAINED = "Sustained" # 差し
    REAR = "Rear"           # 追込

class StrategyConfig:
    # 各脚質ごとの物理パラメータ補正
    PARAMS = {
        StrategyType.LEAD: {
            "cruising_coeff": 1.05,  # 前半から飛ばす
            "spurt_dist": 600.0,     # 早めにスパート
        },
        StrategyType.FRONT: {
            "cruising_coeff": 1.00,  # 標準的
            "spurt_dist": 600.0,
        },
        StrategyType.SUSTAINED: {
            "cruising_coeff": 0.96,  # 道中温存
            "spurt_dist": 500.0,     # 直線手前から
        },
        StrategyType.REAR: {
            "cruising_coeff": 0.92,  # かなり温存
            "spurt_dist": 400.0,     # 直線勝負
        }
    }

    @classmethod
    def get(cls, strategy: str):
        return cls.PARAMS.get(strategy, cls.PARAMS[StrategyType.FRONT])
