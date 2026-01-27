import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import math

# --- CONFIGURAZIONE ---
DATA_FILE = 'CSD_emissions.xlsx'
# Lista generale degli anni di interesse
POTENTIAL_YEARS = ['2010', '2020', '2030', '2040', '2050']
REF_START_ORIG = "CSD_S1S1S1"
REF_END_ORIG = "Net0_Simplified"

# Mapping dei fogli e nomi visualizzati
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

# Dimensioni: 33cm x 14.5cm
W_IN = 33 / 2.54
H_IN = 14.5 / 2.54

def format_label(val):
    """Pulisce le etichette delle probabilità (es. '10' invece di '10.0')."""
    s = str(val).strip()
    if s.endswith('.0'):
        s = s[:-2]
    return s

def plot_emissions_grid(sector_df, sector_display_name):
    """Genera un grid di line chart con gestione flessibile degli anni e notazione scientifica."""
    # 1. Filtro per GWP_100
    df = sector_df[sector_df['emissions_comm'] == 'GWP_100'].copy()
    if df.empty:
        return False

    # 2. Identificazione dinamica degli anni presenti in questo foglio
    available_years = [yr for yr in POTENTIAL_YEARS if yr in df.columns]
    if not available_years:
        return False

    # 3. Controllo se le emissioni negli anni disponibili sono diverse da zero
    if df[available_years].abs().sum().sum() == 0:
        return False

    df['Probability of disruption'] = df['Probability of disruption'].apply(format_label)

    # Scenari di confronto
    comparison_scenarios = [s for s in df['scenario'].unique() 
                            if s not in [REF_START_ORIG, REF_END_ORIG, "CSD", "NZE"]]
    comparison_scenarios.sort()

    if not comparison_scenarios:
        return False

    cols = 3
    rows = math.ceil(len(comparison_scenarios) / cols)

    # Calcolo dei limiti asse Y (Min e Max globali del settore) per gestire valori negativi
    temp_sum = df.groupby(['scenario', 'Probability of disruption'])[available_years].sum()
    y_min = temp_sum.min().min()
    y_max = temp_sum.max().max()
    
    range_val = y_max - y_min
    if range_val == 0: range_val = 1
    limit_min = y_min - (0.1 * abs(range_val))
    limit_max = y_max + (0.1 * abs(range_val))

    fig, axes = plt.subplots(nrows=rows, ncols=cols, figsize=(W_IN, H_IN))
    axes_flat = axes.flatten()

    # Riferimenti
    ref_csd = df[df['scenario'] == REF_START_ORIG]
    ref_nze = df[df['scenario'] == REF_END_ORIG]

    csd_line = ref_csd[available_years].sum().values if not ref_csd.empty else None
    nze_line = ref_nze[available_years].sum().values if not ref_nze.empty else None

    legend_handles, legend_labels = None, None

    for i, scen in enumerate(comparison_scenarios):
        ax = axes_flat[i]
        scen_data = df[df['scenario'] == scen]

        # Linea dello ZERO (per settori con assorbimenti negativi)
        ax.axhline(0, color='grey', linewidth=0.8, linestyle='-', alpha=0.5)

        # Plot NZE (Verde punteggiata)
        if nze_line is not None:
            ax.plot(available_years, nze_line, color='green', linestyle=':', linewidth=2, label='NZE')

        # Plot Probabilità numeriche
        raw_probs = [p for p in scen_data['Probability of disruption'].unique() if p not in ["CSD", "NZE"]]
        sorted_probs = sorted(raw_probs, key=lambda x: float(x) if x.replace('.','',1).isdigit() else x)

        for prob in sorted_probs:
            prob_data = scen_data[scen_data['Probability of disruption'] == prob]
            y_vals = prob_data[available_years].sum().values
            ax.plot(available_years, y_vals, marker='o', markersize=3, label=f"{prob}%")

        # Plot CSD (Nera tratteggiata)
        if csd_line is not None:
            ax.plot(available_years, csd_line, color='black', linestyle='--', linewidth=1.5, label='CSD')

        # --- NOTAZIONE SCIENTIFICA DINAMICA ---
        # Imposta il formattatore per usare la notazione scientifica
        formatter = ticker.ScalarFormatter(useMathText=True)
        formatter.set_scientific(True)
        formatter.set_powerlimits((0, 0)) # Forza la notazione scientifica per ogni ordine di grandezza
        ax.yaxis.set_major_formatter(formatter)

        ax.set_title(f"Scenario: {scen}", fontsize=9, fontweight='bold')
        ax.set_ylim(limit_min, limit_max)
        ax.grid(axis='both', linestyle='--', alpha=0.3)
        ax.tick_params(axis='both', labelsize=7)

        if i % cols == 0:
            ax.set_ylabel("GWP_100", fontsize=8)
        if i >= (rows - 1) * cols:
            ax.set_xlabel("Year", fontsize=8)

        if i == 0:
            legend_handles, legend_labels = ax.get_legend_handles_labels()

    # Legenda
    if legend_handles:
        fig.legend(legend_handles, legend_labels, loc='lower right', 
                   bbox_to_anchor=(0.95, 0.08), title="Probabilities / Refs", 
                   ncol=2, fontsize=7, title_fontsize=8, frameon=True)

    # Nasconde subplot inutilizzati
    for j in range(i + 1, len(axes_flat)):
        axes_flat[j].axis('off')

    plt.subplots_adjust(top=0.88, bottom=0.15, left=0.1, right=0.95, hspace=0.4, wspace=0.3)
    fig.suptitle(f"{sector_display_name} Sector Emissions Trends (GWP_100)", 
                 fontsize=14, fontweight='bold', y=0.96)
    
    plt.savefig(f"Emissions_Trend_{sector_display_name}.png", dpi=300)
    plt.close()
    return True

if __name__ == "__main__":
    try:
        xls = pd.ExcelFile(DATA_FILE)
        all_sector_data = []

        for sheet_name, display_name in SHEET_TO_SECTOR.items():
            if sheet_name in xls.sheet_names:
                df_sheet = pd.read_excel(xls, sheet_name=sheet_name)
                df_sheet.columns = [str(col).strip() for col in df_sheet.columns]
                
                if plot_emissions_grid(df_sheet, display_name):
                    print(f"Grafico generato per: {display_name}")
                    all_sector_data.append(df_sheet)
                else:
                    print(f"Settore {display_name} saltato (nessun dato o valori nulli).")

        # Generazione Grafico AGGREGATO di sistema
        if all_sector_data:
            print("\nGenerazione grafico delle emissioni totali di sistema...")
            full_system_df = pd.concat(all_sector_data, ignore_index=True)
            plot_emissions_grid(full_system_df, "Total System Aggregated")

        print("\n✅ Elaborazione completata con notazione scientifica dinamica.")
    except Exception as e:
        print(f"Errore: {e}")