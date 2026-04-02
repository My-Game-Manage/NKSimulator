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

class StrategyParamKey:
    """辞書のキーとして使用する定数群"""
    CRUISING_COEFF = "cruising_coeff"
    SPURT_DIST = "spurt_dist"
    EXHAUST_SPEED_COEFF = "exhaust_speed_coeff"

STRATEGY_STAMINA_MAP = {
    StrategyType.LEAD: 0.92,      # 逃げ：ハイペース耐性が低い想定
    StrategyType.FRONT: 0.98,     # 先行：標準よりやや低め
    StrategyType.SUSTAINED: 1.05,  # 差し：スタミナ温存が得意
    StrategyType.REAR: 1.12        # 追込：直線にかけるため最大まで温存
}

STRATEGY_LANE_MAP = {
    StrategyType.LEAD: 0,
    StrategyType.FRONT: 1,
    StrategyType.SUSTAINED: 3,
    StrategyType.REAR: 5
}

class StrategyConfig:
    # 各脚質ごとの物理パラメータ補正
    # Keyには定義した定数を使用し、数値は直接指定する構成
    PARAMS = {
        StrategyType.LEAD: {
            StrategyParamKey.CRUISING_COEFF: 1.04,
            StrategyParamKey.SPURT_DIST: 350.0,
            StrategyParamKey.EXHAUST_SPEED_COEFF: 0.90,
        },
        StrategyType.FRONT: {
            StrategyParamKey.CRUISING_COEFF: 1.00,
            StrategyParamKey.SPURT_DIST: 400.0,
            StrategyParamKey.EXHAUST_SPEED_COEFF: 0.88,
        },
        StrategyType.SUSTAINED: {
            StrategyParamKey.CRUISING_COEFF: 0.95,
            StrategyParamKey.SPURT_DIST: 550.0,
            StrategyParamKey.EXHAUST_SPEED_COEFF: 0.80,
        },
        StrategyType.REAR: {
            StrategyParamKey.CRUISING_COEFF: 0.92,
            StrategyParamKey.SPURT_DIST: 600.0,
            StrategyParamKey.EXHAUST_SPEED_COEFF: 0.75,
        }
    }

    @classmethod
    def get(cls, strategy_type: str) -> dict:
        """指定された脚質のパラメータを返す。存在しない場合は先行(FRONT)を返す。"""
        return cls.PARAMS.get(strategy_type, cls.PARAMS[StrategyType.FRONT])
