import os
import pandas as pd
import matplotlib.pyplot as plt
import math

# --- CONFIGURATION ---
DATA_FILE = 'CSD_capacity.xlsx'
MAPPING_FILE = 'Stochastic.xlsx'
SECTORS_TO_PLOT = ["Power", "Transport", "Storage", "H2"]
# Updated to include 2010 and 2020
YEAR_COLS = ['2010', '2020', '2030', '2040', '2050'] 

SECTOR_UNITS = {
    "H2": "PJ",
    "Storage": "GW",
    "Power": "GW",
    "Transport": "Bvkm"
}

# Image Dimensions: 33cm x 14.5cm converted to inches
FIG_WIDTH_IN = 33 / 2.54
FIG_HEIGHT_IN = 14.5 / 2.54

# 1. LOAD TECHNOLOGY MAPPING
# Expects columns: Sector, Group, Technology
map_df = pd.read_excel(MAPPING_FILE)
tech_to_group = {}
for _, row in map_df.iterrows():
    tech_to_group[(row['Sector'], row['Technology'])] = row['Group']

# 2. COLOR MAPPING
tech_color_map = {
    'Wind (onshore)': '#A2D9CE', 'Wind (offshore)': '#5DADE2', 'Solar': '#FFD700',
    'Oil': '#7B7D7D', 'Nuclear': '#6C3483', 'NGA': '#E67E22', 'Hydropower': '#3498DB',
    'Geothermal': '#C0392B', 'Coal': '#2C3E50', 'Bioenergy': '#27AE60',
    'PSH': '#3498DB', 'LIBs': '#7B7D7D', 'BEV': '#27AE60', 'Traditional car': '#2C3E50',
    'FCV': '#C0392B', 'FHEV': '#3498DB', 'H2': '#85C1E9'
}
default_colors = plt.cm.get_cmap('Set3').colors

def plot_sector_grid(sector_name, sector_df, year_col):
    # Map Technologies to Groups
    sector_df['Group'] = sector_df['tech'].apply(lambda x: tech_to_group.get((sector_name, x)))
    plot_data = sector_df.dropna(subset=['Group']).copy()

    # Identify Reference rows for the CSD and NZE anchor bars
    # Updated to 'Net0_Simplified'
    ref_csd = plot_data[plot_data['scenario'] == "CSD_S1S1S1"]
    ref_nze = plot_data[plot_data['scenario'] == "Net0_Simplified"]
    
    # Filter for comparison scenarios (S1, S2, etc.)
    # Updated to exclude 'Net0_Simplified'
    comparison_scenarios = [s for s in plot_data['scenario'].unique() 
                            if s not in ["CSD_S1S1S1", "Net0_Simplified", "CSD", "NZE"]]
    
    if not comparison_scenarios:
        return

    # Calculate Global Y-Limit for unified scaling across the grid
    temp_pivot = plot_data.pivot_table(index=['scenario', 'Probability of disruption'], values=year_col, aggfunc='sum')
    global_max = temp_pivot[year_col].max() if not temp_pivot.empty else 100

    cols = 3
    rows = math.ceil(len(comparison_scenarios) / cols)
    
    # Initialize figure
    fig, axes = plt.subplots(nrows=rows, ncols=cols, figsize=(FIG_WIDTH_IN, FIG_HEIGHT_IN))
    
    if rows == 1 and cols == 1: 
        axes = [axes]
    else: 
        axes = axes.flatten()

    unit = SECTOR_UNITS.get(sector_name, "")
    legend_handles, legend_labels = None, None

    for i, scen in enumerate(comparison_scenarios):
        ax = axes[i]
        scen_subset = plot_data[plot_data['scenario'] == scen]
        
        # Combine CSD bar + Scenario Probs + NZE bar
        combined = pd.concat([ref_csd, scen_subset, ref_nze])
        pivot_df = combined.pivot_table(index='Probability of disruption', columns='Group', values=year_col, aggfunc='sum')
        
        # Enforce X-axis order
        probs = sorted([p for p in pivot_df.index if p not in ["CSD", "NZE"]])
        x_order = ["NZE"] + probs + ["CSD"]
        pivot_df = pivot_df.reindex(x_order)
        
        colors = [tech_color_map.get(col, default_colors[idx % len(default_colors)]) 
                  for idx, col in enumerate(pivot_df.columns)]
        
        # Plot stacked bar
        pivot_df.plot(kind='bar', stacked=True, ax=ax, legend=False, width=0.75, 
                      color=colors, edgecolor='white', linewidth=0.2)
        
        # Formatting
        ax.set_ylim(0, global_max * 1.1)
        ax.set_title(f"Scenario: {scen}", fontsize=9, fontweight='bold', pad=2)
        ax.set_xticklabels(x_order, rotation=0, fontsize=7)
        ax.set_xlabel("")
        ax.tick_params(axis='both', which='major', labelsize=7)
        
        if i % cols == 0:
            ax.set_ylabel(f"Capacity [{unit}]", fontsize=8)
        else:
            ax.set_ylabel("")

        # Capture legend info from the first plot
        if i == 0:
            legend_handles, legend_labels = ax.get_legend_handles_labels()

    # LEGEND: Placed in the bottom-right corner area in 2 columns
    if legend_handles:
        fig.legend(legend_handles[::-1], legend_labels[::-1], 
                   loc='lower right', bbox_to_anchor=(0.95, 0.08), 
                   title="Technology Groups", title_fontsize=8, 
                   fontsize=7, ncol=2, frameon=True)

    # Hide unused axes
    for j in range(i + 1, len(axes)):
        axes[j].axis('off')

    # Adjust layout to prevent overlap of title and labels
    plt.subplots_adjust(top=0.88, bottom=0.15, left=0.08, right=0.95, hspace=0.4, wspace=0.25)
    
    fig.suptitle(f"{sector_name} Sector technology mix [{unit}] - {year_col}", 
                 fontsize=14, fontweight='bold', x=0.5, y=0.96)
    
    # Save the output
    plt.savefig(f"{sector_name}_Grid_{year_col}.png", dpi=300)
    plt.close()

# --- EXECUTION ---
if __name__ == "__main__":
    for sector in SECTORS_TO_PLOT:
        try:
            df_sector = pd.read_excel(DATA_FILE, sheet_name=sector)
            df_sector.columns = [str(col) for col in df_sector.columns]
            for year in YEAR_COLS:
                if year in df_sector.columns:
                    plot_sector_grid(sector, df_sector, year)
                    print(f"Finalized: {sector} {year}")
        except Exception as e:
            print(f"Error in {sector}: {e}")

    print("\n✅ Processing complete for years 2010-2050.")