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

STRATEGY_STAMINA_MAP = {
    StrategyType.LEAD: 0.92,      # 逃げ：ハイペース耐性が低い想定
    StrategyType.FRONT: 0.98,     # 先行：標準よりやや低め
    StrategyType.SUSTAINED: 1.05,  # 差し：スタミナ温存が得意
    StrategyType.REAR: 1.12        # 追込：直線にかけるため最大まで温存
}

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
