# -*- coding: utf-8 -*-
"""
Created on Tue Dec  2 17:53:47 2025

@author: OguchiLab
"""

# -*- coding: utf-8 -*-
"""
r02 / r07 の no04・no06 だけの時系列折れ線図を描画するスクリプト
 - 15分間隔を等間隔の数値軸で扱う
 - 指標：平均速度 V_net, TTT, 総走行距離（台キロ/15分）
 - ネットワーク全体（subset 分けなし）
@author: OguchiLab
"""

import pandas as pd
import numpy as np
from pathlib import Path
import glob, os, re

# ====== 設定 ======
base_dir = Path(r"C:\Users\OguchiLab\OneDrive\デスクトップ\randy_utokyo\拡張シナリオ\simcase22")
out_dir = base_dir / "analysis"
out_dir.mkdir(exist_ok=True)

EXCLUDE_KEYS = ["Zone"]
SKIP_PATTERNS = ["r05", "r10"]  # 念のため
TIME_START = "0700"
TIME_END   = "1830"

TARGET_SCENARIOS = ["no04", "no06"]     # 描画するシナリオ
TARGET_RUNS      = ["r02", "r07"]       # 描画するラン

# ====== ユーティリティ ======
def should_skip(filename: str) -> bool:
    fname = os.path.basename(filename)
    return any(pat in fname for pat in SKIP_PATTERNS)

def _to_slot_code(val):
    """'7:00' などの文字列を '0700' の4桁コードに変換"""
    try:
        s = str(val)
        m = re.search(r'(\d{1,2}):(\d{2})', s)
        if not m:
            return None
        hh = int(m.group(1)); mm = int(m.group(2))
        return f"{hh:02d}{mm:02d}"
    except Exception:
        return None

def load_volspd(path):
    """volspd CSVを読み込んで、リンク別の距離・時間・台数などを整形"""
    df = pd.read_csv(path)

    link_col   = [c for c in df.columns if "link" in c.lower() or "id" in c.lower()][0]
    length_col = [c for c in df.columns if "len" in c.lower()][0]
    trvt_col   = [c for c in df.columns if "trvt" in c.lower()][0]
    count_col  = [c for c in df.columns if "count" in c.lower()][0]
    time_col_cands = [c for c in df.columns if "time" in c.lower() or "slot" in c.lower()]
    time_col   = time_col_cands[0] if time_col_cands else None

    out = pd.DataFrame()
    out["link_id"]  = df[link_col].astype(str)
    out["length_m"] = pd.to_numeric(df[length_col], errors="coerce")
    out["trvt_s"]   = pd.to_numeric(df[trvt_col], errors="coerce").replace(-1, np.nan)
    out["count"]    = pd.to_numeric(df[count_col], errors="coerce").replace(-1, 0)

    # ゾーン等のダミー行を除外
    out = out[~out["link_id"].str.contains("|".join(EXCLUDE_KEYS))].copy()

    if time_col:
        out["timestr"]   = df[time_col].astype(str)
        out["slot_code"] = out["timestr"].map(_to_slot_code)
    else:
        out["timestr"]   = np.arange(len(df)).astype(str)
        out["slot_code"] = None

    out["row_dist_m"] = out["length_m"] * out["count"]
    out["row_time_s"] = out["trvt_s"] * out["count"]
    return out

def network_timeseries(df: pd.DataFrame) -> pd.DataFrame:
    """ネットワーク時系列（15分ごと）を集計"""
    g = df.groupby(["timestr", "slot_code"], dropna=False).agg(
        dist_m=("row_dist_m", "sum"),
        time_s=("row_time_s", "sum"),
    ).reset_index()
    g["V_net_kmh"]   = (g["dist_m"] / g["time_s"]) * 3.6
    g["TTT_sec"]     = g["time_s"]
    g["flow_kmveh"]  = g["dist_m"] / 1000.0
    return g

def _to_hhmm(sc):
    if isinstance(sc, str) and len(sc) == 4 and sc.isdigit():
        return f"{sc[:2]}:{sc[2:]}"
    return sc

# ====== ファイル探索（no04 / no06 のみ） ======
files_by_scen = {scen: [] for scen in TARGET_SCENARIOS}

for scen_dir in sorted(base_dir.glob("no[0-9][0-9]")):
    scen = scen_dir.name  # 例: 'no04'
    if scen not in TARGET_SCENARIOS:
        continue
    files = sorted(glob.glob(str(scen_dir / "rand*" / "*_volspd.csv")))
    files = [f for f in files if not should_skip(f)]
    files_by_scen[scen] = files

print("📂 読み込むファイル数:", {k: len(v) for k, v in files_by_scen.items()})

# ====== プロット設定 ======
import matplotlib
from matplotlib import font_manager as fm
import matplotlib.pyplot as plt

font_path = r"C:\Windows\Fonts\meiryo.ttc"
prop = fm.FontProperties(fname=font_path)
plt.rcParams["font.family"] = prop.get_name()
plt.rcParams["axes.unicode_minus"] = False

# シナリオラベル（凡例用）
scenario_labels = {
    "no04": "1.0AV-〇",
    "no06": "0.7AV-〇",
}

# モノクロ＋形だけで区別
style_map = {
    "no04": {"marker": "s", "color": "0.2"},  # 少し濃いグレー
    "no06": {"marker": "^", "color": "0.6"},  # 少し薄いグレー
}

# ====== ランごとの時系列を作成 & 描画 ======
def build_timeseries_for_run(run_key: str) -> pd.DataFrame:
    """
    指定run（例: 'r02'）について、
    no04 / no06 のネットワーク時系列をまとめたDataFrameを返す
    """
    ts_list = []
    for scen in TARGET_SCENARIOS:
        for f in files_by_scen.get(scen, []):
            fname = os.path.basename(f)
            if run_key not in fname:
                continue

            df = load_volspd(f)
            if df.empty:
                continue

            ts = network_timeseries(df)
            ts = ts[ts["slot_code"].notna()].copy()
            ts = ts[(ts["slot_code"] >= TIME_START) & (ts["slot_code"] <= TIME_END)]
            if ts.empty:
                continue

            ts["scenario"] = scen
            ts["run"]      = fname
            ts_list.append(ts)

    if not ts_list:
        return pd.DataFrame()

    ts_all = pd.concat(ts_list, ignore_index=True)

    # 15分スロットを等間隔の数値軸に変換
    slot_list = sorted(ts_all["slot_code"].unique())
    slot_to_idx = {sc: i for i, sc in enumerate(slot_list)}
    ts_all["t_idx"] = ts_all["slot_code"].map(slot_to_idx)
    ts_all["hhmm"]  = ts_all["slot_code"].map(_to_hhmm)
    return ts_all, slot_list

def plot_run_timeseries(run_key: str, ts_all: pd.DataFrame, slot_list):
    """
    1つの run（r02 or r07）について、
    3指標（V_net, TTT, flow）の折れ線図を縦3段で描画
    """
    if ts_all.empty:
        print(f"⚠ run {run_key} の有効なデータがありません。スキップします。")
        return

    fig, axes = plt.subplots(3, 1, figsize=(16, 12), sharex=True)

    metrics = [
        ("V_net_kmh",  "平均速度 [km/h]"),
        ("TTT_sec",    "TTT [sec]"),
        ("flow_kmveh", "総走行距離 [台・km/15分]"),
    ]

    for ax, (ycol, ylabel) in zip(axes, metrics):
        for scen in TARGET_SCENARIOS:
            sub = ts_all[ts_all["scenario"] == scen].sort_values("t_idx")
            if sub.empty:
                continue
            style = style_map.get(scen, {"marker": "o", "color": "0.3"})
            label = scenario_labels.get(scen, scen)
            ax.plot(
                sub["t_idx"],
                sub[ycol],
                label=label,
                linestyle="solid",
                marker=style["marker"],
                linewidth=1.5,
                markersize=7,
                color=style["color"],
            )

        ax.set_ylabel(ylabel, fontproperties=prop, fontsize=14)
        ax.grid(True, axis="y", alpha=0.3)
        ax.tick_params(axis="y", labelsize=12)

    # x軸：1時間ごと（= 4スロットごと）にラベル表示
    tick_step = 4  # 15分×4 = 1時間
    ticks = list(range(0, len(slot_list), tick_step))
    tick_labels = [_to_hhmm(slot_list[i]) for i in ticks]
    axes[-1].set_xticks(ticks)
    axes[-1].set_xticklabels(tick_labels, rotation=45, fontsize=12)
    axes[-1].set_xlabel("時刻（HH:MM）", fontproperties=prop, fontsize=14)

    # タイトルと凡例
    fig.suptitle(f"r{run_key} における no04・no06 の時系列比較", fontproperties=prop, fontsize=16)

    # 凡例は一番上の軸にまとめて表示
    handles, labels = axes[0].get_legend_handles_labels()
    axes[0].legend(handles, labels, fontsize=12, loc="upper right")

    plt.tight_layout(rect=[0, 0, 1, 0.95])
    out_path = out_dir / f"timeseries_r{run_key}_no04_no06.png"
    fig.savefig(out_path, dpi=300)
    plt.close()
    print(f"✅ 図を保存しました: {out_path}")

# ====== 実行：r02 と r07 ======
for run in TARGET_RUNS:
    ts_all, slot_list = build_timeseries_for_run(run)
    plot_run_timeseries(run, ts_all, slot_list)

print("🎉 r02 / r07 の折れ線図出力完了")
