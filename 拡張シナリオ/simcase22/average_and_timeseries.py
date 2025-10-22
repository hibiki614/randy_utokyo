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
base_dir = Path(r"C:/Users/OguchiLab/OneDrive/デスクトップ/randy_utokyo/拡張シナリオ/simcase22")
out_dir = base_dir / "analysis"
out_dir.mkdir(exist_ok=True)

EXCLUDE_KEYS = ["Zone"]
SKIP_PATTERNS = ["r05","r10"]
TIME_START = "0700"
TIME_END   = "1830"

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

# ===== 折れ線図（速度・距離・TTT） =====
def _to_hhmm(sc):
    if isinstance(sc,str) and len(sc)==4 and sc.isdigit():
        return f"{sc[:2]}:{sc[2:]}"
    return sc

for subset_label in ["all","target","non_target"]:
    df = timeseries_all_df[timeseries_all_df["subset"]==subset_label].copy()
    df["hhmm"] = df["slot_code"].map(_to_hhmm)

    def save_ts(ycol, ylabel, fname):
        plt.figure(figsize=(14,6))
        for scen in sorted(df["scenario"].unique()):
            sub = df[df["scenario"]==scen]
            plt.plot(sub["hhmm"], sub[ycol], label=scen)
        plt.xlabel("時刻（HH:MM）", fontproperties=prop)
        plt.ylabel(ylabel, fontproperties=prop)
        plt.title(f"時間別 {ylabel}（{subset_label}）", fontproperties=prop)
        plt.legend(ncol=2)
        plt.tight_layout()
        plt.savefig(out_dir/f"{fname}_{subset_label}.png", dpi=300)
        plt.close()

    save_ts("V_net_mean", "平均速度 [km/h]", "timeseries_speed")
    save_ts("TTT_mean", "TTT [sec]", "timeseries_ttt")
    save_ts("flow_kmveh_mean", "総走行距離 [台・km/15分]", "timeseries_distance")

print("✅ 全図保存完了:", out_dir)
