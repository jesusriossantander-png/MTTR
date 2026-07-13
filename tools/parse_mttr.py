# -*- coding: utf-8 -*-
"""Convierte el CSV exportado de la hoja IMPRESION en data.js para el dashboard.

Criterios (siguiendo la hoja MTTR donde es reproducible):
- Cada reparación se cuenta en el mes de su fecha de egreso REAL.
- Las reparaciones marcadas "NO" en la columna de representativas cuentan como
  egresadas pero se excluyen del promedio MTTR (días y horas), igual que en la
  hoja MTTR.

Solo publica AGREGADOS (mes x tipo x clase x prioridad); los registros
individuales (TAG, OT, descripciones, motivos) nunca salen de este script.

Uso:  python tools/parse_mttr.py impresion.csv [data.js]
"""
import csv, re, json, sys
from datetime import date

MESES = {'ene':1,'feb':2,'mar':3,'abr':4,'may':5,'jun':6,'jul':7,'ago':8,
         'sep':9,'set':9,'oct':10,'nov':11,'dic':12}
DESDE = date(2024, 1, 1)   # inicio de la serie publicada
BINS = [(0,1),(2,5),(6,10),(11,20),(21,40),(41,80),(81,10**9)]

def parse_date(s, ref=None):
    """Acepta d/m/aaaa, d/m/aa, d/m (sin año) y 'd-mmm' en español. ref da el año base."""
    s = (s or '').strip().lower()
    if not s or s in ('-', '--'):
        return None
    m = re.match(r'^(\d{1,2})/(\d{1,2})/(\d{2,4})$', s)
    if m:
        d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if y < 100: y += 2000
        try: return date(y, mo, d)
        except ValueError: return None
    m = re.match(r'^(\d{1,2})/(\d{1,2})$', s)
    if m and ref:
        d, mo = int(m.group(1)), int(m.group(2))
        y = ref.year + (1 if mo < ref.month - 6 else 0)
        try: return date(y, mo, d)
        except ValueError: return None
    m = re.match(r'^(\d{1,2})\s*-\s*([a-zñ]{3,4})\.?$', s)
    if m and ref:
        d, mo = int(m.group(1)), MESES.get(m.group(2)[:3])
        if not mo: return None
        y = ref.year + (1 if mo < ref.month - 6 else 0)
        try: return date(y, mo, d)
        except ValueError: return None
    return None

def clean(s):
    return re.sub(r'\s+', ' ', (s or '').strip())

def horas(s):
    """HORAS TOTALES viene con coma decimal ('33,5')."""
    s = (s or '').strip().replace(',', '.')
    try:
        v = float(s)
        return v if 0 < v < 20000 else None
    except ValueError:
        return None

def main():
    src = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else 'data.js'
    rows = list(csv.reader(open(src, encoding='utf-8')))[1:]
    hoy = date.today()

    groups, wip = {}, {}
    total, nrep_total, ult_egreso = 0, 0, None
    for r in rows:
        if len(r) < 16:
            continue
        fing = parse_date(r[3])
        if not fing:
            continue
        real = parse_date(r[6], ref=fing)
        tipo = clean(r[11]).upper() or 'S/D'
        clase = clean(r[12]).upper()
        if clase not in ('RG', 'RP'):
            clase = 'S/D'
        prio = clean(r[2]) or '-'
        if prio not in ('0', '1', '2', '3'):
            prio = '-'
        if not real:
            k = (tipo, clase, prio)
            wip[k] = wip.get(k, 0) + 1
            continue
        if real < DESDE or (real - hoy).days > 60:
            continue  # histórico previo a la serie, o fecha con error de tipeo
        mes = real.strftime('%Y-%m')
        representativa = clean(r[23]).upper() != 'NO' if len(r) > 23 else True
        dias = (real - fing).days
        if dias < 0 or dias > 3000:
            dias = None
        prog = parse_date(r[5], ref=fing)
        atraso = (real - prog).days if prog else None
        if atraso is not None and abs(atraso) > 400:
            atraso = None
        h = horas(r[25]) if len(r) > 25 else None
        total += 1
        ult_egreso = max(ult_egreso, real) if ult_egreso else real
        k = (mes, tipo, clase, prio)
        g = groups.setdefault(k, [0, 0, 0, 0, 0, 0, 0, 0.0, [0]*len(BINS)])
        g[0] += 1                                   # n egresadas (Reparaci.)
        if atraso is not None:
            g[3] += 1                               # n con fecha programada
            if atraso <= 0:
                g[4] += 1                           # n en fecha
        if not representativa:
            continue                                # excluida del MTTR, como en la hoja
        g[1] += 1                                   # n representativas
        nrep_total += 1
        if dias is not None:
            g[2] += 1; g[5] += dias                 # n con días, suma de días
            for i, (a, b) in enumerate(BINS):
                if a <= dias <= b:
                    g[8][i] += 1; break
        if h is not None:
            g[6] += 1; g[7] += h                    # n con horas, suma de horas

    if total < 300:
        print(f'ERROR: solo {total} egresos parseados; se aborta para no perder datos.')
        sys.exit(1)
    data = {
        # [mes, tipo, clase, prio, n, nRep, nDias, sumDias, nProg, nEnFecha, nHoras, sumHoras, bins]
        'groups': [[k[0], k[1], k[2], k[3], v[0], v[1], v[2], v[5], v[3], v[4], v[6], round(v[7], 1), v[8]]
                   for k, v in sorted(groups.items())],
        'wip': [[k[0], k[1], k[2], v] for k, v in sorted(wip.items())],
        'last': ult_egreso.isoformat(),
    }
    with open(out, 'w', encoding='utf-8') as f:
        f.write('const MTTR_DATA=' + json.dumps(data, ensure_ascii=False, separators=(',', ':')) + ';')
    print(f'OK: {total} egresos ({nrep_total} representativas) en {len(data["groups"])} grupos, '
          f'{sum(wip.values())} en taller -> {out}')

if __name__ == '__main__':
    main()
