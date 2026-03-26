# -*- coding: utf-8 -*-
"""
plot_02_S_vs_dopt_pace_with_fit.py

② 横軸：S(Λ), S(Λclose), S(Λfar)
   縦軸：doptの1kmあたりペース（分/km）
   路線ごとに色を変えて散布図（3枚）
   ＋ 全データでの近似曲線（回帰）

出力：
  out_figs/out_02_*.png  (近似曲線入り)
  out_figs/out_02_correlations_overall.csv
  out_figs/out_02_correlations_by_route.csv
  out_figs/out_02_data_used.csv
  out_figs/out_02_fit_summary.csv   ★追加（回帰係数やR2など）
"""

import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.stats import pearsonr, spearmanr

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

S_COLS = ["S(Λ)", "S(Λclose)", "S(Λfar)"]

# 近似曲線の次数（1=直線, 2=2次曲線）
DEGREE = 1

# partial相関（速度をコントロール）を出すか
DO_PARTIAL = True

# =======================
# ユーティリティ
# =======================
def partial_corr(x, y, z):
    z_ = np.vstack([np.ones_like(z), z]).T
    bx = np.linalg.lstsq(z_, x, rcond=None)[0]
    by = np.linalg.lstsq(z_, y, rcond=None)[0]
    rx = x - z_ @ bx
    ry = y - z_ @ by
    r, _ = pearsonr(rx, ry)
    return r

def safe_corr(a, b, method="pearson"):
    a = np.asarray(a, float)
    b = np.asarray(b, float)
    m = np.isfinite(a) & np.isfinite(b)
    a = a[m]; b = b[m]
    n = len(a)
    if n < 3:
        return n, np.nan
    if method == "pearson":
        r, _ = pearsonr(a, b)
    elif method == "spearman":
        r, _ = spearmanr(a, b)
    else:
        raise ValueError(method)
    return n, r

def fit_poly_and_r2(x, y, degree=1):
    """y ~ poly(x) の係数とR^2を返す（NaN除外済み前提）"""
    coeffs = np.polyfit(x, y, deg=degree)  # coeffs[0]*x^deg + ... + coeffs[-1]
    p = np.poly1d(coeffs)
    yhat = p(x)
    ss_res = np.sum((y - yhat) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else np.nan
    return coeffs, r2

# =======================
# 読み込み & ペース列作成
# =======================
df = pd.read_excel(IN_XLSX, sheet_name=SHEET_NAME)

if COL_DIST_TOTAL_M in df.columns:
    dist_m = df[COL_DIST_TOTAL_M].astype(float)
else:
    missing = [c for c in COL_DIST_LINKS_M if c not in df.columns]
    if missing:
        raise KeyError(f"距離列が見つかりません。必要: {COL_DIST_TOTAL_M} または {COL_DIST_LINKS_M} / missing={missing}")
    dist_m = df[COL_DIST_LINKS_M].astype(float).sum(axis=1)

df["dist_km"] = dist_m / 1000.0
df["dopt_sec_per_km"] = df[COL_DOPT].astype(float) / df["dist_km"]
df["dopt_min_per_km"] = df["dopt_sec_per_km"] / 60.0

keep = [COL_ROUTE, COL_SPEED, "dist_km", COL_DOPT, "dopt_sec_per_km", "dopt_min_per_km"] + S_COLS
use = df[keep].copy()

use_csv = os.path.join(OUT_DIR, "0.5out_02_data_used.csv")
use.to_csv(use_csv, index=False, encoding="utf-8-sig")

# =======================
# 図：S vs pace（3枚）＋近似曲線
# =======================
routes = use[COL_ROUTE].astype(int)
route_codes, route_uniques = pd.factorize(routes)

y = use["dopt_min_per_km"].astype(float).to_numpy()  # 表示は分/km

fit_rows = []  # 近似曲線の係数とR2保存

for s_col in S_COLS:
    x_all = use[s_col].astype(float).to_numpy()

    # --- まず散布図 ---
    plt.figure(figsize=(8.5, 6))
    sc = plt.scatter(x_all, y, c=route_codes, s=28)

    plt.xlabel(s_col)
    plt.ylabel("dopt pace (min per km)")

    # --- 近似曲線（全データ） ---
    m = np.isfinite(x_all) & np.isfinite(y)
    x = x_all[m]
    yy = y[m]

    if len(x) >= (DEGREE + 2):
        coeffs, r2 = fit_poly_and_r2(x, yy, degree=DEGREE)
        p = np.poly1d(coeffs)

        # 描画用の滑らかなx
        xs = np.linspace(np.min(x), np.max(x), 300)
        ys = p(xs)

        # 近似曲線を上書き（色指定はしない＝デフォルト色）
        plt.plot(xs, ys, linewidth=2.0)

        # R2 表示（左上）
        plt.text(
            0.02, 0.98,
            f"poly degree={DEGREE}, R$^2$={r2:.3f}",
            transform=plt.gca().transAxes,
            va="top", ha="left"
        )

        # 保存用
        fit_rows.append({
            "x": s_col,
            "y": "dopt_min_per_km",
            "degree": DEGREE,
            "n_used": int(len(x)),
            "r2": float(r2),
            **{f"coef_deg_{DEGREE-i}": float(c) for i, c in enumerate(coeffs)}  # 例: coef_deg_1, coef_deg_0
        })
    else:
        fit_rows.append({
            "x": s_col, "y": "dopt_min_per_km",
            "degree": DEGREE, "n_used": int(len(x)),
            "r2": np.nan
        })

    # カラーバー（路線番号）
    cb = plt.colorbar(sc)
    K = len(route_uniques)
    if K <= 12:
        ticks = np.arange(K)
    else:
        ticks = np.linspace(0, K - 1, 12).round().astype(int)
    cb.set_ticks(ticks)
    cb.set_ticklabels([str(route_uniques[i]) for i in ticks])
    cb.set_label("Route ID")

    plt.tight_layout()
    out_png = os.path.join(
        OUT_DIR,
        f"out_02_{s_col.replace('(', '').replace(')', '').replace('Λ','Lambda')}_vs_pace_fit0.5.png"
    )
    plt.savefig(out_png, dpi=300)
    plt.close()

# 近似曲線の係数など保存
fit_df = pd.DataFrame(fit_rows)
fit_csv = os.path.join(OUT_DIR, "0.5out_02_fit_summary.csv")
fit_df.to_csv(fit_csv, index=False, encoding="utf-8-sig")

# =======================
# 相関：overall（秒/kmで計算）
# =======================
overall_rows = []
speed = use[COL_SPEED].astype(float).to_numpy()
pace_sec = use["dopt_sec_per_km"].astype(float).to_numpy()

for s_col in S_COLS:
    s = use[s_col].astype(float).to_numpy()
    n_p, r_p = safe_corr(s, pace_sec, "pearson")
    n_s, r_s = safe_corr(s, pace_sec, "spearman")

    row = {
        "x": s_col,
        "y": "dopt_sec_per_km",
        "n": n_p,
        "pearson_r": r_p,
        "spearman_r": r_s,
    }
    if DO_PARTIAL:
        m = np.isfinite(s) & np.isfinite(pace_sec) & np.isfinite(speed)
        row["partial_r_control_speed"] = partial_corr(s[m], pace_sec[m], speed[m]) if m.sum() >= 3 else np.nan

    overall_rows.append(row)

overall = pd.DataFrame(overall_rows)
overall_csv = os.path.join(OUT_DIR, "0.5out_02_correlations_overall.csv")
overall.to_csv(overall_csv, index=False, encoding="utf-8-sig")

# =======================
# 相関：by route
# =======================
by_rows = []
for rid, g in use.groupby(COL_ROUTE):
    pace_g = g["dopt_sec_per_km"].astype(float).to_numpy()
    for s_col in S_COLS:
        s_g = g[s_col].astype(float).to_numpy()
        n_p, r_p = safe_corr(s_g, pace_g, "pearson")
        n_s, r_s = safe_corr(s_g, pace_g, "spearman")
        by_rows.append({
            "route_id": int(rid),
            "x": s_col,
            "y": "dopt_sec_per_km",
            "n": n_p,
            "pearson_r": r_p,
            "spearman_r": r_s,
        })

by_route = pd.DataFrame(by_rows)
by_route_csv = os.path.join(OUT_DIR, "0.5out_02_correlations_by_route.csv")
by_route.to_csv(by_route_csv, index=False, encoding="utf-8-sig")

print("Saved figures/CSVs to:", OUT_DIR)
print("Saved:", use_csv)
print("Saved:", fit_csv)
print("Saved:", overall_csv)
print("Saved:", by_route_csv)