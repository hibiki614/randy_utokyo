## 原問題
$$ 
max \sum_{j=1}^n\boldsymbol{c^Tx^j} \tag{1}
$$
subject to
$$
\begin{align}
\sum_{j=1}^n\boldsymbol{A^jx^j}=\boldsymbol{b} \tag{2} \\
\boldsymbol{B^jx^j}=\boldsymbol{b^j} \tag{3} \\
\boldsymbol{x^j}\geq\boldsymbol{0} \tag{4} \\
\end{align}
$$

事業部プログラムの解集合$S_j$は，以下で定義される.(有界であると仮定)
$$
S_j=\{\boldsymbol{x^j} |\boldsymbol{x^j}\geq \boldsymbol{0}, \boldsymbol{B^jx^j}=\boldsymbol{b^j} \}
$$
まず，事業部プログラムは以下のように与えられる．
$$ 
max \quad \boldsymbol{(c^T-u^TA^j)x^j} \tag{5}
$$
subject to
$$
\begin{align}
\boldsymbol{B^jx^j}=\boldsymbol{b^j} \tag{6} \\
\boldsymbol{x^j}\geq\boldsymbol{0} \tag{7} \\
\end{align}
$$
ただし$u$はm次元ベクトルとする．
最適値$\boldsymbol{\overline{x^j}}$が得られたとき，基底変数の番号の集合を$\overline{M_1^j}$非基底変数の番号の集合を$\overline{M_2^j}$とする．
また以下のように基底行列，基底変数ベクトルを$h\in\overline{M_1^j}$で定義する．
$$
\begin{align}
\boldsymbol{\overline{A_1^j}}=(a^j_{ih}) \\
\boldsymbol{\overline{B_1^j}}=(b^j_{ih}) \\
\boldsymbol{\overline{x^{jM_1}}=(\overline{x^j_h})}
\end{align}
$$
また，$\boldsymbol{A^{jh}}$，$\boldsymbol{B^{jh}}$を$\boldsymbol{A^j}$，$\boldsymbol{B^j}$の第$h$列とする．以上から式(6)を書き直す．
