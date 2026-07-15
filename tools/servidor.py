# -*- coding: utf-8 -*-
"""Servidor local del dashboard MTTR con actualización a pedido.

- Sirve SOLO los archivos del dashboard (index.html, data.js, logo) en
  http://127.0.0.1:8747 para el túnel de Cloudflare. El resto (código,
  .git, scripts) responde 404.
- GET/POST /actualizar: requiere la clave del archivo clave-actualizar.txt
  (header X-Clave). Descarga la planilla (autenticada si hay
  service-account.json; pública si no), regenera data.js con
  tools/parse_mttr.py y hace push a GitHub para actualizar el espejo.
  Límite: 1 ejecución por minuto (MIN_INTERVALO).

Uso:  python tools/servidor.py
"""
import http.server, json, os, secrets, subprocess, sys, tempfile, threading, time

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import descargar_planilla

PUERTO = 8747
MIN_INTERVALO = 60  # segundos entre actualizaciones
PERMITIDOS = {'/', '/index.html', '/data.js', '/logo-esim.png', '/favicon.ico'}

def cargar_clave():
    ruta = os.path.join(RAIZ, 'clave-actualizar.txt')
    try:
        clave = open(ruta, encoding='utf-8').read().strip()
        if clave:
            return clave
    except FileNotFoundError:
        pass
    clave = secrets.token_hex(4)
    with open(ruta, 'w', encoding='utf-8') as f:
        f.write(clave + '\n')
    print(f'Se generó una clave nueva en {ruta}')
    return clave

CLAVE = cargar_clave()
estado = {'ultima': 0.0, 'corriendo': False, 'lock': threading.Lock()}

def actualizar():
    with tempfile.TemporaryDirectory() as tmp:
        xlsx = os.path.join(tmp, 'planilla.xlsx')
        modo = descargar_planilla.descargar(xlsx)
        if os.path.getsize(xlsx) < 50000:  # la espejo pesa ~130 KB; el login de Google, ~9 KB
            return {'ok': False, 'msg': 'La descarga de la planilla vino incompleta.'}
        print(f'planilla descargada (acceso {modo})')
        r = subprocess.run([sys.executable, os.path.join(RAIZ, 'tools', 'parse_mttr.py'),
                            xlsx, os.path.join(RAIZ, 'data.js')],
                           capture_output=True, text=True, cwd=RAIZ, timeout=120)
        if r.returncode != 0:
            print('parse_mttr fallo:', (r.stdout + r.stderr)[-500:])
            return {'ok': False, 'msg': 'No se pudo procesar la planilla; revisar la hoja MTTR.'}
        print(r.stdout.strip())
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
        return {'ok': True, 'msg': 'Datos actualizados.' + push}
    return {'ok': True, 'msg': 'Sin cambios: la planilla no tiene datos nuevos.'}

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
        if not secrets.compare_digest(self.headers.get('X-Clave', ''), CLAVE):
            return self.responder(401, {'ok': False, 'auth': True,
                'msg': 'Clave incorrecta o faltante.'})
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
        ruta = self.path.split('?')[0]
        if ruta == '/actualizar':
            return self.manejar_actualizar()
        if ruta == '/favicon.ico':
            self.send_response(301); self.send_header('Location', '/logo-esim.png'); self.end_headers()
            return
        if ruta not in PERMITIDOS:
            return self.send_error(404)
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
        print(f'Dashboard MTTR en http://127.0.0.1:{PUERTO} (con /actualizar protegido por clave)')
        srv.serve_forever()
