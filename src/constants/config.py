"""
config.py の概要

シミュレーションに使われる定数を設定する
"""

class SimConfig:
    # --- タイムステップ ---
    DT = 0.1

    # --- HorseFactory用係数 ---
    # 過去の上がり平均(600/avg_3f)に対する最高速度の倍率
    # 1.05から0.98に調整予定
    MAX_VELOCITY_COEFF = 0.98
    DEFAULT_MAX_VELOCITY = 15.5

    # --- RaceEngine用物理パラメータ ---
    DEFAULT_ACCEL = 0.8
    CORNER_PENALTY_BASE = 0.1
    # 道中の速度係数（0.9 -> 1.02 に引き上げ：道中を現実のペースに合わせる）
    CRUISING_SPEED_COEFF = 1.02
    
    # --- 戦略・スパート関連 ---
    # スパート時のブースト（1.5 -> 0.2 に大幅抑制：上がりを40秒に近づける）
    SPURT_SPEED_BOOST = 0.2
    CRUISING_SPEED_COEFF = 0.95  # 道中の速度抑制（巡航速度）
    
    # --- スタミナ関連 ---
    # スタミナ消費（0.008 -> 0.012 に引き上げ：終盤に足を鈍らせる）
    STAMINA_LOSS_COEFF = 0.048
    EXHAUST_SPEED_COEFF = 0.8  # スタミナ切れ時の速度倍率
    CONSUMPTION_RATE = 2.2

    # --- その他 ---
    SPURT_DISTANCE = 600.0    # 残り何mでスパートするか
    SURFACE_FRICTION_BASE = 0.05
