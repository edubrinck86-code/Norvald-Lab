"""EXPLORATÓRIO (12/11/2026, hipótese do Eduardo): raciocínio longo se descola da memória?
Previsão: em perguntas de dificuldade parecida, as de raciocínio mais longo têm erro menos correlacionado (ρ̄ menor).
Dificuldade = quantos dos 5 acertam em B1. Tamanho = log do raciocínio, padronizado dentro de cada modelo, médio na pergunta.
Em cada estrato de dificuldade, as perguntas são divididas na mediana do tamanho; ρ̄_erro calculado em cada metade juntada.
"""
import json,glob,re,math,random,statistics as st,collections,itertools
from norvald_lab.infrastructure.arof.dataset_store import arof_data_root
from norvald_lab.measures.command import DEFAULT_ANSWERS, DEFAULT_BANKS
from norvald_lab.measures.observation_loader import ObservationLoader
from norvald_lab.measures.question_catalog import QuestionCatalog
root=arof_data_root(); cat=QuestionCatalog.from_files(root,["conf2-mmlu","conf2-banco"],DEFAULT_BANKS,DEFAULT_ANSWERS); L=ObservationLoader(root,cat)
tam={}
for f in glob.glob('/Users/macbook/.norvald/lab/experiments/conf2-*-b1/raw/*/observations.jsonl'):
    for line in open(f):
        o=json.loads(line); r=o.get('result') or {}
        if '<<CONTRIBUTION>>' in (r.get('content') or '') and r.get('reasoning'):
            tam[(o['experiment_id'].rsplit('-',1)[0],o['participant_id'])]=math.log(len(r['reasoning']))
por_m=collections.defaultdict(list)
for (q,m),v in tam.items(): por_m[m].append(v)
z={k:(v-st.mean(por_m[k[1]]))/st.pstdev(por_m[k[1]]) for k,v in tam.items()}
Q=[]
for r in ("conf2-mmlu","conf2-banco"):
    t=L.load([r])
    for u in t.by_question_unit:
        key=t.answer(u[1])
        if not key: continue
        b1={m:x for m,x in dict(t.options(u,"B1")).items() if x is not None}
        q=f"{r}-{u[1]}"; zs=[z[(q,m)] for m in b1 if (q,m) in z]
        if len(b1)<5 or len(zs)<4: continue
        Q.append(dict(err={m:int(x!=key) for m,x in b1.items()},k=sum(x==key for x in b1.values()),z=st.mean(zs)))
def phi(a,b):
    n=len(a); sa=sum(a); sb=sum(b); sab=sum(x*y for x,y in zip(a,b))
    d=math.sqrt(sa*(n-sa)*sb*(n-sb))
    return None if d==0 else (n*sab-sa*sb)/d
def rho(qs):
    ms=sorted(qs[0]['err']); vals=[]
    for a,b in itertools.combinations(ms,2):
        p=phi([q['err'][a] for q in qs],[q['err'][b] for q in qs])
        if p is not None: vals.append(p)
    return st.mean(vals) if vals else float('nan')
longo=[];curto=[]
for k in range(6):
    s=sorted([q for q in Q if q['k']==k],key=lambda q:q['z'])
    h=len(s)//2; curto+=s[:h]; longo+=s[len(s)-h:]
obs=(rho(curto),rho(longo))
random.seed(20261112); dif=[]
for _ in range(5000):
    a=[random.choice(curto) for _ in curto]; b=[random.choice(longo) for _ in longo]
    ra,rb=rho(a),rho(b)
    if not(math.isnan(ra) or math.isnan(rb)): dif.append(rb-ra)
dif.sort()
print(json.dumps(dict(perguntas=len(Q),n_curto=len(curto),n_longo=len(longo),rho_curto=round(obs[0],3),rho_longo=round(obs[1],3),
  diferenca=round(obs[1]-obs[0],3),ic95=[round(dif[int(.025*len(dif))],3),round(dif[int(.975*len(dif))],3)],
  estratos={k:sum(q['k']==k for q in Q) for k in range(6)}),ensure_ascii=False))
