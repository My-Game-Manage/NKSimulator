from dataclasses import dataclass

@dataclass(frozen=True)
class StaticParams:
    # 物理能力
    max_velocity: float      # 最高速度 (m/s)
    base_acceleration: float # 基本加速度
    stamina_capacity: float  # スタミナ総量
    
    # 特性・適性
    power: float             # 坂や重馬場への耐性 (1.0標準)
    intelligence: float      # 折り合いの良さ、スパート判断の正確さ
    grit: float              # 根性（競り合い時の粘り）
