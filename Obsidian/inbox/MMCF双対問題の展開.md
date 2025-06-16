date: 2025/02/14
topic: [[right_angle_ue]]
contents:

# そもそもの定式化 $D_1$

$$\max_{\boldsymbol{\theta,\lambda}}{\sum_{t\in T}{\sum_{s\in S}{d_{st}\theta_{st}}}-\sum_{a\in A}{u_
{a}\lambda_a}}$$
$\text{subject to}$
$$c_{ij}+\theta_{si}+\lambda_{ij}-\theta_{sj} \geq 0 \quad \forall i,j\in A^s, s\in S$$
- 本当は制約は$c_{ij}+\theta_i^s+\lambda_{ij}-\theta_j^s \geq 0 \quad \forall i,j\in A, s\in S$
	- すべてのリンクを対象にする必要あり．でも問題がデカくなるので，通過するリンクのみを考えればいい．だから，列生成で解きますよ，という流れ．
- 最終形にたどり着くには，これを列生成で解くというスタンスが必須．
	- $A^s$が起点$s$で通過するリンクの集合としておき，これを（行）列生成で増やしながら，つまり成約を増やして目的関数を悪化させる方向で最適解を見つける感じになる．
- なので，RMPはこの問題，子問題は使うリンクを特定する問題．というのがこの段階で明確になる．
	- 最短経路木でノードポテンシャルを見て，追加するリンクをみつける感じね．このスタンスは話してた通り．

- $D_1$について，以下を考えてみよう．
	- 列生成繰り返しのイテレータを$n$としたとき，$n$回目のRMPで得られた解を$\theta_{si}^n, \lambda_{sij}^n$と書こう．
		- $n+1$回目と$n$回目の変化量を新たに定義して，$\dot{\theta}_{si}^{n+1} = \theta_{si}^{n+1} -\theta_{si}^{n}$としよう．同様に$\dot{\lambda}_{sij}^{n+1} = \lambda_{sij}^{n+1} -\lambda_{sij}^{n}$
		- この定義は，あとで出てくる．
	- 制約条件について，成立している要件．
		- **使用しているリンクのみを考慮したとき，制約条件は等式で成立する．**
			- corollaryとして書いておく．D_1より前に相補性条件の話をしているはずなので．
- とすれば，
$$c_{ij}+\theta_{si}^n+\lambda_{ij}^n -\theta_{sj}^n = 0 \quad \forall i,j\in A^s, s\in S$$
$$c_{ij}+\theta_{si}^{n+1}-\dot{\theta}_{si}^{n+1}+\lambda_{sij}^{n+1}-\dot{\lambda}_{sij}^{n+1}-\theta_{sj}^{n+1}+\dot{\theta}_{sj}^{n+1} = 0 \quad \forall i,j\in A^s, s\in S$$
ここで，Corollaryより，$c_{ij}+\theta_{si}^{n+1}+\lambda_{sij}^{n+1}-\theta_{sj}^{n+1}=0$であるから，
$$-\dot{\theta}_{si}^{n+1}-\dot{\lambda}_{sij}^{n+1}+\dot{\theta}_{sj}^{n+1} = 0 \quad \forall i,j\in A^s, s\in S \tag{1}$$
が成立する．

- reduced costの話．
	- $n+1$ 回目のRMPで得られる$\boldsymbol{\lambda}$を考慮した子問題で得られたノードポテンシャル（これ変数定義$\theta$じゃないのに変えておいたほうがいいかも:とりあえず$\rho^n$）を考えたとき，$\Delta_{ij}$はreduced costで，
　$$c_{ij}+\rho_{si}^{n+1}+\lambda_{ij}^{n+1}-\rho_{sj}^{n+1} = \Delta_{sij}^{n+1} \quad \forall i,j\in A^s, s\in S$$
とかける．加えて，reduced costが結果的には最終ノードのポテンシャル差のことを指す（これもRemmaか，，，corollaryが要る）ため，
$$\dot{\theta}_{si}^{n+1} = \Delta_{sij}^{n+1}$$

のはず．
- ここで，$J_s^n=\{j\mid \Delta_{sij}^n \neq 0 \quad ij\in A \}$として，reduced costが負の値（やんな？）になっているリンクの終端点を集合にしておく．
- $j\in J_s^n$までの$s$からの経路を考えよう．複数の経路が存在しうる．木でない限りね．
	- $(s,j)$経路の集合を$P_{sj}$としましょう．

## こっからが大事．
- ある経路$p\in P_{sj}$を考えて，含まれるリンクを並べてみよう．(e.g., $(h,i),(i,k),(k,l)\dots (n,j)$)
- では，右辺がそれぞれ0であるから，この並べたリンクそれぞれの制約左辺を全てを足し合わせたときもまた0である．これを実行すると，接続するノードの$\dot{\theta}_{si}^{n+1}$は次々消えて，起点のポテンシャルが0であることを着目すると，結果的に
$$0-\sum_{ij\in p}{\dot{\lambda}_{sij}^{n+1}}+\dot{\theta}_{sj}^{n+1}=0$$
になるので，
$$\sum_{ij\in p}{\dot{\lambda}_{sij}^{n+1}}=\Delta_{sij}^{n+1}$$
### これ，わかる？直列のパターンそのものになってる．
- この前は直列のパターンで話をしていたけど，経路として考えたらわかりやすくて，例えば，$p_1,p_2\in P_{sj}$としたとき，
$$\sum_{ij\in p_1}{\dot{\lambda}_{sij}^{n+1}}=\sum_{ij\in p_2}{\dot{\lambda}_{sij}^{n+1}} \tag{2}$$
になるわけで，しかも$\tilde{A}=p_1\cap p_2$を考える，つまり，経路で同じリンクを含むのであれば，そいつらに対応する$\lambda$は左右それぞれに配置されており，消えていくわけなので，残るのは，**並列関係にあるものだけ**．
- こうなると，並列関係にあるものは，左右で等号が成立せよ，ということが導出できる．

あとは，当然，
$$\dot{\lambda}_{sij}^{n+1} \leq \lambda_{sij}^{n} \tag{3}$$
でねぇといけないので，これで導出ができたことに．

振り返ってもらえばわかるが，双対問題の列生成から，自然に導出できてるでしょ？なので，これの細かいところを証明詰めていけばいいことになる．
- 起点とか，リンクのサフィックスがザーッと書いたので間違ってるかも．

URL: