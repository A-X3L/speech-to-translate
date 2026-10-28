@echo off
title Speech to Translate - Lanceur IA
chcp 65001 >nul
echo ======================================================================
echo  SPEECH TO TRANSLATE - Lancement et Verification
echo ======================================================================
echo.

cd /d "%~dp0"

:: 1. Gestion de la configuration (config.json)
if not exist "config.json" (
    echo [INFO] config.json sera genere automatiquement au lancement.
    echo Pour obtenir une cle API gratuite, consultez help.html
    echo.
)

:: 2. Installation automatique des dependances Python
echo [INSTALLATION] Verification et installation des dependances (requirements.txt)...
python -m pip install -q --upgrade pip
python -m pip install -q -r requirements.txt
echo.

:: 3. Creation automatique du raccourci Bureau en mode silencieux (pythonw)
echo [RACCOURCI] Creation/mise a jour du raccourci Bureau "Speech to Translate"...
powershell -NoProfile -Command ^
    "$WScriptShell = New-Object -ComObject WScript.Shell; " ^
    "$Shortcut = $WScriptShell.CreateShortcut([System.Environment]::GetFolderPath('Desktop') + '\Speech to Translate.lnk'); " ^
    "$Shortcut.TargetPath = 'pythonw.exe'; " ^
    "$Shortcut.Arguments = '\"%~dp0main.py\"'; " ^
    "$Shortcut.WorkingDirectory = '%~dp0'; " ^
    "$Shortcut.Description = 'Speech to Translate - Traduction Vocale IA (Mode Silencieux)'; " ^
    "if (Test-Path '%~dp0assets\STT2.ico') { $Shortcut.IconLocation = '%~dp0assets\STT2.ico,0' }; " ^
    "$Shortcut.Save()"
echo.

:: 4. Lancement en mode GUI pur (sans console d'arriere-plan)
echo ======================================================================
echo  Lancement de Speech to Translate en mode silencieux (GUI pur)...
echo ======================================================================
start "" pythonw "%~dp0main.py"
exit
