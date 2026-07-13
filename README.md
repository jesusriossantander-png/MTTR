# Dashboard MTTR — Taller de Reparaciones

Dashboard interactivo del tiempo medio de reparación (MTTR) del taller. Muestra **los mismos valores de la hoja MTTR** de la planilla (Reparaci., Represent., MTTR por prioridad y total, en días y horas), mes por mes, leídos directamente del Excel exportado — ningún registro individual (TAG, OT, descripciones, motivos) sale de la planilla.

**Ver el dashboard:** https://mttr.esimsrldesarrollos.com.ar (túnel Cloudflare desde la PC del taller) · espejo: https://jesusriossantander-png.github.io/MTTR/

## Contenido

| Archivo | Descripción |
|---|---|
| `index.html` | Dashboard interactivo (HTML + SVG autocontenido, sin dependencias externas) |
| `data.js` | Valores de la hoja MTTR por mes y tipo de equipo (días y horas) |
| `tools/parse_mttr.py` | Lee la hoja MTTR del xlsx exportado y genera `data.js` |
| `.github/workflows/update-data.yml` | Actualización automática 2 veces por día desde la planilla |
| `tunel.cmd` | Sirve el dashboard local y lo publica por túnel de Cloudflare |

## Qué muestra

- **Selector de mes**: tabla del mes en el formato exacto de la hoja MTTR (Reparaci. | Reparaci. Represent | MTTR prioridad 0/1/2 | MTTR total), en **días** y en **horas** (desde ago 2025).
- KPIs del mes, evolución mensual del MTTR (ene 2024 → hoy), matriz tipo × mes, MTTR por tipo y egresos por mes.
- Modo claro/oscuro. Sin dependencias externas.

## Actualización automática

El workflow de GitHub Actions descarga la planilla completa (xlsx) a las 06:00 y 18:00 (hora Argentina), regenera `data.js` y publica solo si hay cambios. Requiere que la planilla siga compartida con enlace ("cualquiera con el enlace puede ver"). También se puede ejecutar a mano desde **Actions → Actualizar datos desde la planilla → Run workflow**.

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
