import pytest
from dataclasses import replace

from src.models.horse_data import HorseProfile, HorseSnapshot, HorseEnvironment, DistContext
from src.constants.enums import HorseStrategyType, SectionName
from src.models.track_data import TrackSection
from src.core.race_logics import (
    get_target_lane,
)

# ベースとなるダミーデータの定義例
def create_base_environment(dist_to_front=999.0, dist_left=999.0, dist_right=999.0):
    # 障害物のないクリーンな環境をデフォルトとする
    ctx = DistContext(
        dist_to_front=dist_to_front,
        dist_to_front_left=999.0,
        dist_to_front_right=999.0,
        dist_to_beside_left=dist_left,
        dist_to_beside_right=dist_right
    )
    return HorseEnvironment(
        race_distance=1600.0, surface=0, condition=0, friction=1.0, corner_radius=0.0,
        num_horses=12, rank=5, dist_context=ctx,
        section=TrackSection(start_at=0, distance=400, type=0, name=SectionName.BACKSTRETCH) # ダミー
    )


@pytest.fixture
def base_profile():
    return HorseProfile(
        horse_id="test_horse", name="テストウマ", bracket_num=1, horse_num=1,
        jockey="武豊", sex=0, age=3, horse_weight=480.0, weight_carried=57.0,
        start_speed=13.0, cruise_speed=16.0, spurt_speed=18.0,
        start_acceleration=3.0, cruise_acceleration=0.5, spurt_acceleration=1.0,
        top_speed_potential=18.5, total_stamina=2000.0, stamina_waste_rate=1.0,
        heavy_track_aptitude=1.0, weight_tolerance=1.0, distance_flexibility=1.0,
        cornering_ability=0.95, gate_reaction=0.0, stability_factor=0.02,
        base_agility=2.0, lane_change_frequency=0.1, prefers_inside=0.5,
        pace_switching_agility=1.0, course_cornering_efficiency=1.0,
        strategy=HorseStrategyType.STALKER, pacing_strategy_bias=0.5,
        grit_factor=1.02, mental_stability=1.0, spurt_trigger_distance=400.0,
        spurt_trigger_type=0
    )

@pytest.fixture
def base_snapshot():
    return HorseSnapshot(
        horse_id="test_horse", step=0, elapsed_time=6.0, accel_power=0.5, accel=0.0,
        target_velocity=16.0, velocity=16.0, distance=100.0, stamina=2000.0,
        target_lane=5.0, lane=5.0, dist_to_front=999.0, dist_to_front_left=999.0,
        dist_to_front_right=999.0, dist_to_side_left=999.0, dist_to_side_right=999.0,
        section=0, behavior=0, strategy=0
    )

# --- テストケース ---

def test_get_target_lane_within_5_seconds(base_profile, base_snapshot):
    """【シナリオ①】5秒未満はレーン移動しないこと"""
    snap = replace(base_snapshot, elapsed_time=4.9, lane=5.0)
    env = create_base_environment(dist_to_front=1.0) # 前を詰まらせる
    
    target = get_target_lane(base_profile, snap, env)
    assert target == 5.0


def test_get_target_lane_prefer_inside_when_clear(base_profile, base_snapshot):
    """【シナリオ②】周囲がクリアなら基本コストが低い内側(左)を選ぶこと"""
    snap = replace(base_snapshot, elapsed_time=6.0, lane=5.0)
    env = create_base_environment() # 全て999.0
    
    target = get_target_lane(base_profile, snap, env)
    assert target == 4.5 # 5.0 - 0.5


def test_get_target_lane_avoids_front_block(base_profile, base_snapshot):
    """【シナリオ③】前方が激しく詰まっている場合、現在のレーン(5.0)を避けること"""
    snap = replace(base_snapshot, elapsed_time=6.0, lane=5.0)
    # 前方距離を 1.0m に（RELEVANT_DIST_JUST_FRONT未満を想定）
    env = create_base_environment(dist_to_front=1.0)
    
    target = get_target_lane(base_profile, snap, env)
    assert target != 5.0 # 現在のレーンはペナルティが高いので選ばれないはず