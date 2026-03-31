import os
import re
import math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# =====================================
# 入力設定
# =====================================
INPUT_XLSX = "results_final.xlsx"
SHEET_NAME = "Sheet1"
OUT_DIR = "route_xhce_plots_pairwise_fixedscale_norm_bigtext_numonly"

P = 0.5

# 各交差点の青時間率
G = {
    0: 0.5,
    1: 0.6,
    2: 0.7,
    3: 0.5,
}

MAX_N = 20
DPI = 220
BAR_WIDTH = 1.8

# 文字サイズ
TITLE_FS = 90
LABEL_FS = 72
TICK_FS = 60
XTICK_FS = 42   # 速度目盛りだけ少し小さく
ANNOT_NUM_FS = 54

# 軸線
SPINE_LW = 2.5
TICK_WIDTH = 2.5

# 路線番号の表示変換
ROUTE_LABEL_MAP = {
    311: 1,
    312: 2,
    313: 3,
    314: 4,
    321: 5,
    322: 6,
    323: 7,
    324: 8,
    331: 9,
    332: 10,
    333: 11,
    334: 12,
}

# =====================================
# 補助関数
# =====================================
def in_interval(x, a, b, eps=1e-12):
    return (a - eps) <= x <= (b + eps)

def parse_lambda_pair(col_name):
    m = re.match(r"Λ\((\d+),(\d+)\)", col_name)
    if not m:
        raise ValueError(f"Λ列名を解釈できません: {col_name}")
    return int(m.group(1)), int(m.group(2))

def pair_params(i, j, G, P):
    gi = G[i]
    gj = G[j]
    gbar = (gi + gj) / 2.0
    delta_g = abs(gj - gi)
    delta_gamma = gbar - P
    return gi, gj, gbar, delta_g, delta_gamma

def xhce_total_width_norm(lam, delta_gamma, max_n=20):
    """
    Δx_hce の合計幅（0~1 正規化オフセット上）
    """
    if pd.isna(lam) or delta_gamma <= 0:
        return 0.0

    total = 0.0

    if in_interval(lam, 0.0, delta_gamma) and lam > 0:
        total += 2.0 * lam

    for N in range(max_n + 1):
        center = N + 0.5
        left = center - delta_gamma
        right = center + delta_gamma
        if in_interval(lam, left, right):
            delta = min(lam - left, right - lam)
            total += 2.0 * max(delta, 0.0)

        center = N + 1.0
        left = center - delta_gamma
        right = center + delta_gamma
        if in_interval(lam, left, right):
            delta = min(lam - left, right - lam)
            total += 2.0 * max(delta, 0.0)

    return total

def xhce_exists_point(lam, delta_gamma, max_n=20, eps=1e-10):
    """
    x_hce が幅0の点として存在するか
    """
    if pd.isna(lam):
        return False

    if abs(delta_gamma) <= eps:
        for N in range(max_n + 1):
            if abs(lam - (N + 0.5)) <= eps or abs(lam - (N + 1.0)) <= eps:
                return True
        return False

    if abs(lam - delta_gamma) <= eps:
        return True

    for N in range(max_n + 1):
        if abs(lam - (N + 0.5 - delta_gamma)) <= eps:
            return True
        if abs(lam - (N + 0.5 + delta_gamma)) <= eps:
            return True
        if abs(lam - (N + 1.0 - delta_gamma)) <= eps:
            return True
        if abs(lam - (N + 1.0 + delta_gamma)) <= eps:
            return True

    return False

def xhce_point_values_norm(lam, delta_gamma, max_n=20, eps=1e-10):
    """
    幅0で存在する x_hce の正規化値（0~1）を返す
    """
    vals = []
    if pd.isna(lam):
        return vals

    if abs(delta_gamma) <= eps:
        for N in range(max_n + 1):
            for candidate in [N + 0.5, N + 1.0]:
                if abs(lam - candidate) <= eps:
                    vals.append(candidate % 1.0)
        return sorted(set([round(v, 10) for v in vals]))

    if abs(lam - delta_gamma) <= eps:
        vals.append(lam % 1.0)

    for N in range(max_n + 1):
        for candidate in [
            N + 0.5 - delta_gamma,
            N + 0.5 + delta_gamma,
            N + 1.0 - delta_gamma,
            N + 1.0 + delta_gamma,
        ]:
            if abs(lam - candidate) <= eps:
                vals.append(candidate % 1.0)

    vals = sorted(set([round(v, 10) for v in vals]))
    return vals

def nice_upper_compact(x):
    """
    上限をややコンパクトに丸める
    """
    if x <= 0 or pd.isna(x):
        return 0.2
    candidates = [0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.4, 0.5, 0.6, 0.8, 1.0]
    for c in candidates:
        if x <= c:
            return c
    return min(1.0, math.ceil(x * 20) / 20)

def format_xhce_ylabel(i, j):
    return rf"$\Delta x_{{hce}}^{{({i},{j})}}$"

def format_route_label(route_id):
    route_id_int = int(route_id)
    disp = ROUTE_LABEL_MAP.get(route_id_int, route_id_int)
    return f"Corridor {disp}"

def set_axis_style(ax):
    for side in ["left", "right", "top", "bottom"]:
        ax.spines[side].set_linewidth(SPINE_LW)
    ax.tick_params(axis="both", width=TICK_WIDTH)

def format_tick_value(x):
    if abs(x - round(x)) < 1e-10:
        return f"{int(round(x))}"
    return f"{x:.2f}".rstrip("0").rstrip(".")

def set_three_yticks(ax, ymax):
    mid = ymax / 2.0
    ticks = [0, mid, ymax]
    ax.set_yticks(ticks)
    ax.set_yticklabels([format_tick_value(t) for t in ticks], fontsize=TICK_FS)

# =====================================
# データ読み込み
# =====================================
os.makedirs(OUT_DIR, exist_ok=True)

df = pd.read_excel(INPUT_XLSX, sheet_name=SHEET_NAME)

route_col = "路線番号"
speed_col = "系統速度"
dopt_col = "dopt(s/veh)"

lambda_cols = [
    "Λ(0,1)",
    "Λ(1,2)",
    "Λ(2,3)",
    "Λ(0,2)",
    "Λ(1,3)",
    "Λ(0,3)",
]

required = [route_col, speed_col, dopt_col] + lambda_cols
missing = [c for c in required if c not in df.columns]
if missing:
    raise ValueError(f"不足列があります: {missing}")

for c in required:
    df[c] = pd.to_numeric(df[c], errors="coerce")

df = df.dropna(subset=[route_col, speed_col, dopt_col]).copy()

# =====================================
# 各 Λ(i,j) ごとに Δxhce幅と点存在を計算
# =====================================
pair_summary_rows = []

for lam_col in lambda_cols:
    i, j = parse_lambda_pair(lam_col)
    gi, gj, gbar, delta_g, delta_gamma = pair_params(i, j, G, P)

    width_norm_col = f"{lam_col}_xhce_width_norm"
    point_flag_col = f"{lam_col}_xhce_point_exists"
    point_vals_col = f"{lam_col}_xhce_point_values_norm"

    df[width_norm_col] = df[lam_col].map(
        lambda lam: xhce_total_width_norm(lam, delta_gamma, max_n=MAX_N)
    )
    df[point_flag_col] = df[lam_col].map(
        lambda lam: xhce_exists_point(lam, delta_gamma, max_n=MAX_N)
    )
    df[point_vals_col] = df[lam_col].map(
        lambda lam: xhce_point_values_norm(lam, delta_gamma, max_n=MAX_N)
    )

    pair_summary_rows.append({
        "lambda_col": lam_col,
        "i": i,
        "j": j,
        "g_i": gi,
        "g_j": gj,
        "gbar": gbar,
        "delta_g": delta_g,
        "deltaGamma": delta_gamma,
    })

pair_summary = pd.DataFrame(pair_summary_rows)

# =====================================
# 路線間で統一する縦軸上限
# =====================================
global_dopt_ylim = 60

global_xhce_ylim = {}
for lam_col in lambda_cols:
    width_norm_col = f"{lam_col}_xhce_width_norm"
    vmax = df[width_norm_col].max()
    global_xhce_ylim[lam_col] = nice_upper_compact(vmax * 1.03) if vmax > 0 else 0.2

# 手動固定
global_xhce_ylim["Λ(0,1)"] = 0.2
global_xhce_ylim["Λ(1,3)"] = 0.2
global_xhce_ylim["Λ(2,3)"] = 0.3
global_xhce_ylim["Λ(0,2)"] = 0.3

# =====================================
# 路線ごとに出力
# =====================================
all_routes = sorted(df[route_col].dropna().unique())

for route_id in all_routes:
    g = df[df[route_col] == route_id].copy()
    g = g.sort_values(speed_col).reset_index(drop=True)

    if g.empty:
        continue

    nrows = 1 + len(lambda_cols)
    fig, axes = plt.subplots(
        nrows=nrows,
        ncols=1,
        figsize=(28, 5.2 * nrows),
        sharex=True,
        constrained_layout=True
    )

    # 1段目: d*
    axes[0].bar(
        g[speed_col],
        g[dopt_col],
        width=BAR_WIDTH,
        alpha=0.9,
        color="orange"
    )
    axes[0].set_ylim(0, global_dopt_ylim)
    set_three_yticks(axes[0], global_dopt_ylim)
    axes[0].set_ylabel(r"$d^*_{v,l}$" + "\n[s/veh]", fontsize=LABEL_FS)
    axes[0].set_title(
        f"{format_route_label(route_id)}",
        fontsize=TITLE_FS,
        pad=26
    )
    axes[0].grid(axis="y", alpha=0.5)
    axes[0].tick_params(axis="x", labelsize=XTICK_FS)
    set_axis_style(axes[0])

    # 2段目以降
    for k, lam_col in enumerate(lambda_cols, start=1):
        ax = axes[k]
        width_norm_col = f"{lam_col}_xhce_width_norm"
        point_flag_col = f"{lam_col}_xhce_point_exists"
        point_vals_col = f"{lam_col}_xhce_point_values_norm"

        i, j = parse_lambda_pair(lam_col)

        vals = g[width_norm_col].fillna(0).values
        point_flags = g[point_flag_col].fillna(False).astype(bool).values

        mask_bar = vals > 0
        if np.any(mask_bar):
            ax.bar(
                g.loc[mask_bar, speed_col],
                vals[mask_bar],
                width=BAR_WIDTH,
                alpha=0.8
            )

        # 幅0の点は数字だけ青字で表示
        mask_point = (~mask_bar) & point_flags
        if np.any(mask_point):
            point_rows = g.loc[mask_point]

            for _, row in point_rows.iterrows():
                xv = row[speed_col]
                point_vals = row[point_vals_col]

                if not (isinstance(point_vals, list) and len(point_vals) > 0):
                    continue

                txt_val = point_vals[0]

                ax.text(
                    xv,
                    global_xhce_ylim[lam_col] * 0.06,
                    f"{txt_val:.2f}",
                    ha="center",
                    va="bottom",
                    fontsize=ANNOT_NUM_FS,
                    color="blue",
                    fontweight="bold"
                )

        ax.set_ylim(0, global_xhce_ylim[lam_col])
        set_three_yticks(ax, global_xhce_ylim[lam_col])
        ax.set_ylabel(format_xhce_ylabel(i, j), fontsize=LABEL_FS)
        ax.grid(axis="y", alpha=0.5)
        ax.tick_params(axis="x", labelsize=XTICK_FS)
        set_axis_style(ax)

    axes[-1].set_xlabel("Speed [km/h]", fontsize=LABEL_FS)
    axes[-1].set_xticks(g[speed_col].values)
    axes[-1].tick_params(axis="x", labelsize=XTICK_FS)
    axes[-1].tick_params(axis="y", labelsize=TICK_FS)

    out_png = os.path.join(
        OUT_DIR,
        f"route_{int(route_id)}_xhce_subplots.png"
    )
    plt.savefig(out_png, dpi=DPI, bbox_inches="tight")
    plt.close(fig)

# =====================================
# 確認用CSV保存
# =====================================
out_csv = os.path.join(OUT_DIR, "route_xhce_width_table.csv")
out_pair_csv = os.path.join(OUT_DIR, "pair_parameter_summary.csv")

df.to_csv(out_csv, index=False, encoding="utf-8-sig")
pair_summary.to_csv(out_pair_csv, index=False, encoding="utf-8-sig")

print("完了しました。")
print(f"入力ファイル: {INPUT_XLSX} / {SHEET_NAME}")
print(f"出力フォルダ: {OUT_DIR}")
print(f"確認用CSV   : {out_csv}")
print(f"ペア別要約  : {out_pair_csv}")
print(f"dopt ylim   : 0 - {global_dopt_ylim}")
for lam_col in lambda_cols:
    print(f"{lam_col} ylim : 0 - {global_xhce_ylim[lam_col]}")