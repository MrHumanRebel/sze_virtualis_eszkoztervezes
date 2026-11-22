@echo off
setlocal EnableExtensions
chcp 65001 >nul
cd /d "%~dp0"
title SzE Plant Simulation - 2D beadando

where py >nul 2>nul
if not errorlevel 1 (
    set "PY=py -3"
) else (
    where python >nul 2>nul
    if errorlevel 1 (
        echo HIBA: Python 3 nincs telepitve. https://www.python.org/downloads/windows/
        pause
        exit /b 1
    )
    set "PY=python"
)

echo.
echo Telepites / Python csomag ellenorzese...
%PY% -m pip install -e ".[windows]"
if errorlevel 1 (
    echo HIBA: Python vagy pywin32 telepitesi problema.
    pause
    exit /b 1
)
echo.
echo Fontos: .spp csak valodi Siemens Plant Simulation alatt jon letre.
echo A Neptun-kodod lesz a fajlnev. Az egyetemi feltetelek szerint
echo beadashoz az output mappabol csak a sajat NEPTUNKOD.spp kell.
echo.
%PY% -m sze_virtualis_eszkoztervezes %*
set "RESULT=%ERRORLEVEL%"
echo.
if not "%RESULT%"=="0" (
    echo Nem teljesult minden ellenorzes! Ne add be ellenorzes nelkul.
    echo Reszletek: output\run.log es output\config_validation.json
) else (
    echo Sikeres programfutas. Ellenorizd a valodi .spp modellt Siemensben.
)
pause
exit /b %RESULT%
