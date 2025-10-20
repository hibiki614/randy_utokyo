# -*- coding: utf-8 -*-
"""
Created on Tue Sep 30 16:04:30 2025

@author: OguchiLab
"""

# -*- coding: utf-8 -*-
"""
no01 を基準に、各シナリオ(no02〜no08)のリンク別「差分のみ」を GeoJSON 出力
・速度(V)、TTT、流量(Flow)を分けて出力
・各レイヤには base(=no01), scen(対象シナリオ), diff(差のみ) を収録
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path

# ===== パス設定 =====
base_dir = Path(r"C:/Users/OguchiLab/OneDrive/デスクトップ/randy_utokyo/拡張シナリオ/simcase")
links_geojson_path = base_dir / "network_geo/links.geojson"      # 既に作成済みのリンク形状
metrics_dir        = base_dir / "analysis"           # perlink_metrics_* がある場所
out_dir            = base_dir / "analysis"           # 差分GeoJSONの出力先
out_dir.mkdir(exist_ok=True)

BASE_SCEN   = "no01"
SCENARIOS   = [f"no0{i}" for i in range(2, 9)]       # no02〜no08

# ===== 読み込みヘルパ =====
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
    lid  = prop.get("link_id")
    if lid is None:
        continue
    link_rows.append({"link_id": lid})
    geoms.append(geom)

links_df = pd.DataFrame(link_rows)
links_df["__geom__"] = geoms

# ===== 基準(no01)メトリクス読み込み =====
base_csv = metrics_dir / f"perlink_metrics_{BASE_SCEN}.csv"
if not base_csv.exists():
    raise FileNotFoundError(f"{base_csv} が見つかりません。")
base_df = read_csv_flex(base_csv)
base_df = base_df.rename(columns={pick_link_id_col(base_df): "link_id"})
base_df = numericize(base_df)

# 列名の候補
V_CANDS    = ["V_link_kmh_mean", "V_mean", "V_link_mean", "V_kmh_mean"]
TTT_CANDS  = ["TTT_sec_mean", "TTT_mean", "TTT_total_mean"]
FLOW_CANDS = ["flow_veh_mean", "count_mean", "veh_count_mean", "flow_mean", "count_sum"]

v_col_base    = choose_metric_column(base_df, V_CANDS)
ttt_col_base  = choose_metric_column(base_df, TTT_CANDS)
flow_col_base = choose_metric_column(base_df, FLOW_CANDS)

metrics_info = []
if v_col_base   is not None: metrics_info.append(("V",    v_col_base))
if ttt_col_base is not None: metrics_info.append(("TTT",  ttt_col_base))
if flow_col_base is not None:metrics_info.append(("FLOW", flow_col_base))

# ===== シナリオごとに差分作成（差分のみ） =====
for scen in SCENARIOS:
    scen_csv = metrics_dir / f"perlink_metrics_{scen}.csv"
    if not scen_csv.exists():
        print(f"[WARN] {scen_csv.name} 不在のためスキップ")
        continue

    scen_df = read_csv_flex(scen_csv)
    scen_df = scen_df.rename(columns={pick_link_id_col(scen_df): "link_id"})
    scen_df = numericize(scen_df)

    for tag, base_col in metrics_info:
        # シナリオ側の列名
        if tag == "V":
            scen_col = (base_col if base_col in scen_df.columns else choose_metric_column(scen_df, V_CANDS))
        elif tag == "TTT":
            scen_col = (base_col if base_col in scen_df.columns else choose_metric_column(scen_df, TTT_CANDS))
        else:  # FLOW
            scen_col = (base_col if base_col in scen_df.columns else choose_metric_column(scen_df, FLOW_CANDS))
        if scen_col is None:
            print(f"[WARN] {scen} の {tag} 指標列が見つからずスキップ")
            continue

        b = base_df[["link_id", base_col]].copy().rename(columns={base_col: "base_val"})
        s = scen_df[["link_id", scen_col]].copy().rename(columns={scen_col: "scen_val"})

        merged = links_df.merge(b, on="link_id", how="left").merge(s, on="link_id", how="left")

        # 差分のみ（0割回避のため比率は作らない）
        merged["diff"] = merged["scen_val"] - merged["base_val"]

        # 必要最低限のプロパティ
        props_cols = ["link_id", "base_val", "scen_val", "diff"]
        feats = []
        for _, row in merged.iterrows():
            props = {k: (None if pd.isna(row[k]) else float(row[k]) if k != "link_id" else row[k]) for k in props_cols}
            props["base_scen"] = BASE_SCEN
            props["scen"]      = scen
            props["metric"]    = tag
            feats.append({
                "type": "Feature",
                "properties": props,
                "geometry": row["__geom__"]
            })

        out_fc = {"type": "FeatureCollection", "features": feats}
        out_path = out_dir / f"linksdiff_{tag}_{scen}.geojson"
        out_path.write_text(json.dumps(out_fc, ensure_ascii=False), encoding="utf-8")
        print(f"[OK] {out_path.name} 出力: features={len(feats)}")

print("✅ 差分GeoJSONの作成が完了（比率なし）。")
