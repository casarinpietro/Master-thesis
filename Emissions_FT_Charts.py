import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import math

# --- CONFIGURAZIONE ---
FLOW_FILE = 'CSD_flow_in.xlsx'
EMISSIONS_FILE = 'CSD_emissions.xlsx'
REF_START_ORIG = "CSD_S1S1S1"
REF_END_ORIG = "Net0_Simplified"

# Mapping Prefisso Tech (da foglio FT) -> Nome Settore (per fogli Emissioni)
SECTOR_CONFIG = {
    "RES": "Residential",
    "COM": "Commercial",
    "TRA": "Transport",
    "ELC": "Power",
    "CCUS": "CCUS",
    "UPS": "Upstream",
    "AGR": "Agriculture",
    "H2": "Hydrogen",
    "IND": "Industry"
}

# Dimensioni: 33cm x 14.5cm
W_IN = 33 / 2.54
H_IN = 14.5 / 2.54

def get_year_columns(df):
    """Rileva dinamicamente le colonne degli anni (formato numerico 4 cifre)."""
    return [col for col in df.columns if str(col).isdigit() and len(str(col)) == 4]

def format_label(val):
    s = str(val).strip()
    return s[:-2] if s.endswith('.0') else s

def plot_dual_axis_sector(emis_df, flow_df, sector_name, filename):
    """Crea grid chart con doppia scala Y e legenda posizionata in un subplot."""
    
    years_emis = get_year_columns(emis_df)
    years_flow = get_year_columns(flow_df)
    years = sorted(list(set(years_emis) & set(years_flow)))
    
    if not years:
        return

    comparison_scenarios = sorted([s for s in emis_df['scenario'].unique() 
                                   if s not in [REF_START_ORIG, REF_END_ORIG, "CSD", "NZE"]])
    
    if not comparison_scenarios: return

    num_scens = len(comparison_scenarios)
    cols = 3
    rows = math.ceil((num_scens + 1) / cols) # +1 per fare spazio alla legenda
    fig, axes = plt.subplots(nrows=rows, ncols=cols, figsize=(W_IN, H_IN))
    axes_flat = axes.flatten()

    e_max = emis_df.groupby(['scenario', 'Probability of disruption'])[years].sum().max().max()
    f_max = flow_df.groupby(['scenario', 'Probability of disruption'])[years].sum().max().max()

    legend_handles = []
    legend_labels = []

    for i, scen in enumerate(comparison_scenarios):
        ax1 = axes_flat[i]
        ax2 = ax1.twinx()
        
        s_emis = emis_df[emis_df['scenario'] == scen]
        s_flow = flow_df[flow_df['scenario'] == scen]
        
        probs = sorted(s_emis['Probability of disruption'].unique(), 
                       key=lambda x: float(x) if str(x).replace('.','').isdigit() else 0)

        for p in probs:
            # Emissioni (Asse Sinistro)
            line1, = ax1.plot(years, s_emis[s_emis['Probability of disruption'] == p][years].sum(), 
                              label=f"Emis {p}%", marker='o', ms=3)
            
            # Flow BIO (Asse Destro)
            line2, = ax2.plot(years, s_flow[s_flow['Probability of disruption'] == p][years].sum(), 
                              label=f"BIO {p}%", marker='x', ms=3, linestyle='--', alpha=0.7)
            
            if i == 0:
                legend_handles.append(line1)
                legend_labels.append(f"Emis {p}%")
                legend_handles.append(line2)
                legend_labels.append(f"BIO {p}%")

        # Formattazione Scientifica
        for ax in [ax1, ax2]:
            fmt = ticker.ScalarFormatter(useMathText=True)
            fmt.set_scientific(True)
            fmt.set_powerlimits((0,0))
            ax.yaxis.set_major_formatter(fmt)

        ax1.set_title(f"Scen: {scen}", fontsize=9, fontweight='bold')
        ax1.set_ylim(0, e_max * 1.1 if e_max > 0 else 1)
        ax2.set_ylim(0, f_max * 1.1 if f_max > 0 else 1)
        ax1.grid(True, alpha=0.2)
        
        if i % cols == 0: ax1.set_ylabel("GWP_100", fontsize=8)
        if (i + 1) % cols == 0: ax2.set_ylabel("BIO PJ", fontsize=8)

    # Posizionamento Legenda nell'ultimo subplot vuoto (più vicina)
    legend_ax = axes_flat[num_scens]
    legend_ax.axis('off')
    if legend_handles:
        legend_ax.legend(legend_handles, legend_labels, loc='center', 
                         title="Series: Emissions & BIO", ncol=2, 
                         fontsize=7, title_fontsize=8, frameon=True)

    # Nascondi eventuali altri subplot vuoti rimanenti
    for j in range(num_scens + 1, len(axes_flat)):
        axes_flat[j].axis('off')

    plt.subplots_adjust(top=0.88, bottom=0.12, left=0.08, right=0.92, hspace=0.5, wspace=0.45)
    fig.suptitle(f"Sector {sector_name}: Emissions vs Bioenergy Input", fontsize=12, fontweight='bold')
    plt.savefig(filename, dpi=300)
    plt.close()

if __name__ == "__main__":
    try:
        df_flow_all = pd.read_excel(FLOW_FILE, sheet_name='FT')
        df_flow_all.columns = [str(c).strip() for c in df_flow_all.columns]
        df_flow_all['Probability of disruption'] = df_flow_all['Probability of disruption'].apply(format_label)
        
        xls_emis = pd.ExcelFile(EMISSIONS_FILE)

        for prefix, emis_sheet in SECTOR_CONFIG.items():
            if emis_sheet not in xls_emis.sheet_names: continue
            
            df_emis = pd.read_excel(xls_emis, sheet_name=emis_sheet)
            df_emis.columns = [str(c).strip() for c in df_emis.columns]
            df_emis = df_emis[df_emis['emissions_comm'] == 'GWP_100']
            df_emis['Probability of disruption'] = df_emis['Probability of disruption'].apply(format_label)

            df_sector_flow = df_flow_all[
                (df_flow_all['tech'].str.startswith(prefix)) & 
                (df_flow_all['input_comm'].str.startswith('BIO_'))
            ]

            if prefix == "IND":
                # Industry FT
                df_ft = df_sector_flow[~df_sector_flow['tech'].str.contains('_FS_')]
                plot_dual_axis_sector(df_emis, df_ft, "Industry (Fuel)", "Dual_IND_FT.png")
                # Industry FS
                df_fs = df_sector_flow[df_sector_flow['tech'].str.contains('_FS_')]
                plot_dual_axis_sector(df_emis, df_fs, "Industry (Feedstock)", "Dual_IND_FS.png")
            else:
                plot_dual_axis_sector(df_emis, df_sector_flow, emis_sheet, f"Dual_{emis_sheet}.png")

        print("✅ Grafici generati con legenda integrata nella griglia.")

    except Exception as e:
        print(f"Errore: {e}")