# -*- coding: utf-8 -*-
import numpy as np
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output

# =========================
# fixed settings
# =========================
V_MAX_KMH = 60
V_STEP_KMH = 5

C_MIN = 60
C_MAX = 150
C_STEP = 10

L_FIXED = C_MAX * (2 * V_MAX_KMH / 3.6)

N_L = 320
N_X = 220

# =========================
# helpers
# =========================
def rho(z):
    return z - np.floor(z)

def d12_norm(x, Lam, g1, g2, P):
    p = rho(Lam - x)
    gav = 0.5 * (g1 + g2)
    RD = 1.0 - 2.0 * gav + P
    out = np.zeros_like(p, dtype=float)

    mask_RD = RD > 0
    if np.isscalar(mask_RD):
        mask_RD = np.full_like(p, mask_RD, dtype=bool)

    m2 = mask_RD & ((g2 - P) <= p) & (p < g2)
    out[m2] = RD * (p[m2] - g2 + P) / P

    m3 = mask_RD & (g2 <= p) & (p < (1.0 - g1 + P))
    out[m3] = (1.0 - g1 - p[m3] + P)
    return out

def d21_norm(x, Lam, g1, g2, P):
    p = rho(Lam + x)
    gav = 0.5 * (g1 + g2)
    RD = 1.0 - 2.0 * gav + P
    out = np.zeros_like(p, dtype=float)

    mask_RD = RD > 0
    if np.isscalar(mask_RD):
        mask_RD = np.full_like(p, mask_RD, dtype=bool)

    m2 = mask_RD & ((g1 - P) <= p) & (p < g1)
    out[m2] = RD * (p[m2] - g1 + P) / P

    m3 = mask_RD & (g1 <= p) & (p < (1.0 - g2 + P))
    out[m3] = (1.0 - g2 - p[m3] + P)
    return out

def d_bidir_norm_general(x, Lam, g1, g2, P):
    return 0.5 * (d12_norm(x, Lam, g1, g2, P) + d21_norm(x, Lam, g1, g2, P))

# =========================
# Λ_hce / Λ_lce
# =========================
def hce_intervals(LamMax, g1, g2, P):
    """
    Λ_hce band: centers at N+0.5 and N+1.0, half-width δΛ=max(gav-P,0)
    returns intervals (a,b) in [0, LamMax]
    """
    gav = 0.5 * (g1 + g2)
    delta = max(gav - P, 0.0)
    if delta <= 1e-12:
        return [], delta

    intervals = []
    centers = (0.5, 1.0)
    N_min = -1
    N_max = int(np.ceil(LamMax + 1))
    for N in range(N_min, N_max + 1):
        for c in centers:
            Lam_c = N + c
            a = Lam_c - delta
            b = Lam_c + delta
            if b < 0 or a > LamMax:
                continue
            a = max(0.0, a)
            b = min(LamMax, b)
            if a < b:
                intervals.append((a, b))
    return intervals, delta

def lce_values(LamMax, g1, g2, P):
    """
    Λ_lce = N + gav - P/(2η) and +0.5, η=1-2(gav-P)
    """
    gav = 0.5 * (g1 + g2)
    eta = 1.0 - 2.0 * (gav - P)
    if abs(eta) < 1e-9:
        return [], eta

    base = gav - P / (2.0 * eta)
    N_min = int(np.floor(-base - 2))
    N_max = int(np.ceil(LamMax - base + 2))

    vals = []
    for N in range(N_min, N_max + 1):
        for add05 in (0.0, 0.5):
            Lam_lce = N + base + add05
            if 0.0 < Lam_lce <= LamMax:
                vals.append(float(Lam_lce))
    return sorted(set(vals)), eta

# =========================
# figure generator
# =========================
def make_figure(V_kmh: int, L0: float, C: float, g1: float, g2: float, P: float, LamMax: float) -> go.Figure:
    V = V_kmh / 3.6
    L_axis_max = float(L_FIXED)

    L_vals = np.linspace(0.0, L_axis_max, N_L)
    x_vals = np.linspace(0.0, 1.0, N_X)
    X, Lm = np.meshgrid(x_vals, L_vals)

    Lam = Lm / (C * V)
    Z = d_bidir_norm_general(X, Lam, g1, g2, P).astype(float)

    # slice
    L0 = float(np.clip(L0, 0.0, L_axis_max))
    Lam0 = L0 / (C * V)
    Z_line = d_bidir_norm_general(x_vals, Lam0, g1, g2, P)

    # hce / lce
    hce_ints, delta = hce_intervals(LamMax, g1, g2, P)
    lce_lams, eta = lce_values(LamMax, g1, g2, P)

    fig = go.Figure()

    # ---- (1) Λ_hce floor fill (z<0), not in legend ----
    z_floor = -0.03
    if delta > 0 and hce_ints:
        mask = np.zeros_like(Lam, dtype=bool)
        for a, b in hce_ints:
            mask |= (a <= Lam) & (Lam <= b)

        fig.add_trace(
            go.Surface(
                x=Lm, y=X, z=np.full_like(Z, z_floor, dtype=float),
                surfacecolor=mask.astype(float),
                cmin=0, cmax=1,
                colorscale=[(0.0, "rgba(0,0,0,0)"), (1.0, "rgba(255,215,0,0.95)")],
                showscale=False,
                opacity=1.0,
                hoverinfo="skip",
                showlegend=False,
                lighting=dict(ambient=1.0, diffuse=0.0, specular=0.0),
            )
        )

    # Legend proxy (clear swatch)
    fig.add_trace(
        go.Scatter3d(
            x=[0, 1], y=[0, 0], z=[z_floor, z_floor],
            mode="lines",
            line=dict(color="rgba(255,215,0,0.95)", width=10),
            name="Λ_hce",
            visible="legendonly",
            showlegend=True,
            hoverinfo="skip",
        )
    )

    # ---- (2) main delay surface ----
    fig.add_trace(
        go.Surface(
            x=Lm, y=X, z=Z,
            customdata=Lam,
            hovertemplate=(
                "L=%{x:.0f} m<br>"
                "x=%{y:.2f}<br>"
                f"V={V_kmh:d} km/h<br>"
                f"C={C:.0f} s<br>"
                f"g1={g1:.2f}, g2={g2:.2f}, P={P:.2f}<br>"
                f"deltaLambda={delta:.2f}, eta={eta:.2f}<br>"
                "Lambda=%{customdata:.2f}<br>"
                "d/C=%{z:.3f}<extra></extra>"
            ),
            colorscale="Viridis",
            opacity=0.92,
            colorbar=dict(title="d/C", x=1.06, y=0.55, len=0.75, thickness=18),
            showlegend=False,
        )
    )

    # ---- (3) integer Λ lines (red dotted), single trace ----
    xL, yL, zL = [], [], []
    for k in range(1, int(LamMax) + 1):
        Lk = k * C * V
        xL += [Lk, Lk, None]
        yL += [0.0, 1.0, None]
        zL += [0.0, 0.0, None]
    fig.add_trace(
        go.Scatter3d(
            x=xL, y=yL, z=zL,
            mode="lines",
            line=dict(color="rgba(255,0,0,0.95)", width=5, dash="dot"),
            name="Λ=1,2,3,...",
            showlegend=True,
            hoverinfo="skip",
        )
    )

    # ---- (4) Λ_lce lines: blue dotted, z=0 fixed ----
    xC, yC, zC = [], [], []
    for lam in lce_lams:
        Lk = lam * C * V
        xC += [Lk, Lk, None]
        yC += [0.0, 1.0, None]
        zC += [0.0, 0.0, None]
    fig.add_trace(
        go.Scatter3d(
            x=xC, y=yC, z=zC,
            mode="lines",
            line=dict(color="rgba(0,90,255,0.95)", width=5, dash="dot"),
            name="Λ_lce",
            showlegend=True,
            hoverinfo="skip",
        )
    )

    # ---- (5) L slice ----
    fig.add_trace(
        go.Scatter3d(
            x=np.full_like(x_vals, L0),
            y=x_vals,
            z=Z_line,
            mode="lines",
            line=dict(color="black", width=6),
            name="L slice",
            showlegend=True,
            hoverinfo="skip",
        )
    )

    # ---- layout: NO axis titles, NO annotations ----
    fig.update_layout(
        title=dict(text="", x=0.0),
        scene=dict(
            xaxis=dict(title=dict(text=""), tickfont=dict(size=16), range=[0, L_axis_max]),
            yaxis=dict(title=dict(text=""), tickfont=dict(size=16), range=[0.0, 1.0]),
            zaxis=dict(title=dict(text=""), tickfont=dict(size=16), range=[-0.06, 0.6]),
            aspectmode="manual",
            aspectratio=dict(x=2.4, y=1.0, z=0.7),
        ),
        legend=dict(
            orientation="h",
            x=0.0, y=-0.18,
            xanchor="left", yanchor="top",
            bgcolor="rgba(255,255,255,0.90)",
            bordercolor="rgba(0,0,0,0.25)",
            borderwidth=1,
            font=dict(size=22),
        ),
        uirevision="keep-camera",
        margin=dict(l=40, r=240, t=30, b=130),
    )
    return fig

# =========================
# Dash app
# =========================
app = Dash(__name__)

app.layout = html.Div(
    style={"maxWidth": "1100px", "margin": "0 auto", "fontFamily": "sans-serif"},
    children=[
        dcc.Graph(id="graph", style={"height": "740px"}, config={"scrollZoom": True}),

        html.Div(style={"display": "grid", "gap": "12px"}, children=[
            html.Div([
                html.Div("Speed V [km/h]"),
                dcc.Slider(
                    id="V-slider",
                    min=10, max=V_MAX_KMH, step=V_STEP_KMH, value=V_MAX_KMH,
                    marks={v: str(v) for v in range(10, V_MAX_KMH + 1, 10)},
                    tooltip={"placement": "bottom", "always_visible": True},
                ),
            ]),
            html.Div([
                html.Div("Cycle length C [s]"),
                dcc.Slider(
                    id="C-slider",
                    min=C_MIN, max=C_MAX, step=C_STEP, value=90,
                    marks={c: str(c) for c in range(C_MIN, C_MAX + 1, 30)},
                    tooltip={"placement": "bottom", "always_visible": True},
                ),
            ]),
            html.Div([
                html.Div("Link length L slice [m] (0 … fixed)"),
                dcc.Slider(
                    id="L-slider",
                    min=0, max=L_FIXED, step=10, value=0,
                    tooltip={"placement": "bottom", "always_visible": True},
                ),
            ]),
            html.Div([
                html.Div("Demand ratio P (0 < P ≤ g1)"),
                dcc.Slider(
                    id="P-slider",
                    min=0.05, max=0.90, step=0.05, value=0.50,
                    marks={0.1: "0.1", 0.3: "0.3", 0.5: "0.5", 0.7: "0.7", 0.9: "0.9"},
                    tooltip={"placement": "bottom", "always_visible": True},
                ),
            ]),
            html.Div([
                html.Div("Green split g1 (P ≤ g1 ≤ g2)"),
                dcc.Slider(
                    id="g1-slider",
                    min=0.05, max=0.95, step=0.05, value=0.50,
                    marks={0.1: "0.1", 0.3: "0.3", 0.5: "0.5", 0.7: "0.7", 0.9: "0.9"},
                    tooltip={"placement": "bottom", "always_visible": True},
                ),
            ]),
            html.Div([
                html.Div("Green split g2 (g1 ≤ g2)"),
                dcc.Slider(
                    id="g2-slider",
                    min=0.05, max=0.95, step=0.05, value=0.50,
                    marks={0.1: "0.1", 0.3: "0.3", 0.5: "0.5", 0.7: "0.7", 0.9: "0.9"},
                    tooltip={"placement": "bottom", "always_visible": True},
                ),
            ]),
            html.Div([
                html.Div("Max Λ to display"),
                dcc.Slider(
                    id="LamMax-slider",
                    min=1, max=20, step=1, value=6,
                    marks={1: "1", 5: "5", 10: "10", 15: "15", 20: "20"},
                    tooltip={"placement": "bottom", "always_visible": True},
                ),
            ]),
        ]),
    ],
)

@app.callback(
    Output("graph", "figure"),
    Input("V-slider", "value"),
    Input("C-slider", "value"),
    Input("L-slider", "value"),
    Input("P-slider", "value"),
    Input("g1-slider", "value"),
    Input("g2-slider", "value"),
    Input("LamMax-slider", "value"),
)
def update(V_kmh, C, L0, P, g1, g2, LamMax):
    fig = make_figure(
        V_kmh=int(V_kmh),
        L0=float(L0),
        C=float(C),
        g1=float(g1),
        g2=float(g2),
        P=float(P),
        LamMax=float(LamMax),
    )
    return fig

if __name__ == "__main__":
    app.run_server(debug=True)
