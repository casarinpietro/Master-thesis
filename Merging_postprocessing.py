import os
import pandas as pd
import re

# --- CONFIGURATION ---
BASE_DIR = r"D:\pietro_casarin\Pietro\Pietro\Pietro"
OUTPUT_DIR = os.path.join(BASE_DIR, "DSG_postprocessing")
SCENARIOS = ["NZE", "DSG", "6040", "7030", "8020", "9010"] 

FILE_MAP = {
  "DSG_capacity.xlsx": ["Agriculture", "Power", "Storage", "Transport", "IND", "RES", "COM", "UPS", "FT", "H2", "C+", "C-", "CCUS", "MAT"],
  "DSG_emissions.xlsx": ["Agriculture", "Power", "Transport", "Storage", "IND", "RES", "COM", "CCUS", "UPS", "FT", "H2", "C+", "C-", "MAT"],
  "DSG_flow_in.xlsx": ["Agriculture", "Power", "Transport", "Storage", "IND", "RES", "COM", "CCUS", "UPS", "FT", "H2", "C+", "C-", "MAT"],
  "DSG_flow_out.xlsx": ["Agriculture", "Power", "Transport", "Storage", "IND", "RES", "COM", "CCUS", "UPS", "FT", "H2", "C+", "C-", "MAT"],
  "DSG_material.xlsx": ["Agriculture", "Power", "Transport", "Storage", "IND", "RES", "COM", "CCUS", "UPS", "FT", "H2", "C+", "C-", "MAT"],
  "DSG_new_capacity.xlsx": ["Agriculture", "Power", "Transport", "Storage", "IND", "RES", "COM", "CCUS", "UPS", "FT", "H2", "C+", "C-", "MAT"]
}

def format_disruption_label(s_val):
    """Logic for 'Probability of disruption' column labels."""
    if s_val == "NZE":
        return "NZE"
    elif s_val == "DSG":
        return "DSG"
    else:
        # Extracts last two digits (e.g., '9010' -> '10')
        return s_val[-2:]

def consolidate_data():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    for master_file, sectors in FILE_MAP.items():
        print(f"Processing Master File: {master_file}...")
        compiled_data = {sector: [] for sector in sectors}

        for s_val in SCENARIOS:
            scenario_folder_name = f"DSG{s_val}"
            scenario_path = os.path.join(
                BASE_DIR, 
                scenario_folder_name, 
                "data_files", "2030-2050_simpl", "s2020", "Full_stochastic"
            )

            if not os.path.exists(scenario_path):
                print(f"  > Warning: Path not found {scenario_path}")
                continue

            for sector in sectors:
                source_file = os.path.join(scenario_path, f"{sector}.xlsx")
                
                if os.path.exists(source_file):
                    try:
                        sheet_name_in_source = master_file.replace("DSG_", "").replace(".xlsx", "")
                        df = pd.read_excel(source_file, sheet_name=sheet_name_in_source)
                        
                        # 1. Specific filter for Emissions file: Keep only GWP_100
                        if master_file == "DSG_emissions.xlsx" and 'emissions_comm' in df.columns:
                            df = df[df['emissions_comm'] == 'GWP_100']

                        # 2. Remove the 'file' column
                        if 'file' in df.columns:
                            df = df.drop(columns=['file'])

                        # 3. Clean up 'scenario' column
                        if 'scenario' in df.columns:
                            # Remove the DSG_XXX... pattern and capitalize 's'
                            df['scenario'] = df['scenario'].str.replace(r"DSG_.*_simpl_s2020\.S", "", regex=True)
                            df['scenario'] = df['scenario'].str.replace("s", "S")

                        # 4. Insert disruption label
                        label = format_disruption_label(s_val)
                        df.insert(0, 'Probability of disruption', label)
                        
                        compiled_data[sector].append(df)
                    except Exception as e:
                        print(f"  > Error reading {sector} in {s_val}: {e}")

        # Save the consolidated data
        master_path = os.path.join(OUTPUT_DIR, master_file)
        with pd.ExcelWriter(master_path, engine='openpyxl') as writer:
            for sector, dfs in compiled_data.items():
                if dfs:
                    final_df = pd.concat(dfs, ignore_index=True)
                    final_df.to_excel(writer, sheet_name=sector, index=False)
                else:
                    pd.DataFrame().to_excel(writer, sheet_name=sector)

    print("\n✅ Consolidation complete. Files saved in:", OUTPUT_DIR)

if __name__ == "__main__":
    consolidate_data()