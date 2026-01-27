import os
import pandas as pd
import matplotlib.pyplot as plt
import math

# --- CONFIGURATION ---
DATA_FILE = 'CSD_material.xlsx'
MAPPING_FILE = 'Stochastic.xlsx'
YEAR_COLS = ['2010', '2020', '2030', '2040', '2050']
TARGET_MATERIAL = 'MAN'  # Manganese

# Image Dimensions: 33cm x 14.5cm
FIG_WIDTH_IN = 33 / 2.54
FIG_HEIGHT_IN = 14.5 / 2.54

# 1. EXPANDED & UNIQUE COLOR PALETTE
# Each group from stochastic.xlsx now has a unique color
tech_color_map = {
    # Power Generation
    'Bioenergy': '#27AE60',      # Green
    'Coal': '#17202A',           # Dark Grey/Black
    'Geothermal': '#922B21',     # Dark Red
    'Hydropower': '#2980B9',     # Blue
    'Wave&Tidal': '#1B4F72',     # Dark Navy
    'NGA': '#D35400',            # Dark Orange
    'Nuclear': '#8E44AD',        # Purple
    'Oil': '#7B7D7D',            # Grey
    'Solar': '#F1C40F',          # Yellow
    'Wind (onshore)': '#A2D9CE', # Teal/Turquoise
    'Wind (offshore)': '#3498DB',# Sky Blue
    
    # Storage & Hydrogen
    'Hydrogen': '#E67E22',       # Orange
    'LIBs': '#95A5A6',           # Concrete Grey
    'PSH': '#2E4053',            # Gunmetal
    'ALK': '#F5B041',            # Goldenrod
    'PEM': '#EB984E',            # Sand/Tan
    'SOEC': '#B9770E',           # Ochre
    
    # Transport
    'Traditional car': '#515A5A',# Steel Grey
    'BEV': '#58D68D',            # Light Green
    'FCV': '#EC7063',            # Soft Red
    'FHEV': '#5499C7'            # Steel Blue
}

# Default colors for any missing groups
default_colors = plt.cm.get_cmap('tab20').colors

# 2. LOAD TECHNOLOGY MAPPING
map_df = pd.read_excel(MAPPING_FILE)
tech_to_group = {}
for _, row in map_df.iterrows():
    tech_to_group[(str(row['Sector']).strip(), str(row['Technology']).strip())] = row['Group']

def get_combined_material_data():
    """Reads all sheets, filters for target material, and aggregates by Group."""
    all_data = []
    xls = pd.ExcelFile(DATA_FILE)

    for sheet_name in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=sheet_name)
        if df.empty: continue
        
        df.columns = [str(col).strip() for col in df.columns]
        if 'material_comm' not in df.columns: continue
            
        df_mat = df[df['material_comm'] == TARGET_MATERIAL].copy()
        if df_mat.empty: continue
            
        df_mat['Group'] = df_mat['tech'].apply(lambda x: tech_to_group.get((sheet_name.strip(), str(x).strip())))
        df_mat = df_mat.dropna(subset=['Group'])
        
        if not df_mat.empty:
            all_data.append(df_mat)
            
    return pd.concat(all_data, ignore_index=True) if all_data else pd.DataFrame()

def plot_material_grid(combined_df, year_col):
    # Convert Tons to Mt
    combined_df[year_col] = combined_df[year_col] / 1e6

    ref_csd = combined_df[combined_df['scenario'] == "CSD_S1S1S1"]
    ref_nze = combined_df[combined_df['scenario'] == "Net0_Simplified"]
    
    comparison_scenarios = [s for s in combined_df['scenario'].unique() 
                            if s not in ["CSD_S1S1S1", "Net0_Simplified", "CSD", "NZE"]]
    
    if not comparison_scenarios: return

    temp_pivot = combined_df.pivot_table(index=['scenario', 'Probability of disruption'], values=year_col, aggfunc='sum')
    global_max = temp_pivot[year_col].max() if not temp_pivot.empty else 1.0

    cols = 3
    rows = math.ceil(len(comparison_scenarios) / cols)
    
    fig, axes = plt.subplots(nrows=rows, ncols=cols, figsize=(FIG_WIDTH_IN, FIG_HEIGHT_IN))
    axes = axes.flatten() if rows * cols > 1 else [axes]

    legend_handles, legend_labels = None, None

    for i, scen in enumerate(comparison_scenarios):
        ax = axes[i]
        scen_subset = combined_df[combined_df['scenario'] == scen]
        plot_subset = pd.concat([ref_nze, scen_subset, ref_csd]) # NZE First, CSD Last
        
        pivot_df = plot_subset.pivot_table(index='Probability of disruption', columns='Group', values=year_col, aggfunc='sum')
        
        probs = sorted([p for p in pivot_df.index if p not in ["CSD", "NZE"]])
        x_order = ["NZE"] + probs + ["CSD"]
        pivot_df = pivot_df.reindex(x_order)
        
        colors = [tech_color_map.get(col, default_colors[idx % len(default_colors)]) 
                  for idx, col in enumerate(pivot_df.columns)]
        
        pivot_df.plot(kind='bar', stacked=True, ax=ax, legend=False, width=0.75, 
                      color=colors, edgecolor='white', linewidth=0.2)
        
        ax.set_ylim(0, global_max * 1.1)
        ax.set_title(f"Scenario: {scen}", fontsize=9, fontweight='bold')
        ax.set_xticklabels(x_order, rotation=0, fontsize=7)
        ax.set_xlabel("")
        if i % cols == 0: ax.set_ylabel("Usage [Mt]", fontsize=8)

        if i == 0:
            legend_handles, legend_labels = ax.get_legend_handles_labels()

    if legend_handles:
        fig.legend(legend_handles[::-1], legend_labels[::-1], 
                   loc='lower right', bbox_to_anchor=(0.95, 0.08), 
                   title="Technology Groups", title_fontsize=8, 
                   fontsize=7, ncol=2, frameon=True)

    for j in range(i + 1, len(axes)): axes[j].axis('off')

    plt.subplots_adjust(top=0.88, bottom=0.15, left=0.08, right=0.95, hspace=0.4, wspace=0.25)
    fig.suptitle(f"{TARGET_MATERIAL} Allocation by Technology Group [Mt] - {year_col}", 
                 fontsize=14, fontweight='bold', x=0.5, y=0.96)
    
    plt.savefig(f"Material_{TARGET_MATERIAL}_Mix_{year_col}.png", dpi=300)
    plt.close()

if __name__ == "__main__":
    combined_mat_df = get_combined_material_data()
    if not combined_mat_df.empty:
        for year in YEAR_COLS:
            if year in combined_mat_df.columns:
                plot_material_grid(combined_mat_df.copy(), year)