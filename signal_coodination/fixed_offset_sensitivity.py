
# -*- coding: utf-8 -*-
"""
固定オフセット感度分析
- 入力: results_final.xlsx
- 各行の最適オフセット x0opt~x3opt を固定
- 評価速度 V を TARGET_SPEEDS で変化
- TTT, FTT, dopt および各交差点遅れを再計算
- ロング表 + ワイド表 + グラフを出力

想定入力列:
路線番号, 系統速度, link(0,1), link(1,2), link(2,3), x0opt, x1opt, x2opt, x3opt
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm

# =====================
# ここだけ編集
# =====================
IN_PATH = "results_final.xlsx"
INPUT_SHEET = "Sheet1"   # "Sheet1" or "Sheet2"
OUT_DIR = "fixed_offset_sensitivity"

# None なら全路線・全基準速度を対象
TARGET_ROUTE_IDS = None
TARGET_BASE_SPEEDS = None

TARGET_SPEEDS = [
    20.0, 22.5, 25.0, 27.5, 30.0, 32.5, 35.0,
    37.5, 40.0, 42.5, 45.0, 47.5, 50.0
]
SPEED_TOL = 1e-9

# True にすると、各路線について
# 「基準速度ごとに1本の線」を dopt/TTT それぞれ描く
PLOT_PER_ROUTE = True

# True にすると、各基準速度について
# 「評価速度ごとの累積曲線」を保存（重いので通常はFalse推奨）
PLOT_CUMULATIVE = False


# =====================
# 固定パラメータ
# =====================
C = 120.0
dx = 1.2
G = {0: 0.5*C, 1: 0.6*C, 2: 0.7*C, 3: 0.5*C}

q = 0.5
GREEN_END_INCLUSIVE = False

WARMUP_CYCLES = 2
EVAL_CYCLES = 3
EXTRA_CYCLES_MARGIN = 10


# =====================
# 日本語フォント
# =====================
def set_japanese_font():
    candidates = [
        "IPAexGothic", "IPAGothic",
        "Noto Sans CJK JP", "Noto Sans JP",
        "Yu Gothic", "YuGothic",
        "Hiragino Sans", "Hiragino Kaku Gothic ProN",
        "Meiryo", "MS Gothic",
    ]
    available = {f.name for f in fm.fontManager.ttflist}
    for name in candidates:
        if name in available:
            plt.rcParams["font.family"] = name
            return name
    plt.rcParams["font.family"] = "sans-serif"
    return None


# =====================
# ユーティリティ
# =====================
def merge_intervals(intervals, eps=1e-12):
    if not intervals:
        return []
    intervals = sorted(intervals, key=lambda z: (z[0], z[1]))
    out = []
    s0, e0, r0 = intervals[0]
    for s, e, r in intervals[1:]:
        if abs(r - r0) < 1e-12 and abs(s - e0) < 1e-9:
            e0 = e
        else:
            if e0 - s0 > eps:
                out.append((s0, e0, r0))
            s0, e0, r0 = s, e, r
    if e0 - s0 > eps:
        out.append((s0, e0, r0))
    return out

def shift_intervals(intervals, dt):
    return [(s + dt, e + dt, r) for (s, e, r) in intervals]

def in_green(t, x, g):
    phi = (t - x) % C
    if GREEN_END_INCLUSIVE:
        return phi <= g + 1e-12
    else:
        return phi < g - 1e-12

def build_signal_change_times(x, g, t0, t1):
    n_start = int(np.floor((t0 - x) / C)) - 2
    n_end   = int(np.ceil((t1 - x) / C)) + 2
    ts = [t0, t1]
    for n in range(n_start, n_end + 1):
        gs = x + n * C
        ge = gs + g
        if t0 - 1e-9 <= gs <= t1 + 1e-9:
            ts.append(gs)
        if t0 - 1e-9 <= ge <= t1 + 1e-9:
            ts.append(ge)
    return sorted(set(ts))

def build_source_arrivals(x_dep, g_dep, cycles_total):
    arr = []
    for n in range(cycles_total):
        s = x_dep + n * C
        e = s + g_dep
        arr.append((s, e, q))
    return merge_intervals(arr)


# =====================
# 累積関数
# =====================
class CumFunc:
    def __init__(self, knots_t, knots_N):
        self.t = np.asarray(knots_t, dtype=float)
        self.N = np.asarray(knots_N, dtype=float)
        if len(self.t) != len(self.N):
            raise ValueError("knots_t and knots_N length mismatch")
        if len(self.t) < 2:
            raise ValueError("Need at least 2 knots")
        dt = np.diff(self.t)
        dN = np.diff(self.N)
        self.r = np.zeros_like(dN)
        mask = dt > 0
        self.r[mask] = dN[mask] / dt[mask]

    @staticmethod
    def from_intervals(intervals, t0=0.0, t1=None):
        intervals = merge_intervals([(s, e, r) for (s, e, r) in intervals if r > 0 and e > s])
        times = [t0]
        for s, e, _ in intervals:
            times.append(s)
            times.append(e)
        if t1 is not None:
            times.append(t1)
        times = sorted(set(times))

        intervals = sorted(intervals, key=lambda z: (z[0], z[1]))
        i = 0
        N = 0.0
        knots_t = [times[0]]
        knots_N = [0.0]

        def rate_at(t):
            nonlocal i
            while i < len(intervals) and intervals[i][1] <= t + 1e-12:
                i += 1
            if i < len(intervals):
                s, e, r = intervals[i]
                if s <= t + 1e-12 < e - 1e-12:
                    return r
            return 0.0

        for k in range(len(times) - 1):
            ta = times[k]
            tb = times[k + 1]
            if tb <= ta + 1e-12:
                continue
            cur_r = rate_at(ta)
            N += cur_r * (tb - ta)
            knots_t.append(tb)
            knots_N.append(N)

        return CumFunc(knots_t, knots_N)

    def inverse_integral(self, n0, n1):
        if n1 < n0:
            n0, n1 = n1, n0
        if n1 <= n0 + 1e-12:
            return 0.0

        Nmax = self.N[-1]
        if n0 < -1e-9 or n1 > Nmax + 1e-9:
            raise ValueError(f"n-range [{n0},{n1}] outside cumulative [0,{Nmax}]")

        n0 = max(0.0, n0)
        n1 = min(Nmax, n1)

        total = 0.0
        for i in range(len(self.r)):
            r = self.r[i]
            if r <= 1e-15:
                continue
            t0 = self.t[i]
            N0 = self.N[i]
            N1 = self.N[i + 1]

            a = max(n0, N0)
            b = min(n1, N1)
            if b <= a + 1e-12:
                continue

            total += (b - a) * t0 + (((b - N0) ** 2 - (a - N0) ** 2) / (2.0 * r))
        return total


# =====================
# 点キュー
# =====================
def simulate_point_queue(arrivals, x_node, g_node, t0, t1):
    arrivals = merge_intervals([(s, e, r) for (s, e, r) in arrivals if r > 0 and e > s])

    times = [t0, t1]
    for s, e, _ in arrivals:
        if t0 - 1e-9 <= s <= t1 + 1e-9:
            times.append(s)
        if t0 - 1e-9 <= e <= t1 + 1e-9:
            times.append(e)
    times += build_signal_change_times(x_node, g_node, t0, t1)
    times = sorted(set(times))

    arrivals = sorted(arrivals, key=lambda z: (z[0], z[1]))
    ai = 0

    def lam_at(t):
        nonlocal ai
        while ai < len(arrivals) and arrivals[ai][1] <= t + 1e-12:
            ai += 1
        if ai < len(arrivals):
            s, e, r = arrivals[ai]
            if s <= t + 1e-12 < e - 1e-12:
                return r
        return 0.0

    def mu_at(t):
        return q if in_green(t, x_node, g_node) else 0.0

    Q = 0.0
    dep = []
    queue_area = 0.0

    for k in range(len(times) - 1):
        ta = times[k]
        tb = times[k + 1]
        if tb <= ta + 1e-12:
            continue
        lam = lam_at(ta)
        mu = mu_at(ta + 1e-9)
        dt = tb - ta

        if Q > 1e-12:
            dep_rate = mu
            dQdt = lam - mu
            if dQdt < -1e-12:
                t_hit = ta + Q / (-dQdt)
                if t_hit < tb - 1e-12:
                    dt1 = t_hit - ta
                    queue_area += Q * dt1 + 0.5 * dQdt * dt1 * dt1
                    dep.append((ta, t_hit, dep_rate))

                    Q = 0.0
                    ta2 = t_hit
                    dep_rate2 = min(lam, mu)
                    dep.append((ta2, tb, dep_rate2))
                    continue

            queue_area += Q * dt + 0.5 * dQdt * dt * dt
            dep.append((ta, tb, dep_rate))
            Q = Q + dQdt * dt
            if Q < 0:
                Q = 0.0

        else:
            dep_rate = min(lam, mu)
            dep.append((ta, tb, dep_rate))
            if lam > mu + 1e-12:
                dQdt = lam - mu
                queue_area += 0.5 * dQdt * dt * dt
                Q = dQdt * dt
            else:
                Q = 0.0

    dep = merge_intervals(dep)
    A_cum = CumFunc.from_intervals(arrivals, t0=t0, t1=t1)
    D_cum = CumFunc.from_intervals(dep, t0=t0, t1=t1)

    return dep, A_cum, D_cum, queue_area


# =====================
# 方向別シミュレーション
# =====================
def simulate_direction_cum(L01, L12, L23, speed_kmh, x, start_node):
    v = speed_kmh / 3.6
    tau01 = L01 / v
    tau12 = L12 / v
    tau23 = L23 / v
    tau_sum = tau01 + tau12 + tau23

    if start_node == 0:
        dep_node = 0
        nodes = [1, 2, 3]
        taus = [tau01, tau12, tau23]
        dest = 3
    else:
        dep_node = 3
        nodes = [2, 1, 0]
        taus = [tau23, tau12, tau01]
        dest = 0

    cycles_demand = WARMUP_CYCLES + EVAL_CYCLES
    t_end = cycles_demand * C + tau_sum + EXTRA_CYCLES_MARGIN * C

    src = build_source_arrivals(x[dep_node], G[dep_node], cycles_demand)
    A_src = CumFunc.from_intervals(src, t0=0.0, t1=t_end)

    arr = shift_intervals(src, taus[0])

    per_node_queue_area = {0: 0.0, 1: 0.0, 2: 0.0, 3: 0.0}
    A_nodes = {}
    D_nodes = {}

    for i, node in enumerate(nodes):
        for _ in range(6):
            dep, A_cum, D_cum, q_area = simulate_point_queue(arr, x[node], G[node], 0.0, t_end)
            if D_cum.N[-1] >= A_cum.N[-1] - 1e-9:
                break
            t_end += C
        per_node_queue_area[node] = q_area
        A_nodes[node] = A_cum
        D_nodes[node] = D_cum

        if i < len(nodes) - 1:
            arr = shift_intervals(dep, taus[i + 1])

    D_out = D_nodes[dest]

    n_warm = q * G[dep_node] * WARMUP_CYCLES
    n_eval = q * G[dep_node] * EVAL_CYCLES
    n0 = n_warm
    n1 = n_warm + n_eval

    I_entry = A_src.inverse_integral(n0, n1)
    I_exit = D_out.inverse_integral(n0, n1)

    mean_TT = (I_exit - I_entry) / (n1 - n0)
    mean_delay = mean_TT - tau_sum

    return {
        "tau_sum": tau_sum,
        "mean_TT": mean_TT,
        "mean_delay": mean_delay,
        "A_src": A_src,
        "D_out": D_out,
        "A_nodes": A_nodes,
        "D_nodes": D_nodes,
        "queue_area_nodes": per_node_queue_area,
        "n0": n0,
        "n1": n1,
        "t_end": t_end,
    }


def mean_wait_eval(A_cum, D_cum, n0, n1):
    I_arr = A_cum.inverse_integral(n0, n1)
    I_dep = D_cum.inverse_integral(n0, n1)
    return (I_dep - I_arr) / (n1 - n0)


# =====================
# 双方向評価
# =====================
def evaluate_fixed_offsets(L01, L12, L23, speed_kmh, x0, x1, x2, x3, want_debug=False):
    x = {0: float(x0), 1: float(x1), 2: float(x2), 3: float(x3)}

    f = simulate_direction_cum(L01, L12, L23, speed_kmh, x, start_node=0)
    b = simulate_direction_cum(L01, L12, L23, speed_kmh, x, start_node=3)

    n_eval_dir = q * G[0] * EVAL_CYCLES
    n_tot = 2.0 * n_eval_dir

    mean_TT = 0.5 * (f["mean_TT"] + b["mean_TT"])
    dopt = 0.5 * (f["mean_delay"] + b["mean_delay"])
    FTT = f["tau_sum"]

    qa = {k: f["queue_area_nodes"].get(k, 0.0) + b["queue_area_nodes"].get(k, 0.0) for k in [0, 1, 2, 3]}
    d_stop_nodes = {k: qa[k] / n_tot for k in [0, 1, 2, 3]}
    d_stop_total = sum(qa.values()) / n_tot

    n0, n1 = f["n0"], f["n1"]
    wF = {node: mean_wait_eval(f["A_nodes"][node], f["D_nodes"][node], n0, n1) for node in f["D_nodes"]}
    wB = {node: mean_wait_eval(b["A_nodes"][node], b["D_nodes"][node], n0, n1) for node in b["D_nodes"]}

    out = {
        "dopt(s/veh)": float(dopt),
        "FTT(s/veh)": float(FTT),
        "TTT(s/veh)": float(FTT + dopt),

        "d0_stop(s/veh)": float(d_stop_nodes[0]),
        "d1_stop(s/veh)": float(d_stop_nodes[1]),
        "d2_stop(s/veh)": float(d_stop_nodes[2]),
        "d3_stop(s/veh)": float(d_stop_nodes[3]),
        "d_stop_total(s/veh)": float(d_stop_total),

        "d0_F(s/veh)": float(wF.get(0, 0.0)),
        "d1_F(s/veh)": float(wF.get(1, 0.0)),
        "d2_F(s/veh)": float(wF.get(2, 0.0)),
        "d3_F(s/veh)": float(wF.get(3, 0.0)),
        "d0_B(s/veh)": float(wB.get(0, 0.0)),
        "d1_B(s/veh)": float(wB.get(1, 0.0)),
        "d2_B(s/veh)": float(wB.get(2, 0.0)),
        "d3_B(s/veh)": float(wB.get(3, 0.0)),

        "Nveh_total_eval": float(n_tot),
    }

    if want_debug:
        out["_debug_f"] = f
        out["_debug_b"] = b
    return out


# =====================
# グラフ
# =====================
def plot_route_lines(df_route, value_col, ylabel, out_png):
    plt.figure(figsize=(8, 5.5))
    base_speeds = sorted(df_route["基準速度"].unique())
    for bs in base_speeds:
        sub = df_route[df_route["基準速度"] == bs].sort_values("評価速度")
        plt.plot(
            sub["評価速度"], sub[value_col],
            marker="o", linewidth=2.0, label=f"Base speed = {bs:g}"
        )
    plt.xlabel("Evaluation speed [km/h]", fontsize=13, fontweight="bold")
    plt.ylabel(ylabel, fontsize=13, fontweight="bold")
    route_id = int(df_route["路線番号"].iloc[0])
    plt.title(f"Route {route_id}", fontsize=15, fontweight="bold")
    plt.grid(True, alpha=0.3)
    plt.legend(fontsize=10)
    plt.tight_layout()
    plt.savefig(out_png, dpi=220, bbox_inches="tight")
    plt.close()


def plot_cumulative_for_case(L01, L12, L23, eval_speed, x0, x1, x2, x3, out_png):
    dbg = evaluate_fixed_offsets(L01, L12, L23, eval_speed, x0, x1, x2, x3, want_debug=True)
    f = dbg["_debug_f"]
    b = dbg["_debug_b"]

    fig, axs = plt.subplots(2, 2, figsize=(12, 8))

    axs[0, 0].plot(f["A_src"].t, f["A_src"].N, linewidth=2, label="A_src")
    axs[0, 0].plot(f["D_out"].t, f["D_out"].N, linewidth=2, label="D_out")
    axs[0, 0].set_title("Forward: Source A(t) and Exit D(t)")
    axs[0, 0].set_xlabel("t [s]")
    axs[0, 0].set_ylabel("N [veh]")
    axs[0, 0].legend()

    axs[0, 1].plot(b["A_src"].t, b["A_src"].N, linewidth=2, label="A_src")
    axs[0, 1].plot(b["D_out"].t, b["D_out"].N, linewidth=2, label="D_out")
    axs[0, 1].set_title("Backward: Source A(t) and Exit D(t)")
    axs[0, 1].set_xlabel("t [s]")
    axs[0, 1].set_ylabel("N [veh]")
    axs[0, 1].legend()

    for node in [1, 2, 3]:
        axs[1, 0].plot(f["D_nodes"][node].t, f["D_nodes"][node].N, linewidth=2, label=f"D_node{node}")
    axs[1, 0].set_title("Forward: Node D(t)")
    axs[1, 0].set_xlabel("t [s]")
    axs[1, 0].set_ylabel("N [veh]")
    axs[1, 0].legend()

    for node in [2, 1, 0]:
        axs[1, 1].plot(b["D_nodes"][node].t, b["D_nodes"][node].N, linewidth=2, label=f"D_node{node}")
    axs[1, 1].set_title("Backward: Node D(t)")
    axs[1, 1].set_xlabel("t [s]")
    axs[1, 1].set_ylabel("N [veh]")
    axs[1, 1].legend()

    plt.tight_layout()
    plt.savefig(out_png, dpi=220, bbox_inches="tight")
    plt.close()


# =====================
# メイン
# =====================
def main():
    set_japanese_font()
    os.makedirs(OUT_DIR, exist_ok=True)
    os.makedirs(os.path.join(OUT_DIR, "plots"), exist_ok=True)
    if PLOT_CUMULATIVE:
        os.makedirs(os.path.join(OUT_DIR, "cumulative_plots"), exist_ok=True)

    df = pd.read_excel(IN_PATH, sheet_name=INPUT_SHEET)
    df.columns = df.columns.astype(str).str.strip()

    needed = [
        "路線番号", "系統速度",
        "link(0,1)", "link(1,2)", "link(2,3)",
        "x0opt", "x1opt", "x2opt", "x3opt"
    ]
    for c in needed:
        if c not in df.columns:
            raise RuntimeError(f"Missing column: {c}")

    # フィルタ
    if TARGET_ROUTE_IDS is not None:
        df = df[df["路線番号"].astype(int).isin([int(x) for x in TARGET_ROUTE_IDS])].copy()

    if TARGET_BASE_SPEEDS is not None:
        targets = np.array([float(x) for x in TARGET_BASE_SPEEDS], dtype=float)
        df = df[df["系統速度"].apply(lambda v: np.any(np.isclose(float(v), targets, atol=SPEED_TOL, rtol=0.0)))].copy()

    df = df.sort_values(["路線番号", "系統速度"], ascending=[True, False]).reset_index(drop=True)

    results = []

    for i, r in df.iterrows():
        route_id = int(r["路線番号"])
        base_speed = float(r["系統速度"])

        L01 = float(r["link(0,1)"])
        L12 = float(r["link(1,2)"])
        L23 = float(r["link(2,3)"])

        x0 = float(r["x0opt"])
        x1 = float(r["x1opt"])
        x2 = float(r["x2opt"])
        x3 = float(r["x3opt"])

        print(f"[{i+1}/{len(df)}] route={route_id}, base_speed={base_speed:g}, fixed x=({x0:.1f},{x1:.1f},{x2:.1f},{x3:.1f})")

        for eval_speed in TARGET_SPEEDS:
            out = evaluate_fixed_offsets(L01, L12, L23, eval_speed, x0, x1, x2, x3, want_debug=False)

            rec = {
                "路線番号": route_id,
                "基準速度": base_speed,
                "評価速度": float(eval_speed),

                "link(0,1)": L01,
                "link(1,2)": L12,
                "link(2,3)": L23,

                "x0_fix": x0,
                "x1_fix": x1,
                "x2_fix": x2,
                "x3_fix": x3,
            }
            rec.update(out)
            results.append(rec)

            if PLOT_CUMULATIVE:
                png = os.path.join(
                    OUT_DIR, "cumulative_plots",
                    f"cum_route{route_id}_base{base_speed:g}_eval{eval_speed:g}.png".replace(".", "p")
                )
                plot_cumulative_for_case(L01, L12, L23, eval_speed, x0, x1, x2, x3, png)

    long_df = pd.DataFrame(results)

    # 元の最適化結果と比較しやすいように、評価速度=基準速度かどうかのフラグを付与
    long_df["is_same_speed"] = np.isclose(long_df["基準速度"], long_df["評価速度"], atol=SPEED_TOL, rtol=0.0)

    # wide表（dopt）
    dopt_wide = long_df.pivot_table(
        index=["路線番号", "基準速度", "x0_fix", "x1_fix", "x2_fix", "x3_fix"],
        columns="評価速度",
        values="dopt(s/veh)"
    ).reset_index()

    # wide表（TTT）
    ttt_wide = long_df.pivot_table(
        index=["路線番号", "基準速度", "x0_fix", "x1_fix", "x2_fix", "x3_fix"],
        columns="評価速度",
        values="TTT(s/veh)"
    ).reset_index()

    # 列名整形
    dopt_wide.columns = [
        f"dopt@V={c:g}" if isinstance(c, (int, float, np.floating)) else c
        for c in dopt_wide.columns
    ]
    ttt_wide.columns = [
        f"TTT@V={c:g}" if isinstance(c, (int, float, np.floating)) else c
        for c in ttt_wide.columns
    ]

    # summary表：各固定オフセットに対して最小/最大など
    summary = long_df.groupby(["路線番号", "基準速度", "x0_fix", "x1_fix", "x2_fix", "x3_fix"], as_index=False).agg(
        dopt_min=("dopt(s/veh)", "min"),
        dopt_max=("dopt(s/veh)", "max"),
        dopt_range=("dopt(s/veh)", lambda s: s.max() - s.min()),
        TTT_min=("TTT(s/veh)", "min"),
        TTT_max=("TTT(s/veh)", "max"),
        TTT_range=("TTT(s/veh)", lambda s: s.max() - s.min()),
    )

    # Excel保存
    out_xlsx = os.path.join(OUT_DIR, "fixed_offset_sensitivity_results.xlsx")
    with pd.ExcelWriter(out_xlsx, engine="openpyxl") as writer:
        long_df.to_excel(writer, sheet_name="long", index=False)
        dopt_wide.to_excel(writer, sheet_name="dopt_wide", index=False)
        ttt_wide.to_excel(writer, sheet_name="TTT_wide", index=False)
        summary.to_excel(writer, sheet_name="summary", index=False)

    print("Wrote:", out_xlsx)

    # 路線ごとの線グラフ
    if PLOT_PER_ROUTE:
        for route_id, g in long_df.groupby("路線番号"):
            g = g.copy()

            out1 = os.path.join(OUT_DIR, "plots", f"route_{int(route_id)}_dopt_vs_speed.png")
            plot_route_lines(
                g, "dopt(s/veh)",
                ylabel="Average delay, dopt [s/veh]",
                out_png=out1
            )

            out2 = os.path.join(OUT_DIR, "plots", f"route_{int(route_id)}_TTT_vs_speed.png")
            plot_route_lines(
                g, "TTT(s/veh)",
                ylabel="Total travel time, TTT [s/veh]",
                out_png=out2
            )

            out3 = os.path.join(OUT_DIR, "plots", f"route_{int(route_id)}_FTT_vs_speed.png")
            plot_route_lines(
                g, "FTT(s/veh)",
                ylabel="Free-flow travel time, FTT [s/veh]",
                out_png=out3
            )

    print("Done.")


if __name__ == "__main__":
    main()
