import re
import json
from pathlib import Path
import chardet

# ====== 設定 ======
case_path = Path("C:\\Users\\hibik\\github\\randy_utokyo\\拡張シナリオ\\simcase\\no07\\Case1_no07_r01.mavn")
out_geojson = Path("zones_polygons_noshapely.geojson")

# ====== 文字コード検出 ======
with open(case_path, "rb") as f:
    raw = f.read()
enc = chardet.detect(raw)["encoding"]
text = raw.decode(enc or "cp932", errors="ignore")

# ====== AvnZone抽出 ======
zone_pattern = re.compile(
    r"CLASS=AvnZone,ID=(?P<id>[^,]+),ZONETYPE=(?P<type>[^,]+),ZONESHAPE=(?P<shape>[^,]+)",
    re.S
)

features = []
for m in zone_pattern.finditer(text):
    zid = m.group("id")
    shape = m.group("shape")
    coords = shape.split(":")
    lonlat_pairs = [[float(coords[i]), float(coords[i + 1])] for i in range(0, len(coords) - 1, 2)]

    # ポリゴン閉じる（最初と最後が同じでない場合）
    if lonlat_pairs[0] != lonlat_pairs[-1]:
        lonlat_pairs.append(lonlat_pairs[0])

    # GeoJSON Featureを組み立て
    feature = {
        "type": "Feature",
        "geometry": {
            "type": "Polygon",
            "coordinates": [lonlat_pairs]
        },
        "properties": {
            "ZoneID": zid,
            "NumVertices": len(lonlat_pairs)
        }
    }
    features.append(feature)

# ====== GeoJSON全体を作成 ======
geojson = {
    "type": "FeatureCollection",
    "features": features
}

# ====== 出力 ======
with open(out_geojson, "w", encoding="utf-8") as f:
    json.dump(geojson, f, ensure_ascii=False, indent=2)

print(f"✅ {len(features)} ゾーンをGeoJSONとして出力しました")
print(f"出力ファイル: {out_geojson.resolve()}")
