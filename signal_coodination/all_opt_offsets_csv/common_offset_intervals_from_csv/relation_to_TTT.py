import os
import pandas as pd
import numpy as np

# =========================
# 設定
# =========================
INTERVAL_CSV = "common_offset_intervals_long_absolute.csv"
RESULTS_FINAL_XLSX = "results_final.xlsx"
RESULTS_SHEET = "Sheet1"   # 必要なら "results" などに変更
OUT_DIR = "interval_ttt_relation"

# TTT一定とみなす閾値
TTT_CONST_THRESHOLD = 0.0
# 例:
# 0.0 なら完全一致
# 0.1 なら 0.1 s/veh 以内を一定とみなす
# 0.5 なら 0.5 s/veh 以内

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


# =========================
# 読み込み
# =========================
interval_df = pd.read_csv(INTERVAL_CSV, encoding="utf-8-sig")
results_df = pd.read_excel(RESULTS_FINAL_XLSX, sheet_name=RESULTS_SHEET)

interval_route_col = detect_route_col(interval_df)
interval_df["start_speed"] = interval_df["start_speed"].map(normalize_speed)
interval_df["end_speed"] = interval_df["end_speed"].map(normalize_speed)

route_col = detect_route_col(results_df)
speed_col = detect_speed_col(results_df)
ttt_col = detect_ttt_col(results_df)

results_df[speed_col] = results_df[speed_col].map(normalize_speed)


# =========================
# 区間ごとの TTT range を計算
# =========================
rows = []

for _, r in interval_df.iterrows():
    route_id = r[interval_route_col]
    v_start = r["start_speed"]
    v_end = r["end_speed"]

    g = results_df[
        (results_df[route_col] == route_id) &
        (results_df[speed_col] >= v_start) &
        (results_df[speed_col] <= v_end)
    ].copy()

    # 速度数チェック
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
    rows.append(row)

merged_df = pd.DataFrame(rows)

# =========================
# 関連を見るためのフラグ
# =========================
merged_df["all_common_flag"] = (merged_df["all_common_count"] >= 1).astype(int)

# クロス集計
cross_tab = pd.crosstab(
    merged_df["ttt_const_flag"],
    merged_df["all_common_flag"],
    rownames=["ttt_const_flag"],
    colnames=["all_common_flag"],
    dropna=False
).reset_index()

# 路線ごとの要約
route_summary = (
    merged_df.groupby(interval_route_col, dropna=False)
    .agg(
        n_intervals=("all_common_count", "size"),
        n_all_common=("all_common_flag", "sum"),
        n_ttt_const=("ttt_const_flag", lambda s: np.nansum(s == 1)),
        n_both=("all_common_flag", lambda s: 0)  # 後で上書き
    )
    .reset_index()
)

both_df = (
    merged_df.assign(both=((merged_df["all_common_flag"] == 1) & (merged_df["ttt_const_flag"] == 1)).astype(int))
    .groupby(interval_route_col, dropna=False)["both"]
    .sum()
    .reset_index()
    .rename(columns={"both": "n_both"})
)

route_summary = route_summary.drop(columns=["n_both"]).merge(both_df, on=interval_route_col, how="left")

# 見やすい上位表
top_df = merged_df.sort_values(
    by=["ttt_const_flag", "all_common_count", "n_speeds", "TTT_range"],
    ascending=[False, False, False, True]
).copy()

# =========================
# 保存
# =========================
mode_name = f"thr_{str(TTT_CONST_THRESHOLD).replace('.', 'p')}"

merged_csv = os.path.join(OUT_DIR, f"interval_ttt_relation_{mode_name}.csv")
cross_csv = os.path.join(OUT_DIR, f"interval_ttt_relation_crosstab_{mode_name}.csv")
route_csv = os.path.join(OUT_DIR, f"interval_ttt_relation_route_summary_{mode_name}.csv")
top_csv = os.path.join(OUT_DIR, f"interval_ttt_relation_top_{mode_name}.csv")
excel_path = os.path.join(OUT_DIR, f"interval_ttt_relation_{mode_name}.xlsx")

merged_df.to_csv(merged_csv, index=False, encoding="utf-8-sig")
cross_tab.to_csv(cross_csv, index=False, encoding="utf-8-sig")
route_summary.to_csv(route_csv, index=False, encoding="utf-8-sig")
top_df.to_csv(top_csv, index=False, encoding="utf-8-sig")

with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
    merged_df.to_excel(writer, sheet_name="interval_ttt_relation", index=False)
    cross_tab.to_excel(writer, sheet_name="crosstab", index=False)
    route_summary.to_excel(writer, sheet_name="route_summary", index=False)
    top_df.to_excel(writer, sheet_name="top", index=False)

print("完了")
print("出力:")
print(merged_csv)
print(cross_csv)
print(route_csv)
print(top_csv)
print(excel_path)