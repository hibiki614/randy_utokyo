# -*- coding: utf-8 -*-
"""
Created on Tue Sep 30 15:43:23 2025

@author: OguchiLab
"""

# -*- coding: utf-8 -*-
import json
import pandas as pd
import numpy as np
from pathlib import Path

# ===== パス設定 =====
base_dir = Path(r"C:/Users/OguchiLab/OneDrive/デスクトップ/randy_utokyo/拡張シナリオ/simcase")
links_geojson_path = base_dir / "network_geo/links.geojson"          # 前工程の出力
metrics_dir        = base_dir / "analysis"               # perlink_metrics_* がある場所
out_dir            = base_dir / "analysis"               # 出力先（analysis配下に保存）
out_dir.mkdir(exist_ok=True)

# 対象シナリオ
SCENARIOS = [f"no0{i}" for i in range(1, 9)]  # no01〜no08

# ===== ユーティリティ =====
def read_csv_flex(path: Path) -> pd.DataFrame:
    # 文字コードの揺れに強く
    for enc in ("utf-8-sig", "cp932", "utf-8"):
        try:
            return pd.read_csv(path, encoding=enc)
        except Exception:
            continue
    return pd.read_csv(path, encoding_errors="ignore")

def pick_link_id_col(df: pd.DataFrame) -> str:
    # link_id 列を探す（完全一致優先、なければ "link" と "id" を両方含む列）
    cols = list(df.columns)
    for c in cols:
        if c == "link_id":
            return c
    cl = [c for c in cols if "link" in c.lower() and "id" in c.lower()]
    if cl:
        return cl[0]
    raise KeyError("perlink_metrics に link_id（またはそれ相当の列名）が見つかりません。")

def to_numeric_df(df: pd.DataFrame) -> pd.DataFrame:
    # 数値っぽい列は数値化。ID系はそのまま。
    out = df.copy()
    for c in out.columns:
        if c == "link_id":
            continue
        if out[c].dtype == object:
            out[c] = pd.to_numeric(out[c], errors="ignore")
    return out

# ===== links.geojson をロード =====
with open(links_geojson_path, "r", encoding="utf-8") as f:
    links_fc = json.load(f)

# GeoJSON → DataFrame（link_id と geometry を分離）
props_rows = []
geoms = []
for feat in links_fc.get("features", []):
    prop = feat.get("properties", {}).copy()
    geom = feat.get("geometry", {})
    link_id = prop.get("link_id")
    if link_id is None:
        continue
    props_rows.append(prop)
    geoms.append(geom)

links_df = pd.DataFrame(props_rows)
links_df["__geom__"] = geoms

if "link_id" not in links_df.columns:
    raise KeyError("links.geojson に link_id プロパティがありません。")

# ===== シナリオごとに perlink_metrics を結合して GeoJSON を出力 =====
for scen in SCENARIOS:
    metrics_path = metrics_dir / f"perlink_metrics_{scen}.csv"
    if not metrics_path.exists():
        print(f"[WARN] {metrics_path.name} が見つからないためスキップ")
        continue

    mdf = read_csv_flex(metrics_path)
    link_col = pick_link_id_col(mdf)
    mdf = mdf.rename(columns={link_col: "link_id"})
    mdf = to_numeric_df(mdf)

    # 数値列のみ抽出（ID・run数など文字列は基本的に除外）
    numeric_cols = ["link_id"] + [c for c in mdf.columns if c != "link_id" and pd.api.types.is_numeric_dtype(mdf[c])]
    mnum = mdf[numeric_cols].copy()

    # 重複があれば集約（平均）しておく（同じ link_id が複数行あるケース対策）
    if mnum["link_id"].duplicated().any():
        mnum = (mnum
                .groupby("link_id", as_index=False)
                .agg({c: "mean" for c in mnum.columns if c != "link_id"}))

    # 結合
    merged = links_df.merge(mnum, on="link_id", how="left")

    # 再び GeoJSON へ
    features = []
    for _, row in merged.iterrows():
        prop = {k: (None if pd.isna(v) else v) for k, v in row.drop(labels="__geom__").to_dict().items()}
        geom = row["__geom__"]
        features.append({
            "type": "Feature",
            "properties": prop,
            "geometry": geom
        })
    out_fc = {"type": "FeatureCollection", "features": features}

    out_path = out_dir / f"links_{scen}.geojson"
    out_path.write_text(json.dumps(out_fc, ensure_ascii=False), encoding="utf-8")
    print(f"[OK] {out_path} を出力（features={len(features)}）")

print("✅ すべてのシナリオの GeoJSON 出力が完了しました。")
