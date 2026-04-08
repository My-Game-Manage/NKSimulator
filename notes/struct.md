# ファイルの構成と、簡単なロジックの流れ

main
-> simulator
    <prepare>
    -> provider >> (data/csv) >> @race_data_set
    -> race_factory >> @race_info
    -> horse_factory >> @horse_info
    ↓
    <main-process>
    -> engine
        -> physics >> @(float)
        -> tactics >> @velocity

# 各modelの関係性

- RaceInfo: レースの基本情報（会場名、コース距離、種別など）
  - RaceState: レース処理中の動的データ（経過時間、各馬のState）＞これを記録するとそのstepのスナップショットになる
- HorseInfo: 馬の基本情報（馬の名前、ID、履歴DFも保持）
  - HorseParam: 馬の基本能力（スピード、パワー、スタミナ、脚質など）
  - HorseState: 馬のレース中の動的データ（速度、距離など）
- JockeyInfo: 騎手の基本情報
  - JockeyParam: 騎手の基本能力（名前、ID、履歴DFも保持）

## 命名規則

Info：基本的な情報。公式なデータからそのまま使える値（名前などで、不変なもの）
Param：データから生成できる静的な値（速度など
State：シミュレーションで生成される動的な値（現在の速さや距離など

すべてをmodels以下にdataclassとして作成し、すべてがImmutableとすること
これらにはメソッドは持たせない（プロパティーくらいならいい。読み取り専用）

Infoは固定値
Paramは色々といじってシミュレートできる固定値。これをJupyterで導入できるように調整
Stateはstep毎に変化する結果データ。これを観測すること

計算上はParamは色々な係数や基本となる値
StateはParam等を元に計算した結果やフラグ

基本的には「静的データ」＝Paramを渡して
「動的データ」＝Stateを受け取る
ただし現在のStateも計算には必要なので、Stateも同時に渡す必要あり

RaceStateに一任するか
RaceParamとRaceStateを同時に渡すか
つまりRaceParamはいつも同じ値だけど、テストがしやすくなる（Engineは数値を持たない）

EngineはParamとStateを見ればいい
今は「RaceState」と「RaceInfo」を受け取っている。それぞれ「HorseState」と「HorseInfo」を持っている
HorseはIDで管理して取り出しやすくしたい（順序などが不要のため）

## レース全体で必要なもの

* Info
  - ID
  - 名前
  - 会場
  - コース種別（距離と種類
  - レース番号
  - 出走馬リスト（馬Info）
* Param
  - 馬場
  - 天候
  - コース幅
  - コーナー係数
  - 馬場摩擦係数
  - コースレイアウト
  - チェックポイント（計測用
* State
  - step
  - 経過時間
  - 馬情報の辞書（ID：馬State）
  - 現在の順位リスト（ID）

基本はRaceStateをレース履歴としてHistoryに保存されていく。
結果に必要なものとしては「順位、馬ID、タイム」（その他上がり等）
レース中に必要なもの「距離、各種補正のための係数」

## 個別の馬に必要なもの

* Info
  - ID
  - 名前
  - 枠番
  - 馬番
  - 騎手
  - 過去レースデータ（DataFrame）
* Param
  - 最高速度
  - 加速力
  - 最大スタミナ
  - 消費効率
  - コーナー能力
  - スタート能力
  - 戦略
  - スパート距離
* State
  - step
  - 経過時間
  - 進んだ距離
  - 現在の速度
  - 目標速度（ここに向かって加速していく
  - 残りのスタミナ
  - スパートモードフラグ
  - バテフラグ
  - 位置情報（セクション、レーン
  - ブロックフラグ（前が詰まっているか

## 騎手に必要なもの

（将来的に実装予定）

* Info
  - ID
  - 名前
  - 過去レースデータ（DataFrame）
* Param
  - 最大体力
  - 得意スタイル
  - コーナー能力
  - 追い込み係数
* State
  - 残り体力

## Simulator について

### Prepare：レースの基本データのリストを作成

Provider == (CSV) => [RaceRawData, ...]
Factory
  == (RawData) => [RaceInfo, ...]   => [{h_id: HorseInfo, ...}, ...]
  == (RawData) => [RaceParam, ...]  => [{h_id: HorseParam, ...}, ...]
  == (RawData) => [RaceState, ...]  => [{h_id: HorseState, ...}, ...]




### Run：レースの基本データセットを用いて、1レースずつ、ループを回す

### PostProcess：順位付けや結果の表示、保存など


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


