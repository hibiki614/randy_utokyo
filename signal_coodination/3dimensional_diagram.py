import numpy as np
import plotly.graph_objects as go

# =========================
# Parameters
# =========================
P = g1 = g2 = 0.5

# =========================
# Delay functions (paper-consistent simplified form)
# =========================
def rho(z):
    return z - np.floor(z)

def d_one_norm(p):
    p = p % 1.0
    return np.where(p < 0.5, p, 1.0 - p)

def d_bidir_norm(x, Lam):
    p12 = rho(Lam - x)
    p21 = rho(Lam + x)
    return 0.5 * (d_one_norm(p12) + d_one_norm(p21))

# =========================
# Grid
# =========================
x_vals = np.linspace(0, 1, 200)
Lam_vals = np.linspace(0.0, 2.0, 120)

X, LAM = np.meshgrid(x_vals, Lam_vals)
Z = d_bidir_norm(X, LAM)

# =========================
# Figure
# =========================
fig = go.Figure()

# --- Surface ---
fig.add_trace(
    go.Surface(
        x=X,
        y=LAM,
        z=Z,
        colorscale="Viridis",
        opacity=0.85,
        colorbar=dict(title="d/C"),
        name="surface"
    )
)

# --- Λ slices (x-direction curves) ---
for Lam in Lam_vals:
    fig.add_trace(
        go.Scatter3d(
            x=x_vals,
            y=np.full_like(x_vals, Lam),
            z=d_bidir_norm(x_vals, Lam),
            mode="lines",
            line=dict(color="red", width=6),
            visible=False,
            name="Lambda slice"
        )
    )

# --- x slices (Λ-direction curves) ---
for x0 in x_vals:
    fig.add_trace(
        go.Scatter3d(
            x=np.full_like(Lam_vals, x0),
            y=Lam_vals,
            z=d_bidir_norm(x0, Lam_vals),
            mode="lines",
            line=dict(color="blue", width=6),
            visible=False,
            name="x slice"
        )
    )

# 初期表示
fig.data[1].visible = True   # first Λ-slice
fig.data[1 + len(Lam_vals)].visible = True  # first x-slice

# =========================
# Λ slider
# =========================
lambda_steps = []
for i, Lam in enumerate(Lam_vals):
    vis = [True] + \
          [j == i for j in range(len(Lam_vals))] + \
          [False] * len(x_vals)
    lambda_steps.append(dict(
        method="update",
        args=[{"visible": vis},
              {"title": f"Λ-slice at Λ = {Lam:.2f}"}]
    ))

# =========================
# x slider
# =========================
x_steps = []
for i, x0 in enumerate(x_vals):
    vis = [True] + \
          [False] * len(Lam_vals) + \
          [j == i for j in range(len(x_vals))]
    x_steps.append(dict(
        method="update",
        args=[{"visible": vis},
              {"title": f"x-slice at x = {x0:.2f}"}]
    ))

# =========================
# Layout
# =========================
fig.update_layout(
    title="Interactive Fig.12-style surface with Λ-slice and x-slice",
    scene=dict(
        xaxis_title="offset x",
        yaxis_title="Λ = L/(CV)",
        zaxis_title="normalized delay d/C",
    ),
    sliders=[
        dict(
            active=0,
            currentvalue={"prefix": "Λ = "},
            steps=lambda_steps,
            y=0.05
        ),
        dict(
            active=0,
            currentvalue={"prefix": "x = "},
            steps=x_steps,
            y=0.0
        )
    ]
)

# =========================
# Show & save
# =========================
fig.show()
fig.write_html("fig12_interactive_Lambda_x.html")
print("Saved: fig12_interactive_Lambda_x.html")
