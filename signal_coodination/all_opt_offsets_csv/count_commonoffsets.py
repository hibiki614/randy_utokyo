import os
import math
import pandas as pd
import numpy as np


# =========================
# 設定
# =========================
INPUT_CSV = "all_opt_offsets.csv"
OUT_DIR = "common_offset_intervals_from_csv"

# False: (x0,x1,x2,x3) の完全一致で比較
# True : (x1-x0, x2-x1, x3-x2) の相対差分一致で比較
USE_RELATIVE = False

# 路線ごとの上位表示件数
TOP_K_INTERVALS_PER_ROUTE = 30

# 出力Excelのファイル名 suffix
MODE_NAME = "relative" if USE_RELATIVE else "absolute"


# =========================
# 補助関数
# =========================
def normalize_speed(v):
    try:
        return float(v)
    except Exception:
        return v


def detect_columns(df: pd.DataFrame):
    cols = list(df.columns)

    route_col_candidates = ["路線番号", "route_id", "Route", "route"]
    speed_col_candidates = ["系統速度", "speed", "V", "coord_speed"]

    x0_candidates = ["x0opt", "x0"]
    x1_candidates = ["x1opt", "x1"]
    x2_candidates = ["x2opt", "x2"]
    x3_candidates = ["x3opt", "x3"]

    def pick(cands, name):
        for c in cands:
            if c in cols:
                return c
        raise ValueError(f"{name} に対応する列が見つかりません。列一覧: {cols}")

    route_col = pick(route_col_candidates, "route")
    speed_col = pick(speed_col_candidates, "speed")
    x0_col = pick(x0_candidates, "x0")
    x1_col = pick(x1_candidates, "x1")
    x2_col = pick(x2_candidates, "x2")
    x3_col = pick(x3_candidates, "x3")

    return route_col, speed_col, x0_col, x1_col, x2_col, x3_col


def make_offset_key(row, x0_col, x1_col, x2_col, x3_col, use_relative=False):
    x0 = float(row[x0_col])
    x1 = float(row[x1_col])
    x2 = float(row[x2_col])
    x3 = float(row[x3_col])

    if use_relative:
        return (
            round(x1 - x0, 10),
            round(x2 - x1, 10),
            round(x3 - x2, 10),
        )
    return (
        round(x0, 10),
        round(x1, 10),
        round(x2, 10),
        round(x3, 10),
    )


def safe_sheet_name(name: str, max_len=31):
    invalid = ['\\', '/', '*', '[', ']', ':', '?']
    for ch in invalid:
        name = name.replace(ch, "_")
    return name[:max_len]


def speed_label(v):
    if isinstance(v, (int, np.integer)):
        return str(v)
    if isinstance(v, float):
        if abs(v - round(v)) < 1e-9:
            return f"{int(round(v))}"
        return f"{v:.1f}".rstrip("0").rstrip(".")
    return str(v)


# =========================
# 読み込み
# =========================
os.makedirs(OUT_DIR, exist_ok=True)

df = pd.read_csv(INPUT_CSV, encoding="utf-8-sig")
route_col, speed_col, x0_col, x1_col, x2_col, x3_col = detect_columns(df)

# 速度は float に寄せる
df[speed_col] = df[speed_col].map(normalize_speed)

# オフセットキー作成
df["_offset_key"] = df.apply(
    lambda r: make_offset_key(
        r, x0_col=x0_col, x1_col=x1_col, x2_col=x2_col, x3_col=x3_col,
        use_relative=USE_RELATIVE
    ),
    axis=1
)

# =========================
# 路線 × 速度ごとの集合を作る
# =========================
route_speed_sets = {}
all_routes = sorted(df[route_col].dropna().unique())

for route_id in all_routes:
    g_route = df[df[route_col] == route_id].copy()
    speeds = sorted(g_route[speed_col].dropna().unique())
    speed_to_set = {}

    for v in speeds:
        gv = g_route[g_route[speed_col] == v]
        speed_to_set[v] = set(gv["_offset_key"].tolist())

    route_speed_sets[route_id] = speed_to_set


# =========================
# 連続速度区間ごとの全体共通数を計算
# =========================
interval_rows = []
max_summary_rows = []

for route_id, speed_to_set in route_speed_sets.items():
    speeds = sorted(speed_to_set.keys())
    n = len(speeds)

    matrix = pd.DataFrame(index=speeds, columns=speeds, dtype=float)

    route_interval_rows = []

    best_len = -1
    best_count = -1
    best_start = None
    best_end = None

    for i in range(n):
        current_intersection = None

        for j in range(i, n):
            v_start = speeds[i]
            v_end = speeds[j]

            s = speed_to_set[speeds[j]]
            if current_intersection is None:
                current_intersection = set(s)
            else:
                current_intersection = current_intersection & s

            all_common_count = len(current_intersection)
            n_speeds = j - i + 1

            interval_row = {
                "route_id": route_id,
                "start_speed": v_start,
                "end_speed": v_end,
                "n_speeds": n_speeds,
                "all_common_count": all_common_count,
                "exists_common": int(all_common_count >= 1),
            }
            route_interval_rows.append(interval_row)
            interval_rows.append(interval_row)

            matrix.loc[v_start, v_end] = all_common_count

            # 最長区間を優先し、同じ長さなら共通数が多い方、さらに同じなら開始速度が小さい方
            if all_common_count >= 1:
                is_better = False
                if n_speeds > best_len:
                    is_better = True
                elif n_speeds == best_len and all_common_count > best_count:
                    is_better = True
                elif n_speeds == best_len and all_common_count == best_count:
                    if best_start is None or v_start < best_start:
                        is_better = True

                if is_better:
                    best_len = n_speeds
                    best_count = all_common_count
                    best_start = v_start
                    best_end = v_end

    route_interval_df = pd.DataFrame(route_interval_rows)

    # 路線別 long CSV
    route_long_path = os.path.join(
        OUT_DIR,
        f"route_{route_id}_common_offset_intervals_long_{MODE_NAME}.csv"
    )
    route_interval_df.to_csv(route_long_path, index=False, encoding="utf-8-sig")

    # 路線別 matrix CSV
    route_matrix_path = os.path.join(
        OUT_DIR,
        f"route_{route_id}_common_offset_interval_matrix_{MODE_NAME}.csv"
    )
    matrix.to_csv(route_matrix_path, encoding="utf-8-sig")

    # 見やすい上位区間
    top_df = route_interval_df[route_interval_df["exists_common"] == 1].copy()
    if not top_df.empty:
        top_df = top_df.sort_values(
            by=["n_speeds", "all_common_count", "start_speed", "end_speed"],
            ascending=[False, False, True, True]
        ).head(TOP_K_INTERVALS_PER_ROUTE)
    else:
        top_df = pd.DataFrame(columns=route_interval_df.columns)

    route_top_path = os.path.join(
        OUT_DIR,
        f"route_{route_id}_top_common_intervals_{MODE_NAME}.csv"
    )
    top_df.to_csv(route_top_path, index=False, encoding="utf-8-sig")

    # 最長区間サマリ
    if best_len >= 1:
        max_summary_rows.append({
            "route_id": route_id,
            "start_speed": best_start,
            "end_speed": best_end,
            "n_speeds": best_len,
            "all_common_count": best_count,
            "exists_common": 1,
        })
    else:
        max_summary_rows.append({
            "route_id": route_id,
            "start_speed": np.nan,
            "end_speed": np.nan,
            "n_speeds": 0,
            "all_common_count": 0,
            "exists_common": 0,
        })


# =========================
# 全体CSV
# =========================
intervals_df = pd.DataFrame(interval_rows)
summary_df = pd.DataFrame(max_summary_rows)

intervals_path = os.path.join(
    OUT_DIR,
    f"common_offset_intervals_long_{MODE_NAME}.csv"
)
summary_path = os.path.join(
    OUT_DIR,
    f"common_offset_intervals_max_summary_{MODE_NAME}.csv"
)

intervals_df.to_csv(intervals_path, index=False, encoding="utf-8-sig")
summary_df.to_csv(summary_path, index=False, encoding="utf-8-sig")


# =========================
# Excel出力
# =========================
excel_path = os.path.join(
    OUT_DIR,
    f"common_offset_intervals_{MODE_NAME}.xlsx"
)

with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
    intervals_df.to_excel(writer, sheet_name="intervals_long", index=False)
    summary_df.to_excel(writer, sheet_name="max_summary", index=False)

    for route_id in all_routes:
        route_long_csv = os.path.join(
            OUT_DIR,
            f"route_{route_id}_common_offset_intervals_long_{MODE_NAME}.csv"
        )
        route_matrix_csv = os.path.join(
            OUT_DIR,
            f"route_{route_id}_common_offset_interval_matrix_{MODE_NAME}.csv"
        )
        route_top_csv = os.path.join(
            OUT_DIR,
            f"route_{route_id}_top_common_intervals_{MODE_NAME}.csv"
        )

        route_long_df = pd.read_csv(route_long_csv, encoding="utf-8-sig")
        route_matrix_df = pd.read_csv(route_matrix_csv, encoding="utf-8-sig", index_col=0)
        route_top_df = pd.read_csv(route_top_csv, encoding="utf-8-sig")

        route_long_df.to_excel(
            writer,
            sheet_name=safe_sheet_name(f"intervals_r{route_id}"),
            index=False
        )
        route_matrix_df.to_excel(
            writer,
            sheet_name=safe_sheet_name(f"matrix_r{route_id}")
        )
        route_top_df.to_excel(
            writer,
            sheet_name=safe_sheet_name(f"top_r{route_id}"),
            index=False
        )

print("完了しました。")
print(f"入力CSV: {INPUT_CSV}")
print(f"出力先   : {OUT_DIR}")
print(f"比較モード: {MODE_NAME}")
print("主な出力:")
print(f" - {intervals_path}")
print(f" - {summary_path}")
print(f" - {excel_path}")