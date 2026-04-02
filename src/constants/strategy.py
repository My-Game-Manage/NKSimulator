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

STRATEGY_LANE_MAP = {
    StrategyType.LEAD: 0,
    StrategyType.FRONT: 1,
    StrategyType.SUSTAINED: 3,
    StrategyType.REAR: 5
}

class StrategyConfig:
# 各脚質ごとの物理パラメータ補正
    PARAMS = {
        StrategyType.LEAD: {
            "cruising_coeff": 1.04,  # 少し抑えて道中のスタミナ温存
            "spurt_dist": 350.0,     # 直線に入ってから一気にスパート
            "exhaust_speed_coeff": 0.90, # バテても粘る（根性）
        },
        StrategyType.FRONT: {
            "cruising_coeff": 1.00,
            "spurt_dist": 400.0,     # 逃げよりは早いが、600mよりは遅らせる
            "exhaust_speed_coeff": 0.88, # 逃げの次に粘る
        },
        StrategyType.SUSTAINED: {
            "cruising_coeff": 0.95,  # 道中はゆったり脚を溜める
            "spurt_dist": 550.0,     # 3-4角の中間付近から進出開始
            "exhaust_speed_coeff": 0.80, # バテると一気に止まる
        },
        StrategyType.REAR: {
            "cruising_coeff": 0.92,
            "spurt_dist": 600.0,     # 最も早くスパートを開始してまくる
            "exhaust_speed_coeff": 0.75, # 最後に賭ける分、切れたら終わり
        }
    }
    @classmethod
    def get(cls, strategy: str):
        return cls.PARAMS.get(strategy, cls.PARAMS[StrategyType.FRONT])
