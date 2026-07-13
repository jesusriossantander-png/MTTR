@echo off
rem Servidor local del dashboard MTTR + sincronizacion automatica.
rem - Sirve esta carpeta en http://127.0.0.1:8747 (para el tunel de Cloudflare)
rem - Cada 30 minutos baja de GitHub los datos nuevos (git pull)
cd /d "%~dp0"
start "servidor-mttr" /b python -m http.server 8747 --bind 127.0.0.1 --directory "%~dp0"
:loop
git pull --ff-only --quiet >nul 2>&1
timeout /t 1800 /nobreak >nul
goto loop
