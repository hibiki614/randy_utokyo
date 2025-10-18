from pathlib import Path
import re

base_dir = Path("C:\\Users\\OguchiLab\\OneDrive\\デスクトップ\\randy_utokyo\\拡張シナリオ\\simcase2")  # ← 各自のパスに変更
pattern = "Case1_no*_r*.mavn"

AUTO_ID = "I_09_1204235410499"   # 自動運転
NORMAL_ID = "I_09_1204235410434" # 通常車

for path in base_dir.glob(pattern):
    text = path.read_text(encoding="cp932", errors="ignore")
    lines = text.splitlines()

    generators = {}
    auto_generators = {}

    # PacketGeneratorを事前にスキャン（シャトル除外）
    for line in lines:
        if not line.startswith("CLASS=PacketGenerator"):
            continue
        if any(key in line for key in [
            "BusGenerate_Shuttle_Out",
            "BusGenerate_Shuttle_Ret"
        ]):
            continue  # シャトルは完全スキップ

        m_id = re.search(r"ID=([^,]+)", line)
        m_schedule = re.search(r"GENSCHEDULE=([\d:]+)", line)
        if not (m_id and m_schedule):
            continue
        id_ = m_id.group(1)
        schedule = list(map(int, m_schedule.group(1).split(":")))

        if id_.endswith("_auto"):
            auto_generators[id_] = (line, schedule)
        else:
            generators[id_] = (line, schedule)

    new_lines = []
    for line in lines:
        # === シャトル関連は一切変更しない ===
        if any(key in line for key in [
            "BusGenerate_Shuttle_Out",
            "BusGenerate_Shuttle_Ret"
        ]):
            new_lines.append(line)
            continue

        # === auto行は削除（マージ済み） ===
        if "_auto" in line and "PacketGenerator" in line:
            continue

        # === 通常PacketGenerator行 ===
        if "PacketGenerator" in line:
            m_id = re.search(r"ID=([^,]+)", line)
            m_schedule = re.search(r"GENSCHEDULE=([\d:]+)", line)
            if m_id and m_schedule:
                id_ = m_id.group(1)
                schedule = list(map(int, m_schedule.group(1).split(":")))
                auto_id = id_ + "_auto"
                if auto_id in auto_generators:
                    auto_schedule = auto_generators[auto_id][1]
                    merged = [a + b for a, b in zip(schedule, auto_schedule)]
                    merged_text = ":".join(map(str, merged))
                    line = re.sub(r"GENSCHEDULE=[\d:]+", f"GENSCHEDULE={merged_text}", line)
            line = line.replace(f"VEHICLETYPE={AUTO_ID}", f"VEHICLETYPE={NORMAL_ID}")

        new_lines.append(line)

    new_text = "\n".join(new_lines)

    # バックアップ
    backup = path.with_suffix(".bak")
    if not backup.exists():
        backup.write_text(text, encoding="cp932")

    # 上書き
    path.write_text(new_text, encoding="cp932")
    print(f"✅ {path.name} 完了（シャトル完全保持・需要統合あり）")

print("=== 全ファイル処理完了 ===")
