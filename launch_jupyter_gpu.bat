@echo off
REM ==============================================================================
REM SecureCode AI — Launch Local GPU JupyterLab (NVIDIA RTX 3050)
REM ==============================================================================

echo [SecureCode AI] Activating GPU Environment (nlp_gpu)...
call C:\Users\tusha\miniconda3\condabin\conda.bat activate nlp_gpu

if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to activate nlp_gpu conda environment.
    pause
    exit /b 1
)

echo [SecureCode AI] Starting JupyterLab on local RTX 3050 GPU...
cd /d "%~dp0"
jupyter lab --notebook-dir="%~dp0"
pause
