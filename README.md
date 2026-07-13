# Dashboard MTTR — Taller de Reparaciones

Dashboard interactivo del tiempo medio de reparación (MTTR) del taller. Los indicadores se calculan desde la hoja **IMPRESION** de la planilla de seguimiento (Google Sheets), pero **solo se publican agregados** por mes, tipo de equipo, clase y prioridad — ningún registro individual (TAG, OT, descripciones, motivos) sale de la planilla.

**Ver el dashboard:** https://mttr.esimsrldesarrollos.com.ar (túnel Cloudflare desde la PC del taller) · espejo: https://jesusriossantander-png.github.io/MTTR/

## Contenido

| Archivo | Descripción |
|---|---|
| `index.html` | Dashboard interactivo (HTML + SVG autocontenido, sin dependencias externas) |
| `data.js` | Indicadores agregados (mes × tipo × clase × prioridad) |
| `tools/parse_mttr.py` | Convierte el CSV de la hoja IMPRESION en `data.js` |
| `.github/workflows/update-data.yml` | Actualización automática 2 veces por día desde la planilla |
| `tunel.cmd` | Sirve el dashboard local y lo publica por túnel de Cloudflare |

## Qué muestra

- **KPIs**: MTTR del período, reparaciones egresadas, % de cumplimiento de fecha programada, equipos en taller.
- **Matriz mensual** de MTTR por tipo de equipo (como la hoja MTTR: meses en columnas, tipos en filas).
- **Métrica seleccionable**: días de reparación u **horas de taller** (ajuste + mecanizado, registrado desde jun 2025).
- MTTR mensual por clase (RG/RP), egresos por mes, MTTR por tipo y por prioridad, distribución de duraciones.
- Filtros por período, métrica, tipo, clase y prioridad. Modo claro/oscuro.

## Actualización automática

El workflow de GitHub Actions descarga la hoja IMPRESION a las 06:00 y 18:00 (hora Argentina), regenera `data.js` y publica solo si hay cambios. Requiere que la planilla siga compartida con enlace ("cualquiera con el enlace puede ver"). También se puede ejecutar a mano desde **Actions → Actualizar datos desde la planilla → Run workflow**.

## Túnel de Cloudflare (mttr.esimsrldesarrollos.com.ar)

El túnel **esimpc** de esta PC publica `http://127.0.0.1:8747` como `mttr.esimsrldesarrollos.com.ar`. Requiere:

1. El hostname agregado en Cloudflare Zero Trust → Networks → Tunnels → esimpc → *Public Hostname* (`mttr.esimsrldesarrollos.com.ar` → HTTP → `localhost:8747`). El túnel es administrado remotamente, por lo que la regla debe estar en el dashboard (el `config.yml` local no aplica).
2. El servidor local corriendo: doble clic a `servidor-mttr.vbs`, o copiarlo a la carpeta `shell:startup` para que arranque con Windows.

Alternativa sin dominio: `tunel.cmd` crea un túnel rápido `https://….trycloudflare.com` (URL distinta en cada ejecución).

## Metodología

- **MTTR en días** = promedio de días corridos entre fecha de ingreso y fecha de egreso real, sobre los equipos egresados en el período.
- **MTTR en horas** = promedio de horas de taller (ajuste + mecanizado) por reparación.
- **Cumplimiento** = % de egresos con fecha real ≤ fecha programada.
- Registros sin fecha de egreso se cuentan como "en taller". Se excluyen fechas ilegibles o con errores de tipeo (<1%).
