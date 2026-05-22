import pytest

from src.utils.utils import (
    get_waku_ban,
)

# (馬番, 総頭数, 期待される枠番) の順でテストデータを定義
@pytest.mark.parametrize("uma_ban, total_horses, expected", [
    (1, 5, 1),   # 5頭立ての1番 → 1枠
    (5, 5, 5),   # 5頭立ての5番 → 5枠
    (1, 18, 1),  # 18頭立ての1番 → 1枠
    (2, 18, 1),  # 18頭立ての2番 → 1枠（1枠は2頭）
    (3, 18, 2),  # 18頭立ての3番 → 2枠
    (18, 18, 8), # 18頭立ての18番 → 8枠
    (1, 15, 1),  # 15頭立ての1番 → 1枠（15頭立ては1枠だけが1頭）
    (2, 15, 2),  # 15頭立ての2番 → 2枠（2番以降は各枠2頭ずつ）
])

def test_get_waku_ban_valid(uma_ban, total_horses, expected):
    assert get_waku_ban(uma_ban, total_horses) == expected

# 例外処理（エラーハンドリング）のテストもシンプル
def test_get_waku_ban_invalid_value():
    with pytest.raises(ValueError):
        get_waku_ban(10, 8)  # 8頭立てなのに10番を指定したらエラー