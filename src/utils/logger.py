"""
logger.py の概要

プログラム実行中のログを取得し、表示したり保存したりする。
"""
import logging
import os
from datetime import datetime

def setup_logger(name: str, level: str = "INFO", log_dir: str = "logs"):
    """
    ロガーを初期化し、コンソールとファイルの両方に出力する設定を行う
    - 引数 level を受け取るように変更
    """
    os.makedirs(log_dir, exist_ok=True)
    
    logger = logging.getLogger(name)
    
    # 文字列のレベルを数値定数に変換（例: "DEBUG" -> 10）
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(numeric_level) 

    if logger.handlers:
        # 既存のハンドラがある場合も、レベルだけは最新の状態に更新する
        logger.setLevel(numeric_level)
        return logger

    # 出力フォーマットの設定（時刻, レベル, メッセージ）
    formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s - %(name)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 1. コンソール出力用の設定
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 2. ファイル出力用の設定 (日付ごとのファイル名にする)
    log_file = os.path.join(log_dir, f"{datetime.now().strftime('%Y%m%d')}.log")
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger
