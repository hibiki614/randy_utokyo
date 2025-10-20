import subprocess
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

base_dir = os.path.abspath(os.path.dirname(__file__))

itlts_path = os.path.abspath(os.path.join(base_dir, "..", "..", "bin", "itlts.exe"))
coverter_path = os.path.abspath(os.path.join(base_dir, "..", "..", "bin", "RecordExtraction.exe"))
sevenzip_path = r"C:\Program Files\7-Zip\7z.exe"

case_no = "no02"

command_pairs = []

# 01〜20 の乱数ファイルに対応
for i in range(1, 5):
    rand_id = f"{i:02d}"
    rand_group = f"rand{rand_id}"
    run_no = f"r{rand_id}"
    case_name = f"Case1_{case_no}_{run_no}"

    csv_input_path = f"{rand_group}\\{case_name}"
    converter_input_dir = f"../../simcase/{case_no}/{rand_group}/"
    csv_output_dir = f"./../../convert/{case_no}/"
    csv_output_file = f"vpos_{case_no}_{run_no}_ext.csv"
    zip_output_file = f"vpos_{case_no}_{run_no}_ext.zip"

    del_input = f"{rand_group}/vpos.csv"
    del_output = os.path.join(csv_output_dir, csv_output_file)

    command_pairs.append((
        [itlts_path, "-v", "-mode", "mav", "-csv", csv_input_path, "-casepfx", case_name, "-caseext", ".mavn"],
        [coverter_path, converter_input_dir, "vpos.csv", csv_output_dir, csv_output_file],
        [sevenzip_path, "a", os.path.join(csv_output_dir, zip_output_file), os.path.join(csv_output_dir, csv_output_file)],
        del_input,
        del_output
    ))


def run_pair(cmd1, cmd2, cmd3, del1, del2):
    try:
        print(f"Starting ITLTS: {cmd1}")
        subprocess.run(cmd1, check=True)

        print(f"Starting Converter: {cmd2}")
        subprocess.run(cmd2, check=True)

        print(f"Starting 7-Zip: {cmd3}")
        subprocess.run(cmd3, check=True)

        del1_path = os.path.abspath(os.path.join(base_dir, del1))
        del2_path = os.path.abspath(os.path.join(base_dir, del2))

        if os.path.exists(del1_path):
            print(f"Deleting: {del1_path}")
            os.remove(del1_path)

        if os.path.exists(del2_path):
            print(f"Deleting: {del2_path}")
            os.remove(del2_path)

        print("Pair completed.\n")

    except Exception as e:
        print(f"Error occurred: {e}")


# 最大2スレッド並列で順次実行
with ThreadPoolExecutor(max_workers=4) as executor:
    futures = [executor.submit(run_pair, *pair) for pair in command_pairs]
    for future in as_completed(futures):
        pass  # 完了を待つだけ（printはrun_pair内でされる）

print("すべてのペアが完了しました。")