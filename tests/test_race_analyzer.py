import pytest
from dataclasses import replace
from src.services.race_analyzer import RaceAnalyer
from src.models.race_data import RaceSnapshot
from src.models.horse_data import HorseSnapshot


# ---------------------------------------------------------
# 1. 最小限のパラメータで HorseSnapshot を作るファクトリ・フィクスチャ
# ---------------------------------------------------------
@pytest.fixture
def create_horse_snapshot():
    """
    テスト用の HorseSnapshot を生成するヘルパー関数を提供します。
    引数で指定されなかったフィールドは、テスト用のデフォルト値が自動で入ります。
    """
    def _create(horse_id: str, **kwargs) -> HorseSnapshot:
        # テスト実行に必要な最小限のベース値を定義
        default_params = {
            "horse_id": horse_id,
            "step": 0,
            "elapsed_time": 0.0,
            "accel_power": 0.0,
            "accel": 0.0,
            "target_velocity": 0.0,
            "velocity": 15.0,
            "distance": 0.0,
            "stamina": 1500.0,
            "target_lane": 0.0,
            "lane": 0.0,
            "dist_to_front": 0.0,
            "dist_to_front_left": 0.0,
            "dist_to_front_right": 0.0,
            "dist_to_side_left": 0.0,
            "dist_to_side_right": 0.0,
            "section": 0,
            "behavior": 0,
            "strategy": 0,
            "is_finished": False,
            "finish_time": None,
            "time_at_600m": None,
            # リスト型のデフォルトは dataclass(field) 側で入るため省略可能ですが、
            # テスト用に要素を確保したい場合はここで指定します
            "laptimes": [0.0] * 10, 
            "checkpoint_ranks": [0] * 4,
        }
        # 呼び出し元から指定された値（kwargs）で上書き
        default_params.update(kwargs)
        return HorseSnapshot(**default_params)
        
    return _create


# ---------------------------------------------------------
# 2. RaceSnapshot を作るフィクスチャ
# ---------------------------------------------------------
@pytest.fixture
def create_race_snapshot():
    def _create(horses_dict: dict[str, HorseSnapshot]) -> RaceSnapshot:
        return RaceSnapshot(
            race_id="TEST_RACE",
            step=0,
            elapsed_time=0.0,
            horses=horses_dict,
            ranks={h_id: 0 for h_id in horses_dict.keys()}
        )
    return _create


# ---------------------------------------------------------
# 3. 実際のテストケース
# ---------------------------------------------------------
def test_update_ranks_correctly_orders_by_distance(create_horse_snapshot, create_race_snapshot):
    """走破距離(distance)の長い順に、正しく順位が更新されるかのテスト"""
    
    # ファクトリを使い、テストに関係ある「distance」だけを指定して綺麗なコードで生成
    h1 = create_horse_snapshot(horse_id="H1", distance=100.0)
    h2 = create_horse_snapshot(horse_id="H2", distance=150.0)  # こっちが1位になるはず
    h3 = create_horse_snapshot(horse_id="H3", distance=50.0)
    
    race_snap = create_race_snapshot({"H1": h1, "H2": h2, "H3": h3})
    
    # テスト実行
    updated_snap = RaceAnalyer.update_ranks(race_snap)
    
    # 検証
    assert updated_snap.ranks["H2"] == 1
    assert updated_snap.ranks["H1"] == 2
    assert updated_snap.ranks["H3"] == 3


def test_is_all_goal_returns_true_when_all_horses_finished(create_horse_snapshot, create_race_snapshot):
    """全馬ゴールフラグが立っている時に True を返すかのテスト"""
    
    # テストに関係ある「is_finished」だけを指定
    h1 = create_horse_snapshot(horse_id="H1", is_finished=True)
    h2 = create_horse_snapshot(horse_id="H2", is_finished=True)
    
    race_snap = create_race_snapshot({"H1": h1, "H2": h2})
    
    assert RaceAnalyer.is_all_goal(race_snap) is True