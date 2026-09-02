@echo off
title Installation du Raccourci Bureau - Xbox Voice Translator
echo ======================================================================
echo  Creation du Raccourci Bureau Windows avec l'Icone Officielle Gaming
echo ======================================================================
echo.

set SCRIPT_DIR=%~dp0
set TARGET_BAT=%SCRIPT_DIR%run_xbox_translator.bat
set ICON_IMG=%SCRIPT_DIR%icon.ico

set VBS_SCRIPT=%TEMP%\CreateXboxShortcut_%RANDOM%.vbs

echo Set oWS = WScript.CreateObject("WScript.Shell") > "%VBS_SCRIPT%"
echo sLinkFile = oWS.SpecialFolders("Desktop") ^& "\Xbox Voice Translator FR-EN.lnk" >> "%VBS_SCRIPT%"
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> "%VBS_SCRIPT%"
echo oLink.TargetPath = "%TARGET_BAT%" >> "%VBS_SCRIPT%"
echo oLink.WorkingDirectory = "%SCRIPT_DIR%" >> "%VBS_SCRIPT%"
echo oLink.Description = "Xbox Game Bar & Forza Horizon - Traducteur Push-to-Talk" >> "%VBS_SCRIPT%"
if exist "%ICON_IMG%" (
    echo oLink.IconLocation = "%ICON_IMG%" >> "%VBS_SCRIPT%"
)
echo oLink.Save >> "%VBS_SCRIPT%"

cscript //nologo "%VBS_SCRIPT%"
del "%VBS_SCRIPT%"

echo [SUCCES] Le raccourci "Xbox Voice Translator FR-EN" a ete cree sur votre Bureau avec l'icone icon.ico !
echo.
pause
