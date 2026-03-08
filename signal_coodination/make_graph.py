import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm

# =========================
# 1) 日本語フォント（文字化け対策）
# =========================
def set_japanese_font():
    candidates = [
        "IPAexGothic", "IPAGothic",
        "Noto Sans CJK JP", "Noto Sans JP",
        "Yu Gothic", "YuGothic",
        "Hiragino Sans", "Hiragino Kaku Gothic ProN",
        "Meiryo", "MS Gothic",
    ]
    available = {f.name for f in fm.fontManager.ttflist}
    for name in candidates:
        if name in available:
            plt.rcParams["font.family"] = name
            return name
    return None

jp_font = set_japanese_font()
if jp_font is None:
    print("⚠ 日本語フォントが見つからず、文字化けする可能性があります。")
else:
    print(f"✅ 日本語フォント設定: {jp_font}")

# =========================
# 2) 全体デザイン
# =========================
plt.rcParams.update({
    "figure.figsize": (6.8, 4.4),
    "figure.dpi": 140,
    "savefig.dpi": 260,

    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.alpha": 0.22,
    "grid.linewidth": 0.9,

    "axes.titlepad": 10,
    "axes.labelpad": 8,

    # 文字サイズ・太さ強化
    "axes.titlesize": 17,
    "axes.titleweight": "bold",
    "axes.labelsize": 12,
    "axes.labelweight": "bold",
    "xtick.labelsize": 12,
    "ytick.labelsize": 12,
    "legend.fontsize": 12,
    "legend.frameon": False,

    # 色を濃く
    "text.color": "black",
    "axes.labelcolor": "black",
    "xtick.color": "black",
    "ytick.color": "black",
})

def prettify_axes(ax):
    ax.minorticks_on()
    ax.grid(which="minor", alpha=0.10, linewidth=0.6)
    ax.tick_params(axis="both", which="major", length=5, width=1.1, direction="out", colors="black")
    ax.tick_params(axis="both", which="minor", length=3, width=0.8, direction="out", colors="black")

    for label in ax.get_xticklabels():
        label.set_fontweight("bold")
        label.set_color("black")
    for label in ax.get_yticklabels():
        label.set_fontweight("bold")
        label.set_color("black")

def add_panel_label(ax, label):
    ax.text(
        -0.10, 1.03, label,
        transform=ax.transAxes,
        ha="left", va="bottom",
        fontsize=16,
        fontweight="bold",
        color="black",
        clip_on=False
    )

def idx_to_panel_label(i):
    return f"({chr(ord('a') + i)})"

def padded_limits(vmin, vmax, pad_ratio=0.06):
    if not np.isfinite(vmin) or not np.isfinite(vmax):
        return None
    if vmax == vmin:
        d = 1.0 if vmin == 0 else abs(vmin) * 0.1
        return (vmin - d, vmax + d)
    pad = (vmax - vmin) * pad_ratio
    return (vmin - pad, vmax + pad)

def style_legend(legend):
    if legend is None:
        return
    for txt in legend.get_texts():
        txt.set_fontweight("bold")
        txt.set_color("black")

TITLE_KW = dict(fontsize=17, fontweight="bold", color="black")
LINE_KW = dict(linewidth=2.0, alpha=0.98, marker="o", markersize=3.6, markeredgewidth=0.0)
BAR_ALPHA = 0.38

# =========================
# 3) 入力と列名
# =========================
xlsx_path = "results_final.xlsx"
out_dir = "plots_by_routever2"
os.makedirs(out_dir, exist_ok=True)

COL_ROUTE = "路線番号"
COL_SPEED = "系統速度"
COL_TTT   = "TTT(s/veh)"
COL_FTT   = "FTT(s/veh)"
COL_DOPT  = "dopt(s/veh)"

COL_L01 = "link(0,1)"
COL_L12 = "link(1,2)"
COL_L23 = "link(2,3)"

COL_LAM_01 = "Λ(0,1)"
COL_LAM_12 = "Λ(1,2)"
COL_LAM_23 = "Λ(2,3)"
COL_LAM_02 = "Λ(0,2)"
COL_LAM_13 = "Λ(1,3)"
COL_LAM_03 = "Λ(0,3)"

route_map = {
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

# =========================
# 4) 読み込み＆前処理
# =========================
df = pd.read_excel(xlsx_path)
df.columns = df.columns.astype(str).str.strip()

need_basic = [COL_ROUTE, COL_SPEED, COL_TTT, COL_DOPT]
missing = [c for c in need_basic if c not in df.columns]
if missing:
    raise KeyError(f"必要な列が見つからない: {missing}\n実際の列: {list(df.columns)}")

for c in [COL_SPEED, COL_TTT, COL_DOPT]:
    df[c] = pd.to_numeric(df[c], errors="coerce")

df[COL_ROUTE] = pd.to_numeric(df[COL_ROUTE], errors="coerce")
df["route_display"] = df[COL_ROUTE].map(route_map)

if df["route_display"].isna().any():
    unmapped = sorted(df.loc[df["route_display"].isna(), COL_ROUTE].dropna().unique().tolist())
    raise ValueError(f"route_map に無い路線番号があります: {unmapped}")

if COL_FTT not in df.columns:
    df[COL_FTT] = df[COL_TTT] - df[COL_DOPT]
else:
    df[COL_FTT] = pd.to_numeric(df[COL_FTT], errors="coerce")

if all(c in df.columns for c in [COL_L01, COL_L12, COL_L23]):
    for c in [COL_L01, COL_L12, COL_L23]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df["dist_km"] = (df[COL_L01] + df[COL_L12] + df[COL_L23]) / 1000.0
else:
    raise KeyError(
        "距離を作るための link 列が見つかりません。\n"
        f"必要: {COL_L01}, {COL_L12}, {COL_L23}"
    )

lam_cols = [COL_LAM_01, COL_LAM_12, COL_LAM_23, COL_LAM_02, COL_LAM_13, COL_LAM_03]
missing_lam = [c for c in lam_cols if c not in df.columns]
if missing_lam:
    raise KeyError(f"Λ列が見つからない: {missing_lam}\n実際の列: {list(df.columns)}")

for c in lam_cols:
    df[c] = pd.to_numeric(df[c], errors="coerce")

need_all = [COL_ROUTE, "route_display", COL_SPEED, COL_TTT, COL_FTT, COL_DOPT, "dist_km"] + lam_cols
df = df.dropna(subset=need_all).copy()
df = df[df["dist_km"] > 0].copy()

# =========================
# 5) pace指標
# =========================
df["TTT_pace"]  = df[COL_TTT]  / df["dist_km"]
df["FTT_pace"]  = df[COL_FTT]  / df["dist_km"]
df["dopt_pace"] = df[COL_DOPT] / df["dist_km"]

# =========================
# 6) S(Λ), S(Λclose), S(Λfar)
# =========================
def mod1(x):
    return np.mod(x, 1.0)

def dist_to_union_intervals(x, intervals):
    x = np.asarray(x)
    d = np.full_like(x, np.inf, dtype=float)

    for (l, u) in intervals:
        inside = (x >= l) & (x <= u)
        d = np.where(inside, 0.0, d)

        d_left = np.where(x < l, l - x, np.inf)
        d_right = np.where(x > u, x - u, np.inf)
        d = np.minimum(d, np.minimum(d_left, d_right))

    return d

def hce_distance(lam, kind):
    x = mod1(lam)

    if kind in ("01", "13"):
        return dist_to_union_intervals(x, [(0.45, 0.55), (0.95, 1.00), (0.00, 0.05)])

    if kind in ("02", "23"):
        return dist_to_union_intervals(x, [(0.40, 0.60), (0.90, 1.00), (0.00, 0.10)])

    if kind == "12":
        return dist_to_union_intervals(x, [(0.35, 0.65), (0.85, 1.00), (0.00, 0.15)])

    if kind == "03":
        return np.minimum(np.minimum(x, 1.0 - x), np.abs(x - 0.5))

    raise ValueError(f"unknown kind: {kind}")

df["d01_hce"] = hce_distance(df[COL_LAM_01].to_numpy(), "01")
df["d12_hce"] = hce_distance(df[COL_LAM_12].to_numpy(), "12")
df["d23_hce"] = hce_distance(df[COL_LAM_23].to_numpy(), "23")
df["d02_hce"] = hce_distance(df[COL_LAM_02].to_numpy(), "02")
df["d13_hce"] = hce_distance(df[COL_LAM_13].to_numpy(), "13")
df["d03_hce"] = hce_distance(df[COL_LAM_03].to_numpy(), "03")

df["S(Lambda_close)"] = np.sqrt(df["d01_hce"]**2 + df["d12_hce"]**2 + df["d23_hce"]**2)
df["S(Lambda_far)"]   = np.sqrt(df["d02_hce"]**2 + df["d13_hce"]**2 + df["d03_hce"]**2)
df["S(Lambda)"]       = np.sqrt(df["S(Lambda_close)"]**2 + df["S(Lambda_far)"]**2)

# =========================
# 7) 図ごとの共通スケール
# =========================
pace_ymin = min(df["FTT_pace"].min(), df["TTT_pace"].min())
pace_ymax = max(df["FTT_pace"].max(), df["TTT_pace"].max())
pace_ylim = padded_limits(pace_ymin, pace_ymax, pad_ratio=0.06)

dopt_ylim = padded_limits(df["dopt_pace"].min(), df["dopt_pace"].max(), pad_ratio=0.06)

s_ymin = min(df["S(Lambda)"].min(), df["S(Lambda_close)"].min(), df["S(Lambda_far)"].min())
s_ymax = max(df["S(Lambda)"].max(), df["S(Lambda_close)"].max(), df["S(Lambda_far)"].max())
s_ylim = padded_limits(s_ymin, s_ymax, pad_ratio=0.06)

scatter_xlim = padded_limits(df["S(Lambda)"].min(), df["S(Lambda)"].max(), pad_ratio=0.06)
scatter_ylim = padded_limits(df["dopt_pace"].min(), df["dopt_pace"].max(), pad_ratio=0.06)

# =========================
# 8) 出力順序
# =========================
routes_sorted = sorted(df["route_display"].unique())

# =========================
# 9) (A) pace図：棒なし
# =========================
for i, route_disp in enumerate(routes_sorted):
    g = df[df["route_display"] == route_disp].sort_values(COL_SPEED)
    x = g[COL_SPEED].to_numpy()

    fig, ax = plt.subplots()

    ax.plot(x, g["FTT_pace"].to_numpy(), label="FTT (pace)", zorder=3, **LINE_KW)
    ax.plot(x, g["TTT_pace"].to_numpy(), label="TTT (pace)", zorder=4, **LINE_KW)

    ax.set_xlabel("Speed (km/h)")
    ax.set_ylabel("Travel time per kilometer [s/(km·veh)]")
    ax.set_title(f"Route {route_disp}", **TITLE_KW)

    if pace_ylim is not None:
        ax.set_ylim(*pace_ylim)

    add_panel_label(ax, idx_to_panel_label(i))
    prettify_axes(ax)

    leg = ax.legend(loc="best", fontsize=12, frameon=False)
    style_legend(leg)

    fig.tight_layout(rect=[0.04, 0.03, 1.00, 0.98])
    fig.savefig(os.path.join(out_dir, f"route_{route_disp}_pace.png"), bbox_inches="tight")
    plt.close(fig)

# =========================
# 10) (B) dopt棒 + S系折れ線（二軸）
# =========================
for i, route_disp in enumerate(routes_sorted):
    g = df[df["route_display"] == route_disp].sort_values(COL_SPEED)
    x = g[COL_SPEED].to_numpy()

    y_d  = g["dopt_pace"].to_numpy()
    y_S  = g["S(Lambda)"].to_numpy()
    y_Sc = g["S(Lambda_close)"].to_numpy()
    y_Sf = g["S(Lambda_far)"].to_numpy()

    fig, ax1 = plt.subplots()

    if len(x) >= 2:
        dx = np.diff(x)
        w = 0.6 * np.min(dx[dx > 0]) if np.any(dx > 0) else 0.8
    else:
        w = 0.8

    ax1.bar(x, y_d, width=w, alpha=BAR_ALPHA, label="dopt (pace)", zorder=2)
    ax1.set_xlabel("Speed (km/h)")
    ax1.set_ylabel("Delay per kilometer [s/(km·veh)]")

    if dopt_ylim is not None:
        ax1.set_ylim(*dopt_ylim)

    prettify_axes(ax1)

    ax2 = ax1.twinx()
    ax2.plot(x, y_S,  label="S(Λ)", zorder=4, **LINE_KW)
    ax2.plot(x, y_Sc, label="S(Λclose)", zorder=4, **LINE_KW)
    ax2.plot(x, y_Sf, label="S(Λfar)", zorder=4, **LINE_KW)
    ax2.set_ylabel("Distance to HCE set (L2 norm)")

    if s_ylim is not None:
        ax2.set_ylim(*s_ylim)

    for label in ax2.get_yticklabels():
        label.set_fontweight("bold")
        label.set_color("black")
    ax2.yaxis.label.set_fontweight("bold")
    ax2.yaxis.label.set_color("black")

    add_panel_label(ax1, idx_to_panel_label(i))

    h1, l1 = ax1.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    leg = ax1.legend(h1 + h2, l1 + l2, loc="best", fontsize=12, frameon=False)
    style_legend(leg)

    ax1.set_title(f"Route {route_disp}", **TITLE_KW)

    fig.tight_layout(rect=[0.04, 0.03, 1.00, 0.98])
    fig.savefig(os.path.join(out_dir, f"route_{route_disp}_doptpace_and_S_2axis.png"), bbox_inches="tight")
    plt.close(fig)

# =========================
# 11) (C) S系のみ
# =========================
for i, route_disp in enumerate(routes_sorted):
    g = df[df["route_display"] == route_disp].sort_values(COL_SPEED)
    x = g[COL_SPEED].to_numpy()

    fig, ax = plt.subplots()
    ax.plot(x, g["S(Lambda)"].to_numpy(),       label="S(Λ)", zorder=3, **LINE_KW)
    ax.plot(x, g["S(Lambda_close)"].to_numpy(), label="S(Λclose)", zorder=3, **LINE_KW)
    ax.plot(x, g["S(Lambda_far)"].to_numpy(),   label="S(Λfar)", zorder=3, **LINE_KW)

    ax.set_xlabel("Speed (km/h)")
    ax.set_ylabel("Distance to HCE set (L2 norm)")
    ax.set_title(f"Route {route_disp}", **TITLE_KW)

    if s_ylim is not None:
        ax.set_ylim(*s_ylim)

    add_panel_label(ax, idx_to_panel_label(i))
    prettify_axes(ax)

    leg = ax.legend(loc="best", fontsize=12, frameon=False)
    style_legend(leg)

    fig.tight_layout(rect=[0.04, 0.03, 1.00, 0.98])
    fig.savefig(os.path.join(out_dir, f"route_{route_disp}_S.png"), bbox_inches="tight")
    plt.close(fig)

# =========================
# 12) (D) 路線別散布図
# =========================
for i, route_disp in enumerate(routes_sorted):
    g = df[df["route_display"] == route_disp]
    if len(g) < 4:
        continue

    fig, ax = plt.subplots()
    ax.scatter(g["S(Lambda)"], g["dopt_pace"], s=28, alpha=0.88)

    ax.set_xlabel("S(Λ)")
    ax.set_ylabel("Delay per kilometer [s/(km·veh)]")
    ax.set_title(f"Route {route_disp}", **TITLE_KW)

    if scatter_xlim is not None:
        ax.set_xlim(*scatter_xlim)
    if scatter_ylim is not None:
        ax.set_ylim(*scatter_ylim)

    add_panel_label(ax, idx_to_panel_label(i))
    prettify_axes(ax)

    fig.tight_layout(rect=[0.04, 0.03, 1.00, 0.98])
    fig.savefig(os.path.join(out_dir, f"route_{route_disp}_scatter_doptpace_vs_S.png"), bbox_inches="tight")
    plt.close(fig)

# =========================
# 13) (E) 全体散布図 + 近似線
# =========================
x_all = df["S(Lambda)"].to_numpy()
y_all = df["dopt_pace"].to_numpy()

coef = np.polyfit(x_all, y_all, 1)
xs = np.linspace(x_all.min(), x_all.max(), 200)
ys = coef[0] * xs + coef[1]

fig, ax = plt.subplots()
ax.scatter(x_all, y_all, s=22, alpha=0.80)
ax.plot(xs, ys, linewidth=2.0)

ax.set_xlabel("S(Λ)")
ax.set_ylabel("Delay per kilometer [s/(km·veh)]")
ax.set_title("All routes", **TITLE_KW)

if scatter_xlim is not None:
    ax.set_xlim(*scatter_xlim)
if scatter_ylim is not None:
    ax.set_ylim(*scatter_ylim)

add_panel_label(ax, "(a)")
prettify_axes(ax)

fig.tight_layout(rect=[0.04, 0.03, 1.00, 0.98])
fig.savefig(os.path.join(out_dir, "overall_scatter_doptpace_vs_S.png"), bbox_inches="tight")
plt.close(fig)

print(f"✅ 保存先: {out_dir}")