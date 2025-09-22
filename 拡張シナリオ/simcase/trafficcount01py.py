import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import glob
import os

# ====== 設定 ======
base_dir = Path("C:/Users/OguchiLab/OneDrive/デスクトップ/randy_utokyo/拡張シナリオ/simcase")
out_dir = base_dir / "analysis_vehicle_counts"
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

    # Zone を除外
    mask = ~out["link_id"].str.contains("|".join(EXCLUDE_KEYS))
    out = out.loc[mask].copy()

    if time_col:
        out["timeslot"] = df[time_col]
    else:
        out["timeslot"] = np.arange(len(df))

    return out

# ====== ファイル探索（no01～no08のみ対象） ======
scenarios = {}
for scen_dir in sorted(base_dir.glob("no[0-8][0-9]")):
    scen_name = scen_dir.name
    if int(scen_name[2:]) > 8:
        continue
    paths = []
    for rand_dir in scen_dir.glob("rand*"):
        paths += glob.glob(str(rand_dir / "*_volspd.csv"))
    scenarios[scen_name] = sorted(paths)

print({k: len(v) for k, v in scenarios.items()})

# ====== 総走行台数の時間帯別集計 ======
counts_all = []

for scen, files in scenarios.items():
    for f in files:
        if any(skip in f for skip in SKIP_FILES):
            print("Skipping outlier file:", f)
            continue
        df = load_volspd(f)
        g = df.groupby("timeslot").agg(total_count=("count", "sum")).reset_index()
        g["scenario"] = scen
        g["run"] = os.path.basename(f)
        counts_all.append(g)

counts_df = pd.concat(counts_all, ignore_index=True)

# シナリオ × 時間帯ごとの平均と標準偏差
counts_summary = counts_df.groupby(["scenario","timeslot"]).agg(
    count_mean=("total_count","mean"),
    count_std=("total_count","std")
).reset_index()

# CSVに保存
counts_summary.to_csv(out_dir / "vehicle_counts_summary.csv", index=False, encoding="utf-8-sig")

# ====== 折れ線グラフ（平均値のみ） ======
plt.figure(figsize=(12,6))
for scen in counts_summary["scenario"].unique():
    ts = counts_summary[counts_summary["scenario"] == scen]
    plt.plot(ts["timeslot"], ts["count_mean"], label=scen)

plt.legend()
plt.title("時間別 総走行台数（各シナリオ平均）")
plt.xlabel("時刻")
plt.ylabel("走行台数 [台]")
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig(out_dir / "timeseries_vehicle_counts.png", dpi=300)
plt.show()
plt.close()

print("✅ 総走行台数の分析完了：結果は", out_dir, "に保存されました")
