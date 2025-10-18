import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import glob
import os

# ====== 設定 ======
base_dir = Path(r"C:/Users/OguchiLab/OneDrive/デスクトップ/randy_utokyo/拡張シナリオ/simcase")
out_dir = base_dir / "analysis"
out_dir.mkdir(exist_ok=True)

# 除外条件（リンク名に "Zone" を含むものは除外）
EXCLUDE_KEYS = ["Zone"]

# 除外ファイル（外れ値）※vol/volspd 両方
SKIP_FILES = {
    "Case1_no07_r05_vol.csv",
    "Case1_no07_r05_volspd.csv",
    "Case1_no08_r10_vol.csv",
    "Case1_no08_r10_volspd.csv",
}

# ====== 読み込み関数（volspd） ======
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
    return V_net, time_s  # time_s がネットワークTTT[sec]

def per_link_TTT(df):
    g = df.groupby("link_id").agg(
        dist_m=("row_dist_m", "sum"),
        time_s=("row_time_s", "sum")
    ).reset_index()
    g["TTT_sec"] = g["time_s"]
    g["V_link_kmh"] = (g["dist_m"] / g["time_s"]) * 3.6
    return g.sort_values("TTT_sec", ascending=False)

def read_total_from_vol(vol_path):
    """vol.csv から Total 列（大文字小文字どちらでも）を見つけて合計を返す"""
    vdf = pd.read_csv(vol_path)
    # 列名候補を柔軟に探索
    total_cols = [c for c in vdf.columns if c.lower() == "total"]
    if not total_cols:
        # もし 15分列だけで構成され Total が無い場合、全15分列を合算
        quarter_cols = [c for c in vdf.columns if c.lower().startswith("vol_")]
        if not quarter_cols:
            return np.nan
        return pd.to_numeric(vdf[quarter_cols], errors="coerce").sum(axis=1).sum()
    total_col = total_cols[0]
    return pd.to_numeric(vdf[total_col], errors="coerce").sum()

# ====== ファイル探索（no01～no08のみ） ======
scenarios = {}
for scen_dir in sorted(base_dir.glob("no[0-9][0-9]")):
    scen_name = scen_dir.name
    # no09以上はスキップ
    try:
        if int(scen_name[2:]) > 8:
            continue
    except ValueError:
        continue
    paths = []
    for rand_dir in sorted(scen_dir.glob("rand*")):
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
    V_runs, TTT_runs, Q_runs = [], [], []
    ts_runs = []

    for f in files:
        volspd_name = os.path.basename(f)
        vol_name = volspd_name.replace("_volspd.csv", "_vol.csv")
        vol_path = str(Path(f).with_name(vol_name))

        # 除外（vol/volspd どちらかがヒットしたらスキップ）
        if volspd_name in SKIP_FILES or os.path.basename(vol_path) in SKIP_FILES:
            print("Skipping outlier file:", volspd_name, " / ", os.path.basename(vol_path))
            skipped_records.append({"scenario": scen, "file": volspd_name})
            continue

        # ここから集計
        df = load_volspd(f)
        V_net, TTT = network_metrics(df)
        ts = network_timeseries(df)

        # 総走行台数（vol.csv から Total 合計）
        traffic_total = read_total_from_vol(vol_path)

        # 蓄積
        V_runs.append(V_net)
        TTT_runs.append(TTT)
        Q_runs.append(traffic_total)

        ts["run"] = volspd_name
        ts["scenario"] = scen
        ts_runs.append(ts)

        perlink_all.append(per_link_TTT(df).assign(run=volspd_name))

        records_all.append({
            "scenario": scen,
            "run": volspd_name,
            "V_net": V_net,                # 平均速度 [km/h]
            "TTT": TTT,                    # 総旅行時間 [sec]
            "traffic_total": traffic_total # 総走行台数
        })

    # ---- シナリオごとの代表値 ----
    totals_records.append({
        "scenario": scen,
        "V_net_mean": np.nanmean(V_runs),
        "V_net_std": np.nanstd(V_runs, ddof=1) if len(V_runs) > 1 else np.nan,
        "TTT_mean": np.nanmean(TTT_runs),
        "TTT_std": np.nanstd(TTT_runs, ddof=1) if len(TTT_runs) > 1 else np.nan,
        "traffic_total_mean": np.nanmean(Q_runs),
        "traffic_total_std": np.nanstd(Q_runs, ddof=1) if len(Q_runs) > 1 else np.nan,
        "n_runs": len(V_runs)
    })

    # ---- 時間別出力 ----
    if ts_runs:
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
    if perlink_all:
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
if timeseries_all:
    timeseries_all_df = pd.concat(timeseries_all, ignore_index=True)
    timeseries_all_df.to_csv(out_dir / "timeseries_summary.csv", index=False, encoding="utf-8-sig")
else:
    timeseries_all_df = pd.DataFrame()

# ---- 全乱数結果まとめ ----
records_df = pd.DataFrame(records_all)
records_df.to_csv(out_dir / "all_runs_summary.csv", index=False, encoding="utf-8-sig")

# ---- スキップしたファイル記録 ----
pd.DataFrame(skipped_records).to_csv(out_dir / "skipped_files.csv", index=False, encoding="utf-8-sig")

print("records_df shape:", records_df.shape)
print(records_df.head())

# ====== 箱ひげ図（3枚） ======
import matplotlib
from matplotlib import font_manager as fm
import matplotlib.pyplot as plt

# 日本語フォント候補（Windows優先 → 他OSもカバー）
JP_FONT_CANDIDATES = [
    "Meiryo", "Yu Gothic", "MS Gothic",         # Windows
    "Hiragino Sans", "Hiragino Kaku Gothic ProN",  # macOS
    "Noto Sans CJK JP", "IPAPGothic", "IPAMincho"  # Linux等
]

def set_japanese_font():
    # システムに入っているフォント名を列挙
    installed = set(f.name for f in fm.fontManager.ttflist)
    for name in JP_FONT_CANDIDATES:
        if name in installed:
            matplotlib.rcParams["font.family"] = name
            matplotlib.rcParams["axes.unicode_minus"] = False  # マイナス記号の豆腐化対策
            print(f"[Font] Use Japanese font: {name}")
            return
    print("[Font] *日本語フォントが見つかりませんでした*。'Noto Sans CJK JP' などをOSにインストールしてください。")

set_japanese_font()

sns.set(style="whitegrid")

# 速度
plt.figure(figsize=(12,6))
sns.boxplot(x="scenario", y="V_net", data=records_df, order=sorted(records_df["scenario"].unique()))
plt.title("平均速度の分布（20乱数）")
plt.xlabel("Scenario")
plt.ylabel("平均速度 [km/h]")
plt.tight_layout()
plt.savefig(out_dir / "boxplot_speed.png", dpi=300)
plt.close()

# 交通量（総走行台数）
plt.figure(figsize=(12,6))
sns.boxplot(x="scenario", y="traffic_total", data=records_df, order=sorted(records_df["scenario"].unique()))
plt.title("総走行台数の分布（20乱数）")
plt.xlabel("Scenario")
plt.ylabel("総走行台数 [台]")
plt.tight_layout()
plt.savefig(out_dir / "boxplot_traffic.png", dpi=300)
plt.close()

# TTT
plt.figure(figsize=(12,6))
sns.boxplot(x="scenario", y="TTT", data=records_df, order=sorted(records_df["scenario"].unique()))
plt.title("総旅行時間の分布（20乱数）")
plt.xlabel("Scenario")
plt.ylabel("TTT [sec]")
plt.tight_layout()
plt.savefig(out_dir / "boxplot_ttt.png", dpi=300)
plt.close()

print("✅ 分析完了：", out_dir, "に CSV と 箱ひげ図3枚を保存しました")
