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
L_FIXED = C_MAX * (2*V_MAX_KMH / 3.6)  # いまの最大(Λ=1)を基準に固定レンジにする例
# もっと広くしたいなら例えば:
# L_FIXED = 6000  # [m] 好きな固定値でもOK

# grid resolution
N_L = 320
N_X = 220

# =========================
# math helpers
# =========================
def rho(z):
    """fractional part in [0,1)"""
    return z - np.floor(z)

def clamp01(x):
    return float(np.clip(x, 0.0, 1.0))

# =========================
# delay model (general case: P <= g1 <= g2)
# returns normalized delay d/C
# =========================
def d12_norm(x, Lam, g1, g2, P):
    """
    1->2 direction, normalized d12/C
    based on eq (3.4.2) with p'12s(x)=rho(Lam-x)
    """
    p = rho(Lam - x)

    # RD = 1 - 2*gav + P, gav=(g1+g2)/2
    gav = 0.5 * (g1 + g2)
    RD = 1.0 - 2.0 * gav + P

    # default 0
    out = np.zeros_like(p, dtype=float)

    # if RD <= 0 => 0 for all x
    mask_RD = RD > 0
    if np.isscalar(mask_RD):
        mask_RD = np.full_like(p, mask_RD, dtype=bool)

    # piecewise for RD > 0
    m1 = mask_RD & (0.0 <= p) & (p < (g2 - P))
    # out already 0

    m2 = mask_RD & ((g2 - P) <= p) & (p < g2)
    out[m2] = RD * (p[m2] - g2 + P) / P

    m3 = mask_RD & (g2 <= p) & (p < (1.0 - g1 + P))
    out[m3] = (1.0 - g1 - p[m3] + P)

    m4 = mask_RD & ((1.0 - g1 + P) <= p) & (p < 1.0)
    # out already 0

    return out

def d21_norm(x, Lam, g1, g2, P):
    """
    2->1 direction, normalized d21/C
    based on eq (3.4.7) with p'21s(x)=rho(Lam+x)
    """
    p = rho(Lam + x)

    gav = 0.5 * (g1 + g2)
    RD = 1.0 - 2.0 * gav + P

    out = np.zeros_like(p, dtype=float)

    mask_RD = RD > 0
    if np.isscalar(mask_RD):
        mask_RD = np.full_like(p, mask_RD, dtype=bool)

    m1 = mask_RD & (0.0 <= p) & (p < (g1 - P))
    # out already 0

    m2 = mask_RD & ((g1 - P) <= p) & (p < g1)
    out[m2] = RD * (p[m2] - g1 + P) / P

    m3 = mask_RD & (g1 <= p) & (p < (1.0 - g2 + P))
    out[m3] = (1.0 - g2 - p[m3] + P)

    m4 = mask_RD & ((1.0 - g2 + P) <= p) & (p < 1.0)
    # out already 0

    return out

def d_bidir_norm_general(x, Lam, g1, g2, P):
    """normalized bidirectional delay d/C = (d12 + d21)/2"""
    return 0.5 * (d12_norm(x, Lam, g1, g2, P) + d21_norm(x, Lam, g1, g2, P))

# =========================
# figure generator
# =========================
def make_figure(V_kmh: int, L0: float, C: float, g1: float, g2: float, P: float, LamMax: float) -> go.Figure:
    V = V_kmh / 3.6
    L_axis_max = L_FIXED
    L_vals = np.linspace(0.0, L_axis_max, N_L)
    x_vals = np.linspace(0.0, 1.0, N_X)
    X, Lm = np.meshgrid(x_vals, L_vals)

    Lam = Lm / (C * V)

    Z = d_bidir_norm_general(X, Lam, g1, g2, P).astype(float)
    #Z[Lam > 1.0] = np.nan  # one-cycle only

    # Λ = 1 boundary
    L_lambda1 = C * V

    # L slice (clip)
    L0 = float(np.clip(L0, 0.0, L_lambda1))
    Lam0 = L0 / (C * V)
    Z_line = d_bidir_norm_general(x_vals, Lam0, g1, g2, P)

    # RD (for info)
    gav = 0.5 * (g1 + g2)
    RD = 1.0 - 2.0 * gav + P

    fig = go.Figure()

    fig.add_trace(
        go.Surface(
            x=Lm,
            y=X,
            z=Z,
            customdata=Lam,
            hovertemplate=(
                "L = %{x:.0f} m<br>"
                "x = %{y:.2f}<br>"
                f"V = {V_kmh:d} km/h<br>"
                f"C = {C:.0f} s<br>"
                f"g(1) = {g1:.2f}, g(2) = {g2:.2f}, P = {P:.2f}<br>"
                f"RD = {RD:.2f}<br>"
                "Λ = %{customdata:.2f}<br>"
                "d/C = %{z:.3f}<extra></extra>"
            ),
            colorscale="Viridis",
            opacity=0.92,
            colorbar=dict(title="d/C"),
        )
    )
    # --- Recommended: Λ = k guide lines within fixed L range ---
    period = C * V  # = C·V
    kmax = int(np.floor(L_FIXED / period))

    for k in range(1, kmax + 1):
        Lk = k * period
        fig.add_trace(
            go.Scatter3d(
                x=[Lk, Lk],
                y=[0, 1],
                z=[0, 0],
                mode="lines",
                line=dict(width=3, dash="dash"),
                name=f"Λ={k}",
                showlegend=(k == 1),
                hovertemplate=(
                    f"Λ = {k}<br>L = {Lk:.0f} m<br>"
                    f"V = {V_kmh:d} km/h<br>C = {C:.0f} s<extra></extra>"
                ),
            )
        )
    # --- end guide lines ---

    # Λ = 1 guide line
    fig.add_trace(
        go.Scatter3d(
            x=[L_lambda1, L_lambda1],
            y=[0, 1],
            z=[0, 0],
            mode="lines",
            line=dict(color="red", width=6, dash="dash"),
            name="Λ = 1 (L = C·V)",
            hovertemplate=(
                f"Λ = 1<br>L = {L_lambda1:.0f} m<br>"
                f"V = {V_kmh:d} km/h<br>C = {C:.0f} s<extra></extra>"
            ),
        )
    )
    # Λ = k guide lines (k = 1..LamMax)
    for k in range(1, int(LamMax) + 1):
        Lk = k * C * V
        fig.add_trace(
            go.Scatter3d(
                x=[Lk, Lk],
                y=[0, 1],
                z=[0, 0],
                mode="lines",
                line=dict(color="red", width=4, dash="dash") if k == 1 else dict(color="gray", width=2, dash="dash"),
                name=f"Λ = {k}",
                showlegend=(k == 1),  # 凡例は1本だけ（邪魔なら）
                hovertemplate=(
                    f"Λ = {k}<br>L = {Lk:.0f} m<br>"
                    f"V = {V_kmh:d} km/h<br>C = {C:.0f} s<extra></extra>"
                ),
            )
        )

    # L slice line
    fig.add_trace(
        go.Scatter3d(
            x=np.full_like(x_vals, L0),
            y=x_vals,
            z=Z_line,
            mode="lines",
            line=dict(color="black", width=6),
            name="L slice",
            hovertemplate=(
                f"L = {L0:.0f} m<br>"
                "x = %{y:.2f}<br>"
                f"V = {V_kmh:d} km/h<br>"
                f"C = {C:.0f} s<br>"
                f"g(1) = {g1:.2f}, g(2) = {g2:.2f}, P = {P:.2f}<br>"
                f"RD = {RD:.2f}<br>"
                f"Λ = {Lam0:.2f}<br>"
                "d/C = %{z:.3f}<extra></extra>"
            ),
        )
    )

    # z-range: general case can exceed 0.5 depending on parameters; keep a safe upper bound
    fig.update_layout(
        title=(
            "Delay surface d(x, L) (Λ ≤ 1)  |  "
            f"V = {V_kmh:d} km/h,  C = {C:.0f} s,  "
            f"g(1)={g1:.2f}, g(2)={g2:.2f}, P={P:.2f},  "
            f"L slice = {L0:.0f} m"
        ),
        scene=dict(
            xaxis=dict(title="Link length L [m]", range=[0, L_axis_max]),
            yaxis=dict(title="Offset x (cycle fraction)", range=[0, 1]),
            zaxis=dict(title="Normalized delay d/C", range=[0, 0.6]),
            aspectmode="manual",
            aspectratio=dict(x=2.4, y=1.0, z=0.7),
        ),
        uirevision="keep-camera",
        margin=dict(l=0, r=0, t=60, b=0),
    )

    return fig

# =========================
# Dash app
# =========================
app = Dash(__name__)

app.layout = html.Div(
    style={"maxWidth": "1100px", "margin": "0 auto", "fontFamily": "sans-serif"},
    children=[
        html.H3("3D Delay surface d(x, L) (general case: P ≤ g(1) ≤ g(2), Λ ≤ 1)"),

        dcc.Graph(
            id="graph",
            style={"height": "720px"},
            config={"scrollZoom": True},
        ),

        html.Div(style={"display": "grid", "gap": "12px"}, children=[

            html.Div([
                html.Div("Speed V [km/h]"),
                dcc.Slider(
                    id="V-slider",
                    min=10,
                    max=V_MAX_KMH,
                    step=V_STEP_KMH,
                    value=V_MAX_KMH,
                    marks={v: str(v) for v in range(10, V_MAX_KMH + 1, 10)},
                    tooltip={"placement": "bottom", "always_visible": True},
                ),
            ]),

            html.Div([
                html.Div("Cycle length C [s]"),
                dcc.Slider(
                    id="C-slider",
                    min=C_MIN,
                    max=C_MAX,
                    step=C_STEP,
                    value=90,
                    marks={c: str(c) for c in range(C_MIN, C_MAX + 1, 30)},
                    tooltip={"placement": "bottom", "always_visible": True},
                ),
            ]),

            html.Div([
                html.Div(id="L-label"),
                dcc.Slider(
                    id="L-slider",
                    min=0,
                    max=L_FIXED,
                    step=10,
                    value=0,
                    tooltip={"placement": "bottom", "always_visible": True},
                ),
            ]),

            html.Div([
                html.Div("Demand ratio P (0 < P ≤ g(1))"),
                dcc.Slider(
                    id="P-slider",
                    min=0.05,
                    max=0.90,
                    step=0.05,
                    value=0.50,
                    marks={0.1: "0.1", 0.3: "0.3", 0.5: "0.5", 0.7: "0.7", 0.9: "0.9"},
                    tooltip={"placement": "bottom", "always_visible": True},
                ),
            ]),

            html.Div([
                html.Div("Green split g(1) (P ≤ g(1) ≤ g(2))"),
                dcc.Slider(
                    id="g1-slider",
                    min=0.05,
                    max=0.95,
                    step=0.05,
                    value=0.50,
                    marks={0.1: "0.1", 0.3: "0.3", 0.5: "0.5", 0.7: "0.7", 0.9: "0.9"},
                    tooltip={"placement": "bottom", "always_visible": True},
                ),
            ]),

            html.Div([
                html.Div("Green split g(2) (g(1) ≤ g(2))"),
                dcc.Slider(
                    id="g2-slider",
                    min=0.05,
                    max=0.95,
                    step=0.05,
                    value=0.50,
                    marks={0.1: "0.1", 0.3: "0.3", 0.5: "0.5", 0.7: "0.7", 0.9: "0.9"},
                    tooltip={"placement": "bottom", "always_visible": True},
                ),
            ]),

            html.Div([
                html.Div("Max Λ to display"),
                dcc.Slider(
                    id="LamMax-slider",
                    min=1,
                    max=20,
                    step=1,
                    value=6,
                    marks={1:"1",5:"5",10:"10",15:"15",20:"20"},
                    tooltip={"placement": "bottom", "always_visible": True},
                ),
            ]),


        ]),
    ],
)

@app.callback(
    Output("graph", "figure"),
    Output("L-slider", "value"),
    Output("L-label", "children"),
    Input("V-slider", "value"),
    Input("C-slider", "value"),
    Input("L-slider", "value"),
    Input("P-slider", "value"),
    Input("g1-slider", "value"),
    Input("g2-slider", "value"),
    Input("LamMax-slider", "value"),
)
def update(V_kmh, C, L0, P, g1, g2, LamMax):
    V = V_kmh / 3.6
    L_max = float(LamMax * C * V)   # ← ここが肝
    L0 = float(np.clip(L0, 0.0, L_FIXED))
    label = f"Link length L slice [m] (0 … {L_FIXED:.0f} fixed)"
    fig = make_figure(V_kmh=int(V_kmh), L0=L0, C=float(C), g1=float(g1), g2=float(g2), P=float(P), LamMax=float(LamMax))
    return fig, L0, label


if __name__ == "__main__":
    app.run_server(debug=True)
