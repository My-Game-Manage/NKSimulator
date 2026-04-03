from typing import List, Dict, Any
from dataclasses import dataclass
from constants.schema import SegmentType, CourseLocation

@dataclass
class TrackSegment:
    location: CourseLocation  # 名前ではなく役割で管理
    start: float
    end: float
    segment_type: SegmentType
    radius: float = 0.0

class Track:
    def __init__(self, name: str, distance: int, segments: List[TrackSegment]):
        self.name = name
        self.distance = distance
        self.segments = segments
        self.effective_lane_width = 0.7 

    def get_segment(self, position: float) -> TrackSegment:
        for seg in self.segments:
            if seg.start <= position < seg.end:
                return seg
        return self.segments[-1]

    def calculate_curvature_loss_coeff(self, position: float, current_lane: float) -> float:
        segment = self.get_segment(position)
        if segment.segment_type == SegmentType.CURVE and segment.radius > 0:
            # 外回りによる実質的な距離延長・速度ロスを計算
            return segment.radius / (segment.radius + (current_lane * self.effective_lane_width))
        return 1.0

    @classmethod
    def from_config(cls, config: Dict[str, Any]):
        """
        JSONや辞書形式の設定データからTrackインスタンスを生成する。
        これにより oi_1200 等の個別メソッドが不要になる。
        """
        segments = [
            TrackSegment(
                location=CourseLocation(s["location"]),
                start=s["start"],
                end=s["end"],
                segment_type=SegmentType(s["type"]),
                radius=s.get("radius", 0.0)
            ) for s in config["segments"]
        ]
        return cls(config["name"], config["distance"], segments)