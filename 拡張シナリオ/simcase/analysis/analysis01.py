import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import glob
import os

# ====== 設定 ======
base_dir = Path("C:/Users/OguchiLab/OneDrive/デスクトップ/randy_utokyo/拡張シナリオ/simcase")
out_dir = base_dir / "analysis"
out_dir.mkdir(exist_ok=True)

# 除外条件（Zone のみ除外）
EXCLUDE_KEYS = ["Zone"]

# 除外ファイル（外れ値）
SKIP_FILES = [
    "Case1_no07_r05_volspd.csv",
    "Case1_no08_r10_volspd.csv"
]


# ====== 読み込み関数 ======
def load_volspd(path):
    df = pd.read_csv(path)
    link_col   = [c for c in df.columns if "link" in c.lower() or "id" in c.lower()][0]
    length_col = [c for c in df.columns if "len" in c.lower()][0]
    trvt_col   = [c for c in df.columns if "trvt" in c.lower()][0]
    count_col  = [c for c in df.columns if "count" in c.lower()][0]
    time_col   = [c for c in df.columns if "time" in c.lower() or "slot" in c.lower()]
    time_col   = time_col[0] if time_col else None

    out = pd.DataFrame()
    out["link_id"] = df[link_col].astype(str)
    out["length_m"] = pd.to_numeric(df[length_col], errors="coerce")
    out["trvt_s"]   = pd.to_numeric(df[trvt_col], errors="coerce").replace(-1, np.nan)
    out["count"]    = pd.to_numeric(df[count_col], errors="coerce").replace(-1, 0)

    # 除外リンク
    mask = ~out["link_id"].str.contains("|".join(EXCLUDE_KEYS))
    out = out.loc[mask].copy()

    if time_col:
        out["timeslot"] = df[time_col]
    else:
        out["timeslot"] = np.arange(len(df))

    out["row_dist_m"] = out["length_m"] * out["count"]
    out["row_time_s"] = out["trvt_s"] * out["count"]
    return out

def network_timeseries(df):
    g = df.groupby("timeslot").agg(
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

def per_link_TTT(df):
    g = df.groupby("link_id").agg(
        dist_m=("row_dist_m", "sum"),
        time_s=("row_time_s", "sum")
    ).reset_index()
    g["TTT_sec"] = g["time_s"]
    g["V_link_kmh"] = (g["dist_m"] / g["time_s"]) * 3.6
    return g.sort_values("TTT_sec", ascending=False)

# ====== ファイル探索（no01～no08のみ対象） ======
scenarios = {}
for scen_dir in sorted(base_dir.glob("no[0-8][0-9]")):
    scen_name = scen_dir.name
    if int(scen_name[2:]) > 8:  # no09以上はスキップ
        continue
    paths = []
    for rand_dir in scen_dir.glob("rand*"):
        paths += glob.glob(str(rand_dir / "*_volspd.csv"))
    scenarios[scen_name] = sorted(paths)

print({k: len(v) for k, v in scenarios.items()})

# ====== 集計 ======
totals_records = []
timeseries_all = []
records_all = []
skipped_records = []

for scen, files in scenarios.items():
    perlink_all = []
    V_runs, TTT_runs = [], []
    ts_runs = []

    for f in files:
        if any(skip in f for skip in SKIP_FILES):
            print("Skipping outlier file:", f)
            skipped_records.append({"scenario": scen, "file": os.path.basename(f)})
            continue

        df = load_volspd(f)
        V_net, TTT = network_metrics(df)
        V_runs.append(V_net)
        TTT_runs.append(TTT)

        ts = network_timeseries(df)
        ts["run"] = os.path.basename(f)
        ts["scenario"] = scen
        ts_runs.append(ts)

        perlink_all.append(per_link_TTT(df).assign(run=os.path.basename(f)))

        records_all.append({
            "scenario": scen,
            "run": os.path.basename(f),
            "V_net": V_net,
            "TTT": TTT
        })

    # ---- 全体平均値 ----
    totals_records.append({
        "scenario": scen,
        "V_net_mean": np.mean(V_runs),
        "V_net_std": np.std(V_runs, ddof=1),
        "TTT_mean": np.mean(TTT_runs),
        "TTT_std": np.std(TTT_runs, ddof=1),
        "n_runs": len(V_runs)
    })

    # ---- 時間別 ----
    ts_df = pd.concat(ts_runs, ignore_index=True)
    ts_summary = ts_df.groupby(["scenario","timeslot"]).agg(
        V_net_mean=("V_net_kmh", "mean"),
        V_net_std=("V_net_kmh", "std"),
        TTT_mean=("TTT_sec", "mean"),
        TTT_std=("TTT_sec", "std")
    ).reset_index()
    ts_summary.to_csv(out_dir / f"timeseries_{scen}.csv", index=False, encoding="utf-8-sig")
    timeseries_all.append(ts_summary)

    # ---- リンク別TTTランキング ----
    perlink_df = pd.concat(perlink_all, ignore_index=True)
    perlink_summary = perlink_df.groupby("link_id").agg(
        TTT_mean=("TTT_sec", "mean"),
        TTT_std=("TTT_sec", "std"),
        V_mean=("V_link_kmh", "mean")
    ).reset_index().sort_values("TTT_mean", ascending=False)
    perlink_summary.to_csv(out_dir / f"perlink_TTT_{scen}.csv", index=False, encoding="utf-8-sig")

# ---- 全体代表値まとめ ----
totals_df = pd.DataFrame(totals_records)
totals_df.to_csv(out_dir / "totals_summary.csv", index=False, encoding="utf-8-sig")

# ---- 全シナリオ時間別まとめ ----
timeseries_all_df = pd.concat(timeseries_all, ignore_index=True)
timeseries_all_df.to_csv(out_dir / "timeseries_summary.csv", index=False, encoding="utf-8-sig")

# ---- 全乱数結果まとめ ----
records_df = pd.DataFrame(records_all)
records_df.to_csv(out_dir / "all_runs_summary.csv", index=False, encoding="utf-8-sig")

# ---- スキップしたファイル記録 ----
pd.DataFrame(skipped_records).to_csv(out_dir / "skipped_files.csv", index=False, encoding="utf-8-sig")

# ====== 箱ひげ図 ======
plt.figure(figsize=(14,6))
plt.subplot(1,2,1)
sns.boxplot(x="scenario", y="V_net", data=records_df)
plt.title("平均速度 [km/h]")
plt.xlabel("Scenario")
plt.ylabel("速度 [km/h]")

plt.subplot(1,2,2)
sns.boxplot(x="scenario", y="TTT", data=records_df)
plt.title("総旅行時間 [sec]")
plt.xlabel("Scenario")
plt.ylabel("TTT [sec]")

plt.tight_layout()
plt.savefig(out_dir / "boxplot_metrics.png", dpi=300)
plt.show()
plt.close()

# ====== 折れ線図 ======
plt.figure(figsize=(12,6))
for scen in scenarios.keys():
    ts = timeseries_all_df[timeseries_all_df["scenario"] == scen]
    plt.plot(ts["timeslot"], ts["V_net_mean"], label=scen)

plt.legend()
plt.title("時間別ネットワーク平均速度（各シナリオ）")
plt.xlabel("時刻")
plt.ylabel("V_net [km/h]")
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig(out_dir / "timeseries_speed.png", dpi=300)
plt.show()
plt.close()

print("✅ 分析完了：結果は", out_dir, "に保存されました")
