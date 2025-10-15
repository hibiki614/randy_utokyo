import re
import pandas as pd
from pathlib import Path
import chardet

# ===== 設定 =====
case_path = Path("C:\\Users\\hibik\\github\\randy_utokyo\\拡張シナリオ\\simcase\\no07\\Case1_no07_r01.mavn")   # 読み込みたいケースファイル
out_csv = Path("OD_table_all_classes.csv")

# ===== ファイルの文字コードを自動検出 =====
with open(case_path, "rb") as f:
    raw = f.read()
enc = chardet.detect(raw)["encoding"]
print(f"Detected encoding: {enc}")
text = raw.decode(enc or "cp932", errors="ignore")

# ===== PacketGenerator + BusGenerate 対応パターン =====
pattern = re.compile(
    r"CLASS=(?:PacketGenerator|BusGenerate_[^,]*),.*?"
    r"ORIGIN=(?P<origin>[^,]+),DESTINATION=(?P<dest>[^,]+),"
    r"VEHICLETYPE=(?P<veh>[^,]+),.*?"
    r"GENSCHEDULE=(?P<genschedule>[\d:]+)",
    re.S
)

records = []
for m in pattern.finditer(text):
    origin = m.group("origin")
    dest = m.group("dest")
    veh = m.group("veh")
    genschedule = m.group("genschedule")
    counts = [int(x) for x in genschedule.split(":") if x.isdigit()]
    total = sum(counts)
    if total > 0:  # 発生があるODのみ記録
        records.append({
            "Origin": origin,
            "Destination": dest,
            "VehicleType": veh,
            "Trips": total
        })

# ===== DataFrame作成・集計 =====
df = pd.DataFrame(records)
if df.empty:
    print("⚠️ データが見つかりません。パターン・ファイルを確認してください。")
else:
    df_grouped = df.groupby(["VehicleType", "Origin", "Destination"], as_index=False)["Trips"].sum()
    df_grouped = df_grouped.sort_values(["VehicleType", "Trips"], ascending=[True, False])
    df_grouped.to_csv(out_csv, index=False, encoding="utf-8-sig")

    print(f"\n✅ OD表を作成しました: {out_csv.resolve()}\n")
    print("=== VehicleType別 集計件数 ===")
    print(df_grouped["VehicleType"].value_counts())
    print("\n=== 上位10件 ===")
    print(df_grouped.head(10))
