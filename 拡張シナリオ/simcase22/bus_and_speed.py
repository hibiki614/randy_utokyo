# -*- coding: utf-8 -*-
import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt

base_dir = Path(r"C:/Users/OguchiLab/OneDrive/デスクトップ/randy_utokyo/拡張シナリオ/simcase22")
out_dir  = base_dir / "analysis"

# ① no01 のバス台数（volspdベースの乱数平均）
bus_summary_path = out_dir / "vehicle_flow_timeseries_no01_summary.csv"  # 先ほど作ったやつ
bus_summary = pd.read_csv(bus_summary_path)
# 必要列チェック
need_bus_cols = {"slot_code","bus_mean"}
missing = need_bus_cols - set(bus_summary.columns)
if missing:
    raise KeyError(f"{bus_summary_path.name} に必要列がありません: {missing}")

# 時刻ラベル（HH:MM）
def hhmm_label(code):
    s = str(int(code)) if str(code).isdigit() else str(code)
    return f"{s.zfill(4)[:2]}:{s.zfill(4)[2:]}"

bus_base = (bus_summary[["slot_code","bus_mean"]]
            .drop_duplicates()
            .assign(HHMM=lambda d: d["slot_code"].apply(hhmm_label)))

# ② 速度/TTTの時系列
ts_all = pd.read_csv(out_dir / "timeseries_summary.csv")
# 列→ slot_code を必ず持つように正規化
if "slot_code" not in ts_all.columns:
    # 既存の timestr に "YYYY/MM/DD HH:MM" が居るのでそこから作る
    if "timestr" in ts_all.columns:
        ts_all = ts_all.assign(
            slot_code=ts_all["timestr"].astype(str).str.split().str[-1].str.replace(":", "", regex=False).str[:4]
        )
    else:
        raise KeyError("timeseries_summary.csv に slot_code/timestr がありません。")

# ③ ターゲットと指標
TARGET_SCENARIOS = ["no01","no03","no05"]   # 必要に応じて変更
VALUE_COL = "V_net_mean"                    # "TTT_mean" に差し替えればTTTで描ける

# ④ シナリオごとに重ね描き
for scen in TARGET_SCENARIOS:
    ts_s = (ts_all.loc[ts_all["scenario"]==scen, ["slot_code", VALUE_COL]]
                 .merge(bus_base[["slot_code","HHMM","bus_mean"]], on="slot_code", how="inner")
                 .sort_values("slot_code"))

    if ts_s.empty:
        print(f"(info) {scen}: マージ結果が空。スキップ")
        continue

    fig, ax1 = plt.subplots(figsize=(11,5))
    ax1.plot(ts_s["HHMM"], ts_s["bus_mean"], label="Bus count (no01 mean)", linewidth=2)
    ax1.set_xlabel("時刻")
    ax1.set_ylabel("バス台数 [台/15分]")
    ax1.tick_params(axis='x', rotation=0)

    ax2 = ax1.twinx()
    ax2.plot(ts_s["HHMM"], ts_s[VALUE_COL], linestyle="--", label=f"{VALUE_COL} ({scen})", linewidth=2)
    ax2.set_ylabel("ネットワーク速度 [km/h]" if VALUE_COL=="V_net_mean" else "TTT [sec]")

    lines, labels = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines+lines2, labels+labels2, loc="upper right")

    plt.title(f"Bus count (no01) vs {('Speed' if VALUE_COL=='V_net_mean' else 'TTT')}  [{scen}]")
    plt.tight_layout()
    figpath = out_dir / f"overlay_bus_no01_vs_{('speed' if VALUE_COL=='V_net_mean' else 'TTT')}_{scen}.png"
    plt.savefig(figpath, dpi=300)
    plt.close()
    print("📈 図を保存:", figpath)

# ⑤ 後工程用に、結合したデータもCSVで出しておく（全シナリオまとめ）
merged_rows = []
for scen in ts_all["scenario"].unique():
    subset = (ts_all.loc[ts_all["scenario"]==scen, ["slot_code","scenario","V_net_mean","TTT_mean"]]
                    .merge(bus_base[["slot_code","bus_mean","HHMM"]], on="slot_code", how="inner"))
    merged_rows.append(subset)
merged_df = pd.concat(merged_rows, ignore_index=True)
merged_df.to_csv(out_dir / "bus_no01_with_speed_ttt_by_scenario.csv", index=False, encoding="utf-8-sig")
print("💾 結合CSV:", out_dir / "bus_no01_with_speed_ttt_by_scenario.csv")
