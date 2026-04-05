# main.py
import argparse
import sys
from src.utils.logger import setup_logger
from src.utils.date_utils import get_today_jst, normalize_date_format
from src.utils.numeric_utils import parse_list_from_args_with_comma, fill_list_if_empty, convert_to_int_list
from src.utils.course_id_utils import is_valid_course_name
from src.constants.course_master import COURSE_MASTER
from src.core.simulator import RaceSimulator


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

    # 2. 会場フィルタ (大井、中山など)
    parser.add_argument(
        "--course", 
        type=parse_list_from_args_with_comma, 
        default=[],
        help="会場コードのカンマ区切り (例: 44,54). 指定なしで全会場"
    )

    # 3. レース番号フィルタ (1,11 など)
    parser.add_argument(
        "--race_num", 
        type=parse_list_from_args_with_comma, 
        default=[],
        help="レース番号のカンマ区切り (例: 1,11). 指定なしで全レース"
    )

    # 4. ログレベルの設定
    parser.add_argument(
        '--log', 
        default='INFO', 
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='ログレベルを指定します (デフォルト: INFO)'
    )
    args = parser.parse_args()

    args = parser.parse_args()
    # 日付のフォーマットを 20260327 形式に正規化
    target_date = normalize_date_format(args.date)

    # 会場指定（名前）のリスト
    target_course_codes = [c for c in args.course if is_valid_course_name(c)]

    # レース番号をint型に修正し、空っぽならフル番号で埋める
    target_race_nums = fill_list_if_empty(convert_to_int_list(args.race_num))

    # ログレベルの設定
    # setup_loggerに引数から渡されたレベルをセット
    logger = setup_logger("KeibaSimulator", level=args.log)

    # logger実行
    logger.debug("細かい計算過程を表示します（デバッグ用）")
    logger.info("シミュレーションを開始します")
    
    # シミュレーターの実行
    try:
        sim = RaceSimulator()
        sim.run(
            date=target_date,
            courses=target_course_codes,
            race_numbers=target_race_nums,
        )
    except KeyboardInterrupt:
        print("\nユーザーにより中断されました。")
        sys.exit(0)
    except Exception as e:
        print(f"致命的なエラーが発生しました: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
