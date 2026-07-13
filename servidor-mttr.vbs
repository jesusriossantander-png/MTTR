' Servidor local del dashboard MTTR (corre oculto, sin ventana).
' Sirve F:\mttr en http://127.0.0.1:8747 para el tunel de Cloudflare.
'
' PARA QUE ARRANQUE SOLO CON WINDOWS (hacerlo una sola vez):
'   1. Presiona Win+R, escribe:  shell:startup   y da Enter.
'   2. Copia este archivo (servidor-mttr.vbs) a esa carpeta.
'
' Para iniciarlo a mano ahora mismo: doble clic a este archivo.
Set sh = CreateObject("WScript.Shell")
sh.Run "python -m http.server 8747 --bind 127.0.0.1 --directory F:\mttr", 0, False
