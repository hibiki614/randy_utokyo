# -*- coding: utf-8 -*-
"""
Created on Tue Sep 30 15:02:34 2025

@author: OguchiLab
"""

# -*- coding: utf-8 -*-
"""
.mavn ファイルからノードとリンクの位置情報を抽出し、GeoJSONに出力
"""

import re, json
from pathlib import Path

mavn_path = Path(r"C:/Users/OguchiLab/OneDrive/デスクトップ/randy_utokyo/拡張シナリオ/simcase/no01/Case1_no01_r01.mavn")
out_dir   = mavn_path.parent / "network_geo"
out_dir.mkdir(exist_ok=True)

nodes = {}   # {node_id: (lon, lat)}
roads = {}   # {road_id: [ (lon,lat), (lon,lat), ... ]}
links = []   # list of dicts

with open(mavn_path, "r", encoding="cp932", errors="ignore") as f:
    for line in f:
        line = line.strip()
        if line.startswith("CLASS=MavNode"):
            # 例: CLASS=MavNode,ID=533967_00280,COORDVAL=139.9450290000:35.8876410000
            m = re.search(r"ID=([^,]+).*COORDVAL=([\d\.\-]+):([\d\.\-]+)", line)
            if m:
                nid, lon, lat = m.group(1), float(m.group(2)), float(m.group(3))
                nodes[nid] = (lon, lat)

        elif line.startswith("CLASS=Road"):
            # 例: CLASS=Road,ID=533967_01405_01406,NODE1=...,NODE2=...,INTERPOLATE=lon:lat:lon:lat:...
            m = re.search(r"ID=([^,]+).*INTERPOLATE=([0-9\.\:\-]+)", line)
            if m:
                rid = m.group(1)
                coords_raw = m.group(2).split(":")
                coords = [(float(coords_raw[i]), float(coords_raw[i+1])) for i in range(0, len(coords_raw), 2)]
                roads[rid] = coords

        elif line.startswith("CLASS=AvnLink"):
            # 例: CLASS=AvnLink,ID=533967_01405_01406_1,UPNODE=...,DOWNNODE=...,ROADID=...
            m = re.search(r"ID=([^,]+),UPNODE=([^,]+),DOWNNODE=([^,]+),ROADID=([^,]+)", line)
            if m:
                link_id, up, down, road_id = m.groups()
                coords = roads.get(road_id, [])
                # 向き調整
                if coords:
                    if road_id in roads:
                        # Road の始点ノード
                        road_start, road_end = coords[0], coords[-1]
                        node1, node2 = line.split("NODE1=")[1].split(",")[0], line.split("NODE2=")[1].split(",")[0]

                        if node1 == up:
                            coords_use = coords  # 順方向
                        elif node1 == down:
                            coords_use = list(reversed(coords))  # 逆方向
                        else:
                            coords_use = coords
                    else:
                        coords_use = coords
                else:
                    coords_use = []

                links.append({
                    "id": link_id,
                    "upnode": up,
                    "downnode": down,
                    "road_id": road_id,
                    "geometry": coords_use
                })

# --- GeoJSON 出力 ---
def save_geojson(features, outpath, geom_type):
    geo = {
        "type": "FeatureCollection",
        "features": []
    }
    for feat in features:
        if geom_type == "Point":
            lon, lat = feat["geometry"]
            geom = {"type": "Point", "coordinates": [lon, lat]}
        else:  # LineString
            geom = {"type": "LineString", "coordinates": feat["geometry"]}
        geo["features"].append({
            "type": "Feature",
            "geometry": geom,
            "properties": {k: v for k, v in feat.items() if k != "geometry"}
        })
    with open(outpath, "w", encoding="utf-8") as f:
        json.dump(geo, f, ensure_ascii=False, indent=2)

# ノード出力
node_features = [{"id": nid, "geometry": coord} for nid, coord in nodes.items()]
save_geojson(node_features, out_dir / "nodes.geojson", "Point")

# リンク出力
save_geojson(links, out_dir / "links.geojson", "LineString")

print("✅ Exported:")
print(" -", out_dir / "nodes.geojson")
print(" -", out_dir / "links.geojson")
