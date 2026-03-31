import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
from matplotlib.patches import Patch

# =========================
# 設定
# =========================
INPUT_CSV = "all_opt_offsets.csv"
OUT_DIR = "offset_common_blocks"

CYCLE = 120.0
Y_BIN = 0.01

# 今回は存在有無だけを描く
USE_COUNTS = False

# 横軸は 20~50 を 2.5 km/h 刻みで固定
SPEED_MIN = 20.0
SPEED_MAX = 50.0
SPEED_STEP = 2.5

OFFSET_COLS = [
    ("x1opt", "Intersection 1"),
    ("x2opt", "Intersection 2"),
    ("x3opt", "Intersection 3"),
]

# 白 / 薄赤
binary_cmap = ListedColormap(["white", "#f4cccc"])
binary_norm = BoundaryNorm([-0.5, 0.5, 1.5], binary_cmap.N)


# =========================
# 補助関数
# =========================
def detect_route_col(df):
    for c in ["route_id", "路線番号", "Route", "route"]:
        if c in df.columns:
            return c
    raise ValueError(f"route列が見つかりません: {list(df.columns)}")

def detect_speed_col(df):
    for c in ["系統速度", "speed", "V", "coord_speed"]:
        if c in df.columns:
            return c
    raise ValueError(f"speed列が見つかりません: {list(df.columns)}")

def normalize_speed(v):
    try:
        return float(v)
    except Exception:
        return v

def build_speed_axis():
    n = int(round((SPEED_MAX - SPEED_MIN) / SPEED_STEP)) + 1
    return [round(SPEED_MIN + i * SPEED_STEP, 10) for i in range(n)]

def compute_x_edges(speeds):
    speeds = list(map(float, speeds))
    mids = [(speeds[i] + speeds[i + 1]) / 2 for i in range(len(speeds) - 1)]
    left = speeds[0] - (mids[0] - speeds[0])
    right = speeds[-1] + (speeds[-1] - mids[-1])
    return np.array([left] + mids + [right], dtype=float)

def offset_to_bin(offset_value):
    y = (float(offset_value) / CYCLE) % 1.0
    idx = int(np.floor(y / Y_BIN))
    idx = max(0, min(idx, int(round(1 / Y_BIN)) - 1))
    return idx

def make_matrix(route_df, speed_col, offset_col, speeds):
    n_y = int(round(1.0 / Y_BIN))
    n_x = len(speeds)
    mat = np.zeros((n_y, n_x), dtype=float)

    speed_to_idx = {float(v): i for i, v in enumerate(speeds)}

    for _, row in route_df.iterrows():
        v = float(row[speed_col])
        if v not in speed_to_idx:
            continue
        x_idx = speed_to_idx[v]
        y_idx = offset_to_bin(row[offset_col])
        mat[y_idx, x_idx] += 1.0

    # 存在有無だけにする
    mat = (mat > 0).astype(float)
    return mat


# =========================
# メイン
# =========================
os.makedirs(OUT_DIR, exist_ok=True)

df = pd.read_csv(INPUT_CSV, encoding="utf-8-sig")
route_col = detect_route_col(df)
speed_col = detect_speed_col(df)
df[speed_col] = df[speed_col].map(normalize_speed)

for col, _ in OFFSET_COLS:
    if col not in df.columns:
        raise ValueError(f"{col} 列が見つかりません。列一覧: {list(df.columns)}")

all_routes = sorted(df[route_col].dropna().unique())

# 横軸は全路線共通で固定
speeds = build_speed_axis()
x_edges = compute_x_edges(speeds)
y_edges = np.arange(0.0, 1.0 + Y_BIN, Y_BIN)

for route_id in all_routes:
    g = df[df[route_col] == route_id].copy()

    fig, axes = plt.subplots(
        nrows=3, ncols=1, figsize=(12, 10), sharex=True, constrained_layout=True
    )

    for ax, (offset_col, title) in zip(axes, OFFSET_COLS):
        mat = make_matrix(g, speed_col, offset_col, speeds)

        ax.pcolormesh(
            x_edges,
            y_edges,
            mat,
            shading="flat",
            cmap=binary_cmap,
            norm=binary_norm,
        )

        ax.set_ylim(0, 1)
        ax.set_xlim(SPEED_MIN - SPEED_STEP / 2, SPEED_MAX + SPEED_STEP / 2)
        ax.set_ylabel("Normalized offset (x/C)")
        ax.set_title(title)
        ax.set_yticks(np.arange(0, 1.01, 0.1))

        # 横軸目盛りを 2.5 km/h 刻みに固定
        ax.set_xticks(np.arange(SPEED_MIN, SPEED_MAX + 0.001, SPEED_STEP))

    axes[-1].set_xlabel("Speed [km/h]")
    fig.suptitle(
        f"Route {int(route_id)}: optimal offset distribution by speed",
        fontsize=14
    )

    # 凡例
    legend_handles = [
        Patch(facecolor="#f4cccc", edgecolor="black", label="Optimal offset exists"),
        Patch(facecolor="white", edgecolor="black", label="No optimal offset"),
    ]
    axes[0].legend(
        handles=legend_handles,
        loc="upper right",
        frameon=True,
        fontsize=10
    )

    out_png = os.path.join(OUT_DIR, f"route_{int(route_id)}_offset_blocks.png")
    plt.savefig(out_png, dpi=220, bbox_inches="tight")
    plt.close(fig)

print("完了しました。")
print(f"入力CSV: {INPUT_CSV}")
print(f"出力先  : {OUT_DIR}")