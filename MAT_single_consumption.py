import pandas as pd
import matplotlib.pyplot as plt
import math
import os

# --- CONFIGURATION ---
DATA_FILE = 'CSD_material.xlsx'
YEARS = ['2010', '2020', '2030', '2040', '2050']

# Define individual materials and groups
# For groups, provide a list of the material_comm codes
ANALYSIS_ITEMS = {
    'DYS': 'DYS',
    'LIT': 'LIT',
    'MAN': 'MAN',
    'NEO': 'NEO',
    'REEs': ['CER', 'DYS', 'EUP', 'GAD', 'LAN', 'NEO', 'PRA', 'TER', 'YTT']
}

# Disruption Factors (only for specific items)
disruption_factors = {
    'DYS': 0.59,
    'LIT': 0.38,
    'MAN': 0.59,
    'NEO': 0.55
}

REF_START_ORIG = "CSD_S1S1S1"
REF_END_ORIG = "Net0_Simplified"

# Dimensions: 33 x 14.5 cm
W_IN = 33 / 2.54
H_IN = 14.5 / 2.54

def is_disrupted_scen(scenario, year):
    if scenario == REF_START_ORIG or scenario == "CSD":
        return year in ['2030', '2040', '2050']
    mapping = {'2030': 1, '2040': 3, '2050': 5}
    if str(scenario).startswith('S') and len(str(scenario)) == 6:
        if year in mapping:
            return str(scenario)[mapping[year]] == '1'
    return False

def get_combined_material_data(item_name, item_val):
    """Aggregates data for a single material or a group of materials."""
    all_data = []
    xls = pd.ExcelFile(DATA_FILE)
    
    # If it's a list, we filter for all materials in that list
    target_list = item_val if isinstance(item_val, list) else [item_val]
    
    for sheet in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=sheet)
        if df.empty or 'material_comm' not in df.columns:
            continue
        df.columns = [str(col).strip() for col in df.columns]
        
        # Filter for the target material(s)
        df_filtered = df[df['material_comm'].isin(target_list)].copy()
        if not df_filtered.empty:
            all_data.append(df_filtered)
    
    if not all_data: return pd.DataFrame()
    combined = pd.concat(all_data, ignore_index=True)
    # Group and sum so that multiple materials in a group are aggregated
    return combined.groupby(['scenario', 'Probability of disruption'])[YEARS].sum().reset_index()

def plot_material_relative_trends(df, item_name):
    # 1. Establish NZE Baseline
    nze_absolute = df[df['scenario'] == REF_END_ORIG][YEARS].sum(axis=0)
    if nze_absolute.empty or nze_absolute.sum() == 0:
        print(f"Warning: No valid NZE reference found for {item_name}")
        return

    scenarios = [s for s in df['scenario'].unique() if s not in [REF_START_ORIG, REF_END_ORIG, "CSD", "NZE"]]
    scenarios.sort()

    # Check if a disruption factor exists for this item
    factor = disruption_factors.get(item_name)
    
    num_scens = len(scenarios)
    cols = 3
    rows = math.ceil(num_scens / cols)
    
    fig, axes = plt.subplots(nrows=rows, ncols=cols, figsize=(W_IN, H_IN), constrained_layout=True)
    axes_flat = axes.flatten()
    
    legend_handles, legend_labels = None, None

    for i, scen in enumerate(scenarios):
        ax = axes_flat[i]
        scen_data = df[df['scenario'] == scen].copy()
        
        # --- PLOT REFERENCE LINES ---
        ax.axhline(1.0, color='green', linestyle=':', linewidth=2, label='NZE baseline')
        
        # Only plot Target Baseline if a factor is defined
        if factor is not None:
            target_line = []
            for y in YEARS:
                target_line.append(1 - factor if is_disrupted_scen(scen, y) else 1.0)
            ax.plot(YEARS, target_line, color='red', linestyle='--', linewidth=1.2, label='Target baseline')

        # CSD Ref line
        csd_data = df[df['scenario'] == REF_START_ORIG][YEARS].sum(axis=0)
        if not csd_data.empty:
            ax.plot(YEARS, csd_data / nze_absolute, color='black', linewidth=1.5, label='CSD Ref')

        # --- PLOT PROBABILITY FOLDERS ---
        raw_probs = scen_data['Probability of disruption'].unique()
        folders = sorted([str(p) for p in raw_probs if str(p) not in ['CSD', 'NZE']])
        
        for folder in folders:
            mask = scen_data['Probability of disruption'].astype(str) == folder
            folder_abs = scen_data[mask][YEARS].sum(axis=0)
            if not folder_abs.empty:
                relative_vals = folder_abs / nze_absolute
                ax.plot(YEARS, relative_vals.values, marker='o', markersize=3, label=f"{folder}%")

        ax.set_title(f"Scenario: {scen}", fontsize=9, fontweight='bold')
        ax.set_ylim(0, 2.2) 
        ax.grid(axis='both', linestyle='--', alpha=0.3)
        
        if i % cols == 0: ax.set_ylabel("Mt / Mt_NZE", fontsize=8)
        if i == 0: legend_handles, legend_labels = ax.get_legend_handles_labels()

    # Legend cleanup
    for j in range(i + 1, len(axes_flat)): axes_flat[j].axis('off')
    if legend_handles:
        fig.legend(legend_handles, legend_labels, loc='lower right', bbox_to_anchor=(0.95, 0.08), 
                   title="Probabilities / Refs", ncol=2, fontsize=7, title_fontsize=8)

    plt.suptitle(f"Metric Trends: {item_name} Consumption relative to NZE", fontsize=13, fontweight='bold')
    plt.savefig(f"Relative_Trend_{item_name}.png", dpi=300)
    plt.close()

if __name__ == "__main__":
    for item_name, item_val in ANALYSIS_ITEMS.items():
        print(f"Processing Relative Trends for: {item_name}...")
        combined_df = get_combined_material_data(item_name, item_val)
        if not combined_df.empty:
            plot_material_relative_trends(combined_df, item_name)

    print("\n✅ Relative trend charts (including REEs) generated successfully.")