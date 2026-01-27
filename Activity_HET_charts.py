import os
import pandas as pd
import matplotlib.pyplot as plt
import math

# --- CONFIGURATION ---
DATA_FILE = 'CSD_flow_out.xlsx'
# Based on your request, we are now targeting the Power sector for heat
SECTORS_TO_PLOT = ["Power"] 
YEAR_COLS = ['2010', '2020', '2030', '2040', '2050'] 

# Image Dimensions: 33cm x 14.5cm
FIG_WIDTH_IN = 33 / 2.54
FIG_HEIGHT_IN = 14.5 / 2.54

# 1. KEYWORD-BASED GROUPING LOGIC
def get_heat_group(tech_name):
    tech_upper = str(tech_name).upper()
    if 'BIO' in tech_upper: return 'Bioenergy'
    if 'COA' in tech_upper: return 'Coal'
    if 'NGA' in tech_upper: return 'NGA'
    if 'OIL' in tech_upper: return 'Oil'
    if 'GEO' in tech_upper: return 'Geothermal'
    if 'SOL' in tech_upper: return 'Solar'
    return None

# 2. COLOR MAPPING
tech_color_map = {
    'Bioenergy': '#27AE60',
    'Coal': '#2C3E50',
    'NGA': '#E67E22',
    'Oil': '#7B7D7D',
    'Geothermal': '#C0392B',
    'Solar': '#FFD700'
}
default_colors = plt.cm.get_cmap('Set3').colors

def plot_heat_grid(sector_name, sector_df, year_col):
    # Filter for Heat Output and create a explicit copy to avoid warnings
    sector_df = sector_df[sector_df['output_comm'] == 'HET'].copy()
    
    # Apply keyword grouping
    sector_df['Group'] = sector_df['tech'].apply(get_heat_group)
    plot_data = sector_df.dropna(subset=['Group']).copy()

    if plot_data.empty:
        print(f"No heat data found for {sector_name} in {year_col}")
        return

    # Identify Reference rows for Anchors
    ref_csd = plot_data[plot_data['scenario'] == "CSD_S1S1S1"]
    ref_nze = plot_data[plot_data['scenario'] == "Net0_Simplified"]
    
    # Filter for comparison scenarios
    comparison_scenarios = [s for s in plot_data['scenario'].unique() 
                            if s not in ["CSD_S1S1S1", "Net0_Simplified", "CSD", "NZE"]]
    
    if not comparison_scenarios:
        return

    # Unified Scaling across the grid
    temp_pivot = plot_data.pivot_table(index=['scenario', 'Probability of disruption'], values=year_col, aggfunc='sum')
    global_max = temp_pivot[year_col].max() if not temp_pivot.empty else 100

    cols = 3
    rows = math.ceil(len(comparison_scenarios) / cols)
    
    fig, axes = plt.subplots(nrows=rows, ncols=cols, figsize=(FIG_WIDTH_IN, FIG_HEIGHT_IN))
    if rows == 1 and cols == 1: axes = [axes]
    else: axes = axes.flatten()

    legend_handles, legend_labels = None, None

    for i, scen in enumerate(comparison_scenarios):
        ax = axes[i]
        scen_subset = plot_data[plot_data['scenario'] == scen]
        combined = pd.concat([ref_csd, scen_subset, ref_nze])
        
        pivot_df = combined.pivot_table(index='Probability of disruption', columns='Group', values=year_col, aggfunc='sum')
        
        # REVERSED Order: NZE -> [Probs] -> CSD
        probs = sorted([p for p in pivot_df.index if p not in ["CSD", "NZE"]])
        x_order = ["NZE"] + probs + ["CSD"]
        pivot_df = pivot_df.reindex(x_order)
        
        colors = [tech_color_map.get(col, default_colors[idx % len(default_colors)]) for idx, col in enumerate(pivot_df.columns)]
        
        pivot_df.plot(kind='bar', stacked=True, ax=ax, legend=False, width=0.75, 
                      color=colors, edgecolor='white', linewidth=0.2)
        
        # Formatting
        ax.set_ylim(0, global_max * 1.1)
        ax.set_title(f"Scenario: {scen}", fontsize=9, fontweight='bold', pad=2)
        ax.set_xticklabels(x_order, rotation=0, fontsize=7)
        ax.set_xlabel("")
        ax.tick_params(axis='both', which='major', labelsize=7)
        
        if i % cols == 0:
            ax.set_ylabel("Output [PJ]", fontsize=8)
        else:
            ax.set_ylabel("")

        if i == 0:
            legend_handles, legend_labels = ax.get_legend_handles_labels()

    # Legend in bottom-right corner
    if legend_handles:
        fig.legend(legend_handles[::-1], legend_labels[::-1], 
                   loc='lower right', bbox_to_anchor=(0.95, 0.08), 
                   title="Heat Technology Groups", title_fontsize=8, 
                   fontsize=7, ncol=2, frameon=True)

    # Clean unused axes
    for j in range(i + 1, len(axes)):
        axes[j].axis('off')

    plt.subplots_adjust(top=0.88, bottom=0.15, left=0.08, right=0.95, hspace=0.4, wspace=0.25)
    
    fig.suptitle(f"Power Sector Heat Production Mix [PJ] - {year_col}", 
                 fontsize=14, fontweight='bold', x=0.5, y=0.96)
    
    plt.savefig(f"Power_HeatMix_Grid_{year_col}.png", dpi=300)
    plt.close()

# --- EXECUTION ---
if __name__ == "__main__":
    for sector in SECTORS_TO_PLOT:
        try:
            df_sector = pd.read_excel(DATA_FILE, sheet_name=sector)
            df_sector.columns = [str(col) for col in df_sector.columns]
            for year in YEAR_COLS:
                if year in df_sector.columns:
                    plot_heat_grid(sector, df_sector, year)
                    print(f"Generated Power Heat Mix chart: {year}")
        except Exception as e:
            print(f"Error: {e}")

    print("\n✅ Heat Mix processing complete with NZE -> CSD x-axis order.")