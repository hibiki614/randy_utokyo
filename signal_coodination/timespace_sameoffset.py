# -*- coding: utf-8 -*-
"""
timespace_plot_from_opt_fixed.py (patched)
- time-space: travel segments use ARRIVAL times (constant slope),
  stops use horizontal segments (arrival->pass)
- 3 cycles
- fixed time axis scale across all saved figures (so you can compare speeds)
- FIX:
  * Remove white gaps at platoon splits by small overlap EPS_T
  * Draw platoon bands via PolyCollection (no edges)
  * Add thin red-wait strips (arr -> signal green start) at stopbars
  * STOPBAR_ALPHA == BAND_ALPHA
"""

import os
import numpy as np
import pandas as pd

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection

# =====================
# DRAW SETTINGS
# =====================
BAND_FILL = "0.75"
BAND_ALPHA = 0.35

STOPBAR_COLOR = BAND_FILL
STOPBAR_ALPHA = BAND_ALPHA   # ★同じ濃淡
STOPBAR_DY = 10.0            # [m] 細帯の太さ（好みで調整）

EPS_T = 0.85                 # ★指定

GREEN_COLOR = (0.2, 0.6, 1.0)
GREEN_ALPHA = 0.18
GREEN_LW = 8

SPLIT_GAP_EXTRA = 1e-3

# =====================
# INPUT / OUTPUT
# =====================
IN_XLSX = "results0.25ver_final.xlsx"
OUT_DIR = "timespace_png0.25ver"

# =====================
# FILTER（optional）
# =====================
TARGET_ROUTE_IDS = []   # e.g. [311,312] ; [] => all
TARGET_SPEEDS = []      # e.g. [50.0]    ; [] => all
SPEED_TOL = 1e-6

# =====================
# MODEL SETTINGS（match your model）
# =====================
C = 120.0
G = {0: 0.5*C, 1: 0.6*C, 2: 0.7*C, 3: 0.5*C}
q = 0.5
h = 1.0 / q  # 2.0 s/veh

SHOW_CYCLES = 3
N_PER_CYCLE = int(round(q * G[0]))

# =====================
# split helpers
# =====================
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

# =====================
# time-space polyline (KEEP ORIGINAL SLOPE)
# =====================
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
            pts.append((t_pas, node))      # stop end (horizontal)
    return pts

def pts_to_xy(pts, X):
    tt = np.array([t for (t, n) in pts], dtype=float)
    yy = np.array([X[int(n)] for (t, n) in pts], dtype=float)
    return tt, yy

# =====================
# signal / simulation
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

# =====================
# draw helpers: red-wait thin strip (arr -> t_sig)
# =====================
def draw_redwait_strip(ax, t_left, t_right, y, dy):
    if not np.isfinite(t_left) or not np.isfinite(t_right):
        return
    if t_right <= t_left + 1e-9:
        return
    y0 = y - 0.5 * dy
    y1 = y + 0.5 * dy
    ax.fill([t_left, t_right, t_right, t_left],
            [y0, y0, y1, y1],
            facecolor=STOPBAR_COLOR,
            edgecolor="none",
            linewidth=0,
            alpha=STOPBAR_ALPHA,
            antialiased=False,
            rasterized=True,
            zorder=3)

def build_polygons_and_redwait(arr, pas, direction, X, x_offsets):
    """
    returns:
      polys: list of (N,2) arrays for PolyCollection
      strips: list of (tL,tR,node) for red-wait thin strips
    """
    if direction == "F":
        nodes_for_break = [1, 2, 3]
        nodes_for_strip = [1, 2, 3]
    else:
        nodes_for_break = [2, 1, 0]
        nodes_for_strip = [2, 1, 0]

    breaks = find_breakpoints_from_pass(pas, nodes=nodes_for_break, h=h)
    segs = segments_from_breaks(pas.shape[0], breaks)

    polys = []
    strips = []

    for (a, b) in segs:
        if b - a <= 1:
            continue

        k0 = a
        k1 = b - 1

        # polygon from first/last vehicle boundaries
        pts_lo = build_boundary_polyline(arr[k0, :], pas[k0, :], direction)
        pts_hi = build_boundary_polyline(arr[k1, :], pas[k1, :], direction)

        t_lo, y_lo = pts_to_xy(pts_lo, X)
        t_hi, y_hi = pts_to_xy(pts_hi, X)

        poly_t = np.concatenate([t_lo, t_hi[::-1]])
        poly_y = np.concatenate([y_lo, y_hi[::-1]])

        # ★white-gap killer: overlap in time
        m = len(t_lo)
        poly_t = poly_t.copy()
        poly_t[:m] -= EPS_T
        poly_t[m:] += EPS_T

        polys.append(np.column_stack([poly_t, poly_y]))

        # red-wait strips: arrival -> signal green start (NOT queue discharge)
        for node in nodes_for_strip:
            a0 = arr[k0, node]
            a1 = arr[k1, node]
            g0 = next_green_start_if_red(a0, x_offsets[node], G[node])
            g1 = next_green_start_if_red(a1, x_offsets[node], G[node])

            if (g0 > a0 + 1e-9) or (g1 > a1 + 1e-9):
                tL = min(a0, a1)
                tR = max(g0, g1)
                strips.append((tL, tR, node))

    return polys, strips

# =====================
# plot
# =====================
def plot_timespace(arr_f, pas_f, arr_b, pas_b, L01, L12, L23, x_offsets, title, out_path, t_xlim):
    X = np.array([0.0, L01, L01 + L12, L01 + L12 + L23], dtype=float)

    fig, ax = plt.subplots(figsize=(13, 7))

    # rasterize fills to avoid seam artifacts
    ax.set_rasterization_zorder(2.0)

    polys = []
    strips = []

    p, s = build_polygons_and_redwait(arr_f, pas_f, "F", X, x_offsets)
    polys += p; strips += s
    p, s = build_polygons_and_redwait(arr_b, pas_b, "B", X, x_offsets)
    polys += p; strips += s

    # platoon bands (NO EDGE)
    pc = PolyCollection(
        polys,
        closed=True,
        facecolors=BAND_FILL,
        edgecolors="none",
        linewidths=0,
        antialiaseds=False,
        alpha=BAND_ALPHA,
        rasterized=True,
        zorder=2,
    )
    ax.add_collection(pc)

    # thin red-wait strips (same shade)
    for (tL, tR, node) in strips:
        draw_redwait_strip(ax, tL, tR, X[node], STOPBAR_DY)

    # green bands
    tmin, tmax = t_xlim
    n0 = int(np.floor((tmin - C) / C)) - 1
    n1 = int(np.ceil((tmax + C) / C)) + 1
    for node in [0, 1, 2, 3]:
        y = X[node]
        for n in range(n0, n1 + 1):
            gs = x_offsets[node] + n * C
            ge = gs + G[node]
            if ge < tmin or gs > tmax:
                continue
            ax.hlines(y, gs, ge, color=GREEN_COLOR, linewidth=GREEN_LW, alpha=GREEN_ALPHA, zorder=1)

    ax.set_xlim(tmin, tmax)
    ax.set_ylim(-0.02 * X[-1], 1.02 * X[-1])
    ax.set_xlabel("time [s]")
    ax.set_ylabel("space [m]")
    ax.set_title(title)
    ax.grid(True, alpha=0.15)

    plt.tight_layout()
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    fig.savefig(out_path, dpi=220, facecolor="white")
    plt.close(fig)

# =====================
# main
# =====================
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

    t_xlim = (0.0, SHOW_CYCLES * C + max_tau_sum + 1.0 * C)
    os.makedirs(OUT_DIR, exist_ok=True)

    for idx in rows:
        r = df.loc[idx]
        rid = int(r["路線番号"])
        spd = float(r["系統速度"])
        L01 = float(r["link(0,1)"])
        L12 = float(r["link(1,2)"])
        L23 = float(r["link(2,3)"])

        x_offsets = {0: 0.0, 1: float(r["x1opt"]), 2: float(r["x2opt"]), 3: float(r["x3opt"])}

        v = spd / 3.6
        tau01 = L01 / v
        tau12 = L12 / v
        tau23 = L23 / v

        arr_f, pas_f = simulate_dir_records([tau01, tau12, tau23], x_offsets, start_node=0, cycles=SHOW_CYCLES)
        arr_b, pas_b = simulate_dir_records([tau23, tau12, tau01], x_offsets, start_node=3, cycles=SHOW_CYCLES)

        title = (
            f"Time–Space (route {rid}, v={spd:.1f} km/h)  "
            f"offsets=({x_offsets[1]:.1f},{x_offsets[2]:.1f},{x_offsets[3]:.1f})  "
            f"cycles={SHOW_CYCLES}, N/cycle={N_PER_CYCLE}"
        )
        out_path = os.path.join(
            OUT_DIR,
            f"timespace_route{rid}_v{spd:.1f}_x{x_offsets[1]:.1f}_{x_offsets[2]:.1f}_{x_offsets[3]:.1f}_cyc{SHOW_CYCLES}.png"
        )

        plot_timespace(arr_f, pas_f, arr_b, pas_b, L01, L12, L23, x_offsets, title, out_path, t_xlim)
        print("saved:", out_path)

if __name__ == "__main__":
    main()
