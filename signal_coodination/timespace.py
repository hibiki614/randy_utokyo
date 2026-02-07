# -*- coding: utf-8 -*-
"""
timespace_plot_from_opt_fixed.py
- time-space: travel segments use ARRIVAL times (constant slope),
  stops use horizontal segments (arrival->pass)
- 3 cycles
- fixed time axis scale across all saved figures (so you can compare speeds)
"""

import os
import numpy as np
import pandas as pd

import matplotlib
matplotlib.use("Agg")  # no blocking on CMD
import matplotlib.pyplot as plt

# ====== platoon-band (split-aware) helpers ======
BAND_FILL = "0.75"
BAND_ALPHA = 0.35
BAND_EDGE = "0.25"
BAND_EDGE_LW = 1.2

SPLIT_GAP_EXTRA = 1e-3  # 分裂判定の余裕（基本このままでOK）

def find_breakpoints_from_pass(pas, nodes, h, extra=SPLIT_GAP_EXTRA):
    breaks = set()
    N = pas.shape[0]
    for node in nodes:
        t = pas[:, node]
        if not np.all(np.isfinite(t)):
            continue
        gaps = t[1:] - t[:-1]
        idx = np.where(gaps > (h + extra))[0]
        for j in idx:
            k = j + 1
            if 0 < k < N:
                breaks.add(k)
    return sorted(breaks)

def segments_from_breaks(N, breaks):
    cuts = [0] + list(breaks) + [N]
    segs = []
    for a, b in zip(cuts[:-1], cuts[1:]):
        if b > a:
            segs.append((a, b))
    return segs

def build_boundary_polyline(arr_row, pas_row, direction):
    if direction == "F":
        start = 0
        order = [1, 2, 3]
    else:
        start = 3
        order = [2, 1, 0]

    pts = []
    pts.append((pas_row[start], start))

    for node in order:
        t_arr = arr_row[node]
        t_pas = pas_row[node]
        pts.append((t_arr, node))          # travel end
        if t_pas > t_arr + 1e-9:
            pts.append((t_pas, node))      # stop end
    return pts

def pts_to_xy(pts, X):
    tt = np.array([t for (t, n) in pts], dtype=float)
    yy = np.array([X[int(n)] for (t, n) in pts], dtype=float)
    return tt, yy

def fill_platoon_band(ax, arr, pas, seg, direction, X):
    a, b = seg
    if b - a <= 0:
        return
    if b - a == 1:
        # 1台だけの塊は塗る面が無いので（必要なら線だけ描く）
        return

    k0 = a
    k1 = b - 1

    pts_lo = build_boundary_polyline(arr[k0, :], pas[k0, :], direction)
    pts_hi = build_boundary_polyline(arr[k1, :], pas[k1, :], direction)

    t_lo, y_lo = pts_to_xy(pts_lo, X)
    t_hi, y_hi = pts_to_xy(pts_hi, X)

    poly_t = np.concatenate([t_lo, t_hi[::-1]])
    poly_y = np.concatenate([y_lo, y_hi[::-1]])

    ax.fill(poly_t, poly_y, color=BAND_FILL, alpha=BAND_ALPHA, linewidth=0)
    ax.plot(t_lo, y_lo, color=BAND_EDGE, linewidth=BAND_EDGE_LW)
    ax.plot(t_hi, y_hi, color=BAND_EDGE, linewidth=BAND_EDGE_LW)

# =====================
# INPUT / OUTPUT
# =====================
IN_XLSX = "results_final.xlsx"
OUT_DIR = "timespace_png"

# =====================
# FILTER（optional）
# =====================
TARGET_ROUTE_IDS = []   # e.g. [311,312] ; [] => all
TARGET_SPEEDS = []      # e.g. [50.0]    ; [] => all
SPEED_TOL = 1e-6

# =====================
# SETTINGS（match your model）
# =====================
C = 120.0
G = {0: 0.5*C, 1: 0.6*C, 2: 0.7*C, 3: 0.5*C}
q = 0.5
h = 1.0 / q  # 2.0 s/veh

SHOW_CYCLES = 3
N_PER_CYCLE = int(round(q * G[0]))  # e.g. 30 if G0=60, q=0.5

# style (paper-like)
TRAJ_COLOR = "k"
STOP_COLOR = "k"
GREEN_COLOR = (0.2, 0.6, 1.0)
GREEN_ALPHA = 0.18
TRAVEL_LW = 0.9
STOP_LW = 1.6

# --- shading controls ---
DRAW_EVERY = 1          # 2にすると半分だけ描く（軽くなる）
SHADE_COLOR = "0.7"     # 薄いグレー（0=黒, 1=白）
SHADE_ALPHA = 0.06      # 薄く（0.03〜0.10くらいで調整）
SHADE_LW = 0.6

SHOW_STOPS = True
STOP_COLOR = "0.25"
STOP_ALPHA = 0.12
STOP_LW = 1.0

# =====================
# Helpers
# =====================
def depart_times_multi(x_start, g_len, n_per_cycle, cycles):
    times = []
    for n in range(cycles):
        s0 = x_start + n * C
        times.append(s0 + (np.arange(n_per_cycle) + 0.5) * (g_len / n_per_cycle))
    return np.concatenate(times)

def next_green_start_if_red(t_arr, x, g):
    phi = (t_arr - x) % C
    if phi < g - 1e-12:
        return t_arr
    return t_arr + (C - phi)

def simulate_dir_records(tau_list, x, start_node, cycles):
    """
    record arrival/pass times at each node for each vehicle
    """
    Ntot = N_PER_CYCLE * cycles

    if start_node == 0:
        s_list = depart_times_multi(x[0], G[0], N_PER_CYCLE, cycles)
        nodes_order = [1, 2, 3]
    else:
        s_list = depart_times_multi(x[3], G[3], N_PER_CYCLE, cycles)
        nodes_order = [2, 1, 0]

    prev = {0: -1e18, 1: -1e18, 2: -1e18, 3: -1e18}

    arr = np.full((Ntot, 4), np.nan, dtype=float)
    pas = np.full((Ntot, 4), np.nan, dtype=float)

    for k, s in enumerate(s_list):
        arr[k, start_node] = s
        pas[k, start_node] = s
        t = s

        for i, node in enumerate(nodes_order):
            a = t + tau_list[i]
            t_sig = next_green_start_if_red(a, x[node], G[node])
            t_pass = max(t_sig, prev[node] + h)
            arr[k, node] = a
            pas[k, node] = t_pass
            prev[node] = t_pass
            t = t_pass

    return arr, pas


def plot_timespace(arr_f, pas_f, arr_b, pas_b, L01, L12, L23, x, title, out_path, t_xlim):
    """
    車両1本1本は描かず、分裂した各プラトーンごとに
    先頭境界線〜最後尾境界線の間を薄グレーで塗る。
    """
    X = np.array([0.0, L01, L01 + L12, L01 + L12 + L23], dtype=float)

    fig, ax = plt.subplots(figsize=(13, 7))

    # ---- forward: split points from nodes 1,2,3 ----
    breaks_F = find_breakpoints_from_pass(pas_f, nodes=[1, 2, 3], h=h)
    segs_F = segments_from_breaks(pas_f.shape[0], breaks_F)
    for seg in segs_F:
        fill_platoon_band(ax, arr_f, pas_f, seg, "F", X)

    # ---- backward: split points from nodes 2,1,0 ----
    breaks_B = find_breakpoints_from_pass(pas_b, nodes=[2, 1, 0], h=h)
    segs_B = segments_from_breaks(pas_b.shape[0], breaks_B)
    for seg in segs_B:
        fill_platoon_band(ax, arr_b, pas_b, seg, "B", X)

    # ---- green bands ----
    tmin, tmax = t_xlim
    n0 = int(np.floor((tmin - C) / C)) - 1
    n1 = int(np.ceil((tmax + C) / C)) + 1
    for node in [0, 1, 2, 3]:
        y = X[node]
        for n in range(n0, n1 + 1):
            gs = x[node] + n * C
            ge = gs + G[node]
            if ge < tmin or gs > tmax:
                continue
            ax.hlines(y, gs, ge, color=GREEN_COLOR, linewidth=8, alpha=GREEN_ALPHA)

    ax.set_xlim(tmin, tmax)  # ★スケール固定
    ax.set_ylim(-0.02 * X[-1], 1.02 * X[-1])
    ax.set_xlabel("time [s]")
    ax.set_ylabel("space [m]")
    ax.set_title(title)
    ax.grid(True, alpha=0.15)

    plt.tight_layout()
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    fig.savefig(out_path, dpi=220)
    plt.close(fig)



def main():
    df = pd.read_excel(IN_XLSX)
    df.columns = df.columns.astype(str).str.strip()

    req = ["路線番号", "系統速度", "link(0,1)", "link(1,2)", "link(2,3)", "x1opt", "x2opt", "x3opt"]
    for c in req:
        if c not in df.columns:
            raise RuntimeError(f"Missing column: {c}")

    route_set = set(int(x) for x in TARGET_ROUTE_IDS) if len(TARGET_ROUTE_IDS) else None
    speed_targets = np.array([float(x) for x in TARGET_SPEEDS], dtype=float)

    def speed_ok(v):
        if speed_targets.size == 0:
            return True
        return np.any(np.isclose(float(v), speed_targets, atol=SPEED_TOL, rtol=0.0))

    rows = []
    max_tau_sum = 0.0

    # collect rows + compute global max travel time (to fix x-axis)
    for i, r in df.iterrows():
        if pd.isna(r["x1opt"]) or pd.isna(r["x2opt"]) or pd.isna(r["x3opt"]):
            continue
        rid = int(r["路線番号"])
        spd = float(r["系統速度"])
        if route_set is not None and rid not in route_set:
            continue
        if not speed_ok(spd):
            continue

        L01 = float(r["link(0,1)"]); L12 = float(r["link(1,2)"]); L23 = float(r["link(2,3)"])
        v = spd / 3.6
        tau_sum = (L01 + L12 + L23) / v
        max_tau_sum = max(max_tau_sum, tau_sum)

        rows.append(i)

    print("rows to plot:", len(rows))
    if not rows:
        print("No rows found. Check IN_XLSX and x1opt/x2opt/x3opt.")
        return

    # ★ fixed time axis for ALL figures (so scale doesn't change by speed)
    # show_cycles*C covers demand duration; add max_tau_sum + one extra cycle for tail
    t_xlim = (0.0, SHOW_CYCLES * C + max_tau_sum + 1.0 * C)

    os.makedirs(OUT_DIR, exist_ok=True)

    for idx in rows:
        r = df.loc[idx]
        rid = int(r["路線番号"])
        spd = float(r["系統速度"])
        L01 = float(r["link(0,1)"])
        L12 = float(r["link(1,2)"])
        L23 = float(r["link(2,3)"])

        x = {0: 0.0, 1: float(r["x1opt"]), 2: float(r["x2opt"]), 3: float(r["x3opt"])}

        v = spd / 3.6
        tau01 = L01 / v
        tau12 = L12 / v
        tau23 = L23 / v

        arr_f, pas_f = simulate_dir_records([tau01, tau12, tau23], x, start_node=0, cycles=SHOW_CYCLES)
        arr_b, pas_b = simulate_dir_records([tau23, tau12, tau01], x, start_node=3, cycles=SHOW_CYCLES)

        title = (
            f"Time–Space (route {rid}, v={spd:.1f} km/h)  "
            f"offsets=({x[1]:.1f},{x[2]:.1f},{x[3]:.1f})  "
            f"cycles={SHOW_CYCLES}, N/cycle={N_PER_CYCLE}"
        )
        out_path = os.path.join(
            OUT_DIR,
            f"timespace_route{rid}_v{spd:.1f}_x{x[1]:.1f}_{x[2]:.1f}_{x[3]:.1f}_cyc{SHOW_CYCLES}.png"
        )

        plot_timespace(arr_f, pas_f, arr_b, pas_b, L01, L12, L23, x, title, out_path, t_xlim)
        print("saved:", out_path)

if __name__ == "__main__":
    main()
