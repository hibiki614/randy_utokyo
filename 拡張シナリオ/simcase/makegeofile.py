# -*- coding: utf-8 -*-
import re, json
from pathlib import Path

# ===== 入力/出力パス =====
# 例) mavn_path = Path(r"C:/.../simcase/Case1_no01_r01.mavn")
mavn_path = Path(r"C:/Users/OguchiLab/OneDrive/デスクトップ/randy_utokyo/拡張シナリオ/simcase/no01/Case1_no01_r01.mavn")
out_dir   = mavn_path.parent
nodes_geojson = out_dir / "nodes.geojson"
links_geojson = out_dir / "links.geojson"

# ===== 収納器 =====
nodes = {}    # {node_id: (lon, lat)}
roads = {}    # {road_id: {"coords":[(lon,lat),...], "node1":str, "node2":str}}
links = []    # [{"id":..., "road_id":..., "upnode":..., "downnode":...}, ...]

def open_text_safely(p: Path):
    # cp932 でまず開く → ダメなら utf-8
    for enc in ("cp932", "utf-8"):
        try:
            return p.open("r", encoding=enc, errors="ignore")
        except Exception:
            continue
    # 最後の手段
    return p.open("r", errors="ignore")

# ===== 1) パース =====
with open_text_safely(mavn_path) as f:
    for raw in f:
        line = raw.strip()
        if not line or "CLASS=" not in line:
            continue

        # --- MavNode ---
        # 例: CLASS=MavNode,ID=533967_00280,COORDVAL=139.9450290000:35.8876410000
        if "CLASS=MavNode" in line:
            m_id  = re.search(r"ID=([^,]+)", line)
            m_xy  = re.search(r"COORDVAL=([0-9\.\-]+):([0-9\.\-]+)", line)
            if m_id and m_xy:
                nid = m_id.group(1)
                lon = float(m_xy.group(1)); lat = float(m_xy.group(2))
                nodes[nid] = (lon, lat)
            continue

        # --- Road ---
        # 例: CLASS=Road,ID=533967_01405_01406,NODE1=533967_01405,NODE2=533967_01406,INTERPOLATE=lon1:lat1:lon2:lat2:...
        if "CLASS=Road" in line:
            m_id    = re.search(r"ID=([^,]+)", line)
            m_n1    = re.search(r"NODE1=([^,]+)", line)
            m_n2    = re.search(r"NODE2=([^,]+)", line)

            coords = None
            m_interp = re.search(r"INTERPOLATE=([0-9\.\:\-]+)", line)
            m_coordv = re.search(r"COORDVAL=([0-9\.\:\-]+)", line)  # まれに COORDVAL の場合も

            raw_coords = None
            if m_interp:
                raw_coords = m_interp.group(1)
            elif m_coordv:
                raw_coords = m_coordv.group(1)

            if m_id and m_n1 and m_n2 and raw_coords:
                rid = m_id.group(1)
                n1  = m_n1.group(1)
                n2  = m_n2.group(1)
                parts = raw_coords.split(":")
                # 偶数個ずつ lon,lat,lon,lat...
                xy = []
                for i in range(0, len(parts)-1, 2):
                    try:
                        lon = float(parts[i]); lat = float(parts[i+1])
                        xy.append((lon, lat))
                    except ValueError:
                        pass
                if len(xy) >= 2:
                    roads[rid] = {"coords": xy, "node1": n1, "node2": n2}
            continue

        # --- AvnLink ---
        # 例: CLASS=AvnLink,ID=533967_01405_01406_1,UPNODE=533967_01406,DOWNNODE=533967_01405,ROADID=533967_01405_01406
        if "CLASS=AvnLink" in line:
            m_id  = re.search(r"ID=([^,]+)", line)
            m_up  = re.search(r"UPNODE=([^,]+)", line)
            m_dn  = re.search(r"DOWNNODE=([^,]+)", line)
            m_rid = re.search(r"ROADID=([^,]+)", line)
            if m_id and m_up and m_dn and m_rid:
                links.append({
                    "id": m_id.group(1),
                    "upnode": m_up.group(1),
                    "downnode": m_dn.group(1),
                    "road_id": m_rid.group(1),
                })
            continue

print(f"Parsed: nodes={len(nodes)}, roads={len(roads)}, links={len(links)}")

# ===== 2) GeoJSON: ノード =====
node_features = []
for nid, (lon, lat) in nodes.items():
    node_features.append({
        "type": "Feature",
        "properties": {"node_id": nid},
        "geometry": {"type": "Point", "coordinates": [lon, lat]}
    })

nodes_fc = {"type": "FeatureCollection", "features": node_features}
nodes_geojson.write_text(json.dumps(nodes_fc, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"Saved: {nodes_geojson} (features={len(node_features)})")

# ===== 3) GeoJSON: リンク（方向を Road に合わせて反転対応） =====
link_features = []
miss_road = 0

for lk in links:
    lid   = lk["id"]
    up    = lk["upnode"]
    dn    = lk["downnode"]
    rid   = lk["road_id"]

    item = roads.get(rid)
    if not item:
        miss_road += 1
        continue

    coords = item["coords"][:]  # copy
    node1  = item["node1"]; node2 = item["node2"]

    # 方向決定：UPNODE が Road.NODE1 なら順方向、DOWNNODE が NODE1 なら逆
    # （両方一致しないパターンがあれば順方向で出す）
    if up == node1 and dn == node2:
        line = coords
    elif up == node2 and dn == node1:
        line = list(reversed(coords))
    else:
        line = coords  # フォールバック

    link_features.append({
        "type": "Feature",
        "properties": {
            "link_id": lid,
            "road_id": rid,
            "upnode": up,
            "downnode": dn,
            "road_node1": node1,
            "road_node2": node2
        },
        "geometry": {"type": "LineString", "coordinates": line}
    })

links_fc = {"type": "FeatureCollection", "features": link_features}
links_geojson.write_text(json.dumps(links_fc, ensure_ascii=False, indent=2), encoding="utf-8")

print(f"Saved: {links_geojson} (features={len(link_features)}, road_miss={miss_road})")
