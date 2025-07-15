import subprocess
import os
import threading

# 処理の順序：
# ITLTS実行 → コンバータ実行 → 7zipで圧縮 → 一時ファイル削除

# このスクリプトファイルのあるディレクトリの絶対パスを取得
base_dir = os.path.abspath(os.path.dirname(__file__))

# 使用する実行ファイルのパスを絶対パスで定義
itlts_path = os.path.abspath(os.path.join(base_dir, "..", "..", "bin", "itlts.exe"))
coverter_path = os.path.abspath(os.path.join(base_dir, "..", "..", "bin", "RecordExtraction.exe"))
sevenzip_path = r"C:\Program Files\7-Zip\7z.exe"  # 7-Zipのパス（環境により変更必要）

case_no = "no01"  # ← ここを変更するだけで別ケースに対応可能

command_pairs = []

for i in range(1, 6):  # 乱数 1～5 に対応
    rand_id = f"{i:02d}"            # 01, 02, ..., 05
    rand_group = f"rand{rand_id}"   # rand01 ～ rand05
    run_no = f"r{rand_id}"          # r01 ～ r05
    case_name = f"Case1_{case_no}_{run_no}"  # 例: Case1_no01_r01

    # 各パスの定義
    csv_input_path = f"{rand_group}\\{case_name}"
    converter_input_dir = f"../../simcase/{case_no}/{rand_group}/"
    csv_output_dir = f"./../../convert/{case_no}/"
    csv_output_file = f"vpos_{case_no}_{run_no}_ext.csv"
    zip_output_file = f"vpos_{case_no}_{run_no}_ext.zip"

    # 削除対象ファイルのパス
    del_input = f"{rand_group}/vpos.csv"
    del_output = os.path.join(csv_output_dir, csv_output_file)

    # コマンド登録
    command_pairs.append((
        [itlts_path, "-v", "-mode", "mav", "-csv", csv_input_path, "-casepfx", case_name, "-caseext", ".mavn"],
        [coverter_path, converter_input_dir, "vpos.csv", csv_output_dir, csv_output_file],
        [sevenzip_path, "a", os.path.join(csv_output_dir, zip_output_file), os.path.join(csv_output_dir, csv_output_file)],
        del_input,
        del_output
    ))

# 各ペアに対して、定義された順序で処理を実行する関数
def run_pair(cmd1, cmd2, cmd3, del1, del2):
    try:
        print(f"Starting ITLTS: {cmd1}")
        subprocess.run(cmd1, check=True)  # ITLTS 実行

        print(f"Starting Converter: {cmd2}")
        subprocess.run(cmd2, check=True)  # ログ変換実行

        print(f"Starting 7-Zip: {cmd3}")
        subprocess.run(cmd3, check=True)  # ZIP 圧縮実行

        # 削除対象ファイルの絶対パスに変換
        del1_path = os.path.abspath(os.path.join(base_dir, del1))
        del2_path = os.path.abspath(os.path.join(base_dir, del2))

        # 元ログファイルを削除
        if os.path.exists(del1_path):
            print(f"Deleting: {del1_path}")
            os.remove(del1_path)

        # 変換後CSVファイルを削除（ZIP済みのため不要）
        if os.path.exists(del2_path):
            print(f"Deleting: {del2_path}")
            os.remove(del2_path)

        print("Pair completed.\n")

    except Exception as e:
        print(f"Error occurred: {e}")

# スレッドを使って各ペアの処理を並列に実行
threads = []
for cmd1, cmd2, cmd3, del1, del2 in command_pairs:
    t = threading.Thread(target=run_pair, args=(cmd1, cmd2, cmd3, del1, del2))
    t.start()
    threads.append(t)

# すべてのスレッドの完了を待機
for t in threads:
    t.join()

print("すべてのペアが完了しました。")