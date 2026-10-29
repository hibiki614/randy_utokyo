# 基軸＋不整合による残差学習（探索的解析）
対象20路線×13速度=260条件。入力は基軸B、重みなし不整合R0、重みありRwのみ。交差点数・速度・リンク長・青時間は入力していない。目的変数はH=D_GA−B。残差は入力にせず、最終予測はB+予測残差。

路線を1つ丸ごと除くLeave-One-Corridor-Outを20回実施。残差教師も評価路線を含めて学習しない。モデルとハイパーパラメータは固定しチューニングなし。Ridge（標準化は各学習fold内）、RandomForest、ExtraTrees、HistGradientBoosting。出力のゼロ切り・上限切りなし。Bそのまま、Bのみで残差学習、B+片方の指標、B+両指標を比較。

最良のB_R0_Rw RandomForestは、未知路線MAE6.259秒、RMSE8.729秒、全遅れR2=.9275、残差R2=.5129。BそのままMAE14.460秒、BのみRandomForest補正MAE7.290秒。RidgeでBのみ補正MAE7.236秒。学習データの評価はscores.csvのtraining行。LOCO値と混同しない。

16仕様の比較から最良を選んだ探索的結果であり、独立テストやnested CVで選択後性能を確認していない。20路線しかなく、未知の交差点数への外挿を検証する分割でもない。残差R2は物理的な原因の説明割合・因果効果ではない。車群の影響と認定できない。GA教師も大域最適保証なし。全遅れR2の高さはBが捉える違いも含む。

source/run.pyで再現。依存: numpy,pandas,scikit-learn,matplotlib。scores.csvは全仕様の学習内/路線外評価、predictions.csvは全260条件の路線外予測、scores_by_intersections.csvは交差点数別MAE/RMSE。
