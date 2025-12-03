# -*- coding: utf-8 -*-
"""
Created on Tue Oct 28 20:05:01 2025

@author: OguchiLab
"""

# -*- coding: utf-8 -*-
"""
no01–no05, no05–no07, no05–no06, no07–no08 のペアでリンク別差分GeoJSONを作成
・速度(V)、TTT、流量(Flow)を分けて出力
・各レイヤには base(基準), scen(比較対象), diff(差のみ) を収録
"""

import json
import pandas as pd
from pathlib import Path

# ===== パス設定 =====
base_dir = Path(r"C:/Users/OguchiLab/OneDrive/デスクトップ/randy_utokyo/拡張シナリオ/simcase22")
links_geojson_path = base_dir / "network_geo/links.geojson"
metrics_dir = base_dir / "analysis"
out_dir = base_dir / "analysis"
out_dir.mkdir(exist_ok=True)

# ===== 比較ペア指定 =====
COMPARE_PAIRS = [
    ("no01", "no05"),
    ("no05", "no07"),
    ("no05", "no06"),
    ("no07", "no08"),
]

# ===== 読み込み関数 =====
def read_csv_flex(path: Path) -> pd.DataFrame:
    for enc in ("utf-8-sig", "cp932", "utf-8"):
        try:
            return pd.read_csv(path, encoding=enc)
        except Exception:
            continue
    return pd.read_csv(path, encoding_errors="ignore")

def pick_link_id_col(df: pd.DataFrame) -> str:
    if "link_id" in df.columns:
        return "link_id"
    cand = [c for c in df.columns if "link" in c.lower() and "id" in c.lower()]
    if cand:
        return cand[0]
    raise KeyError("link_id（相当の列）が見つかりません。")

def choose_metric_column(df: pd.DataFrame, candidates):
    cols_lower = {c.lower(): c for c in df.columns}
    for key in candidates:
        if key.lower() in cols_lower:
            return cols_lower[key.lower()]
    for key in candidates:
        for c in df.columns:
            if key.lower() in c.lower():
                return c
    return None

def numericize(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for c in out.columns:
        if c == "link_id":
            continue
        out[c] = pd.to_numeric(out[c], errors="ignore")
    return out

# ===== links.geojson 読み込み =====
with open(links_geojson_path, "r", encoding="utf-8") as f:
    links_fc = json.load(f)
features = links_fc.get("features", [])
if not features:
    raise RuntimeError("links.geojson に features がありません。")

link_rows, geoms = [], []
for ft in features:
    prop = ft.get("properties", {})
    geom = ft.get("geometry", {})
    lid = prop.get("link_id")
    if lid is None:
        continue
    link_rows.append({"link_id": lid})
    geoms.append(geom)
links_df = pd.DataFrame(link_rows)
links_df["__geom__"] = geoms

# ===== メトリクス列候補 =====
V_CANDS = ["V_link_kmh_mean", "V_mean", "V_link_mean", "V_kmh_mean"]
TTT_CANDS = ["TTT_sec_mean", "TTT_mean", "TTT_total_mean"]
FLOW_CANDS = ["flow_veh_mean", "count_mean", "veh_count_mean", "flow_mean", "count_sum"]

# ===== 各ペアで処理 =====
for base_scen, scen in COMPARE_PAIRS:
    base_csv = metrics_dir / f"perlink_metrics_{base_scen}.csv"
    scen_csv = metrics_dir / f"perlink_metrics_{scen}.csv"

    if not base_csv.exists() or not scen_csv.exists():
        print(f"[WARN] {base_csv.name} または {scen_csv.name} が見つからずスキップ")
        continue

    base_df = read_csv_flex(base_csv)
    base_df = base_df.rename(columns={pick_link_id_col(base_df): "link_id"})
    base_df = numericize(base_df)

    scen_df = read_csv_flex(scen_csv)
    scen_df = scen_df.rename(columns={pick_link_id_col(scen_df): "link_id"})
    scen_df = numericize(scen_df)

    # 指標列の特定
    v_col_base = choose_metric_column(base_df, V_CANDS)
    ttt_col_base = choose_metric_column(base_df, TTT_CANDS)
    flow_col_base = choose_metric_column(base_df, FLOW_CANDS)

    metrics_info = []
    if v_col_base is not None:
        metrics_info.append(("V", v_col_base))
    if ttt_col_base is not None:
        metrics_info.append(("TTT", ttt_col_base))
    if flow_col_base is not None:
        metrics_info.append(("FLOW", flow_col_base))

    # ===== 各指標ごとにGeoJSON作成 =====
    for tag, base_col in metrics_info:
        if tag == "V":
            scen_col = base_col if base_col in scen_df.columns else choose_metric_column(scen_df, V_CANDS)
        elif tag == "TTT":
            scen_col = base_col if base_col in scen_df.columns else choose_metric_column(scen_df, TTT_CANDS)
        else:
            scen_col = base_col if base_col in scen_df.columns else choose_metric_column(scen_df, FLOW_CANDS)

        if scen_col is None:
            print(f"[WARN] {scen} の {tag} 指標列が見つからずスキップ")
            continue

        b = base_df[["link_id", base_col]].copy().rename(columns={base_col: "base_val"})
        s = scen_df[["link_id", scen_col]].copy().rename(columns={scen_col: "scen_val"})
        merged = links_df.merge(b, on="link_id", how="left").merge(s, on="link_id", how="left")

        merged["diff"] = merged["scen_val"] - merged["base_val"]

        props_cols = ["link_id", "base_val", "scen_val", "diff"]
        feats = []
        for _, row in merged.iterrows():
            props = {k: (None if pd.isna(row[k]) else float(row[k]) if k != "link_id" else row[k]) for k in props_cols}
            props["base_scen"] = base_scen
            props["scen"] = scen
            props["metric"] = tag
            feats.append({
                "type": "Feature",
                "properties": props,
                "geometry": row["__geom__"]
            })

        out_fc = {"type": "FeatureCollection", "features": feats}
        out_path = out_dir / f"linksdiff_{tag}_{base_scen}_vs_{scen}.geojson"
        out_path.write_text(json.dumps(out_fc, ensure_ascii=False), encoding="utf-8")
        print(f"[OK] {out_path.name} 出力: features={len(feats)}")

print("✅ 差分GeoJSONの作成が完了（指定ペア比較）。")
