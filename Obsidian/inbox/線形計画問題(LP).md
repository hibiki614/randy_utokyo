# シンプレックス法
## 標準形
$$
max \ \sum_{j=1}^nc_jx_j
$$
subject to
$$
\begin{align}
	\sum_{j=1}^na_{ij}x_j\leq b_i, \ i=1,\cdots,m \\
	x_j\geq0, \ j=1, \cdots, n
\end{align}
$$

- 最小化問題の場合-1倍して最大化問題へ
- 非負制約のない時は非負制約のついた2つの変数を用いて$x_j=x_j^{+}-x_j^{-}$とする
- 等式制約$\sum_{j=1}^na_{ij}x_j= b_i$は$\sum_{j=1}^na_{ij}x_j\leq b_i$と$\sum_{j=1}^na_{ij}x_j\geq b_i$に置き換える
- 不等号が逆向きなら両辺を-1倍する
## 概要
- 非負制約以外の制約がm本，変数がn本の時，実行可能領域はn次元空間内の凸多面体となる．
- 最適解が存在するとき，少なくとも１つの最適解は凸包の端点上にある．(凸包が有界な時)
- シンプレックス法はある端点から出発して，制約式を1本のみ入れ替えて隣の端点へ移動していく
## 方法
- 不等式制約に対してスラック変数を導入する．
- スラック変数を含めてm+n個の変数の中から，制約の本数に対応するm個の変数を基底変数として選び，それ以外の変数(非基底変数)を0にすることにより，基底変数が定まる．
- 目的関数は非基底変数と定数項の線形和で表され，非基底変数の係数が正であるとき，まだ増やせる余地があることを意味する．よってこれを基底変数に追加し，基底変数から1つ削除する．この時削除するのは，一番早く非負制約が効いてしまうものにする．
- これを繰り返す．
## 原理
- スラック変数を入れたうえで行列表記すると定式化は以下のようになる．
$$
max \ \boldsymbol{c^Tx}
$$
subject to
$$
\begin{align}
	\boldsymbol{Ax}=\boldsymbol{b} \\
	\boldsymbol{x}\geq \boldsymbol{0}
\end{align}
$$
- 要素数mの基底変数ベクトル$\boldsymbol{x_B}$，係数ベクトル$\boldsymbol{c_B}$，m×mの部分行列$\boldsymbol{B}$を設定
- 要素数n-mの非基底変数ベクトル$\boldsymbol{x_N}$，係数ベクトル$\boldsymbol{c_N}$，m×(n-m)の部分行列$\boldsymbol{N}$を設定
- 特に$\boldsymbol{B}$が正則であるとき，$\boldsymbol{B}$を基底行列，$\boldsymbol{N}$を非基底行列といい，これらはもともとの制約の行列$\boldsymbol{A}$の列を構成するものであり，以下が成り立つ．
$$
\boldsymbol{Ax}=
\begin{pmatrix}
\boldsymbol{B} & \boldsymbol{N}
\end{pmatrix}
\begin{pmatrix}
\boldsymbol{x_B} \\
\boldsymbol{x_N}
\end{pmatrix}
=\boldsymbol{Bx_B}+\boldsymbol{Nx_N}=\boldsymbol{b} \tag{1}
$$
- 同様に目的関数は以下のようになる
$$
\boldsymbol{z}=
\begin{pmatrix}
\boldsymbol{c_B^T} & \boldsymbol{c_N^T}
\end{pmatrix}
\begin{pmatrix}
\boldsymbol{x_B} \\
\boldsymbol{x_N}
\end{pmatrix}
=\boldsymbol{c_B^Tx_B}+\boldsymbol{c_N^Tx_N} \tag{2}
$$

- (1)式の両辺に左から$\boldsymbol{B^{-1}}$をかけて
$$
\boldsymbol{x_B}=\boldsymbol{B^{-1}b} - \boldsymbol{B^{-1}Nx_N} \tag{3}
$$
- (3)式を(2)式に代入して
$$
\begin{align}
\boldsymbol{z}
&=\boldsymbol{c_B^T(\boldsymbol{B^{-1}b} - \boldsymbol{B^{-1}Nx_N})}+\boldsymbol{c_N^Tx_N}  \\
&=\boldsymbol{c_B^TB^{-1}b}+(\boldsymbol{c_N^T-c_B^TB^{-1}N})\boldsymbol{x_N}
\end{align}
$$
- よって基底解に対応する辞書は
$$
\begin{align}
\boldsymbol{z}
&=\boldsymbol{c_B^TB^{-1}b}+(\boldsymbol{c_N^T-c_B^TB^{-1}N})\boldsymbol{x_N} \\
\boldsymbol{x_B}&=\boldsymbol{B^{-1}b} - \boldsymbol{B^{-1}Nx_N} 
\end{align}
$$

- $\boldsymbol{x_N}=\boldsymbol{0}$と固定すると基底変数が$\boldsymbol{x_B}=\boldsymbol{B^{-1}b}$と一意に定まる．
## 求解アルゴリズム
### 追加する非基底変数の選び方
- 非基底変数の係数$\boldsymbol{\overline{c_N}}=\boldsymbol{c_N^T-c_B^TB^{-1}N}$がポイントで，これを**被約費用(reduced cost)**という
- また，$\boldsymbol{\overline{b}}=\boldsymbol{B^{-1}b}$，$\boldsymbol{\overline{N}}=\boldsymbol{B^{-1}N}$とすると，辞書は以下のように書き換えられる．
$$
\begin{align}
\boldsymbol{z}
&=\boldsymbol{c_B^T\boldsymbol{\overline{b}}}+\boldsymbol{\overline{c_N}^T}\boldsymbol{x_N} \\
\boldsymbol{x_B}&=\boldsymbol{\overline{b}}- \boldsymbol{\overline{N}x_N} 
\end{align}
$$
- $\boldsymbol{\overline{c_N}}$は上式の通り，対応する非基底変数を1増やした時目的関数がどれほど改善するかを表している．
- よって最大化問題においては，最大の$\overline{c_j}$をもつ非基底変数$x_j$を，他の非基底変数を0に保ちながら新たな基底変数として追加すればよい．
- 最終的に$\boldsymbol{\overline{c_N}}\leq0$となれば終了．
### 削除する基底変数の選び方
- 新たに$x_k$を基底変数に追加することを考える．$\boldsymbol{\overline{a_k}}$を$x_k$に対応する$\boldsymbol{\overline{N}}$の列とすると，目的関数と基底変数の値は以下のようになる
$$
\begin{align}
\boldsymbol{z}
&=\boldsymbol{c_B^T\boldsymbol{\overline{b}}}+\overline{c_k}\theta \\
\boldsymbol{x_B}&=\boldsymbol{\overline{b}}- \boldsymbol{\overline{a_k}\theta} 
\end{align}
$$
- $\boldsymbol{x_B}\geq0$を満たす必要があるので，非基底変数$x_k$の値は
$$
\theta=min \left\{\frac{\overline{b_i}}{\overline{a_{ik}}}\middle|{\overline{a_{ik}}>0, i\in{\boldsymbol{B}}} \right\}
$$
までしか増加できないことがわかる．
- $\frac{\overline{b_i}}{\overline{a_{ik}}}=\theta$を満たす基底変数$x_i$の値は0となり，基底変数と非基底変数が入れ替わる．
### 改訂シンプレックス法
- 実際に必要な情報は，被約費用$\boldsymbol{\overline{c_N}}$と$\overline{c_k}>0$を満たす非基底変数$x_k$に対応する列$\boldsymbol{\overline{a_k}}$だけである．
- そこで，まず$\boldsymbol{y}=(\boldsymbol{B^{-1}})^T\boldsymbol{c_B}$を計算して，$\boldsymbol{\overline{c_N}}=\boldsymbol{c_N^T-N^Ty}$を計算する．このとき$\boldsymbol{y}$は双対変数であり，**潜在価格(シャドウコスト)**という．
## 双対問題との関連
- 主問題$P_1$
$$
max \ \boldsymbol{c^Tx}
$$
subject to
$$
\begin{align}
	\boldsymbol{Ax}=\boldsymbol{b} \\
	\boldsymbol{x}\geq \boldsymbol{0}
\end{align}
$$
に対する双対問題$D_1$
$$
min. \ \boldsymbol{b^Ty}
$$
subject to
$$
\boldsymbol{A^Ty}\geq\boldsymbol{c}
$$
を設定する．
### 弱双対定理
$\boldsymbol{x}$と$\boldsymbol{y}$がそれぞれ$P_1$，$D_1$の実行可能解ならば，以下が成り立つ
$$
\boldsymbol{c^Tx}\leq \boldsymbol{b^Ty}
$$
(証明)
$$
\boldsymbol{c^Tx}\leq \boldsymbol{(A^Ty)^Tx}=\boldsymbol{y^T(Ax)}=\boldsymbol{b^Ty}
$$
### 強双対定理
主問題$P_1$に最適解$\boldsymbol{x^*}$が存在するとき，双対問題$D_1$にも最適解$\boldsymbol{y^*}$が存在し，以下が成り立つ．
$$
\boldsymbol{c^Tx^*}= \boldsymbol{b^Ty^*}
$$
(証明)
最適値は以下のように表せる．
$$
\boldsymbol{c^Tx^*}=\boldsymbol{c_B^TB^{-1}b}+(\boldsymbol{c_N^T-c_B^TB^{-1}N})\boldsymbol{x_N^*}
$$
$\boldsymbol{x^*}$は最適基底解なので$\boldsymbol{\overline{c_N^T}}=\boldsymbol{c_N^T-N^T(B^{-1})^Tc_B}\leq0$が成り立つ．
$\boldsymbol{A=(B \ N)}$より以下が成り立つ．
$$
\begin{align}
(\boldsymbol{c_N}+\boldsymbol{c_B})-\boldsymbol{c_B}-\boldsymbol{N^T(B^{-1})^Tc_B}
=\boldsymbol{c}-\boldsymbol{A^T(B^{-1})^Tc_B}\leq0
\end{align}
$$
