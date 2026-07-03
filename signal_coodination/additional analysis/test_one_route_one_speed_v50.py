# -*- coding: utf-8 -*-
from pathlib import Path

"""
Created on Thu Feb  5 01:19:22 2026

@author: OguchiLab
"""

# -*- coding: utf-8 -*-
import numpy as np
import time

# =====================
# 固定パラメータ
# =====================
C = 120.0
dx = 1.2
grid = np.arange(0.0, C, dx)      # 100 values: 0..118.8

# 有効青時間（秒）
G = {0: 0.5*C, 1: 0.6*C, 2: 0.7*C, 3: 0.5*C}

q = 0.5                           # veh/s（全リンク・全交差点同じ）
GREEN_END_INCLUSIVE = False

WARMUP_CYCLES = 2
EVAL_CYCLES = 3

# 解析の安全マージン（到着終了後もQが捌けるまでイベントが必要）
EXTRA_CYCLES_MARGIN = 10   # 普通は十分。足りなければ自動延長も入れてる。

# プロット（最適解で累積図を描きたい時だけ True）
PLOT_CUMULATIVE_FOR_BEST = False

# =====================
# ユーティリティ：区分一定 intervals
# intervals: list of (start, end, rate) with start<end, rate>=0
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
    # 青区間: [x+nC, x+nC+g)
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
    """源点需要：各サイクルで [x_dep+nC, x_dep+nC+g_dep) に q を流す"""
    arr = []
    for n in range(cycles_total):
        s = x_dep + n * C
        e = s + g_dep
        arr.append((s, e, q))
    return merge_intervals(arr)

# =====================
# 累積関数（区分線形）クラス
#  - rate intervals から (t_knots, N_knots, slope per segment) を作る
#  - inverse の積分 ∫ t(n) dn を解析的に計算できる
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
        """
        intervals: (s,e,rate)
        returns cumulative N(t) with N(t0)=0, built on all event times.
        """
        intervals = merge_intervals([(s,e,r) for (s,e,r) in intervals if r > 0 and e > s])
        times = [t0]
        for s,e,_ in intervals:
            times.append(s); times.append(e)
        if t1 is not None:
            times.append(t1)
        times = sorted(set(times))

        # sweep
        intervals = sorted(intervals, key=lambda z: (z[0], z[1]))
        i = 0
        cur_r = 0.0
        N = 0.0
        knots_t = [times[0]]
        knots_N = [0.0]

        def rate_at(t):
            nonlocal i
            while i < len(intervals) and intervals[i][1] <= t + 1e-12:
                i += 1
            if i < len(intervals):
                s,e,r = intervals[i]
                if s <= t + 1e-12 < e - 1e-12:
                    return r
            return 0.0

        for k in range(len(times)-1):
            ta = times[k]
            tb = times[k+1]
            if tb <= ta + 1e-12:
                continue
            cur_r = rate_at(ta)
            N += cur_r * (tb - ta)
            knots_t.append(tb)
            knots_N.append(N)

        return CumFunc(knots_t, knots_N)

    def value_at(self, t_query):
        """piecewise-linear interpolation of N(t)"""
        return np.interp(t_query, self.t, self.N, left=self.N[0], right=self.N[-1])

    def inverse_integral(self, n0, n1):
        """
        ∫_{n0}^{n1} t(n) dn を解析的に計算。
        ここで t(n) は N(t) の逆（単調増加部分上）。
        """
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
                # flat segment (no flow) => no inverse here
                continue
            t0 = self.t[i]
            N0 = self.N[i]
            N1 = self.N[i+1]

            a = max(n0, N0)
            b = min(n1, N1)
            if b <= a + 1e-12:
                continue

            # t(n) = t0 + (n - N0)/r  on [N0,N1]
            # ∫ t(n) dn = (b-a)*t0 + ((b-N0)^2 - (a-N0)^2)/(2r)
            total += (b - a) * t0 + (((b - N0)**2 - (a - N0)**2) / (2.0 * r))

        return total

# =====================
# 点キュー（信号）をイベント時刻で解く
# 返すもの：
#   dep_intervals: (s,e,rate) = 区分一定の流出率
#   A(t), D(t) の累積関数（CumFunc）も作れるように knots を返す
# =====================
def simulate_point_queue(arrivals, x_node, g_node, t0, t1):
    """
    arrivals: intervals of arrival rate [veh/s]
    service: q on green, 0 on red
    returns dep_intervals, (A_cum, D_cum), queue_area_total
    """
    arrivals = merge_intervals([(s,e,r) for (s,e,r) in arrivals if r > 0 and e > s])

    # event times = arrival boundaries + signal change times + [t0,t1]
    times = [t0, t1]
    for s,e,_ in arrivals:
        if t0 - 1e-9 <= s <= t1 + 1e-9: times.append(s)
        if t0 - 1e-9 <= e <= t1 + 1e-9: times.append(e)
    times += build_signal_change_times(x_node, g_node, t0, t1)
    times = sorted(set(times))

    # sweep arrival rate
    arrivals = sorted(arrivals, key=lambda z: (z[0], z[1]))
    ai = 0
    def lam_at(t):
        nonlocal ai
        while ai < len(arrivals) and arrivals[ai][1] <= t + 1e-12:
            ai += 1
        if ai < len(arrivals):
            s,e,r = arrivals[ai]
            if s <= t + 1e-12 < e - 1e-12:
                return r
        return 0.0

    def mu_at(t):
        return q if in_green(t, x_node, g_node) else 0.0

    Q = 0.0
    dep = []
    queue_area = 0.0

    # also build cumulative knots for A and D over [t0,t1]
    A_kn_t = [times[0]]; A_kn_N = [0.0]
    D_kn_t = [times[0]]; D_kn_N = [0.0]
    Acur = 0.0
    Dcur = 0.0

    for k in range(len(times)-1):
        ta = times[k]
        tb = times[k+1]
        if tb <= ta + 1e-12:
            continue
        lam = lam_at(ta)
        mu  = mu_at(ta + 1e-9)  # boundary jitter
        dt = tb - ta

        # arrivals cumulative
        Acur += lam * dt

        if Q > 1e-12:
            dep_rate = mu
            dQdt = lam - mu
            # may hit zero within segment
            if dQdt < -1e-12:
                t_hit = ta + Q / (-dQdt)
                if t_hit < tb - 1e-12:
                    # part1: Q>0
                    dt1 = t_hit - ta
                    queue_area += Q*dt1 + 0.5*dQdt*dt1*dt1
                    dep.append((ta, t_hit, dep_rate))
                    Dcur += dep_rate * dt1

                    # update knots
                    A_kn_t.append(t_hit); A_kn_N.append(Acur - lam*(tb - t_hit))  # careful? simplify by recompute later -> avoid
                    # simpler: don't insert mid knots for A; we'll build A separately from arrivals intervals anyway.
                    # For D, insert knot at t_hit:
                    D_kn_t.append(t_hit); D_kn_N.append(Dcur)

                    # part2: Q=0
                    Q = 0.0
                    ta2 = t_hit
                    dt2 = tb - ta2
                    dep_rate2 = min(lam, mu)
                    dep.append((ta2, tb, dep_rate2))
                    Dcur += dep_rate2 * dt2
                    # Q stays 0
                    # no queue area increase
                    # knot at tb
                    D_kn_t.append(tb); D_kn_N.append(Dcur)
                    # knot at tb for A later
                    continue

            # whole segment Q>0
            queue_area += Q*dt + 0.5*dQdt*dt*dt
            dep.append((ta, tb, dep_rate))
            Dcur += dep_rate * dt
            Q = Q + dQdt * dt
            if Q < 0: Q = 0.0

        else:
            dep_rate = min(lam, mu)
            dep.append((ta, tb, dep_rate))
            Dcur += dep_rate * dt
            # Q grows only if lam>mu
            if lam > mu + 1e-12:
                dQdt = lam - mu
                queue_area += 0.5*dQdt*dt*dt
                Q = dQdt * dt
            else:
                Q = 0.0

        # knot at tb for D
        D_kn_t.append(tb); D_kn_N.append(Dcur)

    dep = merge_intervals(dep)

    # A cumulative is best built directly from arrivals intervals (no need to rely on knots inside loop)
    A_cum = CumFunc.from_intervals(arrivals, t0=t0, t1=t1)
    # D cumulative from dep intervals
    D_cum = CumFunc.from_intervals(dep, t0=t0, t1=t1)

    return dep, A_cum, D_cum, queue_area

# =====================
# 直列ネットワーク（単方向）を累積図で解く
# 評価（離散と同じ）：evalで入った車群 [n0,n1] の平均旅行時間を出口累積で計算
# =====================
def simulate_direction_cum(L01, L12, L23, speed_kmh, x, start_node):
    v = speed_kmh / 3.6
    tau01 = L01 / v
    tau12 = L12 / v
    tau23 = L23 / v
    tau_sum = tau01 + tau12 + tau23

    if start_node == 0:
        dep_node = 0
        nodes = [1,2,3]
        taus  = [tau01, tau12, tau23]
        dest = 3
    else:
        dep_node = 3
        nodes = [2,1,0]
        taus  = [tau23, tau12, tau01]
        dest = 0

    # 需要は warmup+eval まで
    cycles_demand = WARMUP_CYCLES + EVAL_CYCLES

    # 時間ホライズン：需要終了 + 旅行時間 + 余裕（イベント計算なので粗くてもOK）
    t_end_base = cycles_demand*C + tau_sum + EXTRA_CYCLES_MARGIN*C

    # 源点流入（リンクへ入る＝出発時刻）累積
    src = build_source_arrivals(x[dep_node], G[dep_node], cycles_demand)
    A_src = CumFunc.from_intervals(src, t0=0.0, t1=t_end_base)

    # 最初の信号への到着
    arr = shift_intervals(src, taus[0])

    # 各ノードで点キューを解く→次へシフト
    per_node_queue_area = {0:0.0,1:0.0,2:0.0,3:0.0}
    A_nodes = {}
    D_nodes = {}

    t_end = t_end_base

    for i, node in enumerate(nodes):
        # 万一、最後まで捌けていないと困るので自動延長（最大数回）
        for _ in range(6):
            dep, A_cum, D_cum, q_area = simulate_point_queue(arr, x[node], G[node], 0.0, t_end)
            # 到着累積の最終値＝流入総台数。流出最終値が追いついていれば捌けた。
            if D_cum.N[-1] >= A_cum.N[-1] - 1e-9:
                break
            t_end += C  # 1サイクル延長して再計算
        per_node_queue_area[node] = q_area
        A_nodes[node] = A_cum
        D_nodes[node] = D_cum

        if i < len(nodes)-1:
            arr = shift_intervals(dep, taus[i+1])

    # 出口（終点側）の流出累積
    D_out = D_nodes[dest]

    # eval車群（累積台数）範囲：源点での流入台数で定義
    n_warm = q * G[dep_node] * WARMUP_CYCLES
    n_eval = q * G[dep_node] * EVAL_CYCLES
    n0 = n_warm
    n1 = n_warm + n_eval

    # 入口時刻の積分：∫ t_entry(n) dn
    I_entry = A_src.inverse_integral(n0, n1)
    # 出口時刻の積分：∫ t_exit(n) dn
    I_exit  = D_out.inverse_integral(n0, n1)

    mean_TT = (I_exit - I_entry) / (n1 - n0)  # s/veh
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

# =====================
# 双方向合算評価（目的関数は旅行時間ベース遅れ）
# =====================
def evaluate_offsets_cum(L01, L12, L23, speed_kmh, x1, x2, x3, want_debug=False):
    x = {0:0.0, 1:float(x1), 2:float(x2), 3:float(x3)}

    f = simulate_direction_cum(L01, L12, L23, speed_kmh, x, start_node=0)
    b = simulate_direction_cum(L01, L12, L23, speed_kmh, x, start_node=3)

    # eval台数（方向別）は同じ
    n_eval_dir = q * G[0] * EVAL_CYCLES
    n_tot = 2.0 * n_eval_dir

    # 双方向の平均旅行時間・遅れ（台数で重み付け。ここでは同数なので単純平均）
    mean_TT = 0.5*(f["mean_TT"] + b["mean_TT"])
    dopt = 0.5*(f["mean_delay"] + b["mean_delay"])  # s/veh
    FTT = f["tau_sum"]

    # 参考：交差点別の「キュー面積」由来の遅れ（停止遅れっぽい量）
    # これは旅行時間ベースではなく、単に ∫Q dt の合計 / 台数（参考値）
    qa = {k: f["queue_area_nodes"].get(k,0.0) + b["queue_area_nodes"].get(k,0.0) for k in [0,1,2,3]}
    d_stop_nodes = {k: qa[k]/n_tot for k in [0,1,2,3]}
    d_stop_total = sum(qa.values())/n_tot

    out = {
        "x0opt": 0.0,
        "x1opt": float(x1),
        "x2opt": float(x2),
        "x3opt": float(x3),

        # 旅行時間ベース（推奨：既往研究の「総旅行時間差」定義に合わせやすい）
        "dopt(s/veh)": float(dopt),
        "FTT(s/veh)": float(FTT),
        "TTT(s/veh)": float(FTT + dopt),

        # 参考：停止遅れっぽい量（交差点別、ネットワーク合計）
        "d0_stop(s/veh)": float(d_stop_nodes[0]),
        "d1_stop(s/veh)": float(d_stop_nodes[1]),
        "d2_stop(s/veh)": float(d_stop_nodes[2]),
        "d3_stop(s/veh)": float(d_stop_nodes[3]),
        "d_stop_total(s/veh)": float(d_stop_total),

        "Nveh_total_eval": float(n_tot),
    }

    if want_debug:
        out["_debug_f"] = f
        out["_debug_b"] = b

    return out


# =====================
# テスト条件：1路線 × 1速度
# =====================
# 既存路線311（50 km/h基準）のリンク長
ROUTE_ID = "311"
DESIGN_SPEED_KMH = 50.0
EVALUATION_SPEED_KMH = 50.0

L01 = 416.6666667
L12 = 500.0
L23 = 416.6666667

OUTPUT_DIR = Path("test_output")
REPORT_EVERY = 10_000
OPT_ATOL = 1e-6


def evaluate_delay_only(L01, L12, L23, speed_kmh, x1, x2, x3):
    """双方向平均の旅行時間ベース遅れだけを返す。"""
    x = {0: 0.0, 1: float(x1), 2: float(x2), 3: float(x3)}

    forward = simulate_direction_cum(
        L01, L12, L23, speed_kmh, x, start_node=0
    )
    backward = simulate_direction_cum(
        L01, L12, L23, speed_kmh, x, start_node=3
    )

    return 0.5 * (
        forward["mean_delay"] + backward["mean_delay"]
    )


def run_all_offsets():
    """
    全100^3オフセットの遅れを計算して保存する。

    delays[i, j, k] は
      x1 = grid[i]
      x2 = grid[j]
      x3 = grid[k]
    に対応する。
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    speed_tag = str(EVALUATION_SPEED_KMH).replace(".", "p")
    stem = f"route_{ROUTE_ID}_speed_{speed_tag}"

    delay_path = OUTPUT_DIR / f"{stem}_delays.npy"
    optima_path = OUTPUT_DIR / f"{stem}_optima.npy"
    summary_path = OUTPUT_DIR / f"{stem}_summary.json"

    if delay_path.exists():
        raise FileExistsError(
            f"{delay_path} already exists. "
            "Delete it or change the test condition before rerunning."
        )

    delays = np.empty(
        (len(grid), len(grid), len(grid)),
        dtype=np.float32,
    )

    best_val = np.inf
    best_idx = None
    total = len(grid) ** 3
    checked = 0
    started = time.time()

    for i, x1 in enumerate(grid):
        for j, x2 in enumerate(grid):
            for k, x3 in enumerate(grid):
                delay = evaluate_delay_only(
                    L01, L12, L23,
                    EVALUATION_SPEED_KMH,
                    x1, x2, x3,
                )
                delays[i, j, k] = delay

                if delay < best_val:
                    best_val = float(delay)
                    best_idx = (i, j, k)

                checked += 1
                if checked % REPORT_EVERY == 0:
                    elapsed = time.time() - started
                    rate = checked / elapsed if elapsed > 0 else 0.0
                    eta = (
                        (total - checked) / rate
                        if rate > 0 else float("inf")
                    )
                    bx = tuple(float(grid[m]) for m in best_idx)
                    print(
                        f"[{checked:,}/{total:,} "
                        f"({100.0 * checked / total:6.2f}%)] "
                        f"elapsed={elapsed:8.1f}s "
                        f"ETA={eta:8.1f}s "
                        f"best_d={best_val:.6f} "
                        f"best_x={bx}",
                        flush=True,
                    )

    # Save atomically: temporary file -> final file.
    tmp_delay_path = OUTPUT_DIR / f"{stem}_delays.tmp.npy"
    np.save(tmp_delay_path, delays)
    tmp_delay_path.replace(delay_path)

    d_min = float(np.min(delays))
    opt_indices = np.argwhere(
        np.isclose(delays, d_min, atol=OPT_ATOL, rtol=0.0)
    )
    opt_offsets = np.column_stack(
        (
            grid[opt_indices[:, 0]],
            grid[opt_indices[:, 1]],
            grid[opt_indices[:, 2]],
        )
    ).astype(np.float32)
    np.save(optima_path, opt_offsets)

    elapsed = time.time() - started
    representative = opt_offsets[0]

    # Detailed values only for one representative optimum.
    best_detail = evaluate_offsets_cum(
        L01, L12, L23,
        EVALUATION_SPEED_KMH,
        float(representative[0]),
        float(representative[1]),
        float(representative[2]),
        want_debug=False,
    )

    summary = {
        "route_id": ROUTE_ID,
        "design_speed_kmh": DESIGN_SPEED_KMH,
        "evaluation_speed_kmh": EVALUATION_SPEED_KMH,
        "cycle_length_s": C,
        "offset_step_s": dx,
        "grid_size_each_axis": int(len(grid)),
        "number_of_offset_patterns": int(total),
        "L01_m": L01,
        "L12_m": L12,
        "L23_m": L23,
        "d_min_s_per_veh": d_min,
        "representative_x1_s": float(representative[0]),
        "representative_x2_s": float(representative[1]),
        "representative_x3_s": float(representative[2]),
        "number_of_exact_optima": int(len(opt_offsets)),
        "number_within_0p1s": int(np.count_nonzero(delays <= d_min + 0.1)),
        "number_within_0p5s": int(np.count_nonzero(delays <= d_min + 0.5)),
        "number_within_1p0s": int(np.count_nonzero(delays <= d_min + 1.0)),
        "FTT_s_per_veh": float(best_detail["FTT(s/veh)"]),
        "TTT_s_per_veh": float(best_detail["TTT(s/veh)"]),
        "runtime_sec": elapsed,
        "delay_file": str(delay_path),
        "optima_file": str(optima_path),
        "array_definition": "delays[i,j,k] corresponds to x1=grid[i], x2=grid[j], x3=grid[k]",
    }

    import json
    tmp_summary_path = OUTPUT_DIR / f"{stem}_summary.tmp.json"
    with tmp_summary_path.open("w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    tmp_summary_path.replace(summary_path)

    print("\nFinished.")
    print(f"Delay array : {delay_path}")
    print(f"All optima  : {optima_path}")
    print(f"Summary     : {summary_path}")
    print(f"d_min       : {d_min:.6f} s/veh")
    print(
        "representative optimum: "
        f"({representative[0]:.1f}, "
        f"{representative[1]:.1f}, "
        f"{representative[2]:.1f}) s"
    )


if __name__ == "__main__":
    run_all_offsets()
