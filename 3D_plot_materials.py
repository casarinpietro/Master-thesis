import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.interpolate import griddata

# -------------------------
# Load data
# -------------------------
file_path = "Charts_by_Tech_Storage.xlsx"
xls = pd.ExcelFile(file_path)
tech_list = xls.sheet_names[:12] 

rows, cols = 4, 3

fig = make_subplots(
    rows=rows, cols=cols,
    subplot_titles=[f"<b>{t}</b>" for t in tech_list],
    specs=[[{'type': 'surface'}] * cols] * rows,
    vertical_spacing=0.04,
    horizontal_spacing=0.02
)

# -------------------------
# UI & Style Constants
# -------------------------
LABEL_FONT_SIZE = 10
TITLE_FONT_SIZE = 13
TICK_FONT_SIZE = 9
NZE_COLOR = 'rgba(255, 65, 54, 0.4)'
CSD_COLOR = 'rgba(0, 116, 217, 0.4)'

# FIXED NORMALIZATION BASE: +E5 (100,000)
FIXED_EXPONENT = 5
SCALE_FACTOR = 10**FIXED_EXPONENT

for i, tech in enumerate(tech_list):
    df = pd.read_excel(xls, sheet_name=tech)
    r, c = (i // cols) + 1, (i % cols) + 1

    ref_df = df[df["Scenario"].isin(["NZE", "CSD"])]
    main_df = df[~df["Scenario"].isin(["NZE", "CSD"])].dropna(subset=["Probability"])

    scenario_order = sorted(main_df["Scenario"].unique())
    scenario_codes = {s: j for j, s in enumerate(scenario_order)}
    main_df["Scenario_code"] = main_df["Scenario"].map(scenario_codes)

    x, y = main_df["Scenario_code"].values, main_df["Probability"].values
    
    # Normalize Z by 10^5
    z_scaled = main_df["Material consumption"].values / SCALE_FACTOR

    # --- UPDATED: Range Logic with 10% Padding ---
    # Calculate the raw maximum from all data points (including references)
    raw_max = df["Material consumption"].max() / SCALE_FACTOR
    # Set the ceiling to be 1.1x the data max, but at least 1.1 (to keep E5 scale visible)
    axis_ceiling = max(raw_max * 1.1, 1.1)

    unique_probs = sorted(main_df["Probability"].unique())

    xi = np.linspace(x.min(), x.max(), 40)
    yi = np.linspace(y.min(), y.max(), 40)
    Xi, Yi = np.meshgrid(xi, yi)
    Zi = griddata((x, y), z_scaled, (Xi, Yi), method="cubic")

    # Add Main Surface
    fig.add_trace(
        go.Surface(
            x=xi, y=yi, z=Zi,
            colorscale="Viridis",
            showscale=False,
            name="Distribution",
            hovertemplate="Scen: %{x}<br>Prob: %{y}<br>Cons: %{z:.2f} (E5)<extra></extra>"
        ),
        row=r, col=c
    )

    # Add NZE and CSD Reference Planes
    for ref_name, ref_color in [("NZE", NZE_COLOR), ("CSD", CSD_COLOR)]:
        val = ref_df[ref_df["Scenario"] == ref_name]["Material consumption"]
        if not val.empty:
            z_val_scaled = val.values[0] / SCALE_FACTOR
            show_legend = True if i == 0 else False
            
            fig.add_trace(
                go.Surface(
                    x=xi, y=yi, 
                    z=np.full_like(Xi, z_val_scaled),
                    colorscale=[[0, ref_color], [1, ref_color]],
                    showscale=False,
                    name=ref_name,
                    showlegend=show_legend,
                    opacity=0.6,
                    hoverinfo="skip"
                ),
                row=r, col=c
            )

    # Subplot Scene Styling
    fig.update_scenes(
        dict(
            xaxis=dict(
                title="Scenario", tickvals=list(scenario_codes.values()), ticktext=list(scenario_codes.keys()),
                titlefont=dict(size=LABEL_FONT_SIZE), tickfont=dict(size=TICK_FONT_SIZE)
            ),
            yaxis=dict(
                title="Prob.", tickvals=unique_probs,
                titlefont=dict(size=LABEL_FONT_SIZE), tickfont=dict(size=TICK_FONT_SIZE)
            ),
            zaxis=dict(
                title=f"Cons. (+E{FIXED_EXPONENT} kt)", 
                tickformat=".1f",
                exponentformat="none",
                # RANGE: From 0 to our padded ceiling
                range=[0, axis_ceiling],
                titlefont=dict(size=LABEL_FONT_SIZE), 
                tickfont=dict(size=TICK_FONT_SIZE)
            ),
            camera=dict(eye=dict(x=1.5, y=1.5, z=1.2))
        ),
        row=r, col=c
    )

# -------------------------
# Layout & Global Legend
# -------------------------
fig.update_layout(
    title=dict(
        text="Material Consumption Storage sector (2010-2050)",
        x=0.5, y=0.98, font=dict(size=20)
    ),
    width=1200,
    height=1500,
    margin=dict(l=30, r=30, b=30, t=100),
    font=dict(family="Arial, sans-serif"),
    showlegend=True,
    legend=dict(
        title="<b>Reference Scenarios</b>",
        yanchor="top", y=0.97, xanchor="right", x=0.99,
        bgcolor="rgba(255, 255, 255, 0.7)", bordercolor="Black", borderwidth=1
    )
)

for annotation in fig['layout']['annotations']:
    annotation['font'] = dict(size=TITLE_FONT_SIZE)
    annotation['y'] = annotation['y'] + 0.02

fig.show()