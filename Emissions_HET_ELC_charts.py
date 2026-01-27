import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import math

# --- CONFIGURAZIONE ---
DB_SCRIPT = 'TEMOA_Europe.sql'
EMISSIONS_FILE = 'CSD_emissions.xlsx'
YEARS = ['2010', '2020', '2030', '2040', '2050']
REF_START_ORIG = "CSD_S1S1S1"
REF_END_ORIG = "Net0_Simplified"

# Dimensioni: 33cm x 14.5cm convertite in pollici
W_IN, H_IN = 33 / 2.54, 14.5 / 2.54

def format_label(val):
    s = str(val).strip()
    return s[:-2] if s.endswith('.0') else s

def load_and_aggregate_db():
    """Carica il database SQL e calcola i fattori di allocazione per vintage."""
    conn = sqlite3.connect(':memory:')
    cursor = conn.cursor()
    with open(DB_SCRIPT, 'r', encoding='utf-8', errors='ignore') as f:
        cursor.executescript(f.read())
    
    # Estrazione efficienza e EmissionActivity
    df_eff = pd.read_sql_query("SELECT tech, vintage, output_comm, efficiency FROM Efficiency", conn)
    try:
        df_ea = pd.read_sql_query("SELECT tech, vintage, output_comm, emis_act FROM EmissionActivity WHERE emis_comm='GWP_100'", conn)
    except:
        df_ea = pd.DataFrame(columns=['tech', 'vintage', 'output_comm', 'emis_act'])
    conn.close()

    records = []
    all_techs = set(df_eff['tech'].unique()) | set(df_ea['tech'].unique())
    
    for tech in all_techs:
        t_eff = df_eff[df_eff['tech'] == tech]
        t_ea = df_ea[df_ea['tech'] == tech]
        
        for yr_str in YEARS:
            yr = int(yr_str)
            # Trova il regime vintage attivo (ultima vintage <= anno di analisi)
            v_eff = t_eff[t_eff['vintage'] <= yr]
            v_ea = t_ea[t_ea['vintage'] <= yr]
            
            if v_eff.empty:
                records.append({'tech': tech, 'year': yr_str, 'Factor_ELC': 1.0, 'Factor_HET': 0.0})
                continue
                
            latest_v = v_eff['vintage'].max()
            eff_data = v_eff[v_eff['vintage'] == latest_v]
            
            w_elc, w_het = 0.0, 0.0
            for _, row in eff_data.iterrows():
                out = str(row['output_comm'])
                ef_match = v_ea[(v_ea['vintage'] <= yr) & (v_ea['output_comm'] == out)]
                ef = ef_match.sort_values('vintage', ascending=False).iloc[0]['emis_act'] if not ef_match.empty else 1.0
                
                weight = row['efficiency'] * ef
                if 'ELC' in out: w_elc += weight
                elif 'HET' in out: w_het += weight
            
            total_w = w_elc + w_het
            f_elc = w_elc / total_w if total_w > 0 else 1.0
            f_het = w_het / total_w if total_w > 0 else 0.0
            records.append({'tech': tech, 'year': yr_str, 'Factor_ELC': f_elc, 'Factor_HET': f_het})
            
    return pd.DataFrame(records)

def plot_emissions_grid(df, title, filename):
    """Genera i grafici con asse Y in NOTAZIONE SCIENTIFICA."""
    scenarios = sorted([s for s in df['scenario'].unique() if s not in [REF_START_ORIG, REF_END_ORIG, "CSD", "NZE"]])
    df_summed = df.groupby(['scenario', 'Probability of disruption'])[YEARS].sum().reset_index()

    y_min, y_max = df_summed[YEARS].min().min(), df_summed[YEARS].max().max()
    margin = abs(y_max - y_min) * 0.1 if y_max != y_min else 1.0
    
    cols = 3
    rows = math.ceil(len(scenarios) / cols)
    fig, axes = plt.subplots(nrows=rows, ncols=cols, figsize=(W_IN, H_IN))
    axes_flat = axes.flatten()

    ref_csd = df_summed[df_summed['scenario'] == REF_START_ORIG]
    ref_nze = df_summed[df_summed['scenario'] == REF_END_ORIG]

    for i, scen in enumerate(scenarios):
        ax = axes_flat[i]
        scen_data = df_summed[df_summed['scenario'] == scen]
        ax.axhline(0, color='grey', lw=0.8, alpha=0.5)

        # Plot NZE (Verde punteggiata)
        if not ref_nze.empty:
            ax.plot(YEARS, ref_nze[YEARS].iloc[0].values, color='green', ls=':', lw=2, label='NZE')
        
        # Plot Probabilità numeriche
        probs = sorted(scen_data['Probability of disruption'].unique(), 
                       key=lambda x: float(str(x).replace('.','',1)) if str(x).replace('.','',1).isdigit() else 0)
        for p in probs:
            p_vals = scen_data[scen_data['Probability of disruption'] == p][YEARS].iloc[0].values
            ax.plot(YEARS, p_vals, marker='o', ms=3, label=f"{p}%")

        # Plot CSD (Nera tratteggiata)
        if not ref_csd.empty:
            ax.plot(YEARS, ref_csd[YEARS].iloc[0].values, color='black', ls='--', lw=1.5, label='CSD')

        # --- FORMATTAZIONE ASSE Y: NOTAZIONE SCIENTIFICA ---
        ax.yaxis.set_major_formatter(ticker.ScalarFormatter(useMathText=True))
        ax.ticklabel_format(style='sci', axis='y', scilimits=(0,0))
        
        ax.set_title(f"Scenario: {scen}", fontsize=9, fontweight='bold')
        ax.set_ylim(y_min - margin, y_max + margin)
        ax.grid(axis='both', ls='--', alpha=0.3)
        ax.tick_params(axis='both', labelsize=7)
        if i % cols == 0: ax.set_ylabel("GWP_100", fontsize=8)

    # Legenda e salvataggio
    handles, labels = axes_flat[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc='lower right', bbox_to_anchor=(0.95, 0.08), 
               ncol=2, fontsize=7, title="Probabilities / Refs", title_fontsize=8)
    
    for j in range(i + 1, len(axes_flat)): axes_flat[j].axis('off')
    
    plt.subplots_adjust(top=0.88, bottom=0.15, left=0.1, right=0.95, hspace=0.4, wspace=0.3)
    fig.suptitle(title, fontsize=14, fontweight='bold', y=0.96)
    plt.savefig(filename, dpi=300)
    plt.close()

if __name__ == "__main__":
    try:
        # 1. Caricamento fattori dal DB SQL
        factors = load_and_aggregate_db()

        # 2. Caricamento file emissioni
        df_power = pd.read_excel(EMISSIONS_FILE, sheet_name='Power')
        df_power.columns = [str(col).strip() for col in df_power.columns]
        df_power = df_power[df_power['emissions_comm'] == 'GWP_100'].copy()
        df_power['Probability of disruption'] = df_power['Probability of disruption'].apply(format_label)

        # 3. Trasformazione e Merge con i fattori Vintage
        df_long = df_power.melt(id_vars=['scenario', 'Probability of disruption', 'tech'], 
                                value_vars=YEARS, var_name='year', value_name='total_emis')
        df_merged = pd.merge(df_long, factors, on=['tech', 'year'], how='left').fillna({'Factor_ELC': 1.0, 'Factor_HET': 0.0})

        # 4. Allocazione
        df_merged['ELC_val'] = df_merged['total_emis'] * df_merged['Factor_ELC']
        df_merged['HET_val'] = df_merged['total_emis'] * df_merged['Factor_HET']

        # 5. Pivot per il plotting
        elc_final = df_merged.pivot_table(index=['scenario', 'Probability of disruption'], columns='year', values='ELC_val', aggfunc='sum').reset_index()
        het_final = df_merged.pivot_table(index=['scenario', 'Probability of disruption'], columns='year', values='HET_val', aggfunc='sum').reset_index()
        elc_final.columns, het_final.columns = [[str(c) for c in df.columns] for df in [elc_final, het_final]]

        # 6. Generazione grafici
        plot_emissions_grid(elc_final, "Power Sector: Electricity (ELC) GWP_100", "Emissions_Split_ELC_Sci.png")
        plot_emissions_grid(het_final, "Power Sector: Heat (HET) GWP_100", "Emissions_Split_HET_Sci.png")

        print("✅ Grafici generati in notazione scientifica: Emissions_Split_ELC_Sci.png e Emissions_Split_HET_Sci.png")
    
    except Exception as e:
        print(f"Errore: {e}")