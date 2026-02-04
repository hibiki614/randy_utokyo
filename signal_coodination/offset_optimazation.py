import pandas as pd
import numpy as np
import time

# =====================
# ここだけ編集：計算したい対象（複数OK）
# =====================
TARGET_ROUTE_IDS = [311]          # 例: [311, 312]
TARGET_SPEEDS    = [50]           # 例: [50, 45]
SPEED_TOL        = 1e-6           # 速度一致許容

# =====================
# 固定パラメータ
# =====================
C  = 120.0
dx = 1.2
grid = np.arange(0.0, C, dx)      # 100 values: 0..118.8

# greens (sec)
G = {0: 0.5*C, 1: 0.6*C, 2: 0.7*C, 3: 0.5*C}

q = 0.5    # ←ここだけ
h = 1.0 / q
N = int(np.floor(G[0] / h + 1e-9))  # だいたい31になる
#%%

# =====================
# 定常評価（持ち越し）設定
# =====================
WARMUP_CYCLES = 2
EVAL_CYCLES   = 3

# =====================
# helpers
# =====================
def depart_times(x_start, g_len):
    """
    端点需要：青開始ちょうどから飽和放出（ヘッドウェイh刻み）
    例：G0=60,h=2 -> 0,2,4,...,58 の30台
    """
    n = int(np.floor(g_len / h + 1e-9))
    return x_start + np.arange(n) * h

def next_green_time(t, x, g):
    """
    時刻tが青ならそのまま、赤なら次の青開始へ（絶対時刻でもOK）
    """
    phi = (t - x) % C
    return t if phi < g else (t + (C - phi))

def run_dir_multicycle(tau, x, start_node, cycles, prev=None, cycle_offset=0):
    """
    point queue + 飽和流率（ヘッドウェイh）+ 信号
    サイクル跨ぎで prev を引き継ぐ。

    tau: [tau01,tau12,tau23] (方向に合わせて渡す)
    x: {0,1,2,3} offsets in [0,C)
    start_node: 0 (0->3) or 3 (3->0)
    cycles: 回すサイクル数
    prev: 各交差点の「最後の通過時刻」（carry-over状態）
    cycle_offset: 何サイクル目から始めるか（warmup後の巻き戻し防止）
    """
    if prev is None:
        prev = {0: -1e18, 1: -1e18, 2: -1e18, 3: -1e18}

    D = {0: 0.0, 1: 0.0, 2: 0.0, 3: 0.0}

    if start_node == 0:
        dep_node = 0
        nodes = [1, 2, 3]
    else:
        dep_node = 3
        nodes = [2, 1, 0]

    for m in range(cycles):
        mm = cycle_offset + m  # ★絶対サイクル番号（巻き戻し防止）

        # サイクルmmの需要（絶対時刻で生成）
        s_list = depart_times(x[dep_node] + mm * C, G[dep_node])

        for s in s_list:
            t = s
            for i, node in enumerate(nodes):
                a = t + tau[i]  # stop line arrival

                # ★正しい制約：自分の番（prev+h）を先に取り、その時刻が赤なら次青へ
                t_cand = max(a, prev[node] + h)
                t_pass = next_green_time(t_cand, x[node], G[node])

                D[node] += (t_pass - a)
                prev[node] = t_pass
                t = t_pass

    return D, prev

def optimize_one(L01, L12, L23, speed_kmh):
    v = speed_kmh / 3.6
    tau01 = L01 / v
    tau12 = L12 / v
    tau23 = L23 / v
    FTT = tau01 + tau12 + tau23

    best = {"dopt": float("inf")}
    total = len(grid) ** 3

    t0 = time.time()
    checked = 0
    report_every = 10_000

    # 方向別tau
    tau_f = [tau01, tau12, tau23]  # 0->3
    tau_b = [tau23, tau12, tau01]  # 3->0

    for x1 in grid:
        for x2 in grid:
            for x3 in grid:
                checked += 1

                x = {0: 0.0, 1: float(x1), 2: float(x2), 3: float(x3)}

                # ---- forward: warmup then eval (時刻を連続にする) ----
                prev_f = None
                if WARMUP_CYCLES > 0:
                    _, prev_f = run_dir_multicycle(tau_f, x, start_node=0,
                                                   cycles=WARMUP_CYCLES, prev=None, cycle_offset=0)
                Df_eval, _ = run_dir_multicycle(tau_f, x, start_node=0,
                                                cycles=EVAL_CYCLES, prev=prev_f, cycle_offset=WARMUP_CYCLES)

                # ---- backward: warmup then eval ----
                prev_b = None
                if WARMUP_CYCLES > 0:
                    _, prev_b = run_dir_multicycle(tau_b, x, start_node=3,
                                                   cycles=WARMUP_CYCLES, prev=None, cycle_offset=0)
                Db_eval, _ = run_dir_multicycle(tau_b, x, start_node=3,
                                                cycles=EVAL_CYCLES, prev=prev_b, cycle_offset=WARMUP_CYCLES)

                # ---- totals over EVAL window only ----
                D0 = Df_eval[0] + Db_eval[0]
                D1 = Df_eval[1] + Db_eval[1]
                D2 = Df_eval[2] + Db_eval[2]
                D3 = Df_eval[3] + Db_eval[3]
                Dtot = D0 + D1 + D2 + D3

                Ntotal_eval = 2 * N * EVAL_CYCLES  # 双方向×評価サイクル
                d0 = D0 / Ntotal_eval
                d1 = D1 / Ntotal_eval
                d2 = D2 / Ntotal_eval
                d3 = D3 / Ntotal_eval
                dopt = Dtot / Ntotal_eval

                if dopt < best["dopt"]:
                    best = {
                        "x0opt": 0.0,
                        "x1opt": x[1],
                        "x2opt": x[2],
                        "x3opt": x[3],

                        "d0opt(s/veh)": d0,
                        "d1opt(s/veh)": d1,
                        "d2opt(s/veh)": d2,
                        "d3opt(s/veh)": d3,
                        "dopt(s/veh)": dopt,

                        "D0tot(s)": D0,
                        "D1tot(s)": D1,
                        "D2tot(s)": D2,
                        "D3tot(s)": D3,
                        "Dtot(s)": Dtot,

                        "Nveh_dir": int(N),
                        "Nveh_total_eval": int(Ntotal_eval),
                        "WarmupCycles": int(WARMUP_CYCLES),
                        "EvalCycles": int(EVAL_CYCLES),

                        "FTT(s/veh)": float(FTT),
                        "TTT(s/veh)": float(FTT + dopt),

                        "dopt": float(dopt),  # internal
                    }

                if checked % report_every == 0:
                    elapsed = time.time() - t0
                    rate = checked / elapsed if elapsed > 0 else 0.0
                    eta = (total - checked) / rate if rate > 0 else float("inf")
                    pct = 100.0 * checked / total
                    print(
                        f"[{checked:,}/{total:,} = {pct:6.2f}%] "
                        f"elapsed={elapsed:8.1f}s  ETA={eta:8.1f}s  "
                        f"best_dopt={best['dopt']:.6f}  "
                        f"best_x=({best.get('x1opt',np.nan):.1f},"
                        f"{best.get('x2opt',np.nan):.1f},"
                        f"{best.get('x3opt',np.nan):.1f})"
                    )

    if not np.isfinite(best["dopt"]):
        raise RuntimeError("No feasible solution found.")

    best.pop("dopt", None)
    return best

# =====================
# Excel read -> filter -> compute -> write
# =====================
in_path = "experiment.xlsx"
df = pd.read_excel(in_path)

route_set = set(int(x) for x in TARGET_ROUTE_IDS)
speed_targets = np.array([float(x) for x in TARGET_SPEEDS], dtype=float)

def speed_hit(val):
    val = float(val)
    return np.any(np.isclose(val, speed_targets, atol=SPEED_TOL, rtol=0.0))

mask = df["路線番号"].astype(int).isin(route_set) & df["系統速度"].apply(speed_hit)
idxs = df.index[mask].tolist()

print(f"Targets found: {len(idxs)} rows")
print(df.loc[idxs, ["路線番号", "系統速度", "link(0,1)", "link(1,2)", "link(2,3)"]])

for idx in idxs:
    r = df.loc[idx]
    res = optimize_one(
        L01=float(r["link(0,1)"]),
        L12=float(r["link(1,2)"]),
        L23=float(r["link(2,3)"]),
        speed_kmh=float(r["系統速度"]),
    )
    for k, v in res.items():
        df.at[idx, k] = v

out_path = "experiment_with_offsets_filtered.xlsx"
df.to_excel(out_path, index=False)
print("Wrote:", out_path)
