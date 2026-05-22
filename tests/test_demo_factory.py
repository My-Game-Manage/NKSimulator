import pytest

from src.services.factory.demo_factory import DemoRaceFactory, DemoHorseFactory
from src.models.race_data import RaceInfo, RaceProfile
from src.models.horse_data import HorseProfile


class TestDemoHorseFactory:
    """DemoHorseFactory のテスト"""

    def test_create_horse_profile_returns_valid_structure(self):
        """馬プロファイルが正しい初期値とインクリメントされたIDで生成されるか"""
        factory = DemoHorseFactory()
        num_horses = 8

        # 1頭目の生成
        prof1 = factory.create_horse_profile(num_horses=num_horses)
        assert isinstance(prof1, HorseProfile)
        assert prof1.horse_id == "D000000001"
        assert prof1.name == "dummy_horse_1"  # 1始まりに修正した場合を想定
        assert prof1.horse_num == 1
        assert prof1.bracket_num == 1         # 8頭立ての1番は1枠

        # 2頭目の生成（連番の確認）
        prof2 = factory.create_horse_profile(num_horses=num_horses)
        assert prof2.horse_id == "D000000002"
        assert prof2.horse_num == 2

    def test_setup_horse_profile(self):
        """setup_horse_profile で値の一部が正しく上書きされるか"""
        factory = DemoHorseFactory()
        prof = factory.create_horse_profile(num_horses=8)
        
        # 戦略と馬体重を上書き
        updated_prof = factory.setup_horse_profile(prof, strategy=2, horse_weight=500)
        assert updated_prof.strategy == 2
        assert updated_prof.horse_weight == 500
        assert updated_prof.name == prof.name  # 他の値は維持されていること


class TestDemoRaceFactory:
    """DemoRaceFactory のテスト"""

    @pytest.mark.parametrize("num_horses", [5, 12, 18])
    def test_create_single_race_generates_correct_number_of_horses(self, num_horses):
        """指定した頭数分のレース情報が正しく生成されるか（境界値テストを兼ねる）"""
        race_factory = DemoRaceFactory()
        
        # 1600m, 芝(Turf) でレースを作成
        race_info = race_factory.create_single_race(distance=1600, surface="Turf", num_horses=num_horses)
        
        # 戻り値の型チェック
        assert isinstance(race_info, RaceInfo)
        assert isinstance(race_info.profile, RaceProfile)
        
        # レース全体の頭数チェック
        assert race_info.profile.num_horses == num_horses
        assert len(race_info.profile.horses) == num_horses
        assert len(race_info.snapshot.horses) == num_horses

    def test_create_races_warning(self, caplog):
        """create_races を呼んだ際、警告ログが出て1つのレースが返るか"""
        race_factory = DemoRaceFactory()
        
        # ログのキャプチャを開始
        with caplog.at_level("WARNING"):
            races = race_factory.create_races(distance=1600, surface="Turf", num_horses=8)
            
        assert len(races) == 1
        assert "デモレースでは1レースのみ作成できます" in caplog.text