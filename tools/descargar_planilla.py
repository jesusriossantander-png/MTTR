# -*- coding: utf-8 -*-
"""Descarga la planilla como xlsx.

Si existe una credencial de cuenta de servicio de Google (archivo
service-account.json junto al repo, o la ruta en la variable de entorno
GOOGLE_APPLICATION_CREDENTIALS), descarga AUTENTICADO vía la API de Drive:
la planilla puede estar restringida (sin enlace público).

Si no hay credencial, cae al enlace público de exportación (requiere que la
planilla esté compartida como "cualquiera con el enlace puede ver").

Uso:  python tools/descargar_planilla.py destino.xlsx
"""
import os, sys, urllib.request

SHEET_ID = '1uH6TZzYi00e3KIPT4sZUh_1naR8pJGZx46FMEol_jho'
MIME_XLSX = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def _credencial():
    ruta = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS') or os.path.join(RAIZ, 'service-account.json')
    return ruta if os.path.exists(ruta) else None

def descargar(destino):
    """Devuelve 'privado' o 'publico' según el método usado."""
    cred = _credencial()
    if cred:
        try:
            from google.oauth2 import service_account
            from google.auth.transport.requests import Request
            creds = service_account.Credentials.from_service_account_file(
                cred, scopes=['https://www.googleapis.com/auth/drive.readonly'])
            creds.refresh(Request())
            url = (f'https://www.googleapis.com/drive/v3/files/{SHEET_ID}/export'
                   f'?mimeType={urllib.parse.quote(MIME_XLSX)}')
            req = urllib.request.Request(url, headers={'Authorization': f'Bearer {creds.token}'})
            with urllib.request.urlopen(req, timeout=90) as r, open(destino, 'wb') as f:
                f.write(r.read())
            return 'privado'
        except Exception as e:
            print(f'AVISO: descarga autenticada falló ({type(e).__name__}: {e}); '
                  'intento con el enlace público.', file=sys.stderr)
    url = f'https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=xlsx'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=90) as r, open(destino, 'wb') as f:
        f.write(r.read())
    return 'publico'

if __name__ == '__main__':
    destino = sys.argv[1] if len(sys.argv) > 1 else 'planilla.xlsx'
    modo = descargar(destino)
    kb = os.path.getsize(destino) // 1024
    if kb < 300:
        print(f'ERROR: descarga incompleta ({kb} KB).')
        sys.exit(1)
    print(f'OK: {destino} ({kb} KB, acceso {modo})')
