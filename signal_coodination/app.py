# -*- coding: utf-8 -*-
import numpy as np
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output

# =========================
# fixed settings
# =========================
V_MAX_KMH = 80
V_STEP_KMH = 5

C_MIN = 60
C_MAX = 150
C_STEP = 10

# grid resolution
N_L = 320
N_X = 220

# =========================
# delay model (P = g1 = g2 = 0.5)
# =========================
def rho(z):
    return z - np.floor(z)

def d_one_norm(p):
    p = p % 1.0
    return np.where(p < 0.5, p, 1.0 - p)

def d_bidir_norm(x, Lam):
    return 0.5 * (
        d_one_norm(rho(Lam - x)) +
        d_one_norm(rho(Lam + x))
    )

# =========================
# figure generator
# =========================
def make_figure(V_kmh: int, L0: float, C: float) -> go.Figure:
    V = V_kmh / 3.6

    # L-axis fixed by (Vmax, Cmax) for visual consistency
    L_axis_max = C_MAX * (V_MAX_KMH / 3.6)

    L_vals = np.linspace(0.0, L_axis_max, N_L)
    x_vals = np.linspace(0.0, 1.0, N_X)
    X, Lm = np.meshgrid(x_vals, L_vals)

    Lam = Lm / (C * V)
    Z = d_bidir_norm(X, Lam)
    Z = Z.astype(float)
    Z[Lam > 1.0] = np.nan   # one-cycle only

    # Λ = 1 boundary
    L_lambda1 = C * V

    # L slice (clip)
    L0 = float(np.clip(L0, 0.0, L_lambda1))
    Lam0 = L0 / (C * V)
    Z_line = d_bidir_norm(x_vals, Lam0)

    fig = go.Figure()

    # ---- surface (ONLY ONE) ----
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
                "Λ = %{customdata:.2f}<br>"
                "d/C = %{z:.3f}<extra></extra>"
            ),
            colorscale="Viridis",
            opacity=0.92,
            colorbar=dict(title="d/C"),
        )
    )

    # ---- Λ = 1 guide line ----
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

    # ---- L slice line ----
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
                f"Λ = {Lam0:.2f}<br>"
                "d/C = %{z:.3f}<extra></extra>"
            ),
        )
    )

    fig.update_layout(
        title=(
            "Delay surface d(x, L) (Λ ≤ 1)  |  "
            f"V = {V_kmh:d} km/h,  C = {C:.0f} s,  "
            f"L slice = {L0:.0f} m"
        ),
        scene=dict(
            xaxis=dict(title="Link length L [m]", range=[0, L_axis_max]),
            yaxis=dict(title="Offset x (cycle fraction)", range=[0, 1]),
            zaxis=dict(title="Normalized delay d/C", range=[0, 0.5]),
            aspectmode="manual",
            aspectratio=dict(x=2.4, y=1.0, z=0.7),
        ),
        uirevision="keep-camera",   # ★ 視点を保持 ★
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
        html.H3("Final 3D UI: speed–cycle–length interaction (one-cycle view)"),

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
                    max=1,
                    step=10,
                    value=0,
                    tooltip={"placement": "bottom", "always_visible": True},
                ),
            ]),
        ]),
    ],
)

@app.callback(
    Output("graph", "figure"),
    Output("L-slider", "max"),
    Output("L-slider", "value"),
    Output("L-label", "children"),
    Input("V-slider", "value"),
    Input("C-slider", "value"),
    Input("L-slider", "value"),
)
def update(V_kmh, C, L0):
    V = V_kmh / 3.6
    L_max_current = C * V   # Λ = 1 boundary

    if L0 is None:
        L0 = 0.0
    L0 = float(np.clip(L0, 0.0, L_max_current))

    fig = make_figure(int(V_kmh), L0, float(C))
    label = f"L slice [m]  (max = C·V = {L_max_current:.0f} m)"

    return fig, float(L_max_current), L0, label

# =========================
# run
# =========================
if __name__ == "__main__":
    app.run_server(debug=False, use_reloader=False)
