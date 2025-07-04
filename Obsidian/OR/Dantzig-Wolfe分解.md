# まずはDantzig and Wolfe(1961)
- リンクはこちら：https://www.jstor.org/stable/1911818?seq=1
## 1. Decomposed Linear Program

- 主問題のLPを子問題に分解する．子問題同士を結び付ける制約は主問題の制約よりはるかに少ない．
### 主問題$P_1$の定式化
$\boldsymbol{P_1}$
$$
min \ \sum_{j}c_jx_j \tag{1}
$$
subject to 
$$
\begin{align}
\sum_j\boldsymbol{A_jx_j}=\boldsymbol{b} \tag{2} \\
\boldsymbol{B_jx_j}=\boldsymbol{b_j}\ ,\forall \ j \tag{3} \\
\boldsymbol{x_j}\geqq0 \ ,\forall \ j \tag{4}
\end{align}
$$
- $\boldsymbol{A_j}$は$m×n_j$行列，$\boldsymbol{B_j}$は$m_j×n_j$行列，$\boldsymbol{c_j}$は$n_j$列ベクトル，$\boldsymbol{x_j}$は$n_j$行ベクトル
- $\boldsymbol{c}$は$\boldsymbol{c_j}$に分解される，$\boldsymbol{b}$は$m$行ベクトル，$\boldsymbol{b_j}$は$m_j$行ベクトル
- 結果として，変数$\sum_j{n_j}$個，制約$m+\sum_j{m_j}$個の線形計画問題となる．
- <b>式(3)はそれぞれの子問題を構成する独立なもので，式(2)はすべての子問題をつなぐもの</b>
- 有界(と仮定する)な解集合$S_j$を用意する．
$$
S_j = \{\boldsymbol{x_j}|\boldsymbol{x_j} \geq0, \ \boldsymbol{B_jx_j} = \boldsymbol{b_j}\} \tag{5}
$$
- 分解した問題をn変数の一般的な線形計画問題として記述する．このとき記述された問題では，$A_j$は固定されておらず集合(5)の範囲内で自由に決まる．
## 2. The Extremal problem
- 凸多面体$S_j$の端点の集合を$W_j$として以下のように定義する．
$$
W_j=\{x_{j1},\cdots,x_{j{K_j}}\} \tag{6}
$$
- また，$P_{jk}=A_jx_{jk}, c_{jk}=c_jx_{jk}(k=1,\cdots, K_j)$とすると，最適化問題は以下のように書ける．
- これは，分解された問題を$P_1$と同じように書いただけである．
$\boldsymbol{P_2}$
$$
min. \sum_{j, k}c_{jk}s_{jk} \tag{7}
$$
subject to
$$
\begin{align}
	\sum_{j,k}P_{jk}s_{jk}=b, \ s_{jk}\geq0, \forall{j, k} \tag{8}\\
	\sum_ks_{jk}=1 , \forall{j}\tag{9}
\end{align}
$$
なお，以下の補題1が成立するものとする．
$\textbf{補題1}$
$\{s_{jk}\}$が$P_2$の解となるとき，ベクトル
$$
s_j=\sum_kx_{jk}s_{jk}
$$
は主問題$P_1$の解となる．
これは，主問題の解を凸包の端点の凸結合の形で表現しているだけである．詳しくはこちらを参照されたい．
$P_2$の制約の数はm+n個となる．これだけでも，$m_j$が大きい場合計算コストはかなり小さくなる．
しかし，各$\boldsymbol{x_j}$に対しすべての端点を列挙し凸結合で表現するため，計算コストが大きくなるということを考慮できていない．
## The Decomposition Algorithm
- 「普通，大量にある$\sum_{K_j}$個の変数のうち，解に影響するのはごくわずかであるはずだ」というのが本研究のコンセプト．→nを減らせる
- 考慮すべき変数に対してのみ，係数行列を生成してやればよい．→mを減らせる
- 係数の生成は多品種流のこの論文で解説されている：https://www.jstor.org/stable/30046144?seq=1
- 縮退現象を回避する方法は別途紹介されているので，本研究では考えない．
- シンプレックス法と同様の考え方を使うことができる．
- 制約式はm+n本あるので，基底変数の数はm+n個(m+n列できる)
- 1つ目の制約に対して価格ベクトル$\boldsymbol{\pi}$，2つ目の制約に対して価格ベクトル$\boldsymbol{\tilde{\pi}}$を設定すると，被約費用$\delta$は以下のようにあらわせる．
$$
\delta=\boldsymbol{c_{jk}}-\boldsymbol{\pi P_{jk}}+\boldsymbol{\tilde{\pi_j}}
$$
- これが負である非基底変数を基底変数に追加していき，すべての非基底変数の被約費用が非負となれば最適値．
### アルゴリズム
- これを本問題に適応する方法を述べていく
①まず，主問題の実行可能解を見つける(基底変数を制約m+n本定めるだけで解ける)
②双対変数を計算する
③各$j$に対して以下の最小化問題を立てる($\boldsymbol{\tilde{\pi_j}}$は各$j$で一定)
$$
min. (c_{j}-\pi \boldsymbol{A_j})\boldsymbol{x_j}
$$
subject to
$$
\begin{align}
	\boldsymbol{B_{j}x_{j}=b_j}, \ \boldsymbol{x_{j}\geq0}, 
\end{align}
$$
- 得られた最適解$\boldsymbol{\overline{x_j0}}$に対して$\delta$を計算し，符号を確認する．
- 負である場合これを新たな列として追加する
- 主問題の双対変数を計算しなおす．
- すべての$\delta$が非負になるまでシンプレックス法のルールに基づきこれを計算する
