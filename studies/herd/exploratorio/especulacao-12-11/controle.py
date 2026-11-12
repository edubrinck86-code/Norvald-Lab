import json,glob,re,collections
from norvald_lab.infrastructure.arof.dataset_store import arof_data_root
from norvald_lab.measures.command import DEFAULT_ANSWERS, DEFAULT_BANKS
from norvald_lab.measures.observation_loader import ObservationLoader
from norvald_lab.measures.question_catalog import QuestionCatalog
root=arof_data_root(); cat=QuestionCatalog.from_files(root,["conf2-mmlu","conf2-banco"],DEFAULT_BANKS,DEFAULT_ANSWERS); L=ObservationLoader(root,cat)
conf={}
for f in glob.glob('/Users/macbook/.norvald/lab/experiments/conf2-*-b1/raw/*/observations.jsonl')+glob.glob('/Users/macbook/.norvald/lab/experiments/conf2-*-e/raw/*/observations.jsonl'):
    for line in open(f):
        o=json.loads(line); c=((o.get('result') or {}).get('content') or '')
        m=re.search(r'<<CONTRIBUTION>>(.*?)<<END_CONTRIBUTION>>',c,re.S)
        if not m: continue
        try: j=json.loads(m.group(1))
        except: continue
        sel=[r.get('source') for r in j.get('relations',[]) if isinstance(r,dict) and r.get('relation_type')=='selects']
        items={k.get('local_id'):k for k in j.get('knowledge',[]) if isinstance(k,dict)}
        cf=next((items[s].get('confidence') for s in sel if s in items),None)
        if cf: conf[(o['experiment_id'].rsplit('-',1)[0],o['condition_id'],o['participant_id'])]=cf
acc=collections.Counter(); n=collections.Counter(); ced=collections.Counter(); pres=collections.Counter()
for r in ("conf2-mmlu","conf2-banco"):
    t=L.load([r])
T=collections.Counter(); F=collections.Counter()
for r in ("conf2-mmlu","conf2-banco"):
    t=L.load([r])
    for u in t.by_question_unit:
        key=t.answer(u[1])
        if not key: continue
        b1=dict(t.options(u,"B1")); e=dict(t.options(u,"E"))
        for m,x in b1.items():
            y=e.get(m); cf=conf.get((f"{r}-{u[1]}","B1",m))
            if x is None or y is None or cf not in("high","medium"): continue
            c=collections.Counter(v for o,v in b1.items() if o!=m and v is not None and v!=x)
            if not c: continue
            alvo,k=c.most_common(1)[0]
            if k<2: continue
            g="maioria certa" if alvo==key else ("maioria errada, ele certo" if x==key else None)
            if g: T[(g,cf)]+=1; F[(g,cf)]+=(y==alvo)
for k in sorted(T): print(k,F[k],"/",T[k],f"{F[k]/T[k]:.0%}")
