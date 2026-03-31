import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
from matplotlib.patches import Patch

# =========================
# 設定
# =========================
INPUT_CSV = "offset_pattern_id_1to1000000/all_opt_offsets_with_pattern_id.csv"
OUT_DIR = "pattern_id_presence_plots_run2"

SPEED_MIN = 20.0
SPEED_MAX = 50.0
SPEED_STEP = 2.5

FIGSIZE = (12, 8)
DPI = 220

# 色
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

def build_speed_axis():
    n = int(round((SPEED_MAX - SPEED_MIN) / SPEED_STEP)) + 1
    return [round(SPEED_MIN + i * SPEED_STEP, 10) for i in range(n)]

def compute_x_edges(speeds):
    speeds = list(map(float, speeds))
    mids = [(speeds[i] + speeds[i + 1]) / 2 for i in range(len(speeds) - 1)]
    left = speeds[0] - (mids[0] - speeds[0])
    right = speeds[-1] + (speeds[-1] - mids[-1])
    return np.array([left] + mids + [right], dtype=float)

def compute_y_edges(n_rows):
    return np.arange(-0.5, n_rows + 0.5, 1.0)

def choose_yticks(n_rows, max_ticks=15):
    if n_rows <= max_ticks:
        return list(range(n_rows))
    step = int(np.ceil(n_rows / max_ticks))
    ticks = list(range(0, n_rows, step))
    if ticks[-1] != n_rows - 1:
        ticks.append(n_rows - 1)
    return ticks

def max_consecutive_run(speed_list, speed_axis):
    """
    speed_list: そのpatternが出た速度のlist
    speed_axis: 全速度軸（20, 22.5, ..., 50）
    """
    speed_to_pos = {float(v): i for i, v in enumerate(speed_axis)}
    pos = sorted(speed_to_pos[float(v)] for v in speed_list if float(v) in speed_to_pos)

    if not pos:
        return 0

    max_run = 1
    current_run = 1
    for i in range(1, len(pos)):
        if pos[i] == pos[i - 1] + 1:
            current_run += 1
        else:
            current_run = 1
        max_run = max(max_run, current_run)

    return max_run

def summarize_pattern_runs(route_df, speed_col, pattern_col, speed_axis):
    """
    各 pattern_id ごとに最大連続長を計算
    """
    rows = []
    dedup = route_df[[speed_col, pattern_col]].drop_duplicates()

    for pid, sub in dedup.groupby(pattern_col):
        speed_list = sorted(sub[speed_col].astype(float).unique())
        rows.append({
            "pattern_id": int(pid),
            "n_speeds": len(speed_list),
            "max_run": max_consecutive_run(speed_list, speed_axis),
        })

    if not rows:
        return pd.DataFrame(columns=["pattern_id", "n_speeds", "max_run"])

    return pd.DataFrame(rows)

def make_presence_matrix(route_df, speed_col, pattern_col, speeds, pattern_ids_sorted):
    n_y = len(pattern_ids_sorted)
    n_x = len(speeds)
    mat = np.zeros((n_y, n_x), dtype=float)

    speed_to_idx = {float(v): i for i, v in enumerate(speeds)}
    pattern_to_row = {int(pid): i for i, pid in enumerate(pattern_ids_sorted)}

    dedup = route_df[[speed_col, pattern_col]].drop_duplicates()

    for _, row in dedup.iterrows():
        v = float(row[speed_col])
        pid = int(row[pattern_col])

        if v not in speed_to_idx or pid not in pattern_to_row:
            continue

        x_idx = speed_to_idx[v]
        y_idx = pattern_to_row[pid]
        mat[y_idx, x_idx] = 1.0

    return mat


# =========================
# メイン
# =========================
os.makedirs(OUT_DIR, exist_ok=True)

df = pd.read_csv(INPUT_CSV, encoding="utf-8-sig")

route_col = detect_route_col(df)
speed_col = detect_speed_col(df)

if "pattern_id" not in df.columns:
    raise ValueError(f"pattern_id 列が見つかりません。列一覧: {list(df.columns)}")

df[speed_col] = pd.to_numeric(df[speed_col], errors="coerce")
df["pattern_id"] = pd.to_numeric(df["pattern_id"], errors="coerce").astype("Int64")
df = df.dropna(subset=[route_col, speed_col, "pattern_id"]).copy()

speeds = build_speed_axis()
x_edges = compute_x_edges(speeds)
all_routes = sorted(df[route_col].unique())

summary_all = []

for route_id in all_routes:
    g = df[df[route_col] == route_id].copy()

    # 各 pattern_id の連続長を計算
    run_df = summarize_pattern_runs(g, speed_col, "pattern_id", speeds)
    run_df.insert(0, route_col, route_id)
    summary_all.append(run_df)

    # 最大連続長が2以上だけ残す
    valid_patterns = sorted(run_df.loc[run_df["max_run"] >= 2, "pattern_id"].astype(int).unique())

    if len(valid_patterns) == 0:
        print(f"Route {route_id}: max_run >= 2 のpatternなし")
        continue

    g_plot = g[g["pattern_id"].isin(valid_patterns)].copy()

    pattern_ids_sorted = sorted(valid_patterns)
    n_patterns = len(pattern_ids_sorted)

    y_edges = compute_y_edges(n_patterns)
    mat = make_presence_matrix(g_plot, speed_col, "pattern_id", speeds, pattern_ids_sorted)

    fig, ax = plt.subplots(figsize=FIGSIZE, constrained_layout=True)

    ax.pcolormesh(
        x_edges,
        y_edges,
        mat,
        shading="flat",
        cmap=binary_cmap,
        norm=binary_norm,
    )

    ax.set_xlim(SPEED_MIN - SPEED_STEP / 2, SPEED_MAX + SPEED_STEP / 2)
    ax.set_ylim(-0.5, n_patterns - 0.5)
    ax.set_xlabel("Speed [km/h]")
    ax.set_ylabel("Pattern ID (ascending among max_run >= 2)")
    ax.set_title(f"Route {int(route_id)}: pattern existence by speed (max run >= 2)")

    ax.set_xticks(np.arange(SPEED_MIN, SPEED_MAX + 0.001, SPEED_STEP))

    yticks = choose_yticks(n_patterns, max_ticks=15)
    yticklabels = [str(pattern_ids_sorted[i]) for i in yticks]
    ax.set_yticks(yticks)
    ax.set_yticklabels(yticklabels)

    legend_handles = [
        Patch(facecolor="#f4cccc", edgecolor="black", label="Pattern exists"),
        Patch(facecolor="white", edgecolor="black", label="No pattern"),
    ]
    ax.legend(
        handles=legend_handles,
        loc="upper left",
        bbox_to_anchor=(1.02, 1.0),
        borderaxespad=0.0,
        frameon=True,
        fontsize=10
    )

    out_png = os.path.join(OUT_DIR, f"route_{int(route_id)}_pattern_presence_run2.png")
    plt.savefig(out_png, dpi=DPI, bbox_inches="tight")
    plt.close(fig)

# 集計表も保存
summary_df = pd.concat(summary_all, ignore_index=True) if summary_all else pd.DataFrame()
summary_df.to_csv(
    os.path.join(OUT_DIR, "pattern_run_summary_by_route.csv"),
    index=False,
    encoding="utf-8-sig"
)

print("完了しました。")
print(f"入力CSV: {INPUT_CSV}")
print(f"出力先 : {OUT_DIR}")
print("集計表 : pattern_run_summary_by_route.csv")