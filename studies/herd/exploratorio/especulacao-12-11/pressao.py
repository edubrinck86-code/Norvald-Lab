from collections import Counter
from norvald_lab.infrastructure.arof.dataset_store import arof_data_root
from norvald_lab.measures.command import DEFAULT_ANSWERS, DEFAULT_BANKS
from norvald_lab.measures.observation_loader import ObservationLoader
from norvald_lab.measures.question_catalog import QuestionCatalog
root=arof_data_root(); cat=QuestionCatalog.from_files(root,["conf2-mmlu","conf2-banco"],DEFAULT_BANKS,DEFAULT_ANSWERS); L=ObservationLoader(root,cat)
tot=Counter(); foi=Counter(); certo=Counter()
for r in ("conf2-mmlu","conf2-banco"):
    t=L.load([r])
    for u in t.by_question_unit:
        key=t.answer(u[1]); b1=dict(t.options(u,"B1")); e=dict(t.options(u,"E"))
        for m,x in b1.items():
            y=e.get(m)
            if x is None or y is None: continue
            c=Counter(v for o,v in b1.items() if o!=m and v is not None and v!=x)
            if c: alvo,k=c.most_common(1)[0]
            else: alvo,k=None,0
            tot[k]+=1
            if y==alvo: foi[k]+=1; certo[k]+= (alvo==key)
for k in range(5):
    if tot[k]: print(k, tot[k], foi[k], f"{foi[k]/tot[k]:.1%}", certo[k])
