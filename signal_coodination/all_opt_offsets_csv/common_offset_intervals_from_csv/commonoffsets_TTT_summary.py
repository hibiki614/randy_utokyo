import os
import pandas as pd
import numpy as np

# =========================
# 設定
# =========================
INTERVAL_CSV = "common_offset_intervals_long_absolute.csv"
RESULTS_FINAL_XLSX = "results_final.xlsx"
RESULTS_SHEET = "Sheet1"   # 必要に応じて変更
OUT_DIR = "interval_summary_maximal"

# TTT一定とみなす閾値
TTT_CONST_THRESHOLD = 0.1

os.makedirs(OUT_DIR, exist_ok=True)


# =========================
# 補助関数
# =========================
def detect_route_col(df):
    for c in ["路線番号", "route_id", "Route", "route"]:
        if c in df.columns:
            return c
    raise ValueError(f"route列が見つかりません: {list(df.columns)}")

def detect_speed_col(df):
    for c in ["系統速度", "speed", "V", "coord_speed"]:
        if c in df.columns:
            return c
    raise ValueError(f"speed列が見つかりません: {list(df.columns)}")

def detect_ttt_col(df):
    for c in ["TTT(s/veh)", "TTT", "TTT_s_veh"]:
        if c in df.columns:
            return c
    raise ValueError(f"TTT列が見つかりません: {list(df.columns)}")

def normalize_speed(v):
    try:
        return float(v)
    except Exception:
        return v

def get_sorted_speed_list(results_df, route_col, speed_col, route_id):
    g = results_df[results_df[route_col] == route_id].copy()
    return sorted(g[speed_col].dropna().unique())

def is_contained(row_small, row_big):
    """
    small区間がbig区間に包含されるか
    同一路線前提
    """
    return (
        row_big["start_speed"] <= row_small["start_speed"] and
        row_small["end_speed"] <= row_big["end_speed"] and
        (
            row_big["start_speed"] < row_small["start_speed"] or
            row_small["end_speed"] < row_big["end_speed"]
        )
    )

def extract_maximal_intervals(df, route_col_name="route_id"):
    """
    flag=1 の区間群から、包含される部分区間を除いて極大区間だけ残す
    """
    out = []

    for route_id, g in df.groupby(route_col_name, dropna=False):
        rows = g.to_dict("records")
        keep = []

        for i, r in enumerate(rows):
            contained = False
            for j, s in enumerate(rows):
                if i == j:
                    continue
                if is_contained(r, s):
                    contained = True
                    break
            if not contained:
                keep.append(r)

        if keep:
            out.extend(keep)

    if len(out) == 0:
        return pd.DataFrame(columns=df.columns)

    out_df = pd.DataFrame(out).drop_duplicates()
    out_df = out_df.sort_values(
        by=[route_col_name, "start_speed", "end_speed"],
        ascending=[True, True, True]
    ).reset_index(drop=True)
    return out_df


# =========================
# 読み込み
# =========================
interval_df = pd.read_csv(INTERVAL_CSV, encoding="utf-8-sig")
results_df = pd.read_excel(RESULTS_FINAL_XLSX, sheet_name=RESULTS_SHEET)

interval_route_col = detect_route_col(interval_df)
results_route_col = detect_route_col(results_df)
speed_col = detect_speed_col(results_df)
ttt_col = detect_ttt_col(results_df)

interval_df["start_speed"] = interval_df["start_speed"].map(normalize_speed)
interval_df["end_speed"] = interval_df["end_speed"].map(normalize_speed)
results_df[speed_col] = results_df[speed_col].map(normalize_speed)

# route列名を統一
if interval_route_col != "route_id":
    interval_df = interval_df.rename(columns={interval_route_col: "route_id"})
if results_route_col != "route_id":
    results_df = results_df.rename(columns={results_route_col: "route_id"})


# =========================
# interval表に TTT情報を付与
# =========================
rows = []

for _, r in interval_df.iterrows():
    route_id = r["route_id"]
    v_start = r["start_speed"]
    v_end = r["end_speed"]

    g = results_df[
        (results_df["route_id"] == route_id) &
        (results_df[speed_col] >= v_start) &
        (results_df[speed_col] <= v_end)
    ].copy()

    observed_speeds = sorted(g[speed_col].dropna().unique())
    observed_n = len(observed_speeds)

    if g.empty:
        ttt_min = np.nan
        ttt_max = np.nan
        ttt_range = np.nan
        ttt_const_flag = np.nan
    else:
        ttt_min = g[ttt_col].min()
        ttt_max = g[ttt_col].max()
        ttt_range = ttt_max - ttt_min
        ttt_const_flag = int(ttt_range <= TTT_CONST_THRESHOLD)

    row = dict(r)
    row["observed_n_speeds_in_results_final"] = observed_n
    row["TTT_min_in_interval"] = ttt_min
    row["TTT_max_in_interval"] = ttt_max
    row["TTT_range"] = ttt_range
    row["ttt_const_threshold"] = TTT_CONST_THRESHOLD
    row["ttt_const_flag"] = ttt_const_flag
    row["common_flag"] = int(r["all_common_count"] >= 1)
    row["both_flag"] = int((r["all_common_count"] >= 1) and (ttt_const_flag == 1))
    rows.append(row)

integrated_df = pd.DataFrame(rows)

# 並び
integrated_df = integrated_df.sort_values(
    by=["route_id", "start_speed", "end_speed"],
    ascending=[True, True, True]
).reset_index(drop=True)


# =========================
# 1) 共通最適オフセット存在区間の極大区間
# =========================
common_df = integrated_df[integrated_df["common_flag"] == 1].copy()
common_max_df = extract_maximal_intervals(common_df, route_col_name="route_id")

# =========================
# 2) TTT一定区間の極大区間
# =========================
ttt_const_df = integrated_df[integrated_df["ttt_const_flag"] == 1].copy()
ttt_const_max_df = extract_maximal_intervals(ttt_const_df, route_col_name="route_id")

# =========================
# 3) 両方満たす区間の極大区間
# =========================
both_df = integrated_df[integrated_df["both_flag"] == 1].copy()
both_max_df = extract_maximal_intervals(both_df, route_col_name="route_id")

# integrated maximal:
# 全極大区間を1つにまとめて、どの性質で拾われたかを見えるようにする
common_tag = common_max_df.copy()
common_tag["interval_type"] = "common_optimal"

ttt_tag = ttt_const_max_df.copy()
ttt_tag["interval_type"] = "ttt_constant"

both_tag = both_max_df.copy()
both_tag["interval_type"] = "both"

integrated_max_df = pd.concat([common_tag, ttt_tag, both_tag], ignore_index=True)
integrated_max_df = integrated_max_df.sort_values(
    by=["route_id", "interval_type", "start_speed", "end_speed"],
    ascending=[True, True, True, True]
).reset_index(drop=True)


# =========================
# 保存
# =========================
all_csv = os.path.join(OUT_DIR, "integrated_all_intervals.csv")
common_csv = os.path.join(OUT_DIR, "common_maximal_intervals.csv")
ttt_csv = os.path.join(OUT_DIR, "ttt_const_maximal_intervals.csv")
integrated_csv = os.path.join(OUT_DIR, "integrated_maximal_intervals.csv")
both_csv = os.path.join(OUT_DIR, "both_maximal_intervals.csv")
excel_path = os.path.join(OUT_DIR, "integrated_maximal_intervals.xlsx")

integrated_df.to_csv(all_csv, index=False, encoding="utf-8-sig")
common_max_df.to_csv(common_csv, index=False, encoding="utf-8-sig")
ttt_const_max_df.to_csv(ttt_csv, index=False, encoding="utf-8-sig")
both_max_df.to_csv(both_csv, index=False, encoding="utf-8-sig")
integrated_max_df.to_csv(integrated_csv, index=False, encoding="utf-8-sig")

with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
    integrated_df.to_excel(writer, sheet_name="all_intervals", index=False)
    common_max_df.to_excel(writer, sheet_name="common_maximal", index=False)
    ttt_const_max_df.to_excel(writer, sheet_name="ttt_const_maximal", index=False)
    both_max_df.to_excel(writer, sheet_name="both_maximal", index=False)
    integrated_max_df.to_excel(writer, sheet_name="integrated_maximal", index=False)

print("完了")
print("出力:")
print(all_csv)
print(common_csv)
print(ttt_csv)
print(both_csv)
print(integrated_csv)
print(excel_path)