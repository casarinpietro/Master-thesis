import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.interpolate import griddata

# -------------------------
# Load data
# -------------------------
file_path = "Emissions_charts.xlsx"
df_all = pd.read_excel(file_path)

# Identify year columns
year_cols = [2010, 2020, 2030, 2040, 2050]
actual_year_cols = [c for c in df_all.columns if str(c) in [str(y) for y in year_cols]]

# Extract exact unique probability values
unique_probs = sorted(df_all["Probability"].dropna().unique())

# --- GLOBAL SCALING LOGIC ---
raw_max = df_all[actual_year_cols].max().max()
fixed_exponent = int(np.floor(np.log10(abs(raw_max)))) if raw_max != 0 else 0
scale_factor = 10**fixed_exponent

# Identify Reference vs Main Scenarios
REF_NZE = "Net0_simplified"
REF_CSD = "CSD_S1S1S1"

main_scenarios = [s for s in df_all["Scenario"].unique() if s not in [REF_NZE, REF_CSD]][:9]

rows, cols = 3, 3
fig = make_subplots(
    rows=rows, cols=cols,
    subplot_titles=[f"<b>{s}</b>" for s in main_scenarios],
    specs=[[{'type': 'surface'}] * cols] * rows,
    vertical_spacing=0.08,
    horizontal_spacing=0.05
)

# UI Constants
LABEL_FONT_SIZE = 10
TITLE_FONT_SIZE = 14
TICK_FONT_SIZE = 9
NZE_COLOR = 'rgba(255, 65, 54, 0.4)' 
CSD_COLOR = 'rgba(0, 116, 217, 0.4)' 

for i, scen in enumerate(main_scenarios):
    r, c = (i // cols) + 1, (i % cols) + 1
    
    # 1. Process Main Scenario Data
    scen_df = df_all[df_all["Scenario"] == scen].copy()
    if scen_df.empty: continue

    scen_long = scen_df.melt(
        id_vars=["Scenario", "Probability"], 
        value_vars=actual_year_cols,
        var_name="Year", value_name="Emissions"
    ).dropna(subset=["Probability", "Emissions"])

    if scen_long.empty or len(scen_long) < 4: continue

    scen_long["Year"] = pd.to_numeric(scen_long["Year"])
    x_data = scen_long["Probability"].values
    y_data = scen_long["Year"].values
    z_data = scen_long["Emissions"].values / scale_factor

    # Create Interpolation Grid
    xi = np.linspace(min(unique_probs), max(unique_probs), 40)
    yi = np.linspace(y_data.min(), y_data.max(), 40)
    Xi, Yi = np.meshgrid(xi, yi)
    Zi = griddata((x_data, y_data), z_data, (Xi, Yi), method="cubic")

    # Add Main Scenario Surface
    fig.add_trace(
        go.Surface(
            x=Xi, y=Yi, z=Zi,
            colorscale="Viridis", showscale=False,
            name=f"{scen}",
            hovertemplate="Prob: %{x:.0f}<br>Year: %{y}<br>Emiss: %{z:.2f}<extra></extra>"
        ),
        row=r, col=c
    )

    # 2. Overlay NZE and CSD Reference Ribbons
    for ref_label, ref_name, ref_color in [("NZE Ref", REF_NZE, NZE_COLOR), ("CSD Ref", REF_CSD, CSD_COLOR)]:
        ref_data = df_all[df_all["Scenario"] == ref_name]
        if not ref_data.empty:
            ref_row = ref_data.iloc[0]
            z_vals = [ref_row[yc] / scale_factor for yc in actual_year_cols]
            years_numeric = [int(yc) for yc in actual_year_cols]
            
            z_ref_curve = np.interp(yi, years_numeric, z_vals)
            Z_ribbon = np.tile(z_ref_curve, (len(xi), 1)).T
            
            show_legend = True if i == 0 else False
            
            fig.add_trace(
                go.Surface(
                    x=Xi, y=Yi, z=Z_ribbon,
                    colorscale=[[0, ref_color], [1, ref_color]],
                    showscale=False, 
                    name=ref_label,
                    showlegend=show_legend, 
                    opacity=0.45, 
                    hoverinfo="skip"
                ),
                row=r, col=c
            )

    # 3. Subplot Scene Styling
    fig.update_scenes(
        dict(
            aspectmode='manual',
            aspectratio=dict(x=1, y=1, z=0.8),
            xaxis=dict(
                title="Probability", 
                tickvals=unique_probs,
                # FORMAT: Probability labels with zero decimal digits
                ticktext=[f"{p:.0f}" for p in unique_probs],
                titlefont=dict(size=LABEL_FONT_SIZE),
                tickfont=dict(size=TICK_FONT_SIZE)
            ),
            yaxis=dict(
                title="Year", 
                tickvals=year_cols, 
                titlefont=dict(size=LABEL_FONT_SIZE),
                tickfont=dict(size=TICK_FONT_SIZE)
            ),
            zaxis=dict(
                title=f"Emissions (+E{fixed_exponent})", 
                tickformat=".1f",
                exponentformat="none",
                titlefont=dict(size=LABEL_FONT_SIZE),
                tickfont=dict(size=TICK_FONT_SIZE)
            ),
            camera=dict(eye=dict(x=1.7, y=1.7, z=1.1))
        ),
        row=r, col=c
    )

# -------------------------
# Global Layout
# -------------------------
fig.update_layout(
    title=dict(text="CCUS sector emissions among scenarios and probabilities [-GWP_100]", x=0.5, y=0.98, font=dict(size=22)),
    width=1200, height=1350,
    margin=dict(l=60, r=60, b=60, t=100),
    legend=dict(
        title="<b>Reference Benchmarks</b>", yanchor="top", y=0.98, xanchor="right", x=0.99,
        bgcolor="rgba(255,255,255,0.7)", bordercolor="Black", borderwidth=1
    )
)

for annotation in fig['layout']['annotations']:
    annotation['font'] = dict(size=TITLE_FONT_SIZE)
    annotation['y'] = annotation['y'] + 0.02

fig.show()



# 