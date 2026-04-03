
# 平均時速の算出:
# $V_{base} = \frac{Distance}{Time}$
# （例：1800mを120.8秒で走った場合、約14.9 m/s）
def calc_avg_speed(distance, time):
    base_speed = distance / time
    return base_speed

# 上がり3ハロンによる調整
# last_3f を使って、ラスト600mの速度 $V_{finish}$ と、それ以外の道中の速度 $V_{cruise}$ を分離します。
# $V_{finish} = \frac{600}{last\_3f}$
# $V_{cruise} = \frac{Distance - 600}{Time - last\_3f}$
def calc_cruise_speed(distance, time, last_3f):
    cruise_speed = (distance - 600.0) / (time - last_3f)
    return cruise_speed

def calc_finish_speed(last_3f):
    finish_speed = 600 / last_3f
    return finish_speed

def update_velocity_at_exhaustion(current_v, guts_param):
    # 完全にバテた時の最低速度（これ以下には基本ならない）
    v_exhausted = 11.0 
    
    # 基本の減衰率
    base_decay = 0.08 
    
    # 根性による補正（guts_paramが高いほど減速しにくい）
    decay_rate = base_decay * (1.0 - guts_param)
    
    # 次のステップの速度を計算
    new_v = current_v - (current_v - v_exhausted) * decay_rate
    
    return max(new_v, v_exhausted)