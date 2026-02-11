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
# 2) 見た目（あなたのやつ踏襲）
# =========================
plt.rcParams.update({
    "figure.figsize": (6.6, 4.2),
    "figure.dpi": 140,
    "savefig.dpi": 240,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.alpha": 0.22,
    "grid.linewidth": 0.8,
    "axes.titlepad": 10,
    "axes.labelpad": 8,
    "axes.titlesize": 12,
    "axes.labelsize": 11,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "legend.frameon": False,
})

def prettify_axes(ax):
    ax.minorticks_on()
    ax.grid(which="minor", alpha=0.10, linewidth=0.6)
    ax.tick_params(axis="both", which="major", length=5, width=0.9, direction="out")
    ax.tick_params(axis="both", which="minor", length=3, width=0.7, direction="out")

# =========================
# 3) 入力と列名（必要に応じてここだけ変更）
# =========================
xlsx_path = "results0.25ver_final.xlsx"    # <- あなたのファイル名
out_dir = "plots_by_route0.25ver"
os.makedirs(out_dir, exist_ok=True)

COL_ROUTE = "路線番号"
COL_SPEED = "系統速度"          # km/h
COL_TTT   = "TTT(s/veh)"       # s/veh
COL_FTT   = "FTT(s/veh)"       # s/veh（無い場合は TTT-dopt で補完）
COL_DOPT  = "dopt(s/veh)"      # s/veh

# 距離（m）の列（合計してdist_km作る）
COL_L01 = "link(0,1)"
COL_L12 = "link(1,2)"
COL_L23 = "link(2,3)"

# Λ列
COL_LAM_01 = "Λ(0,1)"
COL_LAM_12 = "Λ(1,2)"
COL_LAM_23 = "Λ(2,3)"
COL_LAM_02 = "Λ(0,2)"
COL_LAM_13 = "Λ(1,3)"
COL_LAM_03 = "Λ(0,3)"

# =========================
# 4) 読み込み＆前処理
# =========================
df = pd.read_excel(xlsx_path)
df.columns = df.columns.astype(str).str.strip()

need_basic = [COL_ROUTE, COL_SPEED, COL_TTT, COL_DOPT]
missing = [c for c in need_basic if c not in df.columns]
if missing:
    raise KeyError(f"必要な列が見つからない: {missing}\n実際の列: {list(df.columns)}")

# 数値化
for c in [COL_SPEED, COL_TTT, COL_DOPT]:
    df[c] = pd.to_numeric(df[c], errors="coerce")

# FTTが無ければ補完（TTT = FTT + dopt の前提）
if COL_FTT not in df.columns:
    df[COL_FTT] = df[COL_TTT] - df[COL_DOPT]
else:
    df[COL_FTT] = pd.to_numeric(df[COL_FTT], errors="coerce")

# 距離[km]
if all(c in df.columns for c in [COL_L01, COL_L12, COL_L23]):
    for c in [COL_L01, COL_L12, COL_L23]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df["dist_km"] = (df[COL_L01] + df[COL_L12] + df[COL_L23]) / 1000.0
else:
    raise KeyError(
        "距離を作るための link 列が見つかりません。\n"
        f"必要: {COL_L01},{COL_L12},{COL_L23}（m）\n"
        "代替として dist_km 列をExcelに追加してもOKです。"
    )

# Λ列チェック
lam_cols = [COL_LAM_01, COL_LAM_12, COL_LAM_23, COL_LAM_02, COL_LAM_13, COL_LAM_03]
missing_lam = [c for c in lam_cols if c not in df.columns]
if missing_lam:
    raise KeyError(f"Λ列が見つからない: {missing_lam}\n実際の列: {list(df.columns)}")
for c in lam_cols:
    df[c] = pd.to_numeric(df[c], errors="coerce")

# 欠損除去
need_all = [COL_ROUTE, COL_SPEED, COL_TTT, COL_FTT, COL_DOPT, "dist_km"] + lam_cols
df = df.dropna(subset=need_all).copy()
df = df[df["dist_km"] > 0].copy()

# =========================
# 5) 1kmあたり（pace）へ変換（あなたの希望）
# =========================
df["TTT_pace"]  = df[COL_TTT]  / df["dist_km"]   # s/(km・veh)
df["FTT_pace"]  = df[COL_FTT]  / df["dist_km"]
df["dopt_pace"] = df[COL_DOPT] / df["dist_km"]

# =========================
# 6) S(Λ), S(Λclose), S(Λfar)（あなたのhce条件どおり）
# =========================
def mod1(x):
    return np.mod(x, 1.0)

def dist_to_union_intervals(x, intervals):
    """
    x in [0,1)
    intervals: list of (l,u) with 0<=l<u<=1 (wrapは分割して渡す)
    return: min distance to union (0 if inside)
    """
    x = np.asarray(x)
    d = np.full_like(x, np.inf, dtype=float)

    for (l, u) in intervals:
        inside = (x >= l) & (x <= u)
        d = np.where(inside, 0.0, d)

        d_left  = np.where(x < l, l - x, np.inf)
        d_right = np.where(x > u, x - u, np.inf)
        d = np.minimum(d, np.minimum(d_left, d_right))
    return d

def hce_distance(lam, kind):
    """
    kind:
      01,13: [0.45,0.55] U [0.95,1) U [0,0.05]
      02,23: [0.40,0.60] U [0.90,1) U [0,0.10]
      12:    [0.35,0.65] U [0.85,1) U [0,0.15]
      03: centers at {0, 0.5} (mod1)
    """
    x = mod1(lam)

    if kind in ("01", "13"):
        return dist_to_union_intervals(x, [(0.45, 0.55), (0.95, 1.00), (0.00, 0.05)])

    if kind in ("02", "23"):
        return dist_to_union_intervals(x, [(0.40, 0.60), (0.90, 1.00), (0.00, 0.10)])

    if kind == "12":
        return dist_to_union_intervals(x, [(0.35, 0.65), (0.85, 1.00), (0.00, 0.15)])

    if kind == "03":
        # distance to nearest of {0, 0.5} on circle
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
# 7) 図の出力（色指定なし。デフォルト任せ）
# =========================
LINE_KW = dict(linewidth=1.6, alpha=0.95, marker="o", markersize=3.0, markeredgewidth=0.0)
BAR_ALPHA = 0.35

# (A) 路線ごと：pace図（元のやつ、doptは1kmあたりで棒）
for route, g in df.groupby(COL_ROUTE, sort=True):
    g = g.sort_values(COL_SPEED)
    x = g[COL_SPEED].to_numpy()

    y_ttt = g["TTT_pace"].to_numpy()
    y_ftt = g["FTT_pace"].to_numpy()
    y_d   = g["dopt_pace"].to_numpy()

    fig, ax = plt.subplots()

    if len(x) >= 2:
        dx = np.diff(x)
        w = 0.6 * np.min(dx[dx > 0]) if np.any(dx > 0) else 0.8
    else:
        w = 0.8

    ax.bar(x, y_d, width=w, alpha=BAR_ALPHA, label="dopt（遅れ）[s/(km・veh)]", zorder=2)
    ax.plot(x, y_ftt, label="FTT（希望ペース）", zorder=3, **LINE_KW)
    ax.plot(x, y_ttt, label="TTT（平均ペース）", zorder=4, **LINE_KW)

    ax.set_xlabel("系統速度 (km/h)")
    ax.set_ylabel("ペース  s/(km・veh)")
    ax.set_title(f"路線番号 {route}")

    prettify_axes(ax)
    ax.legend(loc="best", fontsize=10)

    fig.tight_layout()
    fig.savefig(os.path.join(out_dir, f"route_{route}_pace.png"), bbox_inches="tight")
    plt.close(fig)
    # --- (E) 二軸：dopt_pace（棒） + S(Λ)系（右軸）
    y_S  = g["S(Lambda)"].to_numpy()
    y_Sc = g["S(Lambda_close)"].to_numpy()
    y_Sf = g["S(Lambda_far)"].to_numpy()

    fig, ax1 = plt.subplots()

    # 棒幅（元コードと同じ）
    if len(x) >= 2:
        dx = np.diff(x)
        w = 0.6 * np.min(dx[dx > 0]) if np.any(dx > 0) else 0.8
    else:
        w = 0.8

    ax1.bar(x, y_d, width=w, alpha=BAR_ALPHA, label="dopt（遅れ）[s/(km・veh)]", zorder=2)
    ax1.set_xlabel("系統速度 (km/h)")
    ax1.set_ylabel("dopt_pace  s/(km・veh)")
    prettify_axes(ax1)

    ax2 = ax1.twinx()
    ax2.plot(x, y_S,  label="S(Λ)", zorder=4, **LINE_KW)
    ax2.plot(x, y_Sc, label="S(Λclose)", zorder=4, **LINE_KW)
    ax2.plot(x, y_Sf, label="S(Λfar)", zorder=4, **LINE_KW)
    ax2.set_ylabel("S 指標（hce集合までの距離L2）")

    h1, l1 = ax1.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax1.legend(h1 + h2, l1 + l2, loc="best", fontsize=10)

    ax1.set_title(f"路線番号 {route}：dopt_pace と S(Λ)系（2軸）")
    fig.tight_layout()
    out_path = os.path.join(out_dir, f"route_{route}_doptpace_and_S_2axis.png")
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)


# (B) 路線ごと：S(Λ) 系（速度に対して）
for route, g in df.groupby(COL_ROUTE, sort=True):
    g = g.sort_values(COL_SPEED)
    x = g[COL_SPEED].to_numpy()

    fig, ax = plt.subplots()
    ax.plot(x, g["S(Lambda)"].to_numpy(),       label="S(Λ)", zorder=3, **LINE_KW)
    ax.plot(x, g["S(Lambda_close)"].to_numpy(), label="S(Λclose)", zorder=3, **LINE_KW)
    ax.plot(x, g["S(Lambda_far)"].to_numpy(),   label="S(Λfar)", zorder=3, **LINE_KW)

    ax.set_xlabel("系統速度 (km/h)")
    ax.set_ylabel("S 指標（hce集合までの距離L2）")
    ax.set_title(f"路線番号 {route}：S(Λ)")

    prettify_axes(ax)
    ax.legend(loc="best", fontsize=10)

    fig.tight_layout()
    fig.savefig(os.path.join(out_dir, f"route_{route}_S.png"), bbox_inches="tight")
    plt.close(fig)

# (C) 路線ごと：散布図（dopt_pace vs S）
#     速度ごとに点が並んで、相関が目で見えるやつ
for route, g in df.groupby(COL_ROUTE, sort=True):
    if len(g) < 4:
        continue
    fig, ax = plt.subplots()
    ax.scatter(g["S(Lambda)"], g["dopt_pace"], s=18, alpha=0.85)
    ax.set_xlabel("S(Λ)")
    ax.set_ylabel("dopt_pace  [s/(km・veh)]")
    ax.set_title(f"路線番号 {route}：dopt_pace vs S(Λ)")
    prettify_axes(ax)
    fig.tight_layout()
    fig.savefig(os.path.join(out_dir, f"route_{route}_scatter_doptpace_vs_S.png"), bbox_inches="tight")
    plt.close(fig)

# (D) 全体：散布図（dopt_pace vs S）＋近似線（色指定なし）
#     ※回帰線は黒っぽくなるが、指定してないのでmatplotlibが勝手に決める
x_all = df["S(Lambda)"].to_numpy()
y_all = df["dopt_pace"].to_numpy()
coef = np.polyfit(x_all, y_all, 1)  # y = a x + b
xs = np.linspace(x_all.min(), x_all.max(), 200)
ys = coef[0]*xs + coef[1]

fig, ax = plt.subplots()
ax.scatter(x_all, y_all, s=12, alpha=0.75)
ax.plot(xs, ys)
ax.set_xlabel("S(Λ)")
ax.set_ylabel("dopt_pace  [s/(km・veh)]")
ax.set_title("全路線：dopt_pace vs S(Λ)")
prettify_axes(ax)
fig.tight_layout()
fig.savefig(os.path.join(out_dir, "overall_scatter_doptpace_vs_S.png"), bbox_inches="tight")
plt.close(fig)

print(f"✅ 保存先: {out_dir}")
