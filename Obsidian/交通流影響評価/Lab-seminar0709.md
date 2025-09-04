## 構成
- 1台でのシミュレーションの研究
- 交通流と燃料消費量の関係
	- 予測される仮説
- 完全自動運転を想定しがち(既往研究レビュー)
	- 予測される仮説
- MicroAvenueそれ自体の説明
	- なぜこのシミュレーターか
- 計算の仕組みについて
	- バッチファイル詳しい人いませんか，，，
	- 並列計算したいんだけどうまくいかない，誰か助けて，，，
- 今後
	- 今回は評価指標は交通流と燃料消費量，シナリオは普通車とバスの低速と超低速，施策は路側帯
	- 追加の評価指標/シナリオ/施策はないか？
	- 今後の展望
		- 信号制御/都市間比較/歩行者も入れる
## 社会実装の話
- 社会実験めちゃくちゃされてるよね
- テスラやWeimoの登場
- 社会受容性の問題があるのでそう簡単に導入するのは無理
- もし自動運転をいれたらどうなるかを定量的に示すとともにその施策を検討できるような枠組みが求められる
## 既往研究のレビュー

### 自動運転の研究
- 分類(レビュー論文あると良いが)
	- どのような自動運転を想定しているか？
		- 完全自動運転が多いのではないか
		- どのような技術レベルが想定されているか
	- 理想状態が多く社会実装のための研究はもっとたくさん必要
### 柏の葉のバスによる交通流への影響評価
- 柏の葉-柏キャンパスの自動運転シャトルバス(レベル4)が及ぼす柏の葉キャンパス周辺のネットワークへの影響評価
- 6つのケースでシミュレーションを実施
	- 自動運転無し施策無し
	- 自動運転あり施策なし
	- 自動運転あり施策あり
- いずれも大きな影響はなかった
	- バス1台程度なら社会実装しやすい
	- 1台だから影響が少なかったはず
	- 台数を増やしてシミュレーションを行うことが必要
### ACCの論文
- 車間距離(交通量)とACC稼働率(自動運転の割合)の条件ごとに渋滞はどのようになるか
- それと燃料消費量の関係はどのようになるか
	- トレードオフがあるはず
- EVを部分的に入れたときの影響
	- ガソリン車の影響でかえって悪化する説
		- 自動運転と普通車の混在に似てる(これは交通流の話だが，，，)
- 交通流それ自体の分析
	- 中途半端な状態だとかえって悪化する
	- 技術に依存する？
- CO2と合わせた分析
	- 一致しないとはどういうことか
- 「影響」と言っても社会実装のためには複数の側面で評価する必要性がある
- 今回のシミュレーションでは， 渋滞損失時間の削減や平均速度の向上，ガソリン車の燃料消費量の削減を目的とするなら，車間時間が1.0秒から概ね1.9秒~2.2秒までの場合はACC稼働率はより向上させることが望ましいことがわかった．一方，車間時間2.5秒から2.8秒においては，渋滞損失時間削減が目的なら，ACC稼働率は低い方が良く，平均速度向上やガソリン車の燃料消費量削減が目的であれば，ACCは普及させないか，あるいは100%近く普及させるのが望ましい．EVにおける電力消費量削減を目的とするなら，加減速を抑えるために，より車間を開け，ACCを普及するのが望ましい．

このように，従来のガソリン車で望ましいとされてきた条件についても，EVの普及を前提とするならば，再考の余地があることが示された．これはガソリン車とEVでエネルギー消費量が少なくなるメカニズムが異なるためである．



## そこで本研究では
### 分析しなきゃいけないこと
- 交通流
	- 普通車と自動運転車の割合+インフラ施策
- 燃料消費量
	- ガソリン車とEVの割合
- すべてガソリン車の時エネルギー消費量はどうなるか
- すべてEVの時消費量はどうなるか
- おそらくガソリンとEVで挙動が異なるはず
- EVの場合自動運転になればなるほど滑らかな走行が多くなるので消費量は下がる
- ガソリン車の場合特に混在による速度の低下により悪化？
- この辺を詰めて追加シナリオ考え直して議論できれば
- 自動運転の台数/EVの台数を変えながら交通流と燃料消費量のシミュレーション
- 交通流と燃料消費量の関係
- 自動運転車比率と
- シナリオは以下の通り
- 仮説としては

## 計算
- MicroAvenueについて
- ファイルの構成
- 各乱数のファイルがあり20個の結果が出る
	- これを並列実行したい
	- いまこんな感じ
	- コア数を決められない
	- 時間がかかる...

## 今後
- これじたいはITSシンポに出す
- 様々な発展の方向性がある
	- 評価指標/シナリオ/施策を増やす
	- 都市間比較
	- 信号制御
	- 歩行者
	- ネットワークデザイン

発表原稿
## 🔷 Title Slide
 
Today, I’d like to share with you the progress of my current research on the impact of autonomous vehicles on traffic flow and fuel consumption.

---

## 🔷 Slide: Structure

This presentation is structured as follows:

1. Background of the research
    
2. Review of previous research
    
3. My own research
    
4. Future work and discussion
    

---

## 🔷 Slide: Advancement of Autonomous Driving

Let me begin with the background.

Autonomous driving technology has been rapidly evolving in recent years.  
We see the rise of companies like Tesla and Waymo, and more recently, concepts like **vehicle-to-infrastructure communication** are drawing attention as well.

---

## 🔷 Slide: Social Implementation Is Still a Challenge

However, despite technological advances, **real-world implementation remains a major challenge**.

Across Japan, many demonstration experiments are currently underway.  
There is a strong need for research that clarifies the **social and environmental impacts** of introducing autonomous vehicles, and supports evidence-based policymaking.

---

## 🔷 Slide: Previous Study ① – Autonomous Bus in Kashiwanoha

One example of such prior research is a simulation-based study evaluating the effects of an autonomous shuttle bus in the Kashiwanoha area.

Although the actual shuttle bus in operation was **level 2**, the simulation was conducted under the assumption of a **level 4** autonomous vehicle, in preparation for future implementation.

---

## 🔷 Slide: Scenario Setup and Results

In this study, three main scenarios were considered:

1. No autonomous vehicle
    
2. Autonomous vehicles present, but **without any supporting policies**
    
3. Autonomous vehicles present, with supporting policies, such as traffic control improvements, vehicle-to-infrastructure coordination, and designated roadside parking spaces
    
(次のスライド)
The result showed that there was **no significant difference** in traffic flow among the scenarios.
The authors speculated that this was likely because **only one autonomous vehicle** was operating.  
This suggests the importance of increasing the number of autonomous vehicles in the simulation to properly assess their impact.

---

## 🔷 Slide: Previous Study ② – Adaptive Cruise Control (ACC)

Another important prior study analyzed how **adaptive cruise control (ACC)** affects traffic and fuel consumption.

Two simulation models were used:  
one for **traffic flow**, and one for **fuel/energy consumption**.

The following four questions were addressed:

1. How do ACC penetration rate and following distance affect traffic flow?
    
2. How do these conditions affect fuel consumption for gasoline vehicles?
    
3. How do they affect energy use for EVs?
    
4. Under various EV adoption rates, what strategies best reduce energy consumption?
    

---

## 🔷 Slide: Result – Traffic Flow

When the distance between vehicles is short, more ACC leads to higher speed.  
But when the distance is long, speed goes down first and then increases again as ACC reaches full adoption.

---

## 🔷 Slide: Result – Gasoline Vehicles

In the case of gasoline vehicles, higher speeds resulted in **lower fuel consumption**, which is consistent with expectations.  
(画像)

---

## 🔷 Slide: Result – Electric Vehicles

For electric vehicles, however, the trend was different.  
Greater following distances led to better energy efficiency, likely due to **reduced acceleration and deceleration**.  
(画像)

---

## 🔷 Slide: Summary of Considerations

To summarize:

- **Gasoline vehicles** are more sensitive to speed.
    
- **EVs**, on the other hand, are more sensitive to acceleration changes.
    

for gasoline vehicles, there were some cases where **a lower ACC adoption rate** was better, but for EVs, **a higher ACC adoption rate** always resulted in better efficiency.

This may provide valuable insights for **future autonomous vehicle strategies**.

---

## 🔷 Slide: My Research – Motivation and Scope

Building on these insights, my research focuses on simulating the effects of **increasing the number of autonomous vehicles** in the Kashiwanoha network.

I analyze **both traffic flow and energy consumption**, considering both gasoline vehicles and EVs.

---

## 🔷 Slide: Key Analysis Points

In terms of **traffic flow**, I aim to understand:

- How traffic flow changes with different autonomous vehicle penetration rates
    
- How different speed settings for autonomous vehicles impact flow, especially from a safety perspective
    
- How infrastructure improvements affect the overall traffic condition
    

For **fuel/energy consumption**, I will analyze:

- The case where all vehicles are gasoline-powered
    
- The case where all are EVs
    
- The impact of infrastructure improvements in both cases
    

---

## 🔷 Slide: Hypotheses

My hypotheses are:

- For traffic flow, autonomous vehicles might **worsen congestion** if not properly coordinated.
    
- For fuel consumption:
    
    - **Gasoline vehicles** may consume more fuel due to reduced speeds in mixed traffic.
        
    - **EVs**, however, may improve efficiency **as the autonomous vehicle share increases**, due to smoother driving behavior.
        

---

## 🔷 Slide: Simulation Scenarios

 In this study, several scenarios were developed to evaluate the effects of autonomous vehicles and infrastructure measures.

First, we introduced an **infrastructure policy** that adds designated parking and stopping spaces to reduce the impact of parked vehicles on traffic flow.

**Scenario No.1 and No.2** assume **no autonomous vehicles**, with and without the infrastructure policy.

**Scenario No.4 to No.8** assume that **all buses on the Kashiwanoha–UTokyo route are replaced by autonomous buses**.  
To account for safety considerations, AVs operate at **reduced or very low speeds** in these scenarios.

**Scenario No.9 to No.14** focus on **replacing a certain percentage (X%) of private vehicles with AVs**.  
The percentage is varied across different cases to analyze the impacts.

---

## 🔷 Slide: Simulation Setup

The simulation includes 20 random files per scenario.

Each scenario includes:

- Simulation execution
    
- Data conversion for submission
    
- Data compression due to file size
    
- Deletion of raw output files
    

I currently use **batch files** to automate this, but due to the heavy processing load of each simulation, **parallelization has limited effect**.

---

## 🔷 Slide: Future Plans

This research is intended for submission to the **JSCE Autumn Conference** or the **ITS Symposium**.

The timeline is as follows:

- July: Literature review
    
- July–August: Simulation runs
    
- August–October: Analysis
    
- November or December: Final presentation
    

---

## 🔷 Slide: Future Challenges and Discussion Points

There are many possible extensions to this work:

- Additional scenarios and evaluation metrics
    
- Comparison between different cities or regions
    
- Optimization of traffic signal control
    
- Inclusion of pedestrian interactions
    
- Network design for autonomous-friendly infrastructure
    

I would love to discuss these ideas further with you today.

---

## 🔷 Closing

That concludes my presentation.  
Thank you very much for your attention.