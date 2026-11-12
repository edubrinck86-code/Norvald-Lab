import json
from collections import Counter, defaultdict
from norvald_lab.infrastructure.arof.dataset_store import arof_data_root
from norvald_lab.measures.command import DEFAULT_ANSWERS, DEFAULT_BANKS
from norvald_lab.measures.observation_loader import ObservationLoader
from norvald_lab.measures.question_catalog import QuestionCatalog
root = arof_data_root()
cat = QuestionCatalog.from_files(root, ["conf2-mmlu","conf2-banco"], DEFAULT_BANKS, DEFAULT_ANSWERS)
L = ObservationLoader(root, cat)
mudou=Counter(); podia=Counter(); seguido=Counter(); seguido_certo=Counter(); seguido_errado=Counter(); maioria=Counter()
for r in ("conf2-mmlu","conf2-banco"):
    t=L.load([r])
    for u in t.by_question_unit:
        key=t.answer(u[1]); b1=dict(t.options(u,"B1")); e=dict(t.options(u,"E"))
        for m,x in b1.items():
            y=e.get(m)
            if x is None or y is None: continue
            podia[m]+=1
            if x==y: continue
            mudou[m]+=1
            fontes=[o for o,v in b1.items() if o!=m and v==y]
            cnt=Counter(v for o,v in b1.items() if o!=m and v is not None)
            if cnt and y==cnt.most_common(1)[0][0]: maioria["foi p/ maioria"]+=1
            else: maioria["nao maioria"]+=1
            for f in fontes:
                seguido[f]+=1/len(fontes)
                if key: (seguido_certo if y==key else seguido_errado)[f]+=1/len(fontes)
print("modelo | mudou/podia | seguido (credito) | levou p/ certo | levou p/ errado")
for m in sorted(podia):
    print(m, f"{mudou[m]}/{podia[m]}", round(seguido[m],1), round(seguido_certo[m],1), round(seguido_errado[m],1))
print(dict(maioria))
