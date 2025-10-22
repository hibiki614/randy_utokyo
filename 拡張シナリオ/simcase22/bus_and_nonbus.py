# -*- coding: utf-8 -*-
"""
Created on Tue Sep 30 14:27:31 2025
@author: OguchiLab
"""

import pandas as pd
import numpy as np
from pathlib import Path
import glob, os, re

# ===== 設定 =====
base_dir = Path(r"C:/Users/OguchiLab/OneDrive/デスクトップ/randy_utokyo/拡張シナリオ/simcase22")
out_dir  = base_dir / "analysis"
out_dir.mkdir(exist_ok=True)

SCENARIO = "no01"  # 基本情報なので no01 のみ
SKIP_VOLSPD = {"Case1_no07_r05_volspd.csv", "Case1_no08_r10_volspd.csv"}

def slot_code_from_timestr(s: str) -> str:
    # "YYYY/MM/DD HH:MM:SS" などから "HHMM" を作成
    s = str(s)
    if " " in s and ":" in s:
        hh, mm = s.split()[1].split(":")[:2]
        return f"{int(hh):02d}{mm}"
    # すでに 0630 形式ならそのまま
    s2 = s.replace(":", "")
    return s2[:4]

def hhmm_label(code: str) -> str:
    c = str(code).zfill(4)
    return f"{c[:2]}:{c[2:]}"

def one_run_timeseries(volspd_path: Path) -> pd.DataFrame:
    df = pd.read_csv(volspd_path)

    need = ["Time","Count(type3)","Count(type4)"]
    for c in need:
        if c not in df.columns:
            raise KeyError(f"{volspd_path.name} に {c} 列がありません。")

    bus = df["Count(type3)"].fillna(0) + df["Count(type4)"].fillna(0)

    if "Count(total)" in df.columns:
        total = df["Count(total)"].fillna(0)
        nonbus = total - bus
    else:
        nonbus = df.get("Count(type1)", 0).fillna(0) + df.get("Count(type2)", 0).fillna(0)

    ts = pd.DataFrame({
        "slot_code": df["Time"].map(slot_code_from_timestr),
        "bus": bus,
        "nonbus": nonbus
    })
    # 同一時刻で全リンク分を合算
    ts = ts.groupby("slot_code", as_index=False)[["bus","nonbus"]].sum()

    # ---- ここで時間フィルタ（7:00〜18:30） ----
    ts["slot_code_str"] = ts["slot_code"].astype(str).str.zfill(4)
    ts = ts[(ts["slot_code_str"] >= "0700") & (ts["slot_code_str"] <= "1830")].copy()
    # ---------------------------------------------

    ts["HHMM"] = ts["slot_code"].map(hhmm_label)
    return ts[["slot_code","HHMM","bus","nonbus"]]

# ===== no01 の rand* を走査して平均 =====
run_tables = []
for volspd in sorted(glob.glob(str(base_dir / SCENARIO / "rand*" / "*_volspd.csv"))):
    if os.path.basename(volspd) in SKIP_VOLSPD: 
        continue
    run_id = Path(volspd).parent.name
    ts = one_run_timeseries(Path(volspd))
    ts["run"] = run_id
    run_tables.append(ts)

runs_df = pd.concat(run_tables, ignore_index=True).sort_values(["slot_code","run"])

# 乱数平均（時刻別）
summary = (runs_df
           .groupby("slot_code", as_index=False)
           .agg(bus_mean=("bus","mean"),
                bus_std =("bus","std"),
                nonbus_mean=("nonbus","mean"),
                nonbus_std =("nonbus","std"),
                n_runs=("bus","size")))

summary["HHMM"] = summary["slot_code"].map(hhmm_label)
summary["bus_ratio_pct"] = (summary["bus_mean"] / (summary["bus_mean"] + summary["nonbus_mean"])) * 100

# 出力
runs_csv    = out_dir / f"timeseries_bus_nonbus_{SCENARIO}_runs.csv"
summary_csv = out_dir / f"timeseries_bus_nonbus_{SCENARIO}_summary.csv"
runs_df.to_csv(runs_csv, index=False, encoding="utf-8-sig")
summary[["slot_code","HHMM","bus_mean","bus_std","nonbus_mean","nonbus_std","n_runs"]].to_csv(
    summary_csv, index=False, encoding="utf-8-sig"
)

print("✅ 保存:")
print(" -", runs_csv)
print(" -", summary_csv)

# ===== 可視化 =====
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator

summary = summary.sort_values("slot_code").reset_index(drop=True)

x = np.arange(len(summary))
y_bus = summary["bus_mean"].values
y_non = summary["nonbus_mean"].values
labels = summary["HHMM"].tolist()

# --- 車種別台数（平均） ---
fig, ax = plt.subplots(figsize=(11,5))
ax.plot(x, y_bus, label="Bus (type3+4)", linewidth=2)
ax.plot(x, y_non, label="Non-bus (others)", linestyle="--", linewidth=2)
ax.set_ylabel("台数 [台/15分]")
ax.set_title(f"{SCENARIO}：車種別台数（乱数平均）")
ax.xaxis.set_major_locator(MultipleLocator(4))
hour_idx = np.arange(0, len(x), 4)
ax.set_xticks(hour_idx, [labels[i] for i in hour_idx], rotation=0)
ax.grid(True, axis="x", which="major", alpha=0.4)
ax.legend()
for t in (ax.get_xticklabels() + ax.get_yticklabels()):
    t.set_fontsize(11)
plt.tight_layout()
fig.savefig(out_dir / f"timeseries_bus_nonbus_{SCENARIO}_hourly.png", dpi=300)
plt.close()

# --- バス台数＋バス割合（右軸） ---
fig, ax1 = plt.subplots(figsize=(11,5))
ax1.plot(summary["HHMM"], summary["bus_mean"], label="Bus台数", color="tab:blue", linewidth=2)
ax1.plot(summary["HHMM"], summary["nonbus_mean"], label="Non-Bus台数", color="tab:orange", linestyle="--", linewidth=2)
ax1.set_ylabel("台数 [台/15分]")
ax1.tick_params(axis='y', labelcolor="black")
ax2 = ax1.twinx()
ax2.plot(summary["HHMM"], summary["bus_ratio_pct"], label="バス割合", color="tab:green", marker="o")
ax2.set_ylabel("バス割合 [%]")
ax2.tick_params(axis='y', labelcolor="black")
ax1.set_title(f"{SCENARIO}：車種別台数とバス割合（乱数平均）")
hour_idx = np.arange(0, len(summary), 4)
ax1.set_xticks(hour_idx, summary["HHMM"].iloc[::4], rotation=0)
ax1.grid(True, axis="x", alpha=0.3)
fig.legend(loc="upper left", bbox_to_anchor=(0.1,0.95))
plt.tight_layout()
combo_fig = out_dir / f"timeseries_bus_and_ratio_{SCENARIO}.png"
fig.savefig(combo_fig, dpi=300)
plt.close()
print(" -", combo_fig)
