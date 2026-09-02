@echo off
title Xbox Game Bar Voice Translator FR-EN
echo ==============================================================
echo  Xbox Game Bar / Forza Horizon - Traducteur Vocal Instantane IA
echo ==============================================================
echo.

:: Verification de Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERREUR] Python n'est pas installe ou pas ajoute au PATH !
    echo Telechargez Python 3.10+ depuis https://www.python.org/downloads/
    pause
    exit /b
)

:: Verification du dossier venv
if not exist "venv" (
    echo [1/3] Creation de l'environnement virtuel Python (venv)...
    python -m venv venv
)

:: Activation et installation des dependances
echo [2/3] Verification des dependances...
call venv\Scripts\activate.bat
pip install -r requirements.txt --quiet

:: Lancement du script
echo [3/3] Lancement du traducteur Push-to-Talk...
echo.
python main.py

pause
