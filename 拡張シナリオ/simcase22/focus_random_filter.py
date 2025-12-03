# -*- coding: utf-8 -*-
"""
Created on Tue Dec  2 18:19:27 2025

@author: OguchiLab
"""

# -*- coding: utf-8 -*-
# 偶数シナリオのみ：線=グレー統一、マーカー=乱数ごとに色＋形、凡例=乱数
# r02 / r07 のみを描画し、各点に数値ラベルを付与
import re, numpy as np, pandas as pd, matplotlib.pyplot as plt

CSV = "all_runs_summary.csv"  # 必要に応じてパス調整

# 日本語フォント
plt.rcParams["font.family"] = "Meiryo"
plt.rcParams["axes.unicode_minus"] = False

# 読み込み
df = pd.read_csv(CSV).rename(columns={
    "scenario":"scenario", "run":"run", "V_net":"V_net",
    "TTT":"TTT", "dist_kmveh":"dist_kmveh",
})

# run → 乱数ID rXX 抽出
def extract_seed(s: str) -> str:
    s = str(s)
    m = re.search(r"_r(\d{1,2})_", s) or re.search(r"_r(\d{1,2})", s)
    return f"r{int(m.group(1)):02d}" if m else s
df["seed"] = df["run"].apply(extract_seed)

# シナリオ番号（no02 -> 2）
def scen_num(s: str) -> int:
    m = re.match(r"[Nn][Oo](\d+)", str(s))
    return int(m.group(1)) if m else 10**9
df["sc_num"] = df["scenario"].apply(scen_num)

# ★ 偶数シナリオのみ
df = df[df["sc_num"] % 2 == 0].copy().sort_values(["sc_num", "seed"])

# ★ r02 / r07 のみ
df = df[df["seed"].isin(["r02", "r07"])].copy()

# X 位置（縦整列＝ジッター無し）
scenarios = [s for s,_ in sorted(df[["scenario","sc_num"]].drop_duplicates().values, key=lambda x: int(x[1]))]
x_pos = {sc: i for i, sc in enumerate(scenarios, start=1)}
df["x"] = df["scenario"].map(x_pos)

# 乱数ごとのマーカー形＆色（2つだけ）
base_colors = list(plt.cm.tab10.colors) + list(plt.cm.tab20.colors)
markers = ["o","s","D","^","v","P","X","h","*","<",">"]
seed_list = sorted(df["seed"].unique())  # -> ["r02","r07"]
seed_style = {
    sd: dict(color=base_colors[i % len(base_colors)],
             marker=markers[i % len(markers)])
    for i, sd in enumerate(seed_list)
}

def _fmt_value(ycol: str, v: float) -> str:
    """指標ごとに見やすい書式で文字列化"""
    if ycol == "V_net":
        return f"{v:.2f}"         # km/h
    if ycol == "TTT":
        return f"{v/3600:.2f}h"   # 時間表示
    if ycol == "dist_kmveh":
        return f"{v:,.0f}"        # 台・km（整数）
    return f"{v:.2f}"

def plot_metric(ycol: str, ylabel: str, title_suffix: str, outfile: str):
    plt.figure(figsize=(13, 7.2), dpi=220)

    # 1) 線＝グレー統一（乱数の軌跡）
    for sd, g in df.groupby("seed"):
        g = g.sort_values("sc_num")
        if len(g) >= 2:
            plt.plot(g["x"], g[ycol], color="#9aa0a6", linewidth=1.4, alpha=0.75, zorder=1)

    # 2) マーカー＝乱数ごとに色＋形（凡例はこちら）＋数値ラベル
    for sd, g in df.groupby("seed"):
        st = seed_style[sd]
        plt.scatter(g["x"], g[ycol], s=38, alpha=0.98,
                    color=st["color"], marker=st["marker"],
                    edgecolors="white", linewidths=0.7, label=sd, zorder=2)
        # 数値ラベル（少し上にオフセット）
        for _, row in g.iterrows():
            txt = _fmt_value(ycol, row[ycol])
            plt.annotate(
                txt,
                xy=(row["x"], row[ycol]),
                xytext=(0, 7), textcoords="offset points",
                ha="center", va="bottom", fontsize=9,
                color=st["color"], zorder=3
            )

    # 体裁
    plt.xticks([x_pos[sc] for sc in scenarios], scenarios, fontsize=12)
    plt.xlabel("シナリオ（偶数のみ）", fontsize=14)
    plt.ylabel(ylabel, fontsize=14)
    plt.title(f"{title_suffix}（r02 / r07）：線=グレー／マーカー=乱数色＋形（縦整列）", fontsize=16)
    plt.grid(True, axis="y", linestyle="--", linewidth=0.6, alpha=0.6)

    # 凡例（乱数）
    plt.legend(title="乱数（ケース）", loc="best", frameon=True, ncol=2, fontsize=10, title_fontsize=11)

    plt.tight_layout()
    plt.savefig(outfile, dpi=300)
    plt.show()

# 速度
plot_metric("V_net", "平均速度 V_net [km/h]",
            "平均速度", "avg_speed_even_grayline_markers_r02_r07.png")

# TTT（※見やすさ優先でラベルは h 表示）
plot_metric("TTT", "総旅行時間 TTT [sec]",
            "総旅行時間", "ttt_even_grayline_markers_r02_r07.png")

# 総走行距離（台キロ）
plot_metric("dist_kmveh", "総走行距離 [台・km]",
            "総走行距離（台キロ）", "dist_kmveh_even_grayline_markers_r02_r07.png")
