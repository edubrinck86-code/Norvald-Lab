import json,glob,re,collections,random
from norvald_lab.infrastructure.arof.dataset_store import arof_data_root
from norvald_lab.measures.command import DEFAULT_ANSWERS, DEFAULT_BANKS
from norvald_lab.measures.observation_loader import ObservationLoader
from norvald_lab.measures.question_catalog import QuestionCatalog
root=arof_data_root(); cat=QuestionCatalog.from_files(root,["conf2-mmlu","conf2-banco"],DEFAULT_BANKS,DEFAULT_ANSWERS); L=ObservationLoader(root,cat)
txt={}
for f in glob.glob('/Users/macbook/.norvald/lab/experiments/conf2-*-b1/raw/*/observations.jsonl')+glob.glob('/Users/macbook/.norvald/lab/experiments/conf2-*-e/raw/*/observations.jsonl'):
    for line in open(f):
        o=json.loads(line); c=((o.get('result') or {}).get('content') or '')
        m=re.search(r'<<CONTRIBUTION>>(.*?)<<END_CONTRIBUTION>>',c,re.S)
        if not m: continue
        try: j=json.loads(m.group(1))
        except: continue
        t=" | ".join(f"[{k.get('confidence')}] {k.get('content')}" for k in j.get('knowledge',[]) if isinstance(k,dict))
        txt[(o['experiment_id'].rsplit('-',1)[0],o['condition_id'],o['participant_id'])]=t
casos={"A":[],"B":[]}
for r in ("conf2-mmlu","conf2-banco"):
    t=L.load([r])
    for u in t.by_question_unit:
        key=t.answer(u[1])
        if not key: continue
        b1=dict(t.options(u,"B1")); e=dict(t.options(u,"E")); q=f"{r}-{u[1]}"
        for m,x in b1.items():
            y=e.get(m)
            if x is None or y is None: continue
            c=collections.Counter(v for o,v in b1.items() if o!=m and v is not None and v!=x)
            if not c: continue
            alvo,k=c.most_common(1)[0]
            if k<2: continue
            g="A" if alvo==key else ("B" if x==key else None)
            if not g: continue
            casos[g].append(dict(q=q,modelo=m,k=k,gabarito=key,dele_b1=x,alvo=alvo,cedeu=(y==alvo),
              dele_b1_txt=txt.get((q,"B1",m),"")[:500],
              maioria_txt=[txt.get((q,"B1",o),"")[:500] for o,v in b1.items() if o!=m and v==alvo],
              dele_e_txt=txt.get((q,"E",m),"")[:500]))
random.seed(1112)
out={}
for g in casos:
    ced=[c for c in casos[g] if c['cedeu']]; seg=[c for c in casos[g] if not c['cedeu']]
    out[g]=random.sample(ced,min(6,len(ced)))+random.sample(seg,min(6,len(seg)))
json.dump(out,open(f"{'/private/tmp/claude-501/-Users-macbook-Norvald-Lab/f78a0fc3-483c-4597-a774-b93c674bb889/scratchpad'}/casos.json","w"),ensure_ascii=False,indent=1)
print({g:len(v) for g,v in casos.items()})
