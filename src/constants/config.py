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

    # --- RaceEngine用物理パラメータ ---
    DEFAULT_ACCEL = 0.8
    SURFACE_FRICTION_BASE = 0.05
    CORNER_PENALTY_BASE = 0.1

    # --- 戦略・スパート関連 ---
    SPURT_DISTANCE = 600.0  # 残り何mでスパートするか
    SPURT_SPEED_BOOST = 1.5  # スパート時の速度上乗せ(m/s)
    CRUISING_SPEED_COEFF = 0.95  # 道中の速度抑制（巡航速度）
    
    # --- スタミナ関連 ---
    STAMINA_LOSS_COEFF = 0.008  # 消費係数
    EXHAUST_SPEED_COEFF = 0.8  # スタミナ切れ時の速度倍率
