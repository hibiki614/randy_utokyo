# -*- coding: utf-8 -*-
"""
Created on Tue Aug  5 13:34:15 2025

@author: OguchiLab
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# 対象ケース（フォルダ名）
case_list = ['no01', 'no02', 'no11', 'no12', 'no13', 'no14']
rand_list = [f"rand{str(i).zfill(2)}" for i in range(1, 21)]

# ベースディレクトリ（スクリプトと同階層）
base_dir = os.path.abspath(".")

# 結果保存用
summary = {}

for case in case_list:
    case_dir = os.path.join(base_dir, case)
    speed_means = []

    for rand in rand_list:
        rand_dir = os.path.join(case_dir, rand)
        file_name = f"Case1_{case}_r{rand[4:]}_spd.csv"
        file_path = os.path.join(rand_dir, file_name)

        if not os.path.exists(file_path):
            print(f"⚠️ ファイルが見つかりません: {file_path}")
            continue

        try:
            df = pd.read_csv(file_path)
            # -1を除いて平均
            valid_speeds = df[df["Ave.SPD"] != -1]["Ave.SPD"]
            if not valid_speeds.empty:
                speed_means.append(valid_speeds.mean())
        except Exception as e:
            print(f"❌ エラー（{file_path}）: {e}")

    # 結果まとめ
    if speed_means:
        summary[case] = speed_means
        print(f"✅ {case}: 平均={pd.Series(speed_means).mean():.2f}, 分散={pd.Series(speed_means).var():.2f}")
    else:
        print(f"⚠️ {case}: 有効なデータがありません")

# 箱ひげ図の描画
plt.figure(figsize=(10, 6))
df_box = pd.DataFrame(dict([(k, pd.Series(v)) for k, v in summary.items()]))
sns.boxplot(data=df_box, orient="v")
plt.title("Case-wise Distribution of Average Speeds (Ave.SPD)")
plt.ylabel("Average Speed [km/h]")
plt.xlabel("Case")
plt.grid(True)
plt.tight_layout()
plt.savefig("average_speed_boxplot.png")
plt.show()
