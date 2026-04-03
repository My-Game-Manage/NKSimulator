import random

def get_initial_cost(style, bracket_number):
    cost = 1.0
    # 逃げ馬が外枠からハナを切るための負荷
    if style == "逃げ" and bracket_number > 6:
        cost += 0.15 
    # 追込馬が内枠で砂を被るストレス（スタミナ消費増）
    if style == "追込" and bracket_number < 3:
        cost += 0.05
    return cost

def calculate_corner_loss(current_lane):
    # 外側に1レーン膨らむごとの距離ペナルティ
    # 大井競馬場などの半径を考慮した定数を設定
    return current_lane * 1.5

def check_start_success(horse_stats):
    # 基礎出遅れ率（過去データから算出）
    prob = horse_stats['late_start_rate']
    
    # 枠順補正（例：1枠はゲート内で待たされるため+2%）
    if horse_stats['bracket'] == 1:
        prob += 0.02
        
    if random.random() < prob:
        return "LATE"  # 出遅れ発生
    return "GOOD"

# シミュレーション実行時
def recover_proc(start_status):
    if start_status == "LATE":
        # 最初の5秒間の目標速度を 0.7倍 に制限
        current_velocity *= 0.7
        # その後、取り戻そうとしてスタミナを余分に消費する（リカバー動作）
        stamina_drain_multiplier = 1.2
    return current_velocity, stamina_drain_multiplier


def update_ai_decision(horse):
    # 1. 前方の確認
    front_dist, front_horse_speed = scan_front(horse)
    
    # 2. 詰まり判定（前の馬が自分より遅い場合）
    if front_dist < 2.0 and front_horse_speed < horse.velocity:
        if can_move_outer(horse):
            # 外に出して回避
            horse.target_lane += 1
            horse.stamina -= change_lane_cost
        else:
            # 外に出られないなら減速（どん詰まり）
            horse.velocity = front_horse_speed
            horse.stress += 1  # ストレス値がたまるとスタミナ消費増
            
    # 3. 脚質による位置取り
    if horse.style == "差し" and horse.current_rank < horse.target_rank:
        # まだ前に行き過ぎなので、少し控える
        horse.target_velocity = horse.cruise_speed * 0.98

def calculate_mental_stats(horse_history_df):
    # 1. 気性の計算（着順のばらつき）
    rank_std = horse_history_df['rank'].std()
    temperament = 1.0 / (1.0 + rank_std * 0.1) # ばらつきが小さいほど高数値
    
    # 2. 賢さの計算（多頭数での着順維持・向上力）
    heavy_race = horse_history_df[horse_history_df['num_horses'] >= 12]
    intelligence = 1.0 - (heavy_race['rank'].mean() / heavy_race['num_horses'].mean())
    
    return temperament, intelligence

# シミュレーション実行時
if random.random() > horse.temperament:
    # 気性が悪い馬は、スパート開始を間違える、あるいは道中掛かる
    horse.ai_state = "CONTROL_LOST"
    horse.target_speed *= 1.1