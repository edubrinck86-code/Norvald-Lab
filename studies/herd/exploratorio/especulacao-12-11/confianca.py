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
print('confianças lidas',len(conf))
acc=collections.Counter(); n=collections.Counter(); ced=collections.Counter(); pres=collections.Counter()
for r in ("conf2-mmlu","conf2-banco"):
    t=L.load([r])
    for u in t.by_question_unit:
        key=t.answer(u[1]); b1=dict(t.options(u,"B1")); e=dict(t.options(u,"E"))
        for m,x in b1.items():
            cf=conf.get((f"{r}-{u[1]}","B1",m))
            if x is None or cf is None: continue
            if key: n[cf]+=1; acc[cf]+=(x==key)
            y=e.get(m)
            c=collections.Counter(v for o,v in b1.items() if o!=m and v is not None and v!=x)
            if y is not None and c and c.most_common(1)[0][1]>=2:
                pres[cf]+=1; ced[cf]+=(y!=x)
for cf in ("high","medium","low"):
    if n[cf]: print(cf,"acerto",acc[cf],"/",n[cf],f"{acc[cf]/n[cf]:.0%}","| sob pressão (≥2 contra) cedeu",ced[cf],"/",pres[cf], f"{ced[cf]/pres[cf]:.0%}" if pres[cf] else "")
