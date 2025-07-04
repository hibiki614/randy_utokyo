# はじめに
## 多品種流問題の難しさ
- 商品間の相互作用を考慮すると，single-commodityの問題を繰り返し解く必要がある
	- 各品種ごとに独立して解けないということ
## 既往研究
- 多品種流問題の特殊な構造とスパース性を用いたLPのアルゴリズム(そのままだと問題が大きすぎる)
- classicalなものは①price-directive decomposition, ②resource-directive decompositions, ③partitioningの3つで，すべてシンプレックス法に基づく
	- Assad (1978), Kennington (1978), and Ali et al. (1980)がいいらしい
- 近年は内点法か並列アルゴリズムに関するもの
	- 内点法はChoi and Goldfarb (1989) and Bertsimas and Orlin (1991)
	- 並列アルゴリズムはChoi and Goldfarb (1989) as well as Pinar and Zenios (1990)
## スケーリングとは(最適化ハンドブックp227より)
- ビットスケーリングについて
- 最大リンク容量がKビットであるとき，各リンク容量をKビット2進数で表して，まず最初の1ビット目のみの問題$P_1$を解く．得られた最適解を初期解として，最初の2ビットのみの問題$P_2$を解く．これを繰り返す．なぜこれが早くなるかは[[計算時間]]を参照．
### 本研究に戻ろう
- $x$が最適解となるように容量制約またはコスト係数を$\epsilon$だけ動かせるとき，(たぶん[[感度分析]])$x$を「$\epsilon$-optimal」という
- 簡単な問題を，まずは解いていって，得られた解を初期解として．もう少し原問題に近い問題を解く．これを繰り返す
	- min-cost flowに初めて用いたのがEdmonds and Karp (1972) and Dinic (1973)
	- いろんな問題に使ったのがGabow (1985) 
	- 中でも「$\epsilon$-optimal」の考え方が一番効率的で，minimum cost flow (Goldberg and Tarjan 1987, Ahuja et al. 1992, and Orlin 1988) and maximum flow (Ahuja et al. 1989)という感じ
	- これらはすべてsingle-commodity
- 「$\epsilon$-optimal」をmulti-commodityに用いた研究も結構ある
	- Grigoriadis and Khachiyan (1991), Klein et al. (1990a), Leighton et al. (1991), Klein et al. (1990b), and Shahrokhi and Matula (1990)など
	- 精度の良いワーストケース限界を見つけることに焦点を与えている
### 本研究では
- 多品種流問題を一連のpenalty problemとして解く
	- 各問題は容量制約を緩和したうえで，違反に対する条件を付与
	- 詳しくはFiacco and McCormick 1968
	- 「閉路上のフローを動かす」というのが中心的な構成要素
	- 近年の研究といい勝負で，Barnhart (1993), Barnhart and Sheffi (1993), and Farvolden et al. (1993) are based on dual-ascent methods, the primal-dual approach, and partitioning method, respectivelyですよ
- 1章ではペナルティ法と定式化について，それからアルゴリズムについて．2章では最適性条件について．3章では理論的特性の紹介とその説明，4章で計算結果，5章で他のネットワーク問題への展開
# 1. THE SCALING ALGORITHM FOR THE PENALTY PROBLEM
## 問題設定
- many to manyの問題はone to one にできる．
	- super source(sink)ノードから各source(sink)ノードへダミーリンク(容量が需要量に一致し，コストがゼロ)が接続していると考える
- 定式化は式(1)~(4)のように与えられる．
- 容量制約をペナルティ項として$e_{ij}(x)=max\{0, (\sum_{k=1}^Kx_{ij}^k-u_{ij})\}$と定義すればpenalty problem(PMM(ρ))は式(5)(2)(4)のように与えられる．
## アルゴリズム
- 残余ネットワークを作り負閉路消去法によって最適解を求める．
- 残余ネットワークのリンクコストは式(6)~(11)で与えられる
### 条件設定
- 初期解は各起点から終点の最短経路にすべてのフローが存在するとすればよい
- $\delta$，$\rho$，$R$
	- $\delta$は最も大きい需要量を，最も近い2のべき乗数まで切り上げたものを初期値とし，2で割っていく
	- $\rho$，$R$は経験的に得られた値で，$\rho=\rho R$として値を更新する
- 収束判定は$\delta*\rho$か双対ギャップで判定
- アルゴリズムの全体像はFigure2の通り
# 2. OPTIMALITY CONDITIONS
