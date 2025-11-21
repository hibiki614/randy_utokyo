# -*- coding: utf-8 -*-
"""
交通流集計＋可視化（日本語フォント＋r05/r10除外＋台キロ対応＋7:00–18:30制限）
全体／指定リンク群／非指定リンク群で平均速度・TTT・総走行距離を比較出力
@author: OguchiLab
"""

import pandas as pd
import numpy as np
from pathlib import Path
import glob, os, re

# ====== 設定 ======
base_dir = Path(r"C:/Users/hibik/github/randy_utokyo/拡張シナリオ/simcase22")
out_dir = base_dir / "analysis"
out_dir.mkdir(exist_ok=True)

EXCLUDE_KEYS = ["Zone"]
SKIP_PATTERNS = ["r05","r10"]
TIME_START = "0700"
TIME_END   = "1830"

# ★ここに追加（グローバル定義にしておく）★
scenario_labels = {
    "no01": "MV-×",
    "no02": "MV-〇",
    "no03": "1.0AV-×",
    "no04": "1.0AV-〇",
    "no05": "0.7AV-×",
    "no06": "0.7AV-〇",
    "no07": "0.5AV-×",
    "no08": "0.5AV-〇",
}


# 対象リンクリスト
TARGET_LINKS = {
    "533967_00940_13718_0",
    "I_11_533967_13718533967_00977",
    "533967_00939_01421_1",
    "I_11_533967_00977533967_01421",
    "I_11_533967_00977533967_01555",
    "533967_01555_14156_0",
    "533967_00766_14156_1",
    "I_11_533967_01555533967_00977",
    "533967_01555_14156_1",
    "533967_00766_14156_0",
    "533967_00766_11513_0",
    "533967_00538_11513_1",
    "533967_00766_11513_1",
    "533967_00538_11513_0",
}

# ====== ユーティリティ ======
def should_skip(filename):
    fname = os.path.basename(filename)
    return any(pat in fname for pat in SKIP_PATTERNS)

def _to_slot_code(val):
    try:
        s = str(val)
        m = re.search(r'(\d{1,2}):(\d{2})', s)
        if not m:
            return None
        hh = int(m.group(1)); mm = int(m.group(2))
        return f"{hh:02d}{mm:02d}"
    except Exception:
        return None

def load_volspd(path, link_filter=None, invert=False):
    df = pd.read_csv(path)
    link_col   = [c for c in df.columns if "link" in c.lower() or "id" in c.lower()][0]
    length_col = [c for c in df.columns if "len" in c.lower()][0]
    trvt_col   = [c for c in df.columns if "trvt" in c.lower()][0]
    count_col  = [c for c in df.columns if "count" in c.lower()][0]
    time_col_cands = [c for c in df.columns if "time" in c.lower() or "slot" in c.lower()]
    time_col   = time_col_cands[0] if time_col_cands else None

    out = pd.DataFrame()
    out["link_id"] = df[link_col].astype(str)
    out["length_m"] = pd.to_numeric(df[length_col], errors="coerce")
    out["trvt_s"]   = pd.to_numeric(df[trvt_col], errors="coerce").replace(-1, np.nan)
    out["count"]    = pd.to_numeric(df[count_col], errors="coerce").replace(-1, 0)

    out = out[~out["link_id"].str.contains("|".join(EXCLUDE_KEYS))].copy()

    # subset指定時のリンク抽出
    if link_filter is not None:
        if invert:
            out = out[~out["link_id"].isin(link_filter)]
        else:
            out = out[out["link_id"].isin(link_filter)]

    if time_col:
        out["timestr"] = df[time_col].astype(str)
        out["slot_code"] = out["timestr"].map(_to_slot_code)
    else:
        out["timestr"] = np.arange(len(df)).astype(str)
        out["slot_code"] = None

    out["row_dist_m"] = out["length_m"] * out["count"]
    out["row_time_s"] = out["trvt_s"] * out["count"]
    return out

def network_timeseries(df):
    g = df.groupby(["timestr","slot_code"], dropna=False).agg(
        dist_m=("row_dist_m", "sum"),
        time_s=("row_time_s", "sum")
    ).reset_index()
    g["V_net_kmh"] = (g["dist_m"] / g["time_s"]) * 3.6
    g["TTT_sec"]   = g["time_s"]
    g["flow_kmveh"] = g["dist_m"] / 1000.0
    return g

def network_metrics(df):
    dist_m = df["row_dist_m"].sum()
    time_s = df["row_time_s"].sum()
    V_net = (dist_m / time_s) * 3.6 if time_s > 0 else np.nan
    return V_net, time_s, dist_m / 1000.0

# ====== ファイル探索 ======
scenarios = {}
for scen_dir in sorted(base_dir.glob("no[0-9][0-9]")):
    scen = scen_dir.name
    try:
        if int(scen[2:]) > 8:
            continue
    except ValueError:
        continue
    files = sorted(glob.glob(str(scen_dir / "rand*" / "*_volspd.csv")))
    files = [f for f in files if not should_skip(f)]
    scenarios[scen] = files

print({k: len(v) for k,v in scenarios.items()})

# ====== 集計 ======
subsets = {"all": (None, False), "target": (TARGET_LINKS, False), "non_target": (TARGET_LINKS, True)}

records_all, timeseries_all, totals_records = [], [], []

for subset_label, (linkset, invert) in subsets.items():
    print(f"\n==== {subset_label} ====")
    for scen, files in scenarios.items():
        V_runs, TTT_runs, D_runs, ts_runs = [], [], [], []
        for f in files:
            df = load_volspd(f, linkset, invert)
            if df.empty:
                continue
            V_net, TTT, dist_kmveh = network_metrics(df)
            ts = network_timeseries(df)
            ts = ts[(ts["slot_code"] >= TIME_START) & (ts["slot_code"] <= TIME_END)]
            ts["scenario"] = scen; ts["run"] = os.path.basename(f); ts["subset"] = subset_label
            V_runs.append(V_net); TTT_runs.append(TTT); D_runs.append(dist_kmveh)
            ts_runs.append(ts)
            records_all.append({
                "scenario": scen, "run": os.path.basename(f), "subset": subset_label,
                "V_net": V_net, "TTT": TTT, "dist_kmveh": dist_kmveh
            })
        if ts_runs:
            ts_df = pd.concat(ts_runs, ignore_index=True)
            ts_summary = ts_df.groupby(["scenario","timestr","slot_code","subset"]).agg(
                V_net_mean=("V_net_kmh","mean"),
                TTT_mean=("TTT_sec","mean"),
                flow_kmveh_mean=("flow_kmveh","mean")
            ).reset_index()
            timeseries_all.append(ts_summary)
        totals_records.append({
            "scenario": scen, "subset": subset_label,
            "V_net_mean": np.nanmean(V_runs),
            "TTT_mean": np.nanmean(TTT_runs),
            "dist_kmveh_mean": np.nanmean(D_runs),
            "n_runs": len(V_runs)
        })

# ====== 出力 ======
pd.DataFrame(records_all).to_csv(out_dir/"all_runs_summary_subset.csv", index=False, encoding="utf-8-sig")
pd.DataFrame(totals_records).to_csv(out_dir/"totals_summary_subset.csv", index=False, encoding="utf-8-sig")
pd.concat(timeseries_all, ignore_index=True).to_csv(out_dir/"timeseries_summary_subset.csv", index=False, encoding="utf-8-sig")
print("✅ CSV出力完了:", out_dir)

#%% ====== 可視化 ======
import matplotlib
from matplotlib import font_manager as fm
import matplotlib.pyplot as plt
import seaborn as sns

font_path = r"C:\Windows\Fonts\meiryo.ttc"
prop = fm.FontProperties(fname=font_path)
plt.rcParams["font.family"] = prop.get_name()
plt.rcParams["axes.unicode_minus"] = False
sns.set(style="whitegrid", font=prop.get_name())

records_df = pd.read_csv(out_dir/"all_runs_summary_subset.csv")
timeseries_all_df = pd.read_csv(out_dir/"timeseries_summary_subset.csv")

# ===== 箱ひげ図（速度・距離・TTT） =====
for subset_label in ["all","target","non_target"]:
    df = records_df[records_df["subset"]==subset_label]
    order = sorted(df["scenario"].unique())

    def save_boxplot(ycol, title, ylabel, fname):
        plt.figure(figsize=(12,6))
        sns.boxplot(x="scenario", y=ycol, data=df, order=order)
        plt.title(f"{title}（{subset_label}）", fontproperties=prop)
        plt.xlabel("シナリオ", fontproperties=prop)
        plt.ylabel(ylabel, fontproperties=prop)
        plt.tight_layout()
        plt.savefig(out_dir/f"{fname}_{subset_label}.png", dpi=300)
        plt.close()

    save_boxplot("V_net", "平均速度の分布", "平均速度 [km/h]", "boxplot_speed")
    save_boxplot("dist_kmveh", "総走行距離（台キロ）の分布", "総走行距離 [台・km]", "boxplot_distance")
    save_boxplot("TTT", "総旅行時間の分布", "TTT [sec]", "boxplot_ttt")

# ===== 折れ線図（15分間隔を等間隔＋モノクロ：×シナリオ4本だけ） =====
def _to_hhmm(sc):
    if isinstance(sc, str) and len(sc) == 4 and sc.isdigit():
        return f"{sc[:2]}:{sc[2:]}"
    return sc

# 上のほうで定義済みを前提
# scenario_labels = {
#     "no01": "MV-×",
#     "no02": "MV-〇",
#     "no03": "1.0AV-×",
#     "no04": "1.0AV-〇",
#     "no05": "0.7AV-×",
#     "no06": "0.7AV-〇",
#     "no07": "0.5AV-×",
#     "no08": "0.5AV-〇",
# }

# 折れ線で描くのは「×」シナリオだけ
PLOT_SCENARIOS = ["no01", "no03", "no05", "no07"]

# 形（マーカー）で AV レベルを区別（濃さは全部同じでもOKだが少し変化を残す）
style_map = {
    "no01": {"marker": "o", "color": "0.1"},  # MV-×
    "no03": {"marker": "s", "color": "0.3"}, # 1.0AV-×
    "no05": {"marker": "^", "color": "0.45"},  # 0.7AV-×
    "no07": {"marker": "D", "color": "0.6"}, # 0.5AV-×
}

for subset_label in ["all", "target", "non_target"]:
    df = timeseries_all_df[timeseries_all_df["subset"] == subset_label].copy()
    df = df[df["slot_code"].notna()].copy()

    # ==== 15分スロットを等間隔の数値軸に変換 ====
    slot_list = sorted(df["slot_code"].unique())  # "0700","0715",...
    slot_to_idx = {sc: i for i, sc in enumerate(slot_list)}
    df["t_idx"] = df["slot_code"].map(slot_to_idx)
    df["hhmm"] = df["slot_code"].map(_to_hhmm)

    # シナリオは「×」だけに限定
    scenarios_order = [s for s in PLOT_SCENARIOS if s in df["scenario"].unique()]

    def save_ts(ycol, ylabel, fname):
        plt.figure(figsize=(16, 8))  # 少し大きめ

        for scen in scenarios_order:
            sub = df[df["scenario"] == scen].sort_values("t_idx")
            if sub.empty:
                continue

            style = style_map.get(scen, {"marker": "o", "color": "0.3"})
            label = scenario_labels.get(scen, scen)  # MV-× / 1.0AV-× など

            plt.plot(
                sub["t_idx"],          # 等間隔の数値軸
                sub[ycol],
                label=label,
                linestyle="solid",
                marker=style["marker"],
                linewidth=0.7,
                markersize=8,
                color=style["color"],
            )

        # x軸：1時間ごと（= 4スロットごと）にラベル表示
        tick_step = 4  # 15分×4 = 1時間
        ticks = list(range(0, len(slot_list), tick_step))
        tick_labels = [_to_hhmm(slot_list[i]) for i in ticks]
        plt.xticks(ticks, tick_labels, rotation=45, fontsize=20)

        plt.yticks(fontsize=20)
        plt.xlabel("時刻（HH:MM）", fontproperties=prop, fontsize=25)
        plt.ylabel(ylabel, fontproperties=prop, fontsize=25)
        plt.title(f"時間別 {ylabel}（{subset_label}）", fontproperties=prop, fontsize=20)
        plt.legend(ncol=2, fontsize=25)
        plt.grid(True, axis="y", alpha=0.3)

        plt.tight_layout()
        plt.savefig(out_dir / f"{fname}_{subset_label}.png", dpi=300)
        plt.close()

    save_ts("V_net_mean", "平均速度 [km/h]", "timeseries_speed")
    save_ts("TTT_mean", "TTT [sec]", "timeseries_ttt")
    save_ts("flow_kmveh_mean", "総走行距離 [台・km/15分]", "timeseries_distance")


print("✅ 全図保存完了:", out_dir)

#%% ====== 完全修正版：全体・対象・非対象リンクの3指標を縦長1枚で可視化 ======
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np

print("📊 修正版：全体・対象リンク・非対象リンクの比較図を作成中...")

#--- no01を基準に相対化（subset単位で） ---
base_df = records_df[records_df["scenario"] == "no01"].groupby("subset").mean(numeric_only=True)
records_df = records_df.copy()
records_df["TTT_rel"] = records_df.apply(
    lambda r: r["TTT"] / base_df.loc[r["subset"], "TTT"], axis=1)
records_df["dist_kmveh_rel"] = records_df.apply(
    lambda r: r["dist_kmveh"] / base_df.loc[r["subset"], "dist_kmveh"], axis=1)

# --- 設定 ---
colors = {"all": "tab:blue", "target": "tab:red", "non_target": "tab:gray"}
order = sorted(records_df["scenario"].unique())
subsets = ["all", "target", "non_target"]
metrics = [
    ("V_net", "平均速度 [km/h]", False),
    ("TTT_rel", "総旅行時間 [no01比]", True),
    ("dist_kmveh_rel", "総走行距離 [no01比]", True)
]

fig, axes = plt.subplots(3, 1, figsize=(10, 14), sharex=True)

# --- プロット ---
for ax, (col, label, rel) in zip(axes, metrics):
    width = 0.25
    spacing = 0.25  # 横方向のずらし幅
    for i, subset in enumerate(subsets):
        subdf = records_df[records_df["subset"] == subset]
        if subdf.empty:
            continue
        x_positions = np.arange(len(order)) + (i - 1) * spacing
        data = [subdf.loc[subdf["scenario"] == s, col].dropna() for s in order]
        bp = ax.boxplot(
            data,
            positions=x_positions,
            widths=width,
            patch_artist=True,
            boxprops=dict(facecolor=colors[subset], alpha=0.7),
            medianprops=dict(color="black", linewidth=1.5),
            whiskerprops=dict(color="black"),
            capprops=dict(color="black"),
            flierprops=dict(marker="o", markersize=2, color="gray", alpha=0.5),
        )
    ax.set_xticks(np.arange(len(order)))
    ax.set_xticklabels(order, rotation=0)
    ax.set_ylabel(label, fontproperties=prop)
    ax.grid(True, axis="y", alpha=0.3)
    if rel:
        ax.axhline(1.0, color="black", linestyle="--", linewidth=1)
    for tick in ax.get_xticklabels() + ax.get_yticklabels():
        tick.set_fontsize(11)

axes[-1].set_xlabel("シナリオ", fontproperties=prop)

# --- 凡例を上部に一括表示 ---
handles = [
    plt.Line2D([0], [0], color=colors["all"], lw=8, label="全体"),
    plt.Line2D([0], [0], color=colors["target"], lw=8, label="対象リンクのみ"),
    plt.Line2D([0], [0], color=colors["non_target"], lw=8, label="対象外リンクのみ")
]
fig.legend(handles=handles, loc="upper center", ncol=3, fontsize=11, frameon=False)

fig.suptitle("全体・対象リンク・非対象リンクにおける各指標の比較", fontproperties=prop, fontsize=14)
plt.tight_layout(rect=[0, 0, 1, 0.95])
save_path = out_dir / "boxplot_combined_vertical.png"
fig.savefig(save_path, dpi=300)
plt.close()

print(f"✅ 縦長1枚の箱ひげ図を保存しました: {save_path}")

#%% ====== 図1：交通全体（絶対値ver・タイトルのみ） ======
print("📊 図1：交通全体（タイトルのみ）を描画中...")

records_all = records_df[records_df["subset"] == "all"].copy()
if records_all.empty:
    raise ValueError("subset='all' のデータが見つかりません。")

metrics = [
    ("V_net", "平均速度 [km/h]", None),
    ("TTT", "総旅行時間 [sec]", None),
    ("dist_kmveh", "総走行距離 [台・km]", None)
]
order = sorted(records_all["scenario"].unique())

fig, axes = plt.subplots(3, 1, figsize=(10, 14), sharex=True)

for ax, (col, label, ylim) in zip(axes, metrics):
    sns.boxplot(
        data=records_all,
        x="scenario", y=col, order=order,
        color="tab:blue", width=0.5,
        boxprops={"alpha": 0.8},
        showfliers=True,
        flierprops={"marker": "o", "markersize": 3, "alpha": 0.4},
        ax=ax
    )
    ax.set_ylabel(label, fontproperties=prop)
    if ylim: ax.set_ylim(*ylim)
    ax.grid(True, axis="y", alpha=0.3)
    for t in ax.get_yticklabels(): t.set_fontsize(10)
axes[-1].set_xlabel("シナリオ", fontproperties=prop)

# === タイトルのみ ===
axes[0].text(
    0.5, 1.1, "ネットワーク全体における各指標の比較",
    ha="center", va="bottom", transform=axes[0].transAxes,
    fontproperties=prop, fontsize=14
)

plt.tight_layout(rect=[0, 0, 1, 0.95])
save_path1 = out_dir / "boxplot_all_absolute_inaxis_nolegend.png"
fig.savefig(save_path1, dpi=300)
plt.close()
print(f"✅ 図1保存: {save_path1}")



#%% ====== 図2：対象リンク vs 非対象リンク（タイトル＆凡例削除＋シナリオ名変更＋文字大） ======
print("📊 図2：タイトル・凡例調整＆シナリオ名変更版を描画中...")


records_df["scenario_label"] = records_df["scenario"].map(scenario_labels)
order = [scenario_labels[k] for k in sorted(scenario_labels.keys())]

# --- 相対値を生成（no01比） ---
if "TTT_rel" not in records_df.columns:
    base_df = records_df[records_df["scenario"] == "no01"].groupby("subset").mean(numeric_only=True)
    records_df["TTT_rel"] = records_df.apply(
        lambda r: r["TTT"] / base_df.loc[r["subset"], "TTT"], axis=1)
    records_df["dist_kmveh_rel"] = records_df.apply(
        lambda r: r["dist_kmveh"] / base_df.loc[r["subset"], "dist_kmveh"], axis=1)

subsets = ["target", "non_target"]
colors = {"target": "tab:red", "non_target": "tab:gray"}
metrics = [
    ("V_net", "平均速度 [km/h]", False),
    ("TTT_rel", "総旅行時間 [no01比]", True),
    ("dist_kmveh_rel", "総走行距離 [no01比]", True)
]

fig, axes = plt.subplots(3, 1, figsize=(12, 16), sharex=True)

# --- プロット ---
for ax, (col, label, rel) in zip(axes, metrics):
    width = 0.25
    spacing = 0.25
    for i, subset in enumerate(subsets):
        subdf = records_df[records_df["subset"] == subset]
        if subdf.empty:
            continue
        x_positions = np.arange(len(order)) + (i - 0.5) * spacing
        data = [subdf.loc[subdf["scenario_label"] == s, col].dropna() for s in order]
        ax.boxplot(
            data,
            positions=x_positions,
            widths=width,
            patch_artist=True,
            boxprops=dict(facecolor=colors[subset], alpha=0.7),
            medianprops=dict(color="black", linewidth=1.5),
            whiskerprops=dict(color="black", linewidth=1.0),
            capprops=dict(color="black", linewidth=1.0),
            flierprops=dict(marker="o", markersize=3, color="gray", alpha=0.5),
        )

    ax.set_xticks(np.arange(len(order)))
    ax.set_xticklabels(order, fontsize=13)
    ax.set_ylabel(label, fontproperties=prop, fontsize=14)
    ax.grid(True, axis="y", alpha=0.3)
    if rel:
        ax.axhline(1.0, color="black", linestyle="--", linewidth=1.0)
    for tick in ax.get_yticklabels():
        tick.set_fontsize(12)

axes[-1].set_xlabel("シナリオ", fontproperties=prop, fontsize=14)

# === タイトルのみ ===
axes[0].text(
    0.5, 1.12,
    "対象リンクと非対象リンクにおける各指標の比較",
    ha="center", va="bottom", transform=axes[0].transAxes,
    fontproperties=prop, fontsize=17
)

plt.tight_layout(rect=[0, 0, 1, 0.95])
save_path2 = out_dir / "boxplot_target_vs_nontarget_inaxis_largefont_nolegend.png"
fig.savefig(save_path2, dpi=300)
plt.close()
print(f"✅ 図2保存（大文字＆凡例削除＆シナリオ名変更版）: {save_path2}")
