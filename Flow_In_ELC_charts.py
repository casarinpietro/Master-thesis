import os
import pandas as pd
import matplotlib.pyplot as plt
import math

# --- CONFIGURATION ---
DATA_FILE = 'CSD_flow_in.xlsx'
YEAR_COLS = ['2010', '2020', '2030', '2040', '2050']

# Mapping of Sheet Names to Chart Display Names
SHEET_TO_SECTOR = {
    "Agriculture": "Agriculture",
    "Power": "Power",
    "Transport": "Transport",
    "Storage": "Storage",
    "H2": "Hydrogen",
    "CCUS": "CCUS",
    "IND": "Industry",
    "RES": "Residential",
    "COM": "Commercial",
    "UPS": "Upstream"
}

# Image Dimensions: 33cm x 14.5cm
FIG_WIDTH_IN = 33 / 2.54
FIG_HEIGHT_IN = 14.5 / 2.54

# Color Map for Sectors
sector_color_map = {
    'Agriculture': '#A2D9CE',
    'Power': '#3498DB',
    'Transport': '#5DADE2',
    'Storage': '#1B4F72',
    'Hydrogen': '#85C1E9',
    'CCUS': '#6C3483',
    'Industry': '#E67E22',
    'Residential': '#27AE60',
    'Commercial': '#FFD700',
    'Upstream': '#7B7D7D'
}
default_colors = plt.cm.get_cmap('Set3').colors

def get_combined_elc_data():
    """Reads all sheets and filters for ELC_CEN/ELC_DST to create a combined dataset."""
    all_data = []
    
    xls = pd.ExcelFile(DATA_FILE)
    for sheet_name, display_name in SHEET_TO_SECTOR.items():
        if sheet_name in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name=sheet_name)
            df.columns = [str(col) for col in df.columns]
            
            # Filter for Electricity Commodities (CEN and DST)
            # Using .copy() to avoid SettingWithCopyWarning
            df_elc = df[df['input_comm'].isin(['ELC_CEN', 'ELC_DST'])].copy()
            
            if not df_elc.empty:
                df_elc['Sector_Name'] = display_name
                all_data.append(df_elc)
    
    if not all_data:
        return pd.DataFrame()
        
    return pd.concat(all_data, ignore_index=True)

def plot_elc_usage_grid(combined_df, year_col):
    # References for Anchors (NZE first, CSD last)
    ref_csd = combined_df[combined_df['scenario'] == "CSD_S1S1S1"]
    ref_nze = combined_df[combined_df['scenario'] == "Net0_Simplified"]
    
    # Comparison Scenarios
    comparison_scenarios = [s for s in combined_df['scenario'].unique() 
                            if s not in ["CSD_S1S1S1", "Net0_Simplified", "CSD", "NZE"]]
    
    if not comparison_scenarios:
        return

    # Unified Scaling: Aggregate ELC_CEN and ELC_DST values by scenario/probability
    temp_pivot = combined_df.pivot_table(index=['scenario', 'Probability of disruption'], values=year_col, aggfunc='sum')
    global_max = temp_pivot[year_col].max() if not temp_pivot.empty else 100

    cols = 3
    rows = math.ceil(len(comparison_scenarios) / cols)
    
    fig, axes = plt.subplots(nrows=rows, ncols=cols, figsize=(FIG_WIDTH_IN, FIG_HEIGHT_IN))
    if rows == 1 and cols == 1: axes = [axes]
    else: axes = axes.flatten()

    legend_handles, legend_labels = None, None

    for i, scen in enumerate(comparison_scenarios):
        ax = axes[i]
        scen_subset = combined_df[combined_df['scenario'] == scen]
        
        # Combine Reference Bars + Current Scenario
        plot_subset = pd.concat([ref_csd, scen_subset, ref_nze])
        
        # Pivot by Sector_Name (Automatically sums ELC_CEN and ELC_DST together)
        pivot_df = plot_subset.pivot_table(index='Probability of disruption', columns='Sector_Name', values=year_col, aggfunc='sum')
        
        # Order: NZE -> Probs -> CSD
        probs = sorted([p for p in pivot_df.index if p not in ["CSD", "NZE"]])
        x_order = ["NZE"] + probs + ["CSD"]
        pivot_df = pivot_df.reindex(x_order)
        
        colors = [sector_color_map.get(col, default_colors[idx % len(default_colors)]) 
                  for idx, col in enumerate(pivot_df.columns)]
        
        pivot_df.plot(kind='bar', stacked=True, ax=ax, legend=False, width=0.75, 
                      color=colors, edgecolor='white', linewidth=0.2)
        
        # Formatting
        ax.set_ylim(0, global_max * 1.1)
        ax.set_title(f"Scenario: {scen}", fontsize=9, fontweight='bold')
        ax.set_xticklabels(x_order, rotation=0, fontsize=7)
        ax.set_xlabel("")
        if i % cols == 0:
            # Using GW or PJ depending on your data units for electricity
            ax.set_ylabel("Electricity Use", fontsize=8)

        if i == 0:
            legend_handles, legend_labels = ax.get_legend_handles_labels()

    # Legend in bottom-right corner
    if legend_handles:
        fig.legend(legend_handles[::-1], legend_labels[::-1], 
                   loc='lower right', bbox_to_anchor=(0.95, 0.08), 
                   title="Consuming Sectors", title_fontsize=8, 
                   fontsize=7, ncol=2, frameon=True)

    # Hide unused axes
    for j in range(i + 1, len(axes)):
        axes[j].axis('off')

    plt.subplots_adjust(top=0.88, bottom=0.15, left=0.08, right=0.95, hspace=0.4, wspace=0.25)
    fig.suptitle(f"Electricity (CEN+DST) Use Mix across Sectors - {year_col}", 
                 fontsize=14, fontweight='bold', x=0.5, y=0.96)
    
    plt.savefig(f"Electricity_Sector_Use_Mix_{year_col}.png", dpi=300)
    plt.close()

# --- EXECUTION ---
if __name__ == "__main__":
    print("Aggregating electricity consumption (ELC_CEN + ELC_DST) from all sheets...")
    combined_elc_df = get_combined_elc_data()
    
    if not combined_elc_df.empty:
        for year in YEAR_COLS:
            if year in combined_elc_df.columns:
                plot_elc_usage_grid(combined_elc_df, year)
                print(f"Generated Electricity Sector Mix chart for {year}")
    else:
        print("Error: No ELC_CEN or ELC_DST data found in the specified sheets.")

    print("\n✅ Electricity Sector Mix processing complete.")