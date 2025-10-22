# -*- coding: utf-8 -*-
"""
Created on Tue Sep 30 13:45:22 2025
@author: OguchiLab
"""
import pandas as pd
import numpy as np
from pathlib import Path
import re
import matplotlib
from matplotlib import font_manager as fm
import matplotlib.pyplot as plt

# ====== 入出力 ======
base_dir = Path(r"C:/Users/OguchiLab/OneDrive/デスクトップ/randy_utokyo/拡張シナリオ/simcase22")
out_dir  = base_dir / "analysis"
in_csv   = out_dir / "timeseries_summary.csv"
rel_csv  = out_dir / "timeseries_relative.csv"

# ====== 日本語フォント ======
JP_FONT_CANDIDATES = [
    "Meiryo","Yu Gothic","MS Gothic",
    "Hiragino Sans","Hiragino Kaku Gothic ProN",
    "Noto Sans CJK JP","IPAPGothic","IPAMincho"
]
installed = set(f.name for f in fm.fontManager.ttflist)
for name in JP_FONT_CANDIDATES:
    if name in installed:
        matplotlib.rcParams["font.family"] = name
        matplotlib.rcParams["axes.unicode_minus"] = False
        break

# ====== 読み込み ======
ts = pd.read_csv(in_csv)

# ---- 7:00〜18:30 の範囲だけ抽出 ----
ts["slot_code_str"] = ts["slot_code"].astype(str).str.zfill(4)
ts = ts[(ts["slot_code_str"] >= "0700") & (ts["slot_code_str"] <= "1830")].copy()

# ====== HH:MM生成 ======
def _to_hhmm(slot_code, timestr):
    if isinstance(slot_code, str) and len(slot_code) == 4 and slot_code.isdigit():
        return f"{slot_code[:2]}:{slot_code[2:]}"
    s = str(timestr)
    m = re.search(r'(\d{1,2}):(\d{2})', s)
    return f"{int(m.group(1)):02d}:{m.group(2)}" if m else s

if "HHMM" not in ts.columns:
    ts["HHMM"] = [
        _to_hhmm(ts.get("slot_code", pd.Series([None]*len(ts))).iloc[i],
                 ts.get("timestr",   pd.Series([None]*len(ts))).iloc[i])
        for i in range(len(ts))
    ]

# ====== no01 を基準に相対化 ======
base = ts[ts["scenario"] == "no01"][["slot_code","HHMM","V_net_mean","TTT_mean","flow_kmveh_mean"]].copy()
base = base.rename(columns={
    "V_net_mean":"base_V",
    "TTT_mean":"base_TTT",
    "flow_kmveh_mean":"base_flow"
})

df = ts.merge(base[["slot_code","base_V","base_TTT","base_flow"]], on="slot_code", how="inner")

for c in ["base_V","base_TTT","base_flow"]:
    df.loc[df[c] == 0, c] = np.nan

df["V_net_rel"] = df["V_net_mean"] / df["base_V"]
df["TTT_rel"]   = df["TTT_mean"]   / df["base_TTT"]
df["flow_rel"]  = df["flow_kmveh_mean"] / df["base_flow"]

cols_save = ["scenario","timestr","slot_code","HHMM",
             "V_net_rel","TTT_rel","flow_rel",
             "V_net_mean","TTT_mean","flow_kmveh_mean"]
df[cols_save].to_csv(rel_csv, index=False, encoding="utf-8-sig")
print(f"✅ 相対CSVを書き出し: {rel_csv}")

# ====== x軸設定 ======
time_master = (df[["slot_code","HHMM"]]
               .drop_duplicates()
               .sort_values("slot_code"))
pos_map = {sc: i for i, sc in enumerate(time_master["slot_code"])}

def make_ticks(master, target=12):
    n = len(master)
    if n == 0:
        return np.array([]), []
    step = max(1, int(np.ceil(n / target)))
    idx = np.arange(0, n, step)
    if idx[-1] != n-1:
        idx = np.r_[idx, n-1]
    labels = master["HHMM"].iloc[idx].tolist()
    return idx, labels

# ====== プロット関数 ======
def plot_rel(metric_col, ylabel, filename, target_ticks=12):
    plt.figure(figsize=(14,6))
    for scen in sorted(df["scenario"].unique()):
        sub = df[df["scenario"] == scen].copy().sort_values("slot_code")
        x = sub["slot_code"].map(pos_map).values
        y = sub[metric_col].values
        plt.plot(x, y, label=scen)
    ticks, labs = make_ticks(time_master, target=target_ticks)
    plt.xticks(ticks, labs, rotation=0)
    plt.xlabel("時刻（HH:MM）")
    plt.ylim(0.8, 1.2)
    yticks = np.arange(0.8, 1.2001, 0.05)
    plt.yticks(yticks, [f"{t:.2f}" for t in yticks])
    plt.axhline(1.0, color="gray", linewidth=1, linestyle="--", zorder=0)
    plt.ylabel(ylabel + "（no01=1.0）")
    plt.title(f"時間別 {ylabel} の相対値（0.8〜1.2表示）")
    plt.legend(ncol=2)
    plt.tight_layout()
    plt.savefig(out_dir / filename, dpi=300)
    plt.close()
    print(f"🖼 画像保存: {out_dir / filename}")

# ====== 出力（3指標） ======
plot_rel("V_net_rel", "平均速度",  "timeseries_speed_rel.png", target_ticks=14)
plot_rel("TTT_rel",   "TTT",      "timeseries_ttt_rel.png",   target_ticks=14)
plot_rel("flow_rel",  "総走行距離", "timeseries_dist_rel.png", target_ticks=14)
