# Dashboard MTTR — Taller de Reparaciones

Dashboard interactivo del tiempo medio de reparación (MTTR) del taller, generado a partir de la hoja **IMPRESION** de la planilla de seguimiento (Google Sheets).

**Ver el dashboard:** https://jesusriossantander-png.github.io/MTTR/

## Contenido

| Archivo | Descripción |
|---|---|
| `index.html` | Dashboard interactivo (HTML + SVG autocontenido, sin dependencias externas) |
| `data.js` | Datos limpios extraídos de la hoja IMPRESION (1.053 reparaciones, 2024 → jul 2026) |
| `tools/parse_mttr.py` | Script que convierte el CSV exportado de la hoja IMPRESION en `data.js` |

## Qué muestra

- **KPIs**: MTTR del período, reparaciones egresadas, % de cumplimiento de fecha programada, equipos en taller sin egreso.
- **MTTR mensual** por clase de reparación (RG = general, RP = parcial).
- **Egresos por mes** apilados por clase.
- **MTTR por tipo de equipo** y **por prioridad**, distribución de duraciones.
- **Tabla de reparaciones más largas** con motivo de retraso, y tabla de datos completa.
- Filtros por período, tipo de equipo, clase y prioridad. Modo claro/oscuro.

## Metodología

- **MTTR** = promedio de días corridos entre la fecha de ingreso (`F. ING`) y la fecha de egreso real (`REAL`), sobre los equipos egresados en el período.
- **Cumplimiento** = % de egresos con fecha real ≤ fecha programada.
- Registros sin fecha de egreso se cuentan como "en taller". Se excluyen fechas ilegibles o inconsistentes (<1%).

## Actualizar los datos

1. Exportar la hoja IMPRESION como CSV:
   `https://docs.google.com/spreadsheets/d/<ID>/gviz/tq?tqx=out:csv&sheet=IMPRESION`
2. Ejecutar `python tools/parse_mttr.py impresion.csv` (genera `records.json` y con el paso de slim, `data.js`).
3. Reemplazar `data.js` y hacer push.
