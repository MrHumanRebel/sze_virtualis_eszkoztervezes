@echo off
setlocal EnableExtensions EnableDelayedExpansion
chcp 65001 >nul
cd /d "%~dp0"
set "NEPTUN="
set /a COUNT=0

if not exist "output\*.spp" (
    echo HIBA: Nincs .spp az output mappaban.
    pause
    exit /b 1
)

for %%F in (output\*.spp) do (
    set /a COUNT+=1
    set "NEPTUN=%%~nF"
)
if not "!COUNT!"=="1" (
    echo HIBA: Pontosan egy SPP legyen az output mappaban.
    echo Jelenleg !COUNT! talalhato.
    pause
    exit /b 1
)

echo.
echo Korabbi Siemens modell es eredmenyek ellenorzese...
echo Nem futtatjuk ujra a 10000 darabos szimulaciot.
echo.
call "%~dp0INDITAS.bat" --evidence-only --neptun !NEPTUN!
exit /b %ERRORLEVEL%
