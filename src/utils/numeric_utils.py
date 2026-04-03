"""
numeric_utils.py の概要

シンプルな数値に関するヘルパー関数群。
"""


def convert_to_int_list(data_list) -> list:
    """リスト内の要素をすべてint型に変換する関数"""
    return [int(x) for x in data_list]

def fill_list_if_empty(data_list, start_num: int=1, end_range: int=13) -> list:
    """リストが空なら1から12までの数字のリストに置き換える関数"""
    if not data_list:
        return list(range(start_num, end_range))
    return data_list

def parse_list_from_args_with_comma(arg) -> list:
    """カンマ区切りの文字列をリストに変換する汎用関数"""
    if not arg:
        return []
    return [item.strip() for item in arg.split(',')]
