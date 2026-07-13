' Servidor local del dashboard MTTR (corre oculto, sin ventana).
' Sirve F:\mttr en http://127.0.0.1:8747 para el tunel de Cloudflare
' y baja de GitHub los datos nuevos cada 30 minutos.
'
' PARA QUE ARRANQUE SOLO CON WINDOWS (hacerlo una sola vez):
'   1. Presiona Win+R, escribe:  shell:startup   y da Enter.
'   2. Copia este archivo (servidor-mttr.vbs) a esa carpeta.
'
' Para iniciarlo a mano ahora mismo: doble clic a este archivo.
Set sh = CreateObject("WScript.Shell")
sh.Run """F:\mttr\servidor-mttr.cmd""", 0, False
