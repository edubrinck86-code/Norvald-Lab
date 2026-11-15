"""Medidas do painel 5 × Sonnet (B1, B2) e do painel misto no conf2-mmlu, mesmas 140 perguntas."""
import json, itertools, random
from norvald_lab.infrastructure.arof.dataset_store import arof_data_root
from norvald_lab.measures.command import DEFAULT_ANSWERS, DEFAULT_BANKS
from norvald_lab.measures.observation_loader import ObservationLoader
from norvald_lab.measures.question_catalog import QuestionCatalog
key = json.load(open('/Users/macbook/Norvald-Lab/studies/herd/mmlu-pro/answers.json'))['answers']
def rho(T, ids):
    ms = sorted({m for q in ids for m in T[q]})
    ids = [q for q in ids if all(T[q].get(m) for m in ms)]
    E = [[T[q][m] != key[q] for q in ids] for m in ms]
    ph = []
    for x, y in itertools.combinations(E, 2):
        n = len(x); p = sum(a and b for a, b in zip(x, y)); a = sum(x); b = sum(y); d = (a*(n-a)*b*(n-b))**.5
        if d: ph.append((n*p - a*b)/d)
    r = sum(ph)/len(ph); return dict(n=len(ids), erro=round(sum(map(sum, E))/(len(ms)*len(ids)), 3), rho=round(r, 3), neff=round(len(ms)/(1+(len(ms)-1)*r), 2), unan=sum(len(set(T[q][m] for m in ms)) == 1 for q in ids))
def ic(T, ids, reps=2000):
    rnd = random.Random(20261114); v = []
    for _ in range(reps):
        s = [rnd.choice(ids) for _ in ids]; T2 = {f'{q}#{i}': T[q] for i, q in enumerate(s)}
        for k in list(T2): key[k] = key[k.split('#')[0]]
        try: v.append(rho(T2, list(T2))['rho'])
        except ZeroDivisionError: pass
    v.sort(); return round(v[int(.025*len(v))], 3), round(v[int(.975*len(v))], 3)
def mud(A, B):
    p = [(q, m) for q in A for m in A[q] if A[q][m] and B.get(q, {}).get(m)]
    return sum(A[q][m] != B[q][m] for q, m in p), len(p)
C = {}
for l in open('coleta.jsonl'):
    d = json.loads(l); C.setdefault(d['cond'], {}).setdefault(d['q'], {})[d['analyst']] = d.get('option')
root = arof_data_root(); cat = QuestionCatalog.from_files(root, ['conf2-mmlu'], DEFAULT_BANKS, DEFAULT_ANSWERS)
t = ObservationLoader(root, cat).load(['conf2-mmlu'])
M = {c: {} for c in ('B1', 'B2')}
for u in t.by_question_unit:
    for c in M: M[c][u[1]] = dict(t.options(u, c))
ids = sorted(q for q in C['B1'] if len([v for v in C['B1'][q].values() if v]) == 5 and len([v for v in C.get('B2',{}).get(q,{}).values() if v]) == 5)
out = {}
for nome, P in (('sonnet', C), ('misto', M)):
    out[nome] = {c: rho(P[c], ids) for c in ('B1', 'B2')}
    out[nome]['B1']['ic'] = ic(P['B1'], ids)
    m, n = mud(P['B1'], P['B2']); out[nome]['B1->B2'] = f'{m}/{n} = {100*m/n:.1f}%'
print(json.dumps(out, indent=1))
