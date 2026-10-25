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
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
echo.

:: 3. Creation automatique du raccourci Bureau via PowerShell (sans VBS)
echo [RACCOURCI] Creation du raccourci Bureau "Speech to Translate"...
powershell -Command "$WScriptShell = New-Object -ComObject WScript.Shell; $Shortcut = $WScriptShell.CreateShortcut([System.Environment]::GetFolderPath('Desktop') + '\Speech to Translate.lnk'); $Shortcut.TargetPath = '%~f0'; $Shortcut.WorkingDirectory = '%~dp0'; $Shortcut.Description = 'Speech to Translate - Traduction Vocale IA'; if (Test-Path '%~dp0icon.ico') { $Shortcut.IconLocation = '%~dp0icon.ico' } else { if (Test-Path '%~dp0ICO\dango_translate_icon.ico') { $Shortcut.IconLocation = '%~dp0ICO\dango_translate_icon.ico' } }; $Shortcut.Save()"
echo.

echo ======================================================================
echo  Lancement de l'application Speech to Translate...
echo ======================================================================
python main.py

pause
