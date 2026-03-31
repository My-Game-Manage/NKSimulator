# main.py
import argparse
import sys
from src.utils.date_utils import get_today_jst, normalize_date_format
from src.constants.master_data import JYO_NAME_MAP
from src.core.simulator import RaceSimulator

def convert_to_ints(data_list):
    """リスト内の要素をすべてint型に変換する関数"""
    return [int(x) for x in data_list]

def fill_if_empty(data_list):
    """リストが空なら1から12までの数字のリストに置き換える関数"""
    if not data_list:
        return list(range(1, 13))
    return data_list
    
def parse_list_arg(arg):
    """カンマ区切りの文字列をリストに変換する汎用関数"""
    if not arg:
        return []
    return [item.strip() for item in arg.split(',')]

# 名前からコードを引くための辞書を事前に作成 {'札幌': '01', '大井': '44', ...}
NAME_TO_CODE = {v: k for k, v in JYO_NAME_MAP.items()}

def convert_to_course_codes(input_list: list) -> list:
    """
    ['大井', '54'] のような混在リストを ['44', '54'] に統一する
    """
    clean_codes = []
    for item in input_list:
        item = item.strip()
        
        if item.isdigit():
            # 数字ならそのまま採用（0埋めだけ念のため行う）
            clean_codes.append(item.zfill(2))
        elif item in NAME_TO_CODE:
            # 名前なら辞書からコードを引く
            clean_codes.append(NAME_TO_CODE[item])
        else:
            # どちらでもない場合は無視するか、ログを出す
            print(f"Warning: 会場名 '{item}' が見つかりません。")
            
    return clean_codes

def main():
    parser = argparse.ArgumentParser(
        description="NetKeiba Data Collector: 開催日トップから指定条件のレースデータを取得します。"
    )
    
    # 1. 日付指定 (デフォルトは今日)
    parser.add_argument(
        "--date", 
        type=str, 
        default=get_today_jst(),
        help="対象日 (YYYYMMDD). デフォルトは今日の日本時間"
    )

    # 2. 会場フィルタ (コード指定: 44,54 など)
    parser.add_argument(
        "--course", 
        type=parse_list_arg, 
        default=[],
        help="会場コードのカンマ区切り (例: 44,54). 指定なしで全会場"
    )

    # 3. レース番号フィルタ (1,11 など)
    parser.add_argument(
        "--race_num", 
        type=parse_list_arg, 
        default=[],
        help="レース番号のカンマ区切り (例: 1,11). 指定なしで全レース"
    )

    args = parser.parse_args()
    # 日付のフォーマットを 20260327 形式に正規化
    target_date = normalize_date_format(args.date)

    # 会場指定（名前またはコード）をすべてコードに変換
    #target_course_codes = convert_to_course_codes(args.course)
    target_course_codes = args.course

    # レース番号をint型に修正し、空っぽならフル番号で埋める
    target_race_nums = fill_if_empty(convert_to_ints(args.race_num))
    
    # シミュレーターの実行
    try:
        sim = RaceSimulator()
        sim.run(
            target_date=target_date,
            course_filter=target_course_codes,
            race_num_filter=target_race_nums,
        )
    except KeyboardInterrupt:
        print("\nユーザーにより中断されました。")
        sys.exit(0)
    except Exception as e:
        print(f"致命的なエラーが発生しました: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
