# -*- coding: utf-8 -*-
"""
Created on Sat Oct 18 03:34:34 2025

@author: OguchiLab
"""

import pandas as pd
import matplotlib.pyplot as plt
import math
from datetime import datetime, timedelta
import numpy as np

# ===== ファイル設定 =====
record_path = "C:\\Users\\OguchiLab\\OneDrive\\デスクトップ\\randy_utokyo\\拡張シナリオ\\simcase22\\no02\\vpos_no02_r06_ext.csv"
volspd_path = "C:\\Users\\OguchiLab\\OneDrive\\デスクトップ\\randy_utokyo\\拡張シナリオ\\simcase22\\no02\\rand06\\Case1_no02_r06_volspd.csv"
auto_type = "I_09_1204235410434"


# ===== Shuttleルートリンク =====
links_out = [
	"533967_00940_13718_0",
	"I_11_533967_13718533967_00977",
	"I_11_533967_00977533967_01555",
	"533967_01555_14156_0",
	"533967_00766_14156_1",
	"533967_00766_11513_0",
	"533967_00538_11513_1"
]
links_ret = [
	"533967_00538_11513_0",
	"533967_00766_11513_1",
	"533967_00766_14156_0",
	"533967_01555_14156_1",
	"I_11_533967_01555533967_00977",
	"I_11_533967_00977533967_01421",
	"533967_00939_01421_1"
]

linklen={"533967_00940_13718_0": 271.4, "I_11_533967_13718533967_00977": 165.1, "I_11_533967_00977533967_01555": 215.2, "533967_01555_14156_0": 146.2, "533967_00766_14156_1": 453.2, "533967_00766_11513_0": 381.7, "533967_00538_11513_1": 257.1, "533967_00538_11513_0": 256.6, "533967_00766_11513_1": 381.4, "533967_00766_14156_0": 450.6, "533967_01555_14156_1": 146.3, "I_11_533967_01555533967_00977": 242.1, "I_11_533967_00977533967_01421": 228.5, "533967_00939_01421_1": 187.9}
linkpos={"533967_00940_13718_0": 0, "I_11_533967_13718533967_00977": 271.4, "I_11_533967_00977533967_01555": 436.5, "533967_01555_14156_0": 651.7, "533967_00766_14156_1": 797.9, "533967_00766_11513_0": 1251.1, "533967_00538_11513_1": 1632.8, "533967_00538_11513_0": 0, "533967_00766_11513_1": 256.6, "533967_00766_14156_0": 638, "533967_01555_14156_1": 1088.6, "I_11_533967_01555533967_00977": 1234.9, "I_11_533967_00977533967_01421": 1477, "533967_00939_01421_1": 1705.5}

# ===== 読み込み =====
record = pd.read_csv(record_path)
volspd = pd.read_csv(volspd_path)

record = record.dropna(subset=["LinkID", "Time"])
record["LinkID"] = record["LinkID"].astype(str).str.strip()

# ===== 時刻を秒に変換 =====
def time_to_sec(t):
    h, m, s = t.split(":")
    return int(h)*3600 + int(m)*60 + float(s)

record["SimTime"] = record["Time"].apply(time_to_sec)

# ===== 描画関数 =====
def make_timespace(df, links, direction_name, outfile_prefix):
    df = df[df["LinkID"].isin(links)].copy()
    if df.empty:
        print(f"[警告] {direction_name} に該当データなし")
        return

    df["Ypos"] = df["LinkID"].apply(lambda x: linklen[x]) - df["LngPos"] + df["LinkID"].apply(lambda x: linkpos[x])

    # ---- 時間範囲 ----
    tmin, tmax = df["SimTime"].min(), df["SimTime"].max()
    hour_start = int(tmin // 3600)
    hour_end = int(math.ceil(tmax / 3600))

    for hour in range(hour_start, hour_end):
        t0, t1 = hour * 3600, (hour + 1) * 3600
        df_hour = df[(df["SimTime"] >= t0) & (df["SimTime"] < t1)]

        if df_hour.empty:
            continue

        # === 図 ===
        fig, ax = plt.subplots(figsize=(14, 9), dpi=200)
        for vid, g in df_hour.groupby("VID"):
            g = g.sort_values("SimTime")
            # 自動運転車を青、それ以外をグレーに
            color = "blue" if g["Type"].iloc[0] == auto_type else "gray"
            ax.plot(
                g["SimTime"] / 60,  # 分単位
                g["Ypos"],
                color=color,
                lw=0.8 if color == "gray" else 1.6,
                alpha=0.35 if color == "gray" else 0.9,
            )


        # === リンク境界線と番号 ===
        for i, lid in enumerate(links):
            y = linkpos[lid]
            ax.axhline(y=y, color="black", lw=0.5, ls="--", alpha=0.4)
            ax.text(t0/60 + 0.2, linkpos[lid] + linklen[lid] / 2,
                    f"{i+1:02d}", va="center", ha="left",
                    fontsize=9, color="black", bbox=dict(facecolor='white', alpha=0.6, lw=0))

        # === 軸設定 ===
        ax.set_xlim(t0/60, t1/60)
        ax.set_xlabel("Time", fontsize=13)
        ax.set_ylabel("Position along route [m]", fontsize=13)
        ax.grid(ls=":", alpha=0.3)

        # 1分刻みの主目盛，10分ごとにラベル
        xticks = list(range(int(t0/60), int(t1/60) + 1))
        ax.set_xticks(xticks)
        ax.set_xticklabels([(datetime(2025,1,1,hour,0)+timedelta(minutes=x-hour*60)).isoformat()[11:16] if int(x) % 10 == 0 else "" for x in xticks])

        # === タイトル ===
        hour_label = f"{hour:02d}:00–{(hour+1)%24:02d}:00"
        ax.set_title(f"Time–Space Diagram ({direction_name})  [{hour_label}]",
                     fontsize=15, pad=10)
        caption = "Red: Autonomous bus, Grey: Vehicle with driver | Dotted black: Link boundary"
        ax.text(0.02, -0.13, caption, transform=ax.transAxes, fontsize=10,
                va="top", ha="left")

        plt.tight_layout()
        fname = f"{outfile_prefix}_{hour_label.replace(':','')}.png"
        plt.savefig(fname, dpi=350, bbox_inches="tight")
        plt.close(fig)
        print(f"✅ Exported: {fname}")

# ===== 実行 =====
make_timespace(record, links_out, "Shuttle_Out (Zone15→Zone23)", "time_space_out_readable")
make_timespace(record, links_ret, "Shuttle_Ret (Zone23→Zone15)", "time_space_ret_readable")
