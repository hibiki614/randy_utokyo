# -*- coding: utf-8 -*-
"""
plot_01_speed_vs_normdelay_by50.py

① 横軸：平均速度（系統速度）
   縦軸：doptの1kmあたり（秒/km）を、各路線の「50km/h時」を1として正規化した値
   路線ごとに色分けして、速度順に線で結ぶ

OUTPUT:
  out_figs/out_01_speed_vs_normdelay_by50.png
  out_figs/out_01_normdelay_data.csv
"""

import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# =======================
# 設定
# =======================
IN_XLSX = "results0.5ver_final.xlsx"
SHEET_NAME = 0
OUT_DIR = "out_figs"
os.makedirs(OUT_DIR, exist_ok=True)

COL_ROUTE = "路線番号"
COL_SPEED = "系統速度"          # km/h
COL_DOPT  = "dopt(s/veh)"       # s/veh
COL_DIST_TOTAL_M = "link(0,3)"  # m（総延長）
COL_DIST_LINKS_M = ["link(0,1)", "link(1,2)", "link(2,3)"]

SPEED_BASE = 50.0
SPEED_TOL = 1e-6  # 50.0ぴったり判定（50が浮動小数でズレてるなら 0.2 くらいにしてもOK）

# =======================
# 読み込み
# =======================
df = pd.read_excel(IN_XLSX, sheet_name=SHEET_NAME)

# =======================
# 距離(km)
# =======================
if COL_DIST_TOTAL_M in df.columns:
    dist_m = df[COL_DIST_TOTAL_M].astype(float)
else:
    missing = [c for c in COL_DIST_LINKS_M if c not in df.columns]
    if missing:
        raise KeyError(f"距離列が見つかりません。必要: {COL_DIST_TOTAL_M} または {COL_DIST_LINKS_M} / missing={missing}")
    dist_m = df[COL_DIST_LINKS_M].astype(float).sum(axis=1)

df["dist_km"] = dist_m / 1000.0

# doptの1kmあたり（秒/km）
df["dopt_sec_per_km"] = df[COL_DOPT].astype(float) / df["dist_km"]

# =======================
# 50km/hの値で正規化（路線ごと）
# =======================
df[COL_ROUTE] = df[COL_ROUTE].astype(int)
df[COL_SPEED] = df[COL_SPEED].astype(float)

base_map = {}
for rid, g in df.groupby(COL_ROUTE):
    # 50km/h行を探す
    gg = g[np.isclose(g[COL_SPEED].to_numpy(), SPEED_BASE, atol=SPEED_TOL)]
    if len(gg) == 0:
        base_map[rid] = np.nan
    else:
        # 50が複数あれば平均（本当は同一のはず）
        base_map[rid] = float(np.nanmean(gg["dopt_sec_per_km"].to_numpy()))

df["base_50_sec_per_km"] = df[COL_ROUTE].map(base_map)
df["norm_delay_by50"] = df["dopt_sec_per_km"] / df["base_50_sec_per_km"]

# 50が無い路線は除外（normがNaNになる）
use = df[np.isfinite(df["norm_delay_by50"])].copy()

# 保存（確認用）
out_csv = os.path.join(OUT_DIR, "out_01_normdelay_data0.5.csv")
use.to_csv(out_csv, index=False, encoding="utf-8-sig")

# =======================
# プロット（路線ごとに線で結ぶ）
# =======================
route_uniques = np.sort(use[COL_ROUTE].unique())

plt.figure(figsize=(9, 6))

for rid in route_uniques:
    g = use[use[COL_ROUTE] == rid].copy().sort_values(COL_SPEED)
    x = g[COL_SPEED].to_numpy()
    y = g["norm_delay_by50"].to_numpy()
    plt.plot(x, y, marker="o", linewidth=1.2, markersize=3.5, label=str(rid))

plt.xlabel("Average speed (km/h)")
plt.ylabel("Normalized delay per km (50 km/h = 1)")

# y=1基準線（見やすい）
plt.axhline(1.0, linewidth=1.0)

plt.tight_layout()

# 凡例が多いと邪魔なので自動制御
SHOW_LEGEND = (len(route_uniques) <= 12)
if SHOW_LEGEND:
    plt.legend(title="Route ID", fontsize=8, title_fontsize=9, ncol=2, frameon=False)

out_png = os.path.join(OUT_DIR, "0.5out_01_speed_vs_normdelay_by50.png")
plt.savefig(out_png, dpi=300)
plt.close()

print("Saved:", out_png)
print("Saved:", out_csv)
print("Routes kept:", len(route_uniques), "(routes without 50km/h were dropped)")