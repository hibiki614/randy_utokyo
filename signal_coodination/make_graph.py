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
# 2) 見た目（ちょいカッコよく）
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
# 3) 入力と列名
# =========================
xlsx_path = "results_final.xlsx"
out_dir = "plots_by_route"
os.makedirs(out_dir, exist_ok=True)

COL_ROUTE = "路線番号"
COL_SPEED = "系統速度"          # km/h
COL_TTT   = "TTT(s/veh)"       # s/veh
COL_FTT   = "FTT(s/veh)"       # s/veh（無い場合は TTT-dopt で補完）
COL_DOPT  = "dopt(s/veh)"      # s/veh

# 距離（m）の列：この3つがあれば距離[km]を作れる
COL_L01 = "link(0,1)"
COL_L12 = "link(1,2)"
COL_L23 = "link(2,3)"

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

# 距離[km]の作成
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

# 欠損除去
need_all = [COL_ROUTE, COL_SPEED, COL_TTT, COL_FTT, COL_DOPT, "dist_km"]
df = df.dropna(subset=need_all)

# dist_kmが0以下は除外
df = df[df["dist_km"] > 0].copy()

# =========================
# 4) s/(km・veh) への変換（平均ペース）
# =========================
# pace = (s/veh) / km = s/(km・veh)
df["TTT_pace"]  = df[COL_TTT]  / df["dist_km"]
df["FTT_pace"]  = df[COL_FTT]  / df["dist_km"]
df["dopt_pace"] = df[COL_DOPT] / df["dist_km"]

# =========================
# 5) 路線番号ごとに保存：TTT/FTTは折れ線、doptは棒
# =========================
LINE_KW = dict(linewidth=1.6, alpha=0.95, marker="o", markersize=3.0, markeredgewidth=0.0)
BAR_ALPHA = 0.35

for route, g in df.groupby(COL_ROUTE, sort=True):
    g = g.sort_values(COL_SPEED)

    x = g[COL_SPEED].to_numpy()
    y_ttt = g["TTT_pace"].to_numpy()
    y_ftt = g["FTT_pace"].to_numpy()
    y_d   = g["dopt_pace"].to_numpy()

    fig, ax = plt.subplots()

    # 棒：dopt（遅れペース）
    # 速度の刻みが一定じゃない場合もあるので、棒幅は「隣の差の0.6倍」を採用
    if len(x) >= 2:
        dx = np.diff(x)
        w = 0.6 * np.min(dx[dx > 0]) if np.any(dx > 0) else 0.8
    else:
        w = 0.8
    ax.bar(x, y_d, width=w, alpha=BAR_ALPHA, label="dopt（遅れ）", zorder=2)

    # 折れ線：FTT/TTT（希望ペース/平均ペース）
    ax.plot(x, y_ftt, label="FTT（希望ペース）", zorder=3, **LINE_KW)
    ax.plot(x, y_ttt, label="TTT（平均ペース）", zorder=4, **LINE_KW)

    ax.set_xlabel("系統速度 (km/h)")
    ax.set_ylabel("ペース  s/(km・veh)")
    ax.set_title(f"路線番号 {route}")

    prettify_axes(ax)
    ax.legend(loc="best", fontsize=10)

    fig.tight_layout()
    out_path = os.path.join(out_dir, f"route_{route}_pace.png")
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)

print(f"✅ 保存先: {out_dir}")
