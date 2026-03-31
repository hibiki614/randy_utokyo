import os
import numpy as np
import pandas as pd

# =========================
# 設定
# =========================
INPUT_CSV = "all_opt_offsets.csv"
OUT_DIR = "offset_pattern_id_1to1000000"

CYCLE = 120.0
DX = 1.2   # オフセット刻み幅 [s]

OFFSET_COLS = ["x1opt", "x2opt", "x3opt"]


# =========================
# 補助関数
# =========================
def detect_route_col(df):
    for c in ["route_id", "路線番号", "Route", "route"]:
        if c in df.columns:
            return c
    return None

def detect_speed_col(df):
    for c in ["系統速度", "speed", "V", "coord_speed"]:
        if c in df.columns:
            return c
    return None

def normalize_numeric(v):
    try:
        return float(v)
    except Exception:
        return np.nan

def mod_cycle(x, cycle):
    return float(x) % cycle

def offset_to_index(x_mod, dx, cycle):
    """
    x_mod を 0, dx, 2dx, ... の何番目かに変換
    例: cycle=120, dx=1.2 -> 0~99
    """
    n_steps = int(round(cycle / dx))  # 100
    idx = int(round(x_mod / dx))

    # 120.0 ちょうど等が来たときの保険
    idx = idx % n_steps

    # 格子に乗っているか確認（必要なら緩くしてもOK）
    if not np.isclose(x_mod, idx * dx, atol=1e-9):
        raise ValueError(
            f"オフセット {x_mod} は dx={dx} の格子に乗っていません。"
        )
    return idx

def indices_to_pattern_id(i1, i2, i3, base):
    """
    3次元インデックス (0~base-1) を 1~base^3 のIDに変換
    """
    return i1 * (base ** 2) + i2 * base + i3 + 1


# =========================
# メイン
# =========================
os.makedirs(OUT_DIR, exist_ok=True)

df = pd.read_csv(INPUT_CSV, encoding="utf-8-sig")

route_col = detect_route_col(df)
speed_col = detect_speed_col(df)

for col in OFFSET_COLS:
    if col not in df.columns:
        raise ValueError(f"{col} 列が見つかりません。列一覧: {list(df.columns)}")

if speed_col is not None:
    df[speed_col] = df[speed_col].map(normalize_numeric)

# 数値化 + mod
for col in OFFSET_COLS:
    df[col] = df[col].map(normalize_numeric)
    df[f"{col}_mod"] = df[col].map(lambda x: mod_cycle(x, CYCLE))
    df[f"{col}_norm"] = df[f"{col}_mod"] / CYCLE

# 0~99 の離散インデックスへ
n_steps = int(round(CYCLE / DX))   # 100
if n_steps != 100:
    print(f"注意: cycle/dx = {n_steps} 通りです（100通りではありません）")

for col in OFFSET_COLS:
    df[f"{col}_idx"] = df[f"{col}_mod"].map(lambda x: offset_to_index(x, DX, CYCLE))

# 1~1000000 の pattern_id を付与
df["pattern_id"] = df.apply(
    lambda r: indices_to_pattern_id(
        int(r["x1opt_idx"]),
        int(r["x2opt_idx"]),
        int(r["x3opt_idx"]),
        n_steps
    ),
    axis=1
)

# pattern master 作成
pattern_master = (
    df[
        [
            "pattern_id",
            "x1opt_idx", "x2opt_idx", "x3opt_idx",
            "x1opt_mod", "x2opt_mod", "x3opt_mod",
            "x1opt_norm", "x2opt_norm", "x3opt_norm",
        ]
    ]
    .drop_duplicates()
    .sort_values("pattern_id", kind="mergesort")
    .reset_index(drop=True)
)

# 出現回数
count_df = (
    df.groupby("pattern_id", as_index=False)
      .size()
      .rename(columns={"size": "n_rows"})
      .sort_values(["n_rows", "pattern_id"], ascending=[False, True], kind="mergesort")
      .reset_index(drop=True)
)

count_df["display_id_freq"] = np.arange(1, len(count_df) + 1)

# マージ
df = df.merge(
    count_df[["pattern_id", "n_rows", "display_id_freq"]],
    on="pattern_id",
    how="left"
)

pattern_master = pattern_master.merge(
    count_df[["pattern_id", "n_rows", "display_id_freq"]],
    on="pattern_id",
    how="left"
)

# presence table
group_cols = ["pattern_id"]
if route_col is not None:
    group_cols.insert(0, route_col)
if speed_col is not None:
    group_cols.append(speed_col)

pattern_presence = (
    df[group_cols]
    .drop_duplicates()
    .sort_values(group_cols, kind="mergesort")
    .reset_index(drop=True)
)

# 出力
out_main = os.path.join(OUT_DIR, "all_opt_offsets_with_pattern_id.csv")
out_master = os.path.join(OUT_DIR, "pattern_master_1to1000000.csv")
out_presence = os.path.join(OUT_DIR, "pattern_presence_table.csv")

df.to_csv(out_main, index=False, encoding="utf-8-sig")
pattern_master.to_csv(out_master, index=False, encoding="utf-8-sig")
pattern_presence.to_csv(out_presence, index=False, encoding="utf-8-sig")

print("完了しました。")
print(f"入力CSV                 : {INPUT_CSV}")
print(f"出力先                  : {OUT_DIR}")
print(f"cycle                   : {CYCLE}")
print(f"dx                      : {DX}")
print(f"各交差点の離散通り数     : {n_steps}")
print(f"理論上のpattern総数      : {n_steps**3}")
print(f"実際に出現したpattern数  : {pattern_master['pattern_id'].nunique()}")
print(f"ID付きCSV               : {out_main}")
print(f"パターンマスタ          : {out_master}")
print(f"出現テーブル            : {out_presence}")