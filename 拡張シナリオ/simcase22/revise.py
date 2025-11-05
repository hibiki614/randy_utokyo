# -*- coding: utf-8 -*-
"""
交通流集計＋可視化（全体／対象／非対象リンク + 時系列）
フォント拡大・シナリオ名変更・箱ひげ図凡例削除・折れ線凡例維持
@author: OguchiLab
"""

import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib import font_manager as fm

# ====== パス設定 ======
base_dir = Path(r"C:/Users/hibik/github/randy_utokyo/拡張シナリオ/simcase22")
out_dir = base_dir / "analysis"
out_dir.mkdir(exist_ok=True)

# ====== 共通設定 ======
font_path = r"C:\Windows\Fonts\meiryo.ttc"
prop = fm.FontProperties(fname=font_path)
plt.rcParams["font.family"] = prop.get_name()
plt.rcParams["axes.unicode_minus"] = False
sns.set(style="whitegrid", font=prop.get_name())

# ====== シナリオ名変換 ======
SCEN_LABEL = {
    "no01": "MV-×",
    "no02": "MV-〇",
    "no03": "1.0AV-×",
    "no04": "1.0AV-〇",
    "no05": "0.7AV-×",
    "no06": "0.7AV-〇",
    "no07": "0.5AV-×",
    "no08": "0.5AV-〇",
}

# ====== データ読込 ======
records_df = pd.read_csv(out_dir / "all_runs_summary_subset.csv")
timeseries_df = pd.read_csv(out_dir / "timeseries_summary_subset.csv")

records_df["scenario_label"] = records_df["scenario"].map(SCEN_LABEL)
timeseries_df["scenario_label"] = timeseries_df["scenario"].map(SCEN_LABEL)
order = [SCEN_LABEL[k] for k in sorted(SCEN_LABEL.keys())]

# ====== 共通描画パラメータ ======
TITLE_SIZE = 20
LABEL_SIZE = 30
TICK_SIZE = 20

#%% === 図1：全体（絶対値） ===
print("📊 図1：全体（絶対値）を描画中...")

records_all = records_df[records_df["subset"] == "all"].copy()

fig, axes = plt.subplots(3, 1, figsize=(12, 16), sharex=True)

for ax, (col, ylabel) in zip(
    axes,
    [
        ("V_net", "平均速度 [km/h]"),
        ("TTT", r"総旅行時間 [$10^7$ sec]"),
        ("dist_kmveh", "総走行距離 [台・km]")
    ]
):
    df_plot = records_all.copy()

    # ✅ TTTだけ単位を10⁷で割る
    if col == "TTT":
        df_plot[col] = df_plot[col] / 1e7

    sns.boxplot(
        data=df_plot, x="scenario_label", y=col,
        order=order, color="tab:blue", width=0.5,
        boxprops={"alpha": 0.8},
        flierprops={"marker": "o", "markersize": 3, "alpha": 0.4},
        ax=ax
    )

    ax.set_ylabel(ylabel, fontproperties=prop, fontsize=LABEL_SIZE)
    ax.set_xticklabels(order, fontproperties=prop, fontsize=TICK_SIZE)
    ax.grid(True, axis="y", alpha=0.3)
    ax.tick_params(axis='y', labelsize=TICK_SIZE)

axes[-1].set_xlabel("シナリオ", fontproperties=prop, fontsize=LABEL_SIZE)
axes[0].text(
    0.5, 1.1, "ネットワーク全体における各指標の比較",
    ha="center", va="bottom", transform=axes[0].transAxes,
    fontproperties=prop, fontsize=TITLE_SIZE, weight="bold"
)

plt.tight_layout(rect=[0, 0, 1, 0.95])
plt.savefig(out_dir / "boxplot_all_bigfont_TTT_scaled.png", dpi=300)
plt.close()
print("✅ 図1保存完了（TTTのみ10⁷でスケーリングして1.2等の表示）")



#%% === 図2：対象リンク vs 非対象リンク ===
print("📊 図2：対象リンク vs 非対象リンクを描画中...")

metrics = [
    ("V_net", "平均速度 [km/h]", False),
    ("TTT", "総旅行時間 [sec]", True),
    ("dist_kmveh", "総走行距離 [台・km]", True)
]
colors = {"target": "tab:red", "non_target": "tab:gray"}

fig, axes = plt.subplots(3, 1, figsize=(12, 16), sharex=True)
subsets = ["target", "non_target"]

for ax, (col, ylabel, rel) in zip(axes, metrics):
    width = 0.25
    spacing = 0.25
    for i, subset in enumerate(subsets):
        subdf = records_df[records_df["subset"] == subset]
        x_pos = np.arange(len(order)) + (i - 0.5) * spacing
        data = [subdf.loc[subdf["scenario_label"] == s, col].dropna() for s in order]
        ax.boxplot(
            data, positions=x_pos, widths=width,
            patch_artist=True,
            boxprops=dict(facecolor=colors[subset], alpha=0.7),
            medianprops=dict(color="black", linewidth=1.5),
            whiskerprops=dict(color="black", linewidth=1.0),
            capprops=dict(color="black", linewidth=1.0),
            flierprops=dict(marker="o", markersize=3, color="gray", alpha=0.4),
        )
    ax.set_ylabel(ylabel, fontproperties=prop, fontsize=LABEL_SIZE)
    ax.set_xticks(np.arange(len(order)))
    ax.set_xticklabels(order, fontproperties=prop, fontsize=TICK_SIZE)
    if rel:
        ax.axhline(1.0, color="black", linestyle="--", linewidth=1)
    ax.grid(True, axis="y", alpha=0.3)

axes[-1].set_xlabel("シナリオ", fontproperties=prop, fontsize=LABEL_SIZE)
axes[0].text(
    0.5, 1.1, "対象リンクと非対象リンクにおける各指標の比較",
    ha="center", va="bottom", transform=axes[0].transAxes,
    fontproperties=prop, fontsize=TITLE_SIZE, weight="bold"
)
plt.tight_layout(rect=[0, 0, 1, 0.95])
plt.savefig(out_dir / "boxplot_target_vs_nontarget_bigfont.png", dpi=300)
plt.close()
print("✅ 図2保存完了")

#%% === 図3：全体＋対象＋非対象リンク ===
print("📊 図3：全体＋対象＋非対象リンクを描画中...")

colors = {"all": "tab:blue", "target": "tab:red", "non_target": "tab:gray"}
metrics = [
    ("V_net", "平均速度 [km/h]", False),
    ("TTT", "総旅行時間 [sec]", True),
    ("dist_kmveh", "総走行距離 [台・km]", True)
]
subsets = ["all", "target", "non_target"]

fig, axes = plt.subplots(3, 1, figsize=(12, 16), sharex=True)
for ax, (col, ylabel, rel) in zip(axes, metrics):
    width = 0.25
    spacing = 0.25
    for i, subset in enumerate(subsets):
        subdf = records_df[records_df["subset"] == subset]
        x_pos = np.arange(len(order)) + (i - 1) * spacing
        data = [subdf.loc[subdf["scenario_label"] == s, col].dropna() for s in order]
        ax.boxplot(
            data, positions=x_pos, widths=width,
            patch_artist=True,
            boxprops=dict(facecolor=colors[subset], alpha=0.7),
            medianprops=dict(color="black", linewidth=1.5),
            whiskerprops=dict(color="black", linewidth=1.0),
            capprops=dict(color="black", linewidth=1.0),
            flierprops=dict(marker="o", markersize=3, color="gray", alpha=0.4),
        )
    ax.set_ylabel(ylabel, fontproperties=prop, fontsize=LABEL_SIZE)
    ax.set_xticks(np.arange(len(order)))
    ax.set_xticklabels(order, fontproperties=prop, fontsize=TICK_SIZE)
    if rel:
        ax.axhline(1.0, color="black", linestyle="--", linewidth=1)
    ax.grid(True, axis="y", alpha=0.3)

axes[-1].set_xlabel("シナリオ", fontproperties=prop, fontsize=LABEL_SIZE)
axes[0].text(
    0.5, 1.1, "全体・対象・非対象リンクにおける各指標の比較",
    ha="center", va="bottom", transform=axes[0].transAxes,
    fontproperties=prop, fontsize=TITLE_SIZE, weight="bold"
)
plt.tight_layout(rect=[0, 0, 1, 0.95])
plt.savefig(out_dir / "boxplot_all_target_nontarget_bigfont.png", dpi=300)
plt.close()
print("✅ 図3保存完了")

#%% === 時系列（折れ線） ===
print("📈 時系列図を描画中...")

def _to_hhmm(sc):
    """スロットコードを HH:MM 形式に統一変換（数値対応）"""
    try:
        s = str(int(sc)).zfill(4)
        return f"{s[:2]}:{s[2:]}"
    except Exception:
        return None

# slot_code → hhmm に変換
timeseries_df["hhmm"] = timeseries_df["slot_code"].map(_to_hhmm)

metrics = [
    ("V_net_mean", "平均速度 [km/h]", "timeseries_speed"),
    ("TTT_mean", "総旅行時間 [sec]", "timeseries_ttt"),
    ("flow_kmveh_mean", "総走行距離 [台・km/15分]", "timeseries_distance")
]

for subset_label in ["all", "target", "non_target"]:
    df = timeseries_df[timeseries_df["subset"] == subset_label].copy()

    # 文字列として比較（07:00～18:30）
    df = df[(df["hhmm"] >= "07:00") & (df["hhmm"] <= "18:30")]

    # 1時間ごとのラベル作成
    tick_labels = [f"{h:02d}:00" for h in range(7, 19)]

    for ycol, ylabel, fname in metrics:
        plt.figure(figsize=(14, 7))
        for scen in order:
            sub = df[df["scenario_label"] == scen]
            plt.plot(sub["hhmm"], sub[ycol], label=scen, linewidth=2)

        # 軸ラベルを「時刻（HH:MM）」→「時刻」に変更
        plt.xlabel("時刻", fontproperties=prop, fontsize=LABEL_SIZE)
        plt.ylabel(ylabel, fontproperties=prop, fontsize=LABEL_SIZE)
        plt.title(f"時間別 {ylabel}（{subset_label}）", fontproperties=prop, fontsize=TITLE_SIZE, weight="bold")

        plt.legend(fontsize=18, loc="upper right", ncol=2)
        plt.xticks(ticks=tick_labels, labels=tick_labels, fontsize=TICK_SIZE)
        plt.yticks(fontsize=TICK_SIZE)
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(out_dir / f"{fname}_{subset_label}_bigfont.png", dpi=300)
        plt.close()

print("✅ 時系列図 完了（整数→HH:MM変換・1時間刻み・横軸タイトル修正済）")


print("🎉 全図修正版（フォント拡大・凡例制御・シナリオ名変更）出力完了。")
