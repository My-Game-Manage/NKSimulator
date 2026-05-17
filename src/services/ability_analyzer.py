"""
ability_analyzer.py の概要

馬の能力に関する計算を行う。
"""
import pandas as pd
import numpy as np
import logging

# ロガーの取得（__name__ はファイル名/モジュール名になる）
logger = logging.getLogger(__name__)

from src.constants.schema import RaceCol
from src.constants.enums import HorseStrategyType
from src.utils.normalizer import valid_horse_history_df, get_normalized_base_time, correct_surface_effected_time, normalize_horse_performance, correct_weight_carried_effected_time
from src.constants.constants import (
    DEFAULT_STABILITY, STABILITY_FACTOR_BASE, MIN_STABILITY_FACTOR,
    SPEED_DIFF_PER_100M, STARTING_TIME_LOSS,
    SPURT_DIFF_PER_100M,
    START_DIFF_PER_100M,
    TURF_LAST_3F_BASELINE, DIRT_LAST_3F_BASELINE,
    CRUISE_ACCELERATION_RATE,
)


def calculate_min_max_speed(past_records: pd.DataFrame) -> tuple:
    # 不要な値を除去
    valid_records = valid_horse_history_df(past_records)
    # 1. 走破タイム(s)を算出 (タイムが '107.6' などの形式の場合)
    # 2. 全レースの時速(m/s)を計算
    speeds = valid_records[RaceCol.DISTANCE] / valid_records[RaceCol.TIME]
    
    # 3. 上位3件の平均をとる（1回きりのラッキーパンチを防ぐため）
    top_3_avg = speeds.nlargest(3).mean()

    # 4. 下位3件の平均を取る
    worst_3_avg = speeds.nsmallest(3).mean()
    
    # 大井の平均的なC3クラスなら 15.0 ~ 16.5 m/s 程度に収束するはずです
    return top_3_avg, worst_3_avg

def calculate_normalized_speed(past_records: pd.DataFrame) -> float:
    """基本となる速度に補正して返す（レース距離による巡航速度の元になる）"""
    valid_records = get_normalized_speed_records(past_records)

    # この「正規化された速度」で上位3件の平均を取る
    base_ability = valid_records['normalized_speed'].nlargest(3).mean()

    return base_ability

def calculate_normalized_start_speed(past_records: pd.DataFrame) -> float:
    """スタート用の速度を取得する"""
    valid_records = get_normalized_speed_records(past_records)

    # 正規化されたスタート速度から上位3件の平均を取る
    start_ability = valid_records['normalized_start_speed'].nlargest(3).mean()

    return start_ability

def calculate_stability_factor(past_records: pd.DataFrame) -> float:
    """
    馬の過去データから、最低速度の係数(0.85〜0.95程度)を算出する
    """
    valid_df = get_normalized_speed_records(past_records)
    # 1. 正規化された巡航速度のリストを取得 (前述のロジックで算出済みのもの)
    speeds = valid_df['normalized_speed']
    
    if len(speeds) < 3:
        return DEFAULT_STABILITY # データが少ない場合は標準的な値を返す
    
    # 2. 変動係数(CV)の計算
    mean_v = speeds.mean()
    std_v = speeds.std()
    cv = std_v / mean_v
    
    # 3. 係数へのマッピング
    # CVが小さいほど(安定) 0.95 に近く、大きいほど(不安定) 0.85 に近づくよう調整
    # 日本の競馬データだと CV は概ね 0.02〜0.08 程度に収まることが多いです
    stability_factor = STABILITY_FACTOR_BASE - (cv * 1.0) 
    
    # 念のため上下限をクリップ
    return max(MIN_STABILITY_FACTOR, min(STABILITY_FACTOR_BASE, stability_factor))

def calculate_normalized_time_as_1600m(row: pd.Series) -> float:
    """正規化されたbase_timeを返す"""
    # 必要な情報取得
    surface = row[RaceCol.SURFACE]
    condition = row[RaceCol.TRACK_CONDITION]
    distance = row[RaceCol.DISTANCE]

    # 馬場補正
    valid_time = correct_surface_effected_time(row[RaceCol.TIME], condition, surface)
    # 斤量補正
    valid_time = correct_weight_carried_effected_time(valid_time, distance, row[RaceCol.WEIGHT_CARRIED])

    # 1600m基準で正規化
    norm_time = get_normalized_base_time(valid_time, distance, surface)

    return norm_time

def calculate_normalized_speed_correct_weight_surface(row: pd.Series) -> float:
    """正規化されたbase_speedを返す"""
    # 必要な情報取得
    last_3f = row[RaceCol.LAST_3F]

    norm_time = calculate_normalized_time_as_1600m(row)

    norm_v = 1000 / (norm_time - last_3f - 1.5)

    return norm_v

def calculate_normalized_start_speed_corrected(row: pd.Series) -> float:
    """正規化されたstart_speedを返す"""
    # 必要な情報取得
    last_3f = row[RaceCol.LAST_3F]
    num_horses = row[RaceCol.NUM_HORSES]
    passsing_order = row[RaceCol.PASSING_ORDER]
    pass_1st = int(passsing_order.split('-')[0])

    norm_time = calculate_normalized_time_as_1600m(row)

    norm_start_v = 1000 / (norm_time - last_3f) * (1.0 + ((num_horses - pass_1st) / (num_horses - 1)))

    return norm_start_v

def calculate_normalized_spurt_acceleration(row: pd.Series) -> float:
    """正規化されたspurt_accelを返す"""
    # 必要な情報取得
    last_3f = row[RaceCol.LAST_3F]
    surface = row[RaceCol.SURFACE]
    distance = row[RaceCol.DISTANCE]

    base_line = get_baseline_3f(distance, surface)

    # 基準タイムよりどれだけ速いかで相対評価
    # 例: 1600m(基準39.5)で38.5秒なら、差し引き +1.0秒 のアドバンテージ
    # 1秒速いごとに +0.05
    accel_power = 1.0 + (base_line - last_3f) * 0.05

    return accel_power

def get_normalized_speed_records(past_records: pd.DataFrame) -> pd.DataFrame:
    """正規化された巡航速度のDataFrameを返す"""
    # 不要な値を除去
    valid_records = valid_horse_history_df(past_records)
    
    valid_records['normalized_speed'] = valid_records.apply(calculate_normalized_speed_correct_weight_surface, axis=1)
    valid_records['normalized_start_speed'] = valid_records.apply(calculate_normalized_start_speed_corrected, axis=1)

    return valid_records

def get_race_cruise_speed(base_ability: float, race_distance: float) -> float:
    """
    基準能力値(1600m相当)から、指定された距離の巡航速度を算出する
    """
    # 1600mからの乖離距離（100m単位）
    distance_diff_unit = (race_distance - 1600) / 100
    
    # 減衰・加速の計算
    adjustment = distance_diff_unit * SPEED_DIFF_PER_100M
    
    return base_ability - adjustment

def get_race_spurt_speed(base_spurt_ability: float, race_distance: float) -> float:
    """
    基準スパート能力値(1600m相当)から、指定された距離のスパート速度を算出する
    """
    # 1600mからの乖離距離（100m単位）
    distance_diff_unit = (race_distance - 1600) / 100
    
    # 調整値の計算
    adjustment = distance_diff_unit * SPURT_DIFF_PER_100M
    
    # 短距離ならプラス、長距離ならマイナスに働く
    return base_spurt_ability - adjustment

def get_race_start_speed(base_start_ability: float, race_distance: float) -> float:
    """
    基準スタート能力値(1600m相当)から、指定された距離のスパート速度を算出する
    """
    # 1600mからの乖離距離（100m単位）
    distance_diff_unit = (race_distance - 1600) / 100
    
    # 調整値の計算
    adjustment = distance_diff_unit * START_DIFF_PER_100M
    
    # 短距離ならプラス、長距離ならマイナスに働く
    return base_start_ability - adjustment

def get_baseline_3f(distance: float, surface: str) -> float:
    """レース距離に応じた上り3Fの基準を返す"""
    if surface == 'ダ':
        # ダート（大井など）
        if distance <= 1200: return DIRT_LAST_3F_BASELINE[1200]
        elif distance <= 1400: return DIRT_LAST_3F_BASELINE[1400]
        elif distance <= 1600: return DIRT_LAST_3F_BASELINE[1600]
        elif distance <= 1800: return DIRT_LAST_3F_BASELINE[1800]
        else: return DIRT_LAST_3F_BASELINE[2000]
    else:
        # 芝は全体的にダートより2〜3秒速い
        if distance <= 1200: return TURF_LAST_3F_BASELINE[1200]
        elif distance <= 1400: return TURF_LAST_3F_BASELINE[1400]
        elif distance <= 1600: return TURF_LAST_3F_BASELINE[1600]
        elif distance <= 1800: return TURF_LAST_3F_BASELINE[1800]
        else: return TURF_LAST_3F_BASELINE[2000]

def calculate_normalized_spurt_speed(past_records: pd.DataFrame) -> float:
    def _calc_normalized_spurt_speed(row):
        # 実際のスパート速度 (600m / 上り3Fタイム)
        v_spurt = 600 / row[RaceCol.LAST_3F]
    
        diff_dist = (row[RaceCol.DISTANCE] - 1600) / 100
        # 短い距離ほど速いタイムが出やすいので、その分をマイナス補正して1600m相当に直す
        v_norm = v_spurt + (diff_dist * SPURT_DIFF_PER_100M)
    
        return v_norm
    # 不要な値を除去
    valid_records = valid_horse_history_df(past_records)

    # ベース能力の抽出
    valid_records['norm_spurt_speed'] = valid_records.apply(_calc_normalized_spurt_speed, axis=1)
    base_spurt_ability = valid_records['norm_spurt_speed'].nlargest(3).mean()
    
    return base_spurt_ability

def calculate_last_3f(past_records: pd.DataFrame) -> float:
    """上がり3Fの速度を返す（上位の平均）"""
    # 不要な値を除去
    valid_records = valid_horse_history_df(past_records)
    last_3fs = 600 / valid_records[RaceCol.LAST_3F]
    # 上位3件の平均
    top_3_avg = last_3fs.nlargest(3).mean()

    return top_3_avg

def calculate_spurt_acceleration(past_records: pd.DataFrame) -> float:
    """スパート用の加速力を返す"""
    # 不要な値を除去
    valid_records = valid_horse_history_df(past_records)

    valid_records['spurt_accel'] = valid_records.apply(calculate_normalized_spurt_acceleration, axis=1)

    spurt_power = valid_records['spurt_accel'].nlargest(3).mean()

    return spurt_power

def calculate_dash_score(row: pd.Series) -> float:
    """通貨順から指数を返す"""
    first_pos = float(str(row[RaceCol.PASSING_ORDER]).split('-')[0])
    num_horses = float(row[RaceCol.NUM_HORSES])

    # 1.0(最前列) 〜 0.0(最後方) のダッシュスコア
    score = (num_horses - first_pos) / (num_horses - 1)

    return score

def calculate_start_acceleration(past_records: pd.DataFrame) -> float:
    """スタート用の加速力を返す"""
    # 不要な値を除去
    valid_records = valid_horse_history_df(past_records)

    valid_records['dash_score'] = valid_records.apply(calculate_dash_score, axis=1)

    # レースごとのダッシュスコアの平均（デフォルトは中団の 0.5）
    avg_dash_score = valid_records['dash_score'].mean()

    # 馬体重と斤量による物理的な「パワー（筋肉量）/ 重量」の補正
    # 地方・ダートでは特に馬体重が重い（筋肉がある）ほうがスタートダッシュが効く傾向があります
    avg_weight = valid_records[RaceCol.HORSE_WEIGHT].mean()
    avg_carried = valid_records[RaceCol.WEIGHT_CARRIED].mean()

    # 重量の基準値を設定 (例: 馬体重470kg, 斤量55kg を基準の 1.0 と想定)
    weight_factor = 1.0
    if pd.notna(avg_weight) and avg_weight > 0:
        # 馬体重が重いほどプラス、斤量が重いほどマイナス
        weight_factor = (avg_weight / 470.0) - ((avg_carried - 55.0) * 0.01)
        # 補正が極端になりすぎないようクリッピング (0.9 〜 1.1)
        weight_factor = max(0.9, min(1.1, weight_factor))
        
    # ベースのスタート加速度を計算
    # ダッシュスコアが 1.0（常にハナ）なら +0.15、0.0（常に出遅れ・後方）なら -0.15
    start_accel = 1.0 + (avg_dash_score - 0.5) * 0.30
    # 物理補正を乗算
    start_accel *= weight_factor

    return max(0.5, start_accel)

def get_race_cruise_acceleration(base_ability: float) -> float:
    """巡航時の加速力を返す"""
    return base_ability * CRUISE_ACCELERATION_RATE

def calculate_acceleration(past_records: pd.DataFrame) -> float:
    # 不要な値を除去
    valid_records = valid_horse_history_df(past_records)
    # 上がり3F (last_3f) が速いほど高い値を返す
    # 例：平均的な上がりタイムより1秒速ければ +0.1 m/s^2
    avg_last_3f = valid_records[RaceCol.LAST_3F].mean()
    
    # 標準的な加速力を 1.0 とした相対評価
    accel_factor = 1.0 + (39.0 - avg_last_3f) * 0.05 
    return max(0.5, accel_factor)

def calculate_stamina_params(past_records: pd.DataFrame) -> tuple:
    # 不要な値を除去
    valid_records = valid_horse_history_df(past_records)
    # 1. 過去の最長距離をベースにする
    max_dist_history = valid_records[RaceCol.DISTANCE].max()
    avg_weight = valid_records[RaceCol.HORSE_WEIGHT].mean()
    
    # 総スタミナ: 距離適性が高いほど余裕が出るように算出
    total_stamina = max_dist_history * 1.2 + (avg_weight * 0.5)
    
    # 2. 燃費: 過去の上がり3F(last_3f)と走破タイムのバランスを見る
    # 終盤にバテている（上がりタイムが極端に遅い）馬は燃費を悪く設定
    stamina_efficiency = estimate_efficiency(valid_records)
    
    return total_stamina, stamina_efficiency
    
def analyze_horse_agility(past_records: pd.DataFrame) -> dict:
    # 不要な値を除去
    valid_records = valid_horse_history_df(past_records)

    # 1. 外枠時（7, 8枠）の「内への潜り込み」性能を算出
    outer_starts = valid_records[valid_records[RaceCol.BRACKET_NUM] >= 7]
    def get_start_pos(order):
        try: return int(str(order).split('-')[0])
        except: return 10 # 不明な場合は平均的な値を仮定
    
    # (枠番 - 初手順位) が大きいほど、外から内へ鋭く切り込んでいる
    cut_in_scores = outer_starts.apply(
        lambda x: x[RaceCol.BRACKET_NUM] * 1.5 - get_start_pos(x[RaceCol.PASSING_ORDER]), axis=1
    )
    
    # 2. 道中の位置変化（機動力）
    def get_position_variance(order):
        positions = [int(p) for p in str(order).split('-') if p.isdigit()]
        return np.std(positions) if len(positions) > 1 else 0
    
    mobility_scores = valid_records[RaceCol.PASSING_ORDER].apply(get_position_variance)

    return {
        "base_agility": 1.0 + (cut_in_scores.mean() * 0.05 if not cut_in_scores.empty else 0),
        "lane_change_frequency": mobility_scores.mean() * 0.2,
        "prefers_inside": (valid_records[RaceCol.BRACKET_NUM] <= 2).mean() # 内枠を引いた時の先行率
    }

def calculate_gate_reaction(past_records: pd.DataFrame) -> float:
    # 不要な値を除去
    valid_records = valid_horse_history_df(past_records)
    # 各レースの最初の通過順位を取り出す
    # 例: "5-4-3-2" -> 5
    order_records = valid_records.dropna(subset=RaceCol.PASSING_ORDER)
    first_pos = order_records[RaceCol.PASSING_ORDER].str.split('-').str[0].astype(float)
    # 頭数に対する比率にする（14頭立ての5位と、8頭立ての5位は意味が違うため）
    pos_ratio = first_pos / valid_records[RaceCol.NUM_HORSES]

    # 比率が小さい（＝前の方にいる）ほど高い値を返す
    # 標準を1.0とし、逃げ・先行馬なら1.2〜、出遅れがちな馬なら0.8〜
    return 1.2 - pos_ratio.mean()
    
def calculate_cornering_ability(past_records: pd.DataFrame) -> float:
    # 不要な値を除去
    valid_records = valid_horse_history_df(past_records)
    # 3角と4角の順位差の平均を見る
    # "2-2-3-4" のような馬はコーナーで置かれている（適性低め）
    # "8-7-5-3" のような馬はコーナーで加速している（適性高め）
    diffs = []
    order_records = valid_records.dropna(subset=RaceCol.PASSING_ORDER)
    for order in order_records[RaceCol.PASSING_ORDER]:
        pts = order.split('-')
        if len(pts) >= 3:
            # 後半2つのセクションの差分（例: 4角順位 - 3角順位）
            diffs.append(int(pts[-2]) - int(pts[-1])) 

    # 順位が上がっている（差が正）ほど高評価
    ability = 0.5 + (sum(diffs) / len(diffs) if diffs else 0) * 0.1
    return max(0.2, min(1.0, ability))

def determine_strategy(past_records: pd.DataFrame) -> str:
    # 不要な値を除去
    valid_records = valid_horse_history_df(past_records)
    # 最初のコーナー順位の平均比率を算出
    first_pos_ratios = []
    order_records = valid_records.dropna(subset=RaceCol.PASSING_ORDER)
    for _, row in order_records.iterrows():
        first_pos = int(row[RaceCol.PASSING_ORDER].split('-')[0])
        first_pos_ratios.append(first_pos / row[RaceCol.NUM_HORSES])

    avg_ratio = sum(first_pos_ratios) / len(first_pos_ratios)

    # 比率による判定しきい値
    if avg_ratio <= 0.15: return HorseStrategyType.LEADER.value   # 逃げ (最前列)
    if avg_ratio <= 0.40: return HorseStrategyType.STALKER.value  # 先行 (前め)
    if avg_ratio <= 0.70: return HorseStrategyType.CLOSER.value  # 差し (中団)
    return HorseStrategyType.REAR.value                         # 追込 (後方)
    
def calculate_spurt_dist(course_dist: float, strategy: str) -> float:
    # 1. 物理的な最大持続の目安（コースの1/3〜1/4程度）
    # 1600mなら 400m, 2400mなら 600m くらいがベース
    base_dist = course_dist * 0.25
    
    # 2. 脚質による「追い出し」のタイミング補正
    # 正の値は早仕掛け、負の値は待機を意味する
    strategy_offsets = {
        HorseStrategyType.LEADER: 100,    # 逃げ：残り500m (400+100)
        HorseStrategyType.STALKER: 50,  # 先行：残り450m (400+50)
        HorseStrategyType.CLOSER: 0,    # 差し：残り400m
        HorseStrategyType.REAR: -100    # 追込：残り300m
    }
    
    offset = strategy_offsets.get(strategy, 0)
    return base_dist + offset

def estimate_efficiency(past_records: pd.DataFrame) -> float:
    """
    過去データからスタミナ消費効率（燃費）を推定する。
    1.0 を標準とし、値が小さいほど燃費が良い（スタミナが減りにくい）と定義する。
    """
    # 1. 「上がり」の失速度合いをチェック
    # 全体の平均時速に対して、最後の600m(上がり3F)でどれだけ失速しているか
    avg_speed = (past_records[RaceCol.DISTANCE] / past_records[RaceCol.TIME]).mean()
    last_3f_speed = (600.0 / past_records[RaceCol.LAST_3F]).mean()
    
    # 失速率 (値が大きいほど、最後の方でバテている)
    # 通常、ダートでは最後は少し遅くなるので 1.05 くらいが標準
    decline_ratio = avg_speed / last_3f_speed
    
    # 2. 人気と着順の相関（精神的なムラ・掛かり癖の推測）
    # 人気より着順が大幅に悪いレースが多い馬は、道中で体力をロスしていると見なす
    # 数値に変換し、変換できなかった（NaNになった）行を削除
    valid_data = (pd.to_numeric(past_records[RaceCol.RANK], errors='coerce') - 
            pd.to_numeric(past_records[RaceCol.POPULARITY], errors='coerce')).dropna()
    pop_rank_diff = valid_data.mean()

    # 3. 燃費係数の計算
    # ベースを 1.0 とし、失速しやすさとムラを加味
    efficiency = 1.0
    
    # 最後までバテない馬（decline_ratioが低い）は燃費を良くする
    efficiency += (decline_ratio - 1.05) * 0.5
    
    # 人気裏切りが多い馬は、道中の「掛かり」を想定して燃費を悪くする
    if pop_rank_diff > 2.0:
        efficiency += 0.05
        
    # 0.8 (超省エネ) 〜 1.2 (ガス欠しやすい) の範囲に収める
    return max(0.8, min(1.2, efficiency))