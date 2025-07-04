## Merged problem
$$
min. \ \sum_{\phi}\sum_{s\in Q}\sum_{ij\in E}t_{ij}x_{ij}^{\phi s}+\alpha\sum_{ij\in E}\frac{\eta_{ij}\sum_{s\in Q}x_{ij}^{ps}}{u_{ij}} \tag{1}
$$
subject to
$$
\begin{gather}
\sum_{n|j=n,ij\in E}x_{ij}^{\phi s}-\sum_{n|i=n,ij\in E}x_{ij}^{\phi s}=b_{n}^{\phi s} \ \forall n\in N, \ s\in Q, \ \phi\in \{p, c\} \tag{2} \\
0\leq\sum_{s\in Q}x_{ij}^{cs}+\eta_{ij}\sum_{s\in Q}x_{ij}^{ps}\leq u_{ij} \ \forall ij\in E \ \tag{3} \\
x_{ij}^{cs}, \ x_{ij}^{ps}\geq0 \ \forall ij\in E, \ s\in Q \tag{4}
\end{gather} 
$$
## Dual of this problem
$$
max. \ \sum_{\phi}\sum_{s\in Q}\sum_{n\in N}b_{n}^{\phi s}\theta_{n}^{\phi s}-\sum_{ij\in E}\lambda_{ij}u_{ij} \tag{6}
$$
subject to
$$
\begin{gather}
-\theta_{i}^{cs}+\theta_{j}^{cs}-\lambda_{ij}\leq t_{ij} \tag{7} \ \forall{ij}\in E, s\in Q\\
-\theta_{i}^{ps}+\theta_{j}^{ps}-\lambda_{ij}\leq t_{ij}+\alpha\frac{\eta_{ij}}{u_{ij}} \tag{8} \ \forall{ij}\in E,  s\in Q\\
\lambda_{ij} \geq0 \ \forall{ij}\in E \tag{9}
\end{gather}
$$
## Dual complementarity condition
$$
\begin{gather}
\lambda_{ij}^*(u_{ij}-\sum_{s\in Q}{x_{ij}^{cs}}^*-\eta_{ij}\sum_{s\in Q}{x_{ij}^{ps}}^*)=0 \ \forall ij\in E, s\in Q \tag{10} \\
\lambda_{ij}^* \geq0 \ \forall{ij}\in E \tag{11} \\
u_{ij}-\sum_{s\in Q}{x_{ij}^{cs}}^*-\eta_{ij}\sum_{s\in Q}{x_{ij}^{ps}}^* \geq 0 \tag{12} \ \forall ij\in E, s\in Q
\end{gather}
$$



## Primal complementarity condition
$$
\begin{gather}\
\sum_{s \in Q}{x_{ij}^{cs}}^*(t_{ij}+{\theta_i^{cs}}^*-{\theta_j^{cs}}^*+{\lambda_{ij}}^*)=0   \quad \forall (i,j)\in E \tag{13} \\
\sum_{s \in Q}{x_{ij}^{cs}}^*\geqq0 \quad \forall (i,j)\in E \tag{14} \\
t_{ij}+{\theta_i^{cs}}^*-{\theta_j^{cs}}^*+{\lambda_{ij}}^*\geqq0 \quad \forall (i,j)\in E, s\in Q \tag{15} \\
\sum_{s \in Q}{x_{ij}^{ps}}^*(t_{ij}+\alpha\frac{\eta_{ij}}{u_{ij}}+{\theta_i^{ps}}^*-{\theta_j^{ps}}^*+\eta_{ij}{\lambda_{ij}}^*)=0  \quad \forall (i,j)\in E \tag{16} \\
\sum_{s \in Q}{x_{ij}^{ps}}^*\geqq0 \quad \forall (i,j)\in E \tag{17} \\
t_{ij}+\alpha\frac{\eta_{ij}}{u_{ij}}+{\theta_i^{ps}}^*-{\theta_j^{ps}}^*+\eta_{ij}{\lambda_{ij}}^*\geqq0 \quad \forall (i,j)\in E, s\in Q \tag{18}
\end{gather}
$$
## Proposition 1 
- $\lambda_{ij}^*$ represents the link delay time that appears when the capacity constraint is activated.
### Proof.
- $\lambda_{ij}^*$ is always determined as following equation due to the complementarity slackness condition.
$$
\begin{gather}
\lambda_{ij}^*
\begin{cases}
= 0 \quad & \text{if} \quad 0\leqq \sum_{s\in Q}{x_{ij}^{cs}}^*+\eta_{ij}\sum_{s\in Q}{x_{ij}^{ps}}^*<u_{ij} \\
\geq 0 \quad & \text{if} \quad \sum_{s\in Q}{x_{ij}^{cs}}^*+\eta_{ij}\sum_{s\in Q}{x_{ij}^{ps}}^*=u_{ij}
\end{cases}
\end{gather}
$$
## Proposition 2
- The solution of MMCF of **car** is consistent with the UE condition equation.
### Proof.
- There are four possible cases.

|     | car                                         | sum                                                                               | ${\lambda_{ij}}^*$ |
| :-- | ------------------------------------------- | --------------------------------------------------------------------------------- | ------------------ |
| C1  | 0                                           | $0\leq\sum_{s\in Q}{x_{ij}^{ps}}^*< u_{ij}$                                       | 0                  |
| C2  | $0<\sum_{s\in Q}{x_{ij}^{cs}}^*< u_{ij}$    | $0\leq\sum_{s\in Q}{x_{ij}^{cs}}^*+\eta_{ij}\sum_{s\in Q}{x_{ij}^{ps}}^*< u_{ij}$ | 0                  |
| C3  | 0                                           | $u_{ij}$                                                                          | +                  |
| C4  | $0<\sum_{s\in Q}{x_{ij}^{cs}}^*\leq u_{ij}$ | $u_{ij}$                                                                          | +                  |


- When $0<\sum_{s\in Q}{x_{ij}^{cs}}^*+\eta_{ij}\sum_{s\in Q}{x_{ij}^{ps}}^*< u_{ij}$, that is, when the capacity constraint is **not activated**, ${\lambda_{ij}}^*=0$ and ${{\theta_{n}}^{cs}}^*$ satisfies the following two conditions.(C1 and C2)
$$
\begin{equation}
\begin{cases}
{\theta_j^{cs}}^*\leq t_{ij} + {\theta_i^{cs}}^* & \text{if} \quad \sum_{s \in Q}{x_{ij}^{cs}}^*=0 \tag{20} \\
{\theta_j^{cs}}^* = t_{ij} + {\theta_i^{cs}}^* & \text{if} \quad0<\sum_{s \in Q}{x_{ij}^{cs}}^*<u_{ij} 
\end{cases}
\end{equation}
$$
- When $\sum_{s\in Q}{x_{ij}^{cs}}^*+\eta_{ij}\sum_{s\in Q}{x_{ij}^{ps}}^*= u_{ij}$, that is, when the capacity constraint is  **activated**, ${\lambda_{ij}}^*(\geq0)$ and ${{\theta_{n}}^{cs}}^*$ satisfies the following two conditions.(C3 and C4)
$$
\begin{equation}
\begin{cases}
{\theta_j^{cs}}^*\leq t_{ij} + {\lambda_{ij}}^*+ {\theta_i^{cs}}^* & \text{if} \quad \sum_{s \in Q}{x_{ij}^{cs}}^*=0 \\
{\theta_j^{cs}}^* = t_{ij} + {\lambda_{ij}}^* + {\theta_i^{cs}}^* & \text{if} \quad 0<\sum_{s \in Q}{x_{ij}^{cs}}^* \leq u_{ij}  \tag{21}
\end{cases}
\end{equation}
$$
- eq.(20) and eq.(21) can be interpreted as follows.
  -  When $\sum_{s \in Q}{x_{ij}^{cs}}^*=0$, that is, when $(i, j)$ links are not used, the sum of zero-flow cost(or equilibrium cost: $t_{ij}+\lambda_{ij}^*$) and the potential of the link origin node is greater than the potential of the link terminal node.
  - When $\sum_{s \in Q}{x_{ij}^{cs}}^* >0$, that is, when $(i, j)$ link flows exist, the shortest path cost from the origin $s$ to $j$ is the sum of zero-flow cost(or equilibrium cost) and the shortest path cost to $i$.
- From the above, it is shown that the solution of MMCF of **car** satisfies definition of the UE condition.

### Remarks
- Whether the solution of **PT** satisfies UE condition is not clear.
- There 7 possible cases.

|     | car                                      | PT                                                | sum                                                                            | $\lambda_{ij}^*$ |
| --: | ---------------------------------------- | ------------------------------------------------- | ------------------------------------------------------------------------------ | ---------------- |
|  C1 | 0                                        | 0                                                 | 0                                                                              | 0                |
|  C2 | 0                                        | $0<\eta_{ij}\sum_{s\in Q}{x_{ij}^{ps}}^*< u_{ij}$ | $0<\eta_{ij}\sum_{s\in Q}{x_{ij}^{ps}}^*< u_{ij}$                              | 0                |
|  C3 | 0                                        | $u_{ij}$                                          | $u_{ij}$                                                                       | +                |
|  C4 | $0<\sum_{s\in Q}{x_{ij}^{cs}}^*< u_{ij}$ | 0                                                 | $0<\sum_{s\in Q}{x_{ij}^{cs}}^*< u_{ij}$                                       | 0                |
|  C5 | $0<\sum_{s\in Q}{x_{ij}^{cs}}^*< u_{ij}$ | $0<\eta_{ij}\sum_{s\in Q}{x_{ij}^{ps}}^*< u_{ij}$ | $0<\sum_{s\in Q}{x_{ij}^{cs}}^*+\eta_{ij}\sum_{s\in Q}{x_{ij}^{ps}}^*< u_{ij}$ | 0                |
|  C6 | $0<\sum_{s\in Q}{x_{ij}^{cs}}^*< u_{ij}$ | $0<\eta_{ij}\sum_{s\in Q}{x_{ij}^{ps}}^*< u_{ij}$ | $u_{ij}$                                                                       | +                |
|  C7 | $u_{ij}$                                 | 0                                                 | $u_{ij}$                                                                       | +                |



- When $\sum_{s\in Q}{x_{ij}^{cs}}^*=0$，
(i)If $\sum_{s \in S}{x_{ij}^{ps}}^*=0$(case C1)
$$
\begin{gather}
{\theta_j^{ps}}^* \leq t_{ij} + \alpha\frac{\eta_{ij}}{u_{ij}}+{\theta_i^{ps}}^* \\
{\theta_j^{cs}}^* \leq t_{ij} +{\theta_i^{cs}}^* 
\end{gather}
$$
(ii)If $0<\eta_{ij}\sum_{s\in Q}{x_{ij}^{ps}}^*< u_{ij}$(case C2)
$$
\begin{gather}
{\theta_j^{ps}}^* = t_{ij} + \alpha\frac{\eta_{ij}}{u_{ij}}+{\theta_i^{ps}}^* \\
{\theta_j^{cs}}^* \leq t_{ij} +{\theta_i^{cs}}^* 
\end{gather}
$$
(iii)If $\eta_{ij}\sum_{s\in Q}{x_{ij}^{ps}}^*=u_{ij}$(case C3)
$$
\begin{gather}
{\theta_j^{ps}}^* = t_{ij} + \alpha\frac{\eta_{ij}}{u_{ij}}+\eta_{ij}\lambda_{ij}^*+{\theta_i^{ps}}^* \\
{\theta_j^{cs}}^* \leq t_{ij} +\lambda_{ij}^*+{\theta_i^{cs}}^* 
\end{gather}
$$
- When $0<\sum_{s\in Q}{x_{ij}^{cs}}^*< u_{ij}$，
(i)If $\sum_{s \in S}{x_{ij}^{ps}}^*=0$(case C4)
$$
\begin{gather}
{\theta_j^{ps}}^* \leq t_{ij} + \alpha\frac{\eta_{ij}}{u_{ij}}+{\theta_i^{ps}}^* \\
{\theta_j^{cs}}^* = t_{ij} +{\theta_i^{cs}}^* 
\end{gather}
$$
(ii)If $0<\eta_{ij}\sum_{s\in Q}{x_{ij}^{ps}}^*< u_{ij}$ and $0<\sum_{s\in Q}{x_{ij}^{cs}}^*+\eta_{ij}\sum_{s\in Q}{x_{ij}^{ps}}^*< u_{ij}$(case C5)
$$
\begin{gather}
{\theta_j^{ps}}^* = t_{ij} + \alpha\frac{\eta_{ij}}{u_{ij}}+{\theta_i^{ps}}^* \\
{\theta_j^{cs}}^* = t_{ij} +{\theta_i^{cs}}^* 
\end{gather}
$$
(iii)If $0<\eta_{ij}\sum_{s\in Q}{x_{ij}^{ps}}^*< u_{ij}$ and $\sum_{s\in Q}{x_{ij}^{cs}}^*+\eta_{ij}\sum_{s\in Q}{x_{ij}^{ps}}^*= u_{ij}$(case C6)
$$
\begin{gather}
{\theta_j^{ps}}^* = t_{ij} + \alpha\frac{\eta_{ij}}{u_{ij}}+\eta_{ij}\lambda_{ij}^*+{\theta_i^{ps}}^* \\
{\theta_j^{cs}}^* = t_{ij} +\lambda_{ij}^*+{\theta_i^{cs}}^* 
\end{gather}
$$
- When $\sum_{s\in Q}{x_{ij}^{cs}}^*= u_{ij}$(case C7)，
$$
\begin{gather}
{\theta_j^{ps}}^* \leq t_{ij} + \alpha\frac{\eta_{ij}}{u_{ij}}+\eta_{ij}\lambda_{ij}^*+{\theta_i^{ps}}^* \\
{\theta_j^{cs}}^* = t_{ij} +\lambda_{ij}^*+{\theta_i^{cs}}^* 
\end{gather}
$$