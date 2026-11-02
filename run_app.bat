@echo off
title SecureCode AI - Launcher (RTX 3050 GPU Enabled)
echo ======================================================================
echo             SECURECODE AI - ONE-CLICK SYSTEM LAUNCHER
echo ======================================================================
echo.

if exist "C:\Users\tusha\miniconda3\condabin\conda.bat" (
    echo [SecureCode AI] Activating local GPU conda environment (nlp_gpu)...
    call "C:\Users\tusha\miniconda3\condabin\conda.bat" activate nlp_gpu
)

python run_app.py
pause
