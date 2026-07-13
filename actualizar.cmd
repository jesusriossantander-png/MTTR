@echo off
rem Trae AHORA los ultimos datos publicados en GitHub al servidor local del tunel.
cd /d "%~dp0"
git pull --ff-only
echo.
echo Listo. El tunel ya sirve la ultima version.
pause
