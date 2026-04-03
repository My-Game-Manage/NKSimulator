# ファイルの構成と、簡単なロジックの流れ

main
-> simulator
    -> race_provider >> @context
    -> horse_provider >> @state, @info, @param
    ↓
    -> engine
        -> physics >> @(float)
        -> tactics >> @velocity

## main.py

RaceSimulatorの呼び出しと、ターゲットとする「日付」「会場名」「レース番号」を渡す

## simulator.py

RaceContext　と　Horse　を生成し、RaceEngine　に渡して、engineを回す

## engine.py

step毎に、馬のリストを回し、physicsとaiを呼び出して、next_stateを作成する
ここではループはせず、1回の処理に限定（ループさせるのはsimulator側）

## physics.py（新設）

物理演算関数の集合体。クラスはなし（Jupyterでテストしやすいように）

## tactics.py

ai以下にあり、HorseStateと周囲の状況（Perception）を受取り、argetVelocity（目標速度）を返す

## models

各dataclass。
Jupyterで asdict() を使って簡単に辞書変換でき、Pandasとの相性が抜群
`HorseState: replace(state, x=new_x)` を使うことで、元の状態を壊さずに「次の状態」を生成


