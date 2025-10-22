# -*- coding: utf-8 -*-
"""
交通流集計＋可視化（日本語フォント＋r05/r10除外＋台キロ対応＋7:00–18:30制限）
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

# ====== ユーティリティ ======
def should_skip(filename):
    """r05/r10を含むファイルをスキップ"""
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
    out = out[~out["link_id"].str.contains("|".join(EXCLUDE_KEYS))].copy()

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
    g["flow_kmveh"] = g["dist_m"] / 1000.0  # 総走行距離（台キロ）
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

print({k: len(v) for k, v in scenarios.items()})

# ====== 集計 ======
totals_records, timeseries_all, records_all, skipped_records = [], [], [], []

for scen, files in scenarios.items():
    perlink_all, V_runs, TTT_runs, Q_runs, ts_runs = [], [], [], [], []

    for f in files:
        volspd_name = os.path.basename(f)
        vol_name = volspd_name.replace("_volspd.csv", "_vol.csv")
        vol_path = str(Path(f).with_name(vol_name))

        df = load_volspd(f)
        V_net, TTT, dist_kmveh = network_metrics(df)
        ts = network_timeseries(df)

        # 時間範囲を 7:00〜18:30 に制限
        ts = ts[(ts["slot_code"] >= TIME_START) & (ts["slot_code"] <= TIME_END)]

        V_runs.append(V_net)
        TTT_runs.append(TTT)
        Q_runs.append(dist_kmveh)
        ts["run"] = volspd_name
        ts["scenario"] = scen
        ts_runs.append(ts)

        records_all.append({
            "scenario": scen, "run": volspd_name,
            "V_net": V_net, "TTT": TTT, "dist_kmveh": dist_kmveh
        })

    if ts_runs:
        ts_df = pd.concat(ts_runs, ignore_index=True)
        ts_summary = ts_df.groupby(["scenario","timestr","slot_code"]).agg(
            V_net_mean=("V_net_kmh", "mean"),
            V_net_std =("V_net_kmh", "std"),
            TTT_mean  =("TTT_sec", "mean"),
            TTT_std   =("TTT_sec", "std"),
            flow_kmveh_mean=("flow_kmveh","mean"),
            flow_kmveh_std =("flow_kmveh","std"),
        ).reset_index()
        ts_summary.to_csv(out_dir / f"timeseries_{scen}.csv", index=False, encoding="utf-8-sig")
        timeseries_all.append(ts_summary)

    totals_records.append({
        "scenario": scen,
        "V_net_mean": np.nanmean(V_runs),
        "TTT_mean": np.nanmean(TTT_runs),
        "dist_kmveh_mean": np.nanmean(Q_runs),
        "n_runs": len(V_runs)
    })

# ====== 出力 ======
pd.DataFrame(totals_records).to_csv(out_dir / "totals_summary.csv", index=False, encoding="utf-8-sig")
if timeseries_all:
    pd.concat(timeseries_all, ignore_index=True).to_csv(out_dir / "timeseries_summary.csv", index=False, encoding="utf-8-sig")
pd.DataFrame(records_all).to_csv(out_dir / "all_runs_summary.csv", index=False, encoding="utf-8-sig")

print("✅ 集計完了:", out_dir)

#%% ====== 可視化 ======
import matplotlib
from matplotlib import font_manager as fm
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

matplotlib.use("Agg")
font_path = r"C:\Windows\Fonts\meiryo.ttc"
prop = fm.FontProperties(fname=font_path)
plt.rcParams['font.family'] = prop.get_name()
plt.rcParams['font.sans-serif'] = [prop.get_name()]
plt.rcParams['axes.unicode_minus'] = False
print("✅ 現在使用中のフォント:", prop.get_name())
sns.set(font=prop.get_name(), style="whitegrid")

# ====== データ読み込み ======
records_df = pd.read_csv(out_dir / "all_runs_summary.csv")
timeseries_all_df = pd.read_csv(out_dir / "timeseries_summary.csv")


# ====== 箱ひげ図 ======
order = sorted(records_df["scenario"].unique())

# 平均速度
plt.figure(figsize=(12,6))
sns.boxplot(x="scenario", y="V_net", data=records_df, order=order)
plt.title("平均速度の分布", fontproperties=prop)
plt.xlabel("シナリオ", fontproperties=prop); plt.ylabel("平均速度 [km/h]", fontproperties=prop)
plt.tight_layout(); plt.savefig(out_dir / "boxplot_speed.png", dpi=300); plt.close()

# 総走行距離
plt.figure(figsize=(12,6))
sns.boxplot(x="scenario", y="dist_kmveh", data=records_df, order=order)
plt.title("総走行距離（台キロ）の分布", fontproperties=prop)
plt.xlabel("シナリオ", fontproperties=prop)
plt.ylabel("総走行距離 [台・km]", fontproperties=prop)

plt.tight_layout(); plt.savefig(out_dir / "boxplot_distance.png", dpi=300); plt.close()

# 総旅行時間
plt.figure(figsize=(12,6))
sns.boxplot(x="scenario", y="TTT", data=records_df, order=order)
plt.title("総旅行時間の分布", fontproperties=prop)
plt.xlabel("シナリオ", fontproperties=prop); plt.ylabel("TTT [sec]", fontproperties=prop)
plt.tight_layout(); plt.savefig(out_dir / "boxplot_ttt.png", dpi=300); plt.close()

# ====== 折れ線図 ======
time_master = (timeseries_all_df[["timestr","slot_code"]]
               .drop_duplicates()
               .sort_values(["slot_code","timestr"]))
def _to_hhmm(row):
    sc = row.get("slot_code")
    if isinstance(sc, str) and len(sc)==4 and sc.isdigit():
        return f"{sc[:2]}:{sc[2:]}"
    s = str(row.get("timestr"))
    m = re.search(r'(\d{1,2}):(\d{2})', s)
    return f"{int(m.group(1)):02d}:{m.group(2)}" if m else s

time_master["hhmm"] = time_master.apply(_to_hhmm, axis=1)
pos_map = {t: i for i, t in enumerate(time_master["timestr"])}

def plot_timeseries(metric_col, ylabel, filename):
    plt.figure(figsize=(14,6))
    for scen in sorted(timeseries_all_df["scenario"].unique()):
        ts = timeseries_all_df[timeseries_all_df["scenario"]==scen].copy()
        ts = ts.sort_values(["slot_code","timestr"])

        # slot_code を文字列化して時間範囲でフィルタ
        ts["slot_code_str"] = ts["slot_code"].astype(str).str.zfill(4)
        ts = ts[(ts["slot_code_str"] >= TIME_START) & (ts["slot_code_str"] <= TIME_END)]

        x = ts["timestr"].map(pos_map).values
        y = ts[metric_col].values
        plt.plot(x, y, label=scen)

    n=len(time_master)
    step=max(1,n//16)
    tick_pos=np.arange(0,n,step)
    tick_lab=time_master["hhmm"].iloc[tick_pos]
    plt.xticks(tick_pos, tick_lab, rotation=0)
    plt.xlabel("時刻（HH:MM）")
    plt.ylabel(ylabel)
    plt.title(f"時間別 {ylabel}（各シナリオの平均）")
    plt.legend(ncol=2)
    plt.tight_layout()
    plt.savefig(out_dir/filename, dpi=300)
    plt.close()


# 時系列プロット
plot_timeseries("V_net_mean", "平均速度 [km/h]", "timeseries_speed.png")
plot_timeseries("TTT_mean", "TTT [sec]", "timeseries_ttt.png")
plot_timeseries("flow_kmveh_mean", "総走行距離 [台・km/15分]", "timeseries_distance.png")

print("✅ 図を保存しました：", out_dir)
