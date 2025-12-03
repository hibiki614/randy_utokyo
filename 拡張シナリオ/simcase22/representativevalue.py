# -*- coding: utf-8 -*-
"""
Created on Mon Oct 27 22:41:09 2025

@author: OguchiLab
"""

import pandas as pd
import numpy as np
from pathlib import Path

# ====== 入力 ======
base_dir = Path(r"C:/Users/OguchiLab/OneDrive/デスクトップ/randy_utokyo/拡張シナリオ/simcase22")
in_csv = base_dir / "analysis" / "all_runs_summary_subset.csv"
out_csv = base_dir / "analysis" / "representative_runs.csv"

df = pd.read_csv(in_csv)

# ====== 評価指標を標準化して距離を算出 ======
metrics = ["V_net", "TTT", "dist_kmveh"]

rep_records = []

for scen in sorted(df["scenario"].unique()):
    sub = df[df["scenario"] == scen].copy()
    if sub.empty:
        continue

    # subset別に見る場合はここで分けてもOK
    for subset in sub["subset"].unique():
        ssub = sub[sub["subset"] == subset].copy()
        if ssub.empty:
            continue

        # 平均値
        mean_vals = ssub[metrics].mean()

        # 標準化して距離計算（各指標をスケール調整して公平に）
        z = (ssub[metrics] - ssub[metrics].mean()) / ssub[metrics].std(ddof=0)
        ssub["dist"] = np.sqrt((z ** 2).sum(axis=1))  # 多次元距離
        best_row = ssub.loc[ssub["dist"].idxmin()]

        rep_records.append({
            "scenario": scen,
            "subset": subset,
            "representative_run": best_row["run"],
            "dist": best_row["dist"],
            "V_net": best_row["V_net"],
            "TTT": best_row["TTT"],
            "dist_kmveh": best_row["dist_kmveh"]
        })

rep_df = pd.DataFrame(rep_records)
rep_df.to_csv(out_csv, index=False, encoding="utf-8-sig")
print("✅ 代表run一覧を出力:", out_csv)
#%%
import pandas as pd
import numpy as np
from pathlib import Path

# ====== 入力 ======
base_dir = Path(r"C:/Users/OguchiLab/OneDrive/デスクトップ/randy_utokyo/拡張シナリオ/simcase22")
in_csv = base_dir / "analysis" / "all_runs_summary_subset.csv"
df = pd.read_csv(in_csv)

# 対象subset（例：全体）
target_subset = "all"
df = df[df["subset"] == target_subset].copy()

metrics = ["V_net", "TTT", "dist_kmveh"]
results = []

for scen in sorted(df["scenario"].unique()):
    sub = df[df["scenario"] == scen]
    r06 = sub[sub["run"].str.contains("r06", case=False)]
    if r06.empty:
        print(f"⚠ {scen}: r06が見つかりません")
        continue
    r06_row = r06.iloc[0]

    check = {"scenario": scen}
    for m in metrics:
        q1, q3 = sub[m].quantile([0.25, 0.75])
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        val = r06_row[m]
        check[m] = val
        check[f"{m}_in_range"] = lower <= val <= upper
        check[f"{m}_Q1"] = q1
        check[f"{m}_Q3"] = q3
        check[f"{m}_lower"] = lower
        check[f"{m}_upper"] = upper
    results.append(check)

out = pd.DataFrame(results)
print(out[["scenario", "V_net_in_range", "TTT_in_range", "dist_kmveh_in_range"]])
