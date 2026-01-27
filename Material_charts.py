import os
import pandas as pd
import matplotlib.pyplot as plt
import math

# --- CONFIGURAZIONE ---
DATA_FILE = 'CSD_material.xlsx'
POTENTIAL_YEARS = ['2010', '2020', '2030', '2040', '2050']
REF_START_ORIG = "CSD_S1S1S1"
REF_END_ORIG = "Net0_Simplified"

# Dimensioni: 33 x 14.5 cm
W_IN = 33 / 2.54
H_IN = 14.5 / 2.54

# Definizioni Gruppi Materiali
DISTINCT_MATS = ['ALU', 'COP', 'GRA', 'LIT', 'MAN', 'NIC', 'VAN', 'COB']
REE_LIST = ['CER', 'DYS', 'EUP', 'GAD', 'LAN', 'NEO', 'PRA', 'TER', 'YTT']

def map_material_group(mat_name):
    if mat_name in DISTINCT_MATS: return mat_name
    elif mat_name in REE_LIST: return 'REEs'
    else: return 'Others'

def format_label(val):
    """Assicura che i numeri di probabilità siano stringhe pulite (es. '10' non '10.0')."""
    s = str(val).strip()
    if s.endswith('.0'):
        s = s[:-2]
    return s

mat_color_map = {
    'ALU': '#D5D8DC', 'COP': '#E67E22', 'GRA': '#2C3E50', 'LIT': '#AED6F1',
    'MAN': '#8E44AD', 'NIC': '#2ECC71', 'VAN': '#F1C40F', 'COB': '#2980B9',
    'REEs': '#E74C3C', 'Others': '#95A5A6'
}

def process_sheet_data(df, sheet_name):
    if df.empty or 'material_comm' not in df.columns:
        return pd.DataFrame()
        
    df.columns = [str(col).strip() for col in df.columns]
    available_years = [yr for yr in POTENTIAL_YEARS if yr in df.columns]
    
    if not available_years:
        return pd.DataFrame()

    df['Cumulative_Mt'] = df[available_years].sum(axis=1) / 1e6
    df['Material_Group'] = df['material_comm'].apply(map_material_group)
    
    # Formattazione uniforme della colonna probabilità
    if 'Probability of disruption' in df.columns:
        df['Probability of disruption'] = df['Probability of disruption'].apply(format_label)
        
    return df

def create_grid_chart(df, title, filename):
    """Genera il grid chart con aggregazione totale per probabilità (una sola barra per X)."""
    comparison_scenarios = [s for s in df['scenario'].unique() 
                            if s not in [REF_START_ORIG, REF_END_ORIG, "CSD", "NZE"]]
    comparison_scenarios.sort()
    
    if not comparison_scenarios:
        return

    cols = 3
    rows = math.ceil(len(comparison_scenarios) / cols)
    
    # Calcolo scala Y globale basata sulla somma di tutti i materiali per X
    total_heights = df.groupby(['scenario', 'Probability of disruption'])['Cumulative_Mt'].sum()
    global_max = total_heights.max() if not total_heights.empty else 1.0

    fig, axes = plt.subplots(nrows=rows, ncols=cols, figsize=(W_IN, H_IN))
    axes_flat = axes.flatten()
    
    ref_data = df[df['scenario'].isin([REF_START_ORIG, REF_END_ORIG])]
    legend_handles, legend_labels = None, None

    for i, scen in enumerate(comparison_scenarios):
        ax = axes_flat[i]
        scen_subset = df[df['scenario'] == scen]
        plot_subset = pd.concat([ref_data, scen_subset])
        
        # Aggregazione: somma tutti i contributi per Material_Group e Probability
        pivot_df = plot_subset.pivot_table(
            index='Probability of disruption', 
            columns='Material_Group', 
            values='Cumulative_Mt', 
            aggfunc='sum'
        )
        
        # Gestione Ordine X: NZE -> Numeri (ordinati) -> CSD
        all_labels = [str(idx) for idx in pivot_df.index]
        numeric_probs = sorted([l for l in all_labels if l not in ["CSD", "NZE"]], key=lambda x: float(x) if x.replace('.','',1).isdigit() else x)
        x_order = ["NZE"] + numeric_probs + ["CSD"]
        
        # Reindicizzazione per applicare l'ordine e il formato
        pivot_df = pivot_df.reindex(x_order)
        
        colors = [mat_color_map.get(col, '#95A5A6') for col in pivot_df.columns]
        
        pivot_df.plot(kind='bar', stacked=True, ax=ax, legend=False, 
                      width=0.7, color=colors, edgecolor='white', linewidth=0.2)
        
        ax.set_title(f"Scenario: {scen}", fontsize=9, fontweight='bold')
        ax.set_xticklabels(x_order, rotation=0, fontsize=7)
        ax.set_ylim(0, global_max * 1.1)
        ax.set_xlabel("")
        if i % cols == 0:
            ax.set_ylabel("Mt", fontsize=8)
        
        if i == 0:
            legend_handles, legend_labels = ax.get_legend_handles_labels()

    if legend_handles:
        fig.legend(legend_handles[::-1], legend_labels[::-1], loc='lower right', 
                   bbox_to_anchor=(0.98, 0.05), title="Material Group", 
                   ncol=2, fontsize=7, title_fontsize=8, frameon=True)

    for j in range(i + 1, len(axes_flat)):
        axes_flat[j].axis('off')

    plt.subplots_adjust(top=0.88, bottom=0.15, left=0.08, right=0.95, hspace=0.4, wspace=0.25)
    fig.suptitle(title, fontsize=13, fontweight='bold', y=0.96)
    plt.savefig(filename, dpi=300)
    plt.close()

if __name__ == "__main__":
    try:
        xls = pd.ExcelFile(DATA_FILE)
        all_data_list = []
        power_ccus_list = []

        for sheet in xls.sheet_names:
            df_raw = pd.read_excel(xls, sheet_name=sheet)
            df_proc = process_sheet_data(df_raw, sheet)
            if df_proc.empty: continue
            
            all_data_list.append(df_proc)
            
            if sheet in ["Power", "CCUS"]:
                power_ccus_list.append(df_proc)
            elif sheet in ["Transport", "H2", "Storage"]:
                create_grid_chart(df_proc, f"Cumulative Material Mix: {sheet} [Mt]", f"Material_Mix_{sheet}.png")

        if power_ccus_list:
            merged_p_ccus = pd.concat(power_ccus_list, ignore_index=True)
            create_grid_chart(merged_p_ccus, "Cumulative Material Mix: Power + CCUS [Mt]", "Material_Mix_Power_CCUS.png")

        if all_data_list:
            merged_system = pd.concat(all_data_list, ignore_index=True)
            create_grid_chart(merged_system, "Total System Aggregated Material Consumption Mix [Mt]", "Material_Mix_SYSTEM_TOTAL.png")

        print("✅ Elaborazione completata con formattazione uniforme dei numeri.")

    except Exception as e:
        print(f"Errore: {e}")