@echo off
rem Servidor local del dashboard MTTR + sincronizacion automatica.
rem - Sirve esta carpeta en http://127.0.0.1:8747 (para el tunel de Cloudflare)
rem - Boton "Actualizar datos" del dashboard (endpoint /actualizar)
rem - Cada 30 minutos baja de GitHub los datos nuevos (git pull)
cd /d "%~dp0"
python tools\servidor.py
