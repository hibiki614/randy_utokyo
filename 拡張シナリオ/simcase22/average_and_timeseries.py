# -*- coding: utf-8 -*-
"""
Created on Tue Sep 30 13:34:57 2025

@author: OguchiLab
"""

import pandas as pd
import numpy as np
from pathlib import Path
import glob, os, re

# ====== 設定 ======
base_dir = Path(r"C:/Users/OguchiLab/OneDrive/デスクトップ/randy_utokyo/拡張シナリオ/simcase")
out_dir = base_dir / "analysis"
out_dir.mkdir(exist_ok=True)

EXCLUDE_KEYS = ["Zone"]
SKIP_FILES = {
    "Case1_no07_r05_vol.csv",
    "Case1_no07_r05_volspd.csv",
    "Case1_no08_r10_vol.csv",
    "Case1_no08_r10_volspd.csv",
}

# ====== ユーティリティ ======
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

def load_volspd(path):
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

    # 除外リンク
    mask = ~out["link_id"].str.contains("|".join(EXCLUDE_KEYS))
    out = out.loc[mask].copy()

    # 時刻
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
    return g

def network_metrics(df):
    dist_m = df["row_dist_m"].sum()
    time_s = df["row_time_s"].sum()
    V_net = (dist_m / time_s) * 3.6 if time_s > 0 else np.nan
    return V_net, time_s

def per_link_metrics(df):
    """リンク別に TTT・速度・通過台数を算出"""
    g = df.groupby("link_id").agg(
        dist_m=("row_dist_m", "sum"),
        time_s=("row_time_s", "sum"),
        flow_veh=("count", "sum")
    ).reset_index()
    g["TTT_sec"] = g["time_s"]
    g["V_link_kmh"] = (g["dist_m"] / g["time_s"]) * 3.6
    return g.sort_values("TTT_sec", ascending=False)

def read_total_from_vol(vol_path):
    vdf = pd.read_csv(vol_path)
    total_cols = [c for c in vdf.columns if c.lower() == "total"]
    if total_cols:
        return pd.to_numeric(vdf[total_cols[0]], errors="coerce").sum()
    quarter_cols = [c for c in vdf.columns if c.lower().startswith("vol_")]
    if quarter_cols:
        return pd.to_numeric(vdf[quarter_cols], errors="coerce").sum(axis=1).sum()
    return np.nan

def read_flow_timeseries_from_vol(vol_path):
    vdf = pd.read_csv(vol_path)
    quarter_cols = [c for c in vdf.columns if c.lower().startswith("vol_")]
    flow_ts = {}
    for c in quarter_cols:
        code = c.split("_", 1)[1]
        flow_ts[code] = pd.to_numeric(vdf[c], errors="coerce").sum()
    return flow_ts

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
    scenarios[scen] = files

print({k: len(v) for k, v in scenarios.items()})

# ====== 集計 ======
totals_records, timeseries_all, records_all, skipped_records = [], [], [], []

for scen, files in scenarios.items():
    perlink_all, V_runs, TTT_runs, Q_runs, ts_runs = [], [], [], [], []

    for f in files:
        volspd_name = os.path.basename(f)
        vol_name = volspd_name.replace("_volspd.csv", "_vol.csv")
        vol_path = str(Path(f).with_name(vol_name))

        if volspd_name in SKIP_FILES or os.path.basename(vol_path) in SKIP_FILES:
            skipped_records.append({"scenario": scen, "file": volspd_name})
            continue

        df = load_volspd(f)
        V_net, TTT = network_metrics(df)
        ts = network_timeseries(df)

        traffic_total = read_total_from_vol(vol_path)
        flow_ts = read_flow_timeseries_from_vol(vol_path)
        ts["flow_veh"] = ts["slot_code"].map(flow_ts) if "slot_code" in ts.columns else np.nan

        V_runs.append(V_net); TTT_runs.append(TTT); Q_runs.append(traffic_total)
        ts["run"] = volspd_name; ts["scenario"] = scen
        ts_runs.append(ts)

        perlink_all.append(per_link_metrics(df).assign(run=volspd_name))

        records_all.append({
            "scenario": scen, "run": volspd_name,
            "V_net": V_net, "TTT": TTT, "traffic_total": traffic_total
        })

    totals_records.append({
        "scenario": scen,
        "V_net_mean": np.nanmean(V_runs),
        "V_net_std":  np.nanstd(V_runs, ddof=1) if len(V_runs) > 1 else np.nan,
        "TTT_mean":   np.nanmean(TTT_runs),
        "TTT_std":    np.nanstd(TTT_runs, ddof=1) if len(TTT_runs) > 1 else np.nan,
        "traffic_total_mean": np.nanmean(Q_runs),
        "traffic_total_std":  np.nanstd(Q_runs, ddof=1) if len(Q_runs) > 1 else np.nan,
        "n_runs": len(V_runs)
    })

    if ts_runs:
        ts_df = pd.concat(ts_runs, ignore_index=True)
        ts_summary = ts_df.groupby(["scenario","timestr","slot_code"]).agg(
            V_net_mean=("V_net_kmh", "mean"),
            V_net_std =("V_net_kmh", "std"),
            TTT_mean  =("TTT_sec",   "mean"),
            TTT_std   =("TTT_sec",   "std"),
            flow_veh_mean=("flow_veh","mean"),
            flow_veh_std =("flow_veh","std"),
        ).reset_index()
        ts_summary.to_csv(out_dir / f"timeseries_{scen}.csv", index=False, encoding="utf-8-sig")
        timeseries_all.append(ts_summary)

    # ==== リンク別指標 ====
    if perlink_all:
        perlink_df = pd.concat(perlink_all, ignore_index=True)
        perlink_summary = perlink_df.groupby("link_id").agg(
            TTT_mean=("TTT_sec", "mean"),
            TTT_std =("TTT_sec", "std"),
            V_mean  =("V_link_kmh", "mean"),
            V_std   =("V_link_kmh", "std"),
            flow_mean=("flow_veh","mean"),
            flow_std =("flow_veh","std"),
        ).reset_index().sort_values("TTT_mean", ascending=False)
        perlink_summary.to_csv(out_dir / f"perlink_metrics_{scen}.csv", index=False, encoding="utf-8-sig")

pd.DataFrame(totals_records).to_csv(out_dir / "totals_summary.csv", index=False, encoding="utf-8-sig")
if timeseries_all:
    pd.concat(timeseries_all, ignore_index=True).to_csv(out_dir / "timeseries_summary.csv", index=False, encoding="utf-8-sig")
pd.DataFrame(records_all).to_csv(out_dir / "all_runs_summary.csv", index=False, encoding="utf-8-sig")
pd.DataFrame(skipped_records).to_csv(out_dir / "skipped_files.csv", index=False, encoding="utf-8-sig")

print("✅ 集計完了:", out_dir)

#%%
import matplotlib
from matplotlib import font_manager as fm
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from pathlib import Path

base_dir = Path(r"C:/Users/OguchiLab/OneDrive/デスクトップ/randy_utokyo/拡張シナリオ/simcase")
out_dir = base_dir / "analysis"

# ====== 日本語フォント ======
JP_FONT_CANDIDATES = [
    "Meiryo", "Yu Gothic", "MS Gothic",
    "Hiragino Sans", "Hiragino Kaku Gothic ProN",
    "Noto Sans CJK JP", "IPAPGothic", "IPAMincho"
]
installed = set(f.name for f in fm.fontManager.ttflist)
for name in JP_FONT_CANDIDATES:
    if name in installed:
        matplotlib.rcParams["font.family"] = name
        matplotlib.rcParams["axes.unicode_minus"] = False
        break

sns.set(style="whitegrid")

# ====== データ読み込み ======
records_df = pd.read_csv(out_dir / "all_runs_summary.csv")
timeseries_all_df = pd.read_csv(out_dir / "timeseries_summary.csv")

# ====== 箱ひげ図（3枚） ======
order = sorted(records_df["scenario"].unique())

# 速度
plt.figure(figsize=(12,6))
sns.boxplot(x="scenario", y="V_net", data=records_df, order=order)
plt.title("平均速度の分布（20乱数）")
plt.xlabel("Scenario"); plt.ylabel("平均速度 [km/h]")
plt.tight_layout(); plt.savefig(out_dir / "boxplot_speed.png", dpi=300); plt.close()

# 交通量（総走行台数）
plt.figure(figsize=(12,6))
sns.boxplot(x="scenario", y="traffic_total", data=records_df, order=order)
plt.title("総走行台数の分布（20乱数）")
plt.xlabel("Scenario"); plt.ylabel("総走行台数 [台]")
plt.tight_layout(); plt.savefig(out_dir / "boxplot_traffic.png", dpi=300); plt.close()

# TTT
plt.figure(figsize=(12,6))
sns.boxplot(x="scenario", y="TTT", data=records_df, order=order)
plt.title("総旅行時間の分布（20乱数）")
plt.xlabel("Scenario"); plt.ylabel("TTT [sec]")
plt.tight_layout(); plt.savefig(out_dir / "boxplot_ttt.png", dpi=300); plt.close()

# ====== 折れ線図（3枚：シナリオ別の平均時系列；時刻はHH:MMで水平表示） ======
import numpy as np

# 1) まず全体で“時刻の並び”を作る（slot_code → HH:MM）
time_master = (timeseries_all_df[["timestr","slot_code"]]
               .drop_duplicates()
               .sort_values(["slot_code","timestr"]))
# HH:MM ラベル（slot_code が無い/欠損でも timestr から拾えるようフォールバック）
def _to_hhmm(row):
    sc = row.get("slot_code")
    if isinstance(sc, str) and len(sc) == 4 and sc.isdigit():
        return f"{sc[:2]}:{sc[2:]}"
    s = str(row.get("timestr"))
    m = re.search(r'(\d{1,2}):(\d{2})', s)
    return f"{int(m.group(1)):02d}:{m.group(2)}" if m else s

time_master["hhmm"] = time_master.apply(_to_hhmm, axis=1)
# x軸位置（0,1,2,...）に対応させるマップ
pos_map = {t: i for i, t in enumerate(time_master["timestr"])}

def plot_timeseries(metric_col, ylabel, filename, ylim=None):
    plt.figure(figsize=(14,6))
    for scen in sorted(timeseries_all_df["scenario"].unique()):
        ts = timeseries_all_df[timeseries_all_df["scenario"] == scen].copy()
        ts = ts.sort_values(["slot_code","timestr"])
        # xを連番にする（カテゴリ軸の詰まりと傾きを回避）
        x = ts["timestr"].map(pos_map).values
        y = ts[metric_col].values
        plt.plot(x, y, label=scen)

    # 目盛りは等間隔に間引いて見やすく
    n = len(time_master)
    step = max(1, n // 16)  # だいたい16目盛り以内
    tick_pos = np.arange(0, n, step)
    tick_lab = time_master["hhmm"].iloc[tick_pos]

    plt.xticks(tick_pos, tick_lab, rotation=0)   # 水平に
    plt.xlabel("時刻（HH:MM）")
    plt.ylabel(ylabel)
    if ylim is not None:
        plt.ylim(*ylim)
    plt.title(f"時間別 {ylabel}（各シナリオの平均）")
    plt.legend(ncol=2)
    plt.tight_layout()
    plt.savefig(out_dir / filename, dpi=300)
    plt.close()

# 速度（平均）
plot_timeseries("V_net_mean", "平均速度 [km/h]", "timeseries_speed.png")
# TTT（平均）
plot_timeseries("TTT_mean", "TTT [sec]", "timeseries_ttt.png")
# 流量（通過台数の合計、平均）
plot_timeseries("flow_veh_mean", "通過台数（合計）[台/15分]", "timeseries_flow.png")


print("✅ 図を保存しました：", out_dir)
