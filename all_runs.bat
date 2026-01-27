@echo off
REM ============================================
REM Sequential TEMOA-Stochastic runs (Windows .bat version)
REM ============================================

setlocal enabledelayedexpansion
set BASE_DIR=D:\pietro_casarin\Pietro\Pietro\Pietro
set LOG_DIR=%BASE_DIR%\logs

if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

echo Starting all runs at %date% %time%
echo.

REM REM ========== MAIN STOCHASTIC CSD RUNS ==========
REM for %%S in (8515) do (
REM     echo Running stochastic case CSD%%S ...
REM     cd /d "%BASE_DIR%\CSD%%S"
REM     python temoa_model\temoa_stochastic.py --config=temoa_model\config_sample > "%LOG_DIR%\CSD%%S.log" 2>&1
REM )

REM ========== MAIN STOCHASTIC DSG RUNS ==========
for %%S in (6040 7030 8020 9010) do (
    echo Running stochastic case DSG%%S ...
    cd /d "%BASE_DIR%\DSG%%S"
    python temoa_model\temoa_stochastic.py --config=temoa_model\config_sample > "%LOG_DIR%\DSG%%S.log" 2>&1
)

REM ========== POST-PROCESSING ==========
for %%S in (NZE DSG) do (
    echo Running post-processing for DSG%%S ...
    conda activate temoa
    cd /d "%BASE_DIR%\DSG%%S\data_files\2030-2050_simpl\s2020\Full_stochastic"

    python Material_SUP.py   > "%LOG_DIR%\DSG%%S_postprocessing_Material_SUP.log"   2>&1
    python Power.py   > "%LOG_DIR%\DSG%%S_postprocessing_Power_sector.log"   2>&1
    python Storage.py        > "%LOG_DIR%\DSG%%S_postprocessing_Storage.log"        2>&1
    python Transport.py      > "%LOG_DIR%\DSG%%S_postprocessing_Transport.log"      2>&1
    python Agriculture.py          > "%LOG_DIR%\DSG%%S_postprocessing_Agriculture.log"          2>&1
    python C-.py          > "%LOG_DIR%\DSG%%S_postprocessing_C-.log"          2>&1
    python C+.py          > "%LOG_DIR%\DSG%%S_postprocessing_C+.log"          2>&1
    python CCUS.py          > "%LOG_DIR%\DSG%%S_postprocessing_CCUS.log"          2>&1
    python COM.py          > "%LOG_DIR%\DSG%%S_postprocessing_COM.log"          2>&1
    python FT.py          > "%LOG_DIR%\DSG%%S_postprocessing_FT.log"          2>&1
    python H2.py          > "%LOG_DIR%\DSG%%S_postprocessing_H2.log"          2>&1
    python IND.py          > "%LOG_DIR%\DSG%%S_postprocessing_IND.log"          2>&1
    python RES.py          > "%LOG_DIR%\DSG%%S_postprocessing_RES.log"          2>&1
    python UPS.py          > "%LOG_DIR%\DSG%%S_postprocessing_UPS.log"          2>&1
)
cd "%BASE_DIR%"
    echo Running final post-processing for all scenarios
    python Merging_postprocessing.py

echo.
echo ✅ All runs completed successfully at %date% %time%
pause
