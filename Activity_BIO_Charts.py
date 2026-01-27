import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import math

# --- CONFIGURAZIONE ---
FLOW_FILE = 'CSD_flow_in.xlsx'
REF_START_ORIG = "CSD_S1S1S1"
REF_END_ORIG = "Net0_Simplified"

# Dimensioni: 33cm x 14.5cm
W_IN = 33 / 2.54
H_IN = 14.5 / 2.54

def get_year_columns(df):
    """Rileva dinamicamente le colonne degli anni (formato numerico 4 cifre)."""
    return [col for col in df.columns if str(col).isdigit() and len(str(col)) == 4]

def format_label(val):
    s = str(val).strip()
    if s.endswith('.0'): s = s[:-2]
    return s

def get_sector_from_tech(tech_name):
    """Estrae il settore dal prefisso della tecnologia (es. 'TRA' da 'TRA_FT_BUS')."""
    return str(tech_name).split('_')[0]

def plot_stacked_bio_allocation(df, years):
    """Genera un grid chart con colonne impilate per l'allocazione BIO per settore."""
    
    # Identificazione scenari di confronto
    comparison_scenarios = sorted([s for s in df['scenario'].unique() 
                                   if s not in [REF_START_ORIG, REF_END_ORIG, "CSD", "NZE"]])
    
    if not comparison_scenarios: return

    num_scens = len(comparison_scenarios)
    cols = 3
    rows = math.ceil((num_scens + 1) / cols)
    
    fig, axes = plt.subplots(nrows=rows, ncols=cols, figsize=(W_IN, H_IN))
    axes_flat = axes.flatten()

    # Prepariamo i dati di riferimento (NZE e CSD)
    ref_data = df[df['scenario'].isin([REF_START_ORIG, REF_END_ORIG])].copy()
    
    # Calcolo del massimo globale per scala Y coerente
    total_per_x = df.groupby(['scenario', 'Probability of disruption'])[years].sum().sum(axis=1)
    global_max = total_per_x.max()

    legend_handles, legend_labels = None, None

    for i, scen in enumerate(comparison_scenarios):
        ax = axes_flat[i]
        scen_data = df[df['scenario'] == scen]
        plot_subset = pd.concat([ref_data, scen_data])

        # Aggregazione per Scenario, Probabilità e Settore
        # Sommiamo tutti gli anni per avere il valore totale del periodo (o scegli un anno specifico)
        plot_subset['Total_BIO'] = plot_subset[years].sum(axis=1)
        
        pivot_df = plot_subset.pivot_table(
            index='Probability of disruption',
            columns='Sector',
            values='Total_BIO',
            aggfunc='sum'
        ).fillna(0)

        # Ordine X-Axis: NZE -> Probabilità -> CSD
        raw_probs = [str(idx) for idx in pivot_df.index if str(idx) not in ["CSD", "NZE"]]
        probs_sorted = sorted(raw_probs, key=lambda x: float(x) if x.replace('.','').isdigit() else 0)
        x_order = ["NZE"] + probs_sorted + ["CSD"]
        pivot_df = pivot_df.reindex(x_order)

        # Plot
        pivot_df.plot(kind='bar', stacked=True, ax=ax, legend=False, width=0.7, edgecolor='white', linewidth=0.3)
        
        ax.set_title(f"Scen: {scen}", fontsize=9, fontweight='bold')
        ax.set_ylim(0, global_max * 1.1)
        ax.set_xticklabels(x_order, rotation=0, fontsize=7)
        ax.set_xlabel("")
        ax.grid(axis='y', linestyle='--', alpha=0.3)
        
        # Notazione Scientifica
        ax.yaxis.set_major_formatter(ticker.ScalarFormatter(useMathText=True))
        ax.ticklabel_format(style='sci', axis='y', scilimits=(0,0))
        
        if i % cols == 0: ax.set_ylabel("Total BIO PJ", fontsize=8)
        if i == 0: legend_handles, legend_labels = ax.get_legend_handles_labels()

    # Legenda nell'ultimo slot
    legend_ax = axes_flat[num_scens]
    legend_ax.axis('off')
    if legend_handles:
        legend_ax.legend(legend_handles[::-1], legend_labels[::-1], loc='center', 
                         title="Sectors", ncol=2, fontsize=7, title_fontsize=8, frameon=True)

    for j in range(num_scens + 1, len(axes_flat)):
        axes_flat[j].axis('off')

    plt.subplots_adjust(top=0.88, bottom=0.15, left=0.08, right=0.92, hspace=0.5, wspace=0.3)
    fig.suptitle("System-Wide BIO Input Allocation by Sector (PJ)", fontsize=13, fontweight='bold', y=0.96)
    plt.savefig("BIO_Allocation_System_Stacked.png", dpi=300)
    plt.close()

if __name__ == "__main__":
    try:
        # 1. Caricamento dati dal foglio FT
        df_flow = pd.read_excel(FLOW_FILE, sheet_name='FT')
        df_flow.columns = [str(c).strip() for c in df_flow.columns]
        
        # 2. Filtro per commodity BIO_
        df_bio = df_flow[df_flow['input_comm'].str.startswith('BIO_')].copy()
        
        # 3. Formattazione e estrazione Settore
        df_bio['Probability of disruption'] = df_bio['Probability of disruption'].apply(format_label)
        df_bio['Sector'] = df_bio['tech'].apply(get_sector_from_tech)
        
        # 4. Rilevamento anni
        years = get_year_columns(df_bio)
        
        if not df_bio.empty:
            print("Generazione grafico di allocazione BIO aggregata...")
            plot_stacked_bio_allocation(df_bio, years)
            print("✅ Grafico salvato: BIO_Allocation_System_Stacked.png")
        else:
            print("❌ Nessun dato BIO_ trovato nel foglio FT.")

    except Exception as e:
        print(f"Errore: {e}")