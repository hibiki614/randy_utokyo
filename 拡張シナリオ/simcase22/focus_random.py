# -*- coding: utf-8 -*-
# all / target / non_target それぞれで、
# 偶数シナリオのみ：線=グレー統一、マーカー=乱数ごとに色＋形、凡例=乱数
# 指標：V_net / TTT / dist_kmveh

import re, numpy as np, pandas as pd, matplotlib.pyplot as plt

CSV = "all_runs_summary_subset.csv"   # 例: analysis/all_runs_summary_subset.csv

# 日本語フォント
plt.rcParams["font.family"] = "Meiryo"
plt.rcParams["axes.unicode_minus"] = False

# 読み込み
df0 = pd.read_csv(CSV)

# run → 乱数ID rXX
def extract_seed(s: str) -> str:
    s = str(s)
    m = re.search(r"_r(\d{1,2})_", s) or re.search(r"_r(\d{1,2})", s)
    return f"r{int(m.group(1)):02d}" if m else s

# シナリオ番号（no02 -> 2）
def scen_num(s: str) -> int:
    m = re.match(r"[Nn][Oo](\d+)", str(s))
    return int(m.group(1)) if m else 10**9

# 乱数スタイル（全subsetで統一）
def build_seed_style(seeds):
    base_colors = list(plt.cm.tab20.colors) + list(plt.cm.tab10.colors)
    markers = ["o","s","D","^","v","P","X","h","*","<",">"]
    seed_list = sorted(seeds)
    return {
        sd: dict(color=base_colors[i % len(base_colors)],
                 marker=markers[i % len(markers)])
        for i, sd in enumerate(seed_list)
    }, seed_list

def prepare_subset(df_all, subset_label):
    df = df_all[df_all["subset"] == subset_label].copy()
    # 必要列の名前合わせ
    df = df.rename(columns={
        "scenario":"scenario", "run":"run",
        "V_net":"V_net", "TTT":"TTT", "dist_kmveh":"dist_kmveh"
    })
    df["seed"] = df["run"].apply(extract_seed)
    df["sc_num"] = df["scenario"].apply(scen_num)
    # 偶数シナリオのみ
    df = df[df["sc_num"] % 2 == 0].copy().sort_values(["sc_num","seed"])
    # X位置（縦整列）
    scenarios = [s for s,_ in sorted(df[["scenario","sc_num"]].drop_duplicates().values,
                                     key=lambda x: int(x[1]))]
    x_pos = {sc: i for i, sc in enumerate(scenarios, start=1)}
    df["x"] = df["scenario"].map(x_pos)
    return df, scenarios, x_pos

def plot_metric(df, scenarios, x_pos, ycol, ylabel, title_suffix, outfile, seed_style, seed_list):
    plt.figure(figsize=(13, 7.2), dpi=220)

    # 線=グレー統一（乱数の軌跡）
    for sd, g in df.groupby("seed"):
        g = g.sort_values("sc_num")
        if len(g) >= 2:
            plt.plot(g["x"], g[ycol], color="#9aa0a6", linewidth=1.2, alpha=0.7, zorder=1)

    # マーカー=乱数ごと色＋形（凡例はこちら）
    labeled = set()
    for sd, g in df.groupby("seed"):
        st = seed_style[sd]
        label = sd if sd not in labeled else None
        plt.scatter(g["x"], g[ycol], s=34, alpha=0.98,
                    color=st["color"], marker=st["marker"],
                    edgecolors="white", linewidths=0.5, label=label, zorder=2)
        labeled.add(sd)

    # 軸・体裁
    plt.xticks([x_pos[sc] for sc in scenarios], scenarios, fontsize=11)
    plt.xlabel("シナリオ（偶数のみ）", fontsize=14)
    plt.ylabel(ylabel, fontsize=14)
    plt.title(f"{title_suffix}：線=グレー／マーカー=乱数（縦整列）", fontsize=16)
    plt.grid(True, axis="y", linestyle="--", linewidth=0.6, alpha=0.6)

    # 凡例
    ncol = 3 if len(seed_list) > 12 else 2
    plt.legend(title="乱数（ケース）", loc="best", frameon=True, ncol=ncol, fontsize=10, title_fontsize=11)

    plt.tight_layout()
    plt.savefig(outfile, dpi=300)
    plt.show()

# ===== 実行：all / target / non_target を順番に =====
for subset in ["all", "target", "non_target"]:
    df_sub, scenarios, x_pos = prepare_subset(df0, subset)
    if df_sub.empty:
        print(f"[WARN] subset='{subset}' はデータなし")
        continue

    # 乱数の色・形の割当（subset間で統一のため、全体の乱数集合に基づく）
    seed_style, seed_list = build_seed_style(df_sub["seed"].unique())

    # 速度
    plot_metric(df_sub, scenarios, x_pos,
                ycol="V_net", ylabel="平均速度 V_net [km/h]",
                title_suffix=f"{subset} の平均速度",
                outfile=f"avg_speed_even_{subset}.png",
                seed_style=seed_style, seed_list=seed_list)

    # TTT（総旅行時間）
    plot_metric(df_sub, scenarios, x_pos,
                ycol="TTT", ylabel="総旅行時間 TTT [sec]",
                title_suffix=f"{subset} の総旅行時間",
                outfile=f"ttt_even_{subset}.png",
                seed_style=seed_style, seed_list=seed_list)

    # 総走行距離（台キロ）
    plot_metric(df_sub, scenarios, x_pos,
                ycol="dist_kmveh", ylabel="総走行距離 [台・km]",
                title_suffix=f"{subset} の総走行距離（台キロ）",
                outfile=f"dist_kmveh_even_{subset}.png",
                seed_style=seed_style, seed_list=seed_list)
