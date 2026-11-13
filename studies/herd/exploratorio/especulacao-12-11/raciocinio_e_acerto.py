"""EXPLORATÓRIO (12/11): o raciocínio mais longo (padronizado dentro do modelo) acerta mais ou menos? B1, perguntas com gabarito."""
import json,glob,math,statistics as st,collections
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
            tam[(o['experiment_id'].rsplit('-',1)[0],o['participant_id'])]=len(r['reasoning'])
linhas=[]
for r in ("conf2-mmlu","conf2-banco"):
    t=L.load([r])
    for u in t.by_question_unit:
        key=t.answer(u[1])
        if not key: continue
        for m,x in dict(t.options(u,"B1")).items():
            q=f"{r}-{u[1]}"
            if x is not None and (q,m) in tam: linhas.append((m,tam[(q,m)],x==key))
print("modelo | quartil do raciocínio (curto→longo): acerto")
tot=collections.defaultdict(lambda:[0,0])
for m in sorted({l[0] for l in linhas}):
    s=sorted([l for l in linhas if l[0]==m],key=lambda l:l[1]); n=len(s); out=[]
    for i in range(4):
        part=s[i*n//4:(i+1)*n//4]; a=sum(p[2] for p in part); out.append(f"{a/len(part):.0%}")
        tot[i][0]+=a; tot[i][1]+=len(part)
    print(m,out)
print("todos",[f"{tot[i][0]/tot[i][1]:.0%} ({tot[i][0]}/{tot[i][1]})" for i in range(4)])
