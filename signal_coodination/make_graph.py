import os
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm

# =========================
# 1) 日本語フォント（文字化け対策）
# =========================
def set_japanese_font():
    # よく入ってる日本語フォント候補（環境により異なる）
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
    # 見つからない場合：英語ラベルにするか、フォント導入が必要
    return None

jp_font = set_japanese_font()
if jp_font is None:
    print("⚠ 日本語フォントが見つからず、文字化けする可能性があります。"
          "（IPAexGothic等をインストールするか、ラベルを英語にしてください）")
else:
    print(f"✅ 日本語フォント設定: {jp_font}")

# =========================
# 2) 見た目（ちょいカッコよく）
# =========================
plt.rcParams.update({
    "figure.figsize": (6.4, 4.0),
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
xlsx_path = "results_final.xlsx"   # パス適宜
out_dir = "plots_by_route"
os.makedirs(out_dir, exist_ok=True)

COL_ROUTE = "路線番号"
COL_SPEED = "系統速度"        # km/h
COL_TTT   = "TTT(s/veh)"     # s
COL_DOPT  = "dopt(s/veh)"    # s

df = pd.read_excel(xlsx_path)

need = [COL_ROUTE, COL_SPEED, COL_TTT, COL_DOPT]
missing = [c for c in need if c not in df.columns]
if missing:
    raise KeyError(f"必要な列が見つからない: {missing}\n実際の列: {list(df.columns)}")

for c in [COL_SPEED, COL_TTT, COL_DOPT]:
    df[c] = pd.to_numeric(df[c], errors="coerce")
df = df.dropna(subset=need)

# =========================
# 4) 路線番号ごとに保存（プロットを小さめ&上品に）
# =========================
# 「ださい」対策：線/点を細め、小さいマーカー、少し透過、凡例も控えめ
LINE_KW = dict(linewidth=1.4, alpha=0.95)
MARK_KW = dict(marker="o", markersize=3.2, markeredgewidth=0.0)  # 小さめ

for route, g in df.groupby(COL_ROUTE, sort=True):
    g = g.sort_values(COL_SPEED)

    fig, ax = plt.subplots()
    ax.plot(g[COL_SPEED], g[COL_TTT], label="TTT", **LINE_KW, **MARK_KW)
    ax.plot(g[COL_SPEED], g[COL_DOPT], label="dopt", **LINE_KW, **MARK_KW)

    ax.set_xlabel("系統速度 (km/h)")
    ax.set_ylabel("時間 (s)")
    ax.set_title(f"路線番号 {route}")

    prettify_axes(ax)
    ax.legend(loc="best", fontsize=10)

    fig.tight_layout()
    out_path = os.path.join(out_dir, f"route_{route}.png")
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)

print(f"✅ 保存先: {out_dir}")
