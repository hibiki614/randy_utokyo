# -*- coding: utf-8 -*-
from pathlib import Path
import json
import numpy as np
import pandas as pd

# この3ファイルを同じフォルダに置いて実行
BASE_DIR = Path(".")

SUMMARY_PATH = BASE_DIR / "route_311_speed_50p0_summary.json"
OPTIMA_PATH = BASE_DIR / "route_311_speed_50p0_optima.npy"
DELAYS_PATH = BASE_DIR / "route_311_speed_50p0_delays.npy"

OFFSET_STEP = 1.2


def main():
    # 1. JSONを読む
    with SUMMARY_PATH.open("r", encoding="utf-8") as f:
        summary = json.load(f)

    print("=== SUMMARY ===")
    for key, value in summary.items():
        print(f"{key}: {value}")

    # 2. 最適解一覧を読む
    optima = np.load(OPTIMA_PATH)

    print("\n=== OPTIMA ===")
    print("shape:", optima.shape)
    print("first 20 rows:")
    print(optima[:20])

    # 最適解一覧をCSVにする
    optima_df = pd.DataFrame(optima, columns=["x1_s", "x2_s", "x3_s"])
    optima_df.to_csv("route_311_speed_50p0_optima.csv", index=False)

    # 3. 100万通りの遅れ配列を読む
    delays = np.load(DELAYS_PATH)

    print("\n=== DELAYS ===")
    print("shape:", delays.shape)
    print("dtype:", delays.dtype)
    print("min:", float(delays.min()))
    print("max:", float(delays.max()))
    print("mean:", float(delays.mean()))
    print("median:", float(np.median(delays)))

    # 最小値の位置を確認
    d_min = float(delays.min())
    min_indices = np.argwhere(np.isclose(delays, d_min, atol=1e-6))

    print("\nnumber of minimum cells:", len(min_indices))
    print("first 20 minimum indices:")
    print(min_indices[:20])

    # 特定オフセットの遅れを見る例
    x1, x2, x3 = 0.0, 48.0, 42.0
    i = round(x1 / OFFSET_STEP)
    j = round(x2 / OFFSET_STEP)
    k = round(x3 / OFFSET_STEP)

    print(
        f"\ndelay at (x1,x2,x3)=({x1},{x2},{x3}): "
        f"{float(delays[i, j, k])}"
    )

    # x3=42秒の断面だけCSVへ出力
    k_slice = round(42.0 / OFFSET_STEP)
    x_values = np.arange(delays.shape[0]) * OFFSET_STEP

    slice_df = pd.DataFrame({
        "x1_s": np.repeat(x_values, len(x_values)),
        "x2_s": np.tile(x_values, len(x_values)),
        "delay_s_per_veh": delays[:, :, k_slice].ravel(),
    })
    slice_df.to_csv(
        "route_311_speed_50p0_x3_42p0_slice.csv",
        index=False,
    )

    print("\nCSV files written:")
    print("- route_311_speed_50p0_optima.csv")
    print("- route_311_speed_50p0_x3_42p0_slice.csv")


if __name__ == "__main__":
    main()
