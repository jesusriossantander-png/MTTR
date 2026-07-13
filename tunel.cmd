@echo off
rem ============================================================
rem  Publica el dashboard MTTR por tunel de Cloudflare.
rem  Requiere: python y cloudflared instalados.
rem  La URL https://xxxx.trycloudflare.com aparece abajo;
rem  cambia en cada ejecucion. Cerrar esta ventana corta el tunel.
rem ============================================================
cd /d "%~dp0"
echo Iniciando servidor local en http://127.0.0.1:8747 ...
start "servidor-mttr" /min python -m http.server 8747 --bind 127.0.0.1 --directory "%~dp0"
echo Abriendo tunel de Cloudflare (buscar la URL *.trycloudflare.com):
echo.
cloudflared tunnel --url http://127.0.0.1:8747
taskkill /fi "WINDOWTITLE eq servidor-mttr*" /f >nul 2>&1
