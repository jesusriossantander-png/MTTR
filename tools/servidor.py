# -*- coding: utf-8 -*-
"""Servidor local del dashboard MTTR con actualización a pedido.

- Sirve la carpeta del dashboard en http://127.0.0.1:8747 (para el túnel).
- GET/POST /actualizar: descarga la planilla de Google, regenera data.js con
  tools/parse_mttr.py y hace push a GitHub para que el espejo también se
  actualice. Con límite de 1 ejecución cada 2 minutos.

Uso:  python tools/servidor.py
"""
import http.server, json, os, subprocess, sys, tempfile, threading, time, urllib.request

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUERTO = 8747
PLANILLA = ('https://docs.google.com/spreadsheets/d/'
            '1uH6TZzYi00e3KIPT4sZUh_1naR8pJGZx46FMEol_jho/export?format=xlsx')
MIN_INTERVALO = 60  # segundos entre actualizaciones

estado = {'ultima': 0.0, 'corriendo': False, 'lock': threading.Lock()}

def actualizar():
    with tempfile.TemporaryDirectory() as tmp:
        xlsx = os.path.join(tmp, 'planilla.xlsx')
        req = urllib.request.Request(PLANILLA, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=60) as r, open(xlsx, 'wb') as f:
            f.write(r.read())
        if os.path.getsize(xlsx) < 300000:
            return {'ok': False, 'msg': 'La descarga de la planilla vino incompleta.'}
        r = subprocess.run([sys.executable, os.path.join(RAIZ, 'tools', 'parse_mttr.py'),
                            xlsx, os.path.join(RAIZ, 'data.js')],
                           capture_output=True, text=True, cwd=RAIZ, timeout=120)
        if r.returncode != 0:
            return {'ok': False, 'msg': 'Error al procesar la planilla: ' + (r.stdout + r.stderr)[-300:]}
        resumen = r.stdout.strip().splitlines()[-1] if r.stdout.strip() else 'OK'
    cambio = subprocess.run(['git', 'diff', '--quiet', 'data.js'], cwd=RAIZ).returncode != 0
    push = ''
    if cambio:
        try:
            subprocess.run(['git', 'add', 'data.js'], cwd=RAIZ, timeout=30)
            subprocess.run(['git', 'commit', '-m', 'Actualización manual desde el dashboard'],
                           cwd=RAIZ, capture_output=True, timeout=30)
            p = subprocess.run(['git', 'push'], cwd=RAIZ, capture_output=True, timeout=90)
            push = ' Publicado también en GitHub.' if p.returncode == 0 else ' (No se pudo publicar a GitHub; el túnel ya está actualizado.)'
        except Exception:
            push = ' (No se pudo publicar a GitHub; el túnel ya está actualizado.)'
        return {'ok': True, 'msg': 'Datos actualizados. ' + resumen + push}
    return {'ok': True, 'msg': 'Sin cambios: la planilla no tiene datos nuevos. ' + resumen}

class Manejador(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=RAIZ, **kw)

    def log_message(self, *a):  # silencioso
        pass

    def responder(self, code, obj):
        cuerpo = json.dumps(obj, ensure_ascii=False).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Content-Length', str(len(cuerpo)))
        self.end_headers()
        self.wfile.write(cuerpo)

    def manejar_actualizar(self):
        with estado['lock']:
            if estado['corriendo']:
                return self.responder(429, {'ok': False, 'msg': 'Ya hay una actualización en curso.'})
            resto = MIN_INTERVALO - (time.time() - estado['ultima'])
            if resto > 0:
                return self.responder(429, {'ok': False, 'espera': int(resto) + 1,
                    'msg': 'Actualización disponible en unos segundos.'})
            estado['corriendo'] = True
        try:
            resultado = actualizar()
            estado['ultima'] = time.time()
            resultado['espera'] = MIN_INTERVALO
            self.responder(200 if resultado['ok'] else 500, resultado)
        except Exception as e:
            self.responder(500, {'ok': False, 'msg': f'Error: {type(e).__name__}'})
        finally:
            estado['corriendo'] = False

    def do_POST(self):
        if self.path.split('?')[0] == '/actualizar':
            return self.manejar_actualizar()
        self.send_error(404)

    def do_GET(self):
        if self.path.split('?')[0] == '/actualizar':
            return self.manejar_actualizar()
        super().do_GET()

def bucle_pull():
    """Trae cambios de GitHub cada 30 min (por si el workflow programado publicó)."""
    while True:
        time.sleep(1800)
        try:
            subprocess.run(['git', 'pull', '--ff-only', '--quiet'], cwd=RAIZ,
                           capture_output=True, timeout=90)
        except Exception:
            pass

if __name__ == '__main__':
    threading.Thread(target=bucle_pull, daemon=True).start()
    with http.server.ThreadingHTTPServer(('127.0.0.1', PUERTO), Manejador) as srv:
        print(f'Dashboard MTTR en http://127.0.0.1:{PUERTO} (con /actualizar)')
        srv.serve_forever()
