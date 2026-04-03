# 根性フラグの適用例
def apply_guts_logic(horse_data, current_state):
    # CSVから算出した根性値 (0.0〜1.0)
    guts_score = horse_data['guts_rate'] 
    
    # 判定：隣に馬がいる（並走）、かつスタミナが少ない
    if current_state['is_side_by_side'] and current_state['stamina'] < 50:
        # 根性がある馬は、スタミナ消費を一時的に無視して速度を維持する
        current_state['velocity_decay'] *= (1.0 - (guts_score * 0.5))
        
    return current_state

# 脚質判定のPython実装イメージ
# 過去5走程度の平均をとることで、その馬の「得意なスタイル」を特定します
def judge_running_style(passing_orders, num_horses):
    # 例: "9-9-9-7" -> [9, 9, 9, 7]
    pos_list = [int(x) for x in passing_orders.split('-')]
    first_pos = (pos_list[0] - 1) / (num_horses - 1)
    
    if first_pos <= 0.1:
        return "逃げ"
    elif first_pos <= 0.4:
        return "先行"
    elif first_pos <= 0.7:
        return "差し"
    else:
        return "追込"