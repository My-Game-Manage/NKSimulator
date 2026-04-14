# 簡単なシミュレーション例

```python
import numpy as np
import matplotlib.pyplot as plt
from dataclasses import dataclass
from typing import List

@dataclass
class Horse:
    name: str
    max_speed: float      # 最高速度 (m/s)
    acceleration: float   # 初期加速度 (m/s²)
    fatigue_factor: float # 疲労による減速の強さ (小さいほど持久力あり)

    def __post_init__(self):
        self.position = 0.0
        self.velocity = 0.0
        self.acc = 0.0
        self.history = {'time': [], 'position': [], 'velocity': [], 'acceleration': []}

def simulate_race(horses: List[Horse], race_distance: float = 1600.0, dt: float = 0.1, max_time: float = 300.0):
    """
    競馬シミュレーション
    race_distance: レース距離 (m)  例: 1600m = マイル戦
    dt: 単位時間 (秒)
    """
    t = 0.0
    finished = {horse.name: False for horse in horses}
    
    print(f"=== 競馬シミュレーション開始 ===\n距離: {race_distance}m  単位時間: {dt}秒\n")
    
    while t < max_time and not all(finished.values()):
        print(f"\n時間: {t:.1f} 秒")
        
        for horse in horses:
            if finished[horse.name]:
                continue
                
            # 加速度の計算（シンプルなモデル）
            if horse.velocity < horse.max_speed * 0.7:          # 加速フェーズ
                horse.acc = horse.acceleration
            elif horse.velocity < horse.max_speed:              # 巡航フェーズ
                horse.acc = horse.acceleration * 0.2
            else:                                               # 疲労フェーズ
                horse.acc = -horse.fatigue_factor * (horse.velocity / horse.max_speed)
            
            # 速度と位置の更新（等加速度運動の公式）
            horse.velocity += horse.acc * dt
            horse.velocity = max(0.0, min(horse.velocity, horse.max_speed * 1.05))  # 速度制限
            
            distance_moved = horse.velocity * dt
            horse.position += distance_moved
            
            # 記録
            horse.history['time'].append(t)
            horse.history['position'].append(horse.position)
            horse.history['velocity'].append(horse.velocity)
            horse.history['acceleration'].append(horse.acc)
            
            # 結果表示
            print(f"{horse.name:12s} | 位置: {horse.position:6.1f}m | "
                  f"速度: {horse.velocity:5.1f} m/s ({horse.velocity*3.6:5.1f} km/h) | "
                  f"加速度: {horse.acc:6.2f} m/s² | 移動距離: {distance_moved:5.2f}m")
            
            # ゴール判定
            if horse.position >= race_distance and not finished[horse.name]:
                finished[horse.name] = True
                print(f"★★★ {horse.name} がゴール！ タイム: {t:.1f}秒 ★★★")
        
        t += dt
    
    # 結果まとめ
    print("\n=== レース結果 ===")
    for horse in sorted(horses, key=lambda h: h.position, reverse=True):
        print(f"{horse.name}: {horse.position:.1f}m  (最高速度: {horse.max_speed*3.6:.1f} km/h)")

    return horses

# ====================== 使用例 ======================
if __name__ == "__main__":
    # 馬の能力設定（現実的な競走馬の値に基づく）
    horses = [
        Horse("ディープインパクト風", max_speed=18.5, acceleration=2.8, fatigue_factor=0.15),   # 優秀な先行馬
        Horse("ロードカナロア風", max_speed=19.2, acceleration=3.2, fatigue_factor=0.25),     # スプリンター
        Horse("オルフェーヴル風", max_speed=17.8, acceleration=2.5, fatigue_factor=0.08),     # スタミナ型
        Horse("一般馬A",           max_speed=17.0, acceleration=2.4, fatigue_factor=0.20),
    ]
    
    # 1600mレースをシミュレーション
    result_horses = simulate_race(horses, race_distance=1600.0, dt=0.1)
    
    # グラフで可視化
    plt.figure(figsize=(12, 8))
    
    for horse in result_horses:
        plt.subplot(3, 1, 1)
        plt.plot(horse.history['time'], horse.history['position'], label=horse.name)
        plt.subplot(3, 1, 2)
        plt.plot(horse.history['time'], [v*3.6 for v in horse.history['velocity']], label=horse.name)
        plt.subplot(3, 1, 3)
        plt.plot(horse.history['time'], horse.history['acceleration'], label=horse.name)
    
    plt.subplot(3, 1, 1)
    plt.ylabel('位置 (m)')
    plt.legend()
    plt.grid(True)
    
    plt.subplot(3, 1, 2)
    plt.ylabel('速度 (km/h)')
    plt.grid(True)
    
    plt.subplot(3, 1, 3)
    plt.xlabel('時間 (秒)')
    plt.ylabel('加速度 (m/s²)')
    plt.grid(True)
    
    plt.tight_layout()
    plt.show()
```