# -*- coding: utf-8 -*-
"""Parse IMPRESION sheet CSV into clean JSON records for the MTTR dashboard."""
import csv, re, json, sys
from datetime import date

MESES = {'ene':1,'feb':2,'mar':3,'abr':4,'may':5,'jun':6,'jul':7,'ago':8,
         'sep':9,'set':9,'oct':10,'nov':11,'dic':12}

def parse_date(s, ref=None):
    """Parse d/m/yyyy, d/m/yy, d/m (no year), or 'd-mmm' Spanish. ref=(y,m,d) fallback for year."""
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
        y = ref.year + (1 if mo < ref.month - 6 else 0)  # rolled past year end
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

rows = list(csv.reader(open(sys.argv[1], encoding='utf-8')))[1:]
records, skipped = [], 0
for r in rows:
    if len(r) < 16:
        skipped += 1; continue
    tag = clean(r[0])
    fing = parse_date(r[3])
    if not tag and not fing:
        skipped += 1; continue
    if not fing:
        skipped += 1; continue
    prog = parse_date(r[5], ref=fing)
    real = parse_date(r[6], ref=fing)
    inicio = parse_date(r[7], ref=fing)
    av = clean(r[8]).replace('%', '')
    try: av = int(round(float(av)))
    except ValueError: av = None
    dias = (real - fing).days if real else None
    if dias is not None and (dias < 0 or dias > 3000):
        dias = None  # date typo
    atraso = (real - prog).days if (real and prog) else None
    if atraso is not None and abs(atraso) > 400:
        atraso = None
    rec = {
        'tag': tag, 'ot': clean(r[1]), 'prio': clean(r[2]) or '-',
        'fing': fing.isoformat(),
        'prog': prog.isoformat() if prog else None,
        'real': real.isoformat() if real else None,
        'inicio': inicio.isoformat() if inicio else None,
        'av': av,
        'desc': clean(r[4]), 'motivo': clean(r[10]),
        'tipo': clean(r[11]).upper() or 'S/D',
        'clase': clean(r[12]).upper(),         # RG / RP
        'estado': clean(r[13]), 'resp': clean(r[14]).upper(), 'area': clean(r[15]).upper(),
        'dias': dias, 'atraso': atraso,
        'mesReal': real.strftime('%Y-%m') if real else None,
        'mesIng': fing.strftime('%Y-%m'),
    }
    if rec['clase'] not in ('RG', 'RP'):
        rec['clase'] = 'S/D'
    records.append(rec)

records.sort(key=lambda x: x['fing'])
json.dump(records, open('records.json', 'w', encoding='utf-8'), ensure_ascii=False)
print('records:', len(records), 'skipped:', skipped)
from collections import Counter
c = Counter(x['mesReal'] for x in records if x['mesReal'])
print('months with REAL:', sorted(c.items())[:5], '...', sorted(c.items())[-5:])
print('with dias:', sum(1 for x in records if x['dias'] is not None))
print('clase:', Counter(x['clase'] for x in records))
print('tipo top:', Counter(x['tipo'] for x in records).most_common(15))
print('avg dias overall:', round(sum(x['dias'] for x in records if x['dias'] is not None)/max(1,sum(1 for x in records if x['dias'] is not None)),1))
