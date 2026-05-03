"""
ability_analyzer.py の概要

馬の能力に関する計算を行う。
"""
import pandas as pd
import logging

# ロガーの取得（__name__ はファイル名/モジュール名になる）
logger = logging.getLogger(__name__)

from src.constants.schema import RaceCol
from src.constants.enums import HorseStrategyType
from src.utils.normalizer import valid_horse_history_df

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

def calculate_stability_factor(past_records: pd.DataFrame) -> float:
    """
    馬の過去データから、最低速度の係数(0.85〜0.95程度)を算出する
    """
    valid_df = get_normalized_speed_records(past_records)
    # 1. 正規化された巡航速度のリストを取得 (前述のロジックで算出済みのもの)
    speeds = valid_df['normalized_speed']
    
    if len(speeds) < 3:
        return 0.90 # データが少ない場合は標準的な値を返す
    
    # 2. 変動係数(CV)の計算
    mean_v = speeds.mean()
    std_v = speeds.std()
    cv = std_v / mean_v
    
    # 3. 係数へのマッピング
    # CVが小さいほど(安定) 0.95 に近く、大きいほど(不安定) 0.85 に近づくよう調整
    # 日本の競馬データだと CV は概ね 0.02〜0.08 程度に収まることが多いです
    stability_factor = 0.96 - (cv * 1.0) 
    
    # 念のため上下限をクリップ
    return max(0.85, min(0.96, stability_factor))

def get_normalized_speed_records(past_records: pd.DataFrame) -> pd.DataFrame:
    """正規化された巡航速度のDataFrameを返す"""
    def _calc_normalized_speed(row):
        # 実際の巡航速度
        v = (row[RaceCol.DISTANCE] - 600) / (row[RaceCol.TIME] - row[RaceCol.LAST_3F] - 1.5)
    
        # 1600mを基準とした補正 (100mあたり0.15m/sの増減)
        # 距離が短いほど速く出るので、その分をマイナス補正
        # 距離が長いほど遅く出るので、その分をプラス補正
        diff_dist = (row[RaceCol.DISTANCE] - 1600) / 100
        v_norm = v + (diff_dist * 0.15)
    
        return v_norm
    # 不要な値を除去
    valid_records = valid_horse_history_df(past_records)
    
    valid_records['normalized_speed'] = valid_records.apply(_calc_normalized_speed, axis=1)
    return valid_records

def get_race_cruise_speed(base_ability: float, race_distance: float) -> float:
    """
    基準能力値(1600m相当)から、指定された距離の巡航速度を算出する
    """
    # 100mあたりの速度変化係数 (分析データより)
    SPEED_DIFF_PER_100M = 0.15
    
    # 1600mからの乖離距離（100m単位）
    distance_diff_unit = (race_distance - 1600) / 100
    
    # 減衰・加速の計算
    adjustment = distance_diff_unit * SPEED_DIFF_PER_100M
    
    return base_ability - adjustment

def get_race_spurt_speed(base_spurt_ability: float, race_distance: float) -> float:
    """
    基準スパート能力値(1600m相当)から、指定された距離のスパート速度を算出する
    """
    # 100mあたりのスパート速度変化係数 (分析データより 0.016〜0.02)
    # 巡航速度(0.15)に比べて、スパート速度は距離の影響を受けにくい
    SPURT_DIFF_PER_100M = 0.02
    
    # 1600mからの乖離距離（100m単位）
    distance_diff_unit = (race_distance - 1600) / 100
    
    # 調整値の計算
    adjustment = distance_diff_unit * SPURT_DIFF_PER_100M
    
    # 短距離ならプラス、長距離ならマイナスに働く
    return base_spurt_ability - adjustment

def calculate_cruise_speed(past_records: pd.DataFrame) -> float:
    """巡航速度を算出して返す"""
    # 不要な値を除去
    valid_records = valid_horse_history_df(past_records)
    # タイムから上り3Fを引いたもので計算
    starting_loss = 1.0
    speeds = (valid_records[RaceCol.DISTANCE] - 600) / (valid_records[RaceCol.TIME] - valid_records[RaceCol.LAST_3F] - starting_loss)

    # 上位3件の平均を取る
    top_3_avg = speeds.nlargest(3).mean()

    return top_3_avg

def calculate_normalized_spurt_speed(past_records: pd.DataFrame) -> float:
    def _calc_normalized_spurt_speed(row):
        # 実際のスパート速度 (600m / 上り3Fタイム)
        v_spurt = 600 / row['last_3f']
    
        # 1600mを基準とした補正
        # スパート速度の減衰係数は巡航速度より小さく、0.02 程度が妥当 (データ分析結果より)
        SPURT_DIFF_PER_100M = 0.02
    
        diff_dist = (row['distance'] - 1600) / 100
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
    
def calculate_spurt_dist(strategy: str, history: pd.DataFrame) -> float:
    # 基本値は 600m (上がり3F)
    base_dist = 600.0

    # 脚質による調整
    # 逃げ・先行は早めに踏ん張る必要があるため長めにする傾向
    if strategy in (HorseStrategyType.LEADER.value, HorseStrategyType.STALKER.value):
        base_dist += 100.0

    # 過去の「マクリ」傾向（コーナーでの順位押し上げ）があれば加算
    # （前の回答の cornering_ability と連動させると効果的）
    # TODO: 履歴から算出

    return base_dist
    
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