import collections
from norvald_lab.infrastructure.arof.dataset_store import arof_data_root
from norvald_lab.measures.command import DEFAULT_ANSWERS, DEFAULT_BANKS
from norvald_lab.measures.observation_loader import ObservationLoader
from norvald_lab.measures.question_catalog import QuestionCatalog
root=arof_data_root(); cat=QuestionCatalog.from_files(root,["conf2-mmlu","conf2-banco"],DEFAULT_BANKS,DEFAULT_ANSWERS); L=ObservationLoader(root,cat)
T=collections.Counter(); F=collections.Counter()
for r in ("conf2-mmlu","conf2-banco"):
    t=L.load([r])
    for u in t.by_question_unit:
        key=t.answer(u[1])
        if not key: continue
        b1=dict(t.options(u,"B1")); e=dict(t.options(u,"E"))
        for m,x in b1.items():
            y=e.get(m)
            if x is None or y is None: continue
            c=collections.Counter(v for o,v in b1.items() if o!=m and v is not None and v!=x)
            if not c: continue
            alvo,k=c.most_common(1)[0]
            if k<2: continue
            g=("maioria certa (ele errado)" if alvo==key else "maioria errada (ele certo)" if x==key else "maioria errada (ele errado tb)")
            for kk in (k,"≥2"):
                T[(g,kk)]+=1; F[(g,kk)]+=(y==alvo)
for g in ("maioria certa (ele errado)","maioria errada (ele certo)","maioria errada (ele errado tb)"):
    for kk in (2,3,4,"≥2"):
        if T[(g,kk)]: print(g,kk,F[(g,kk)],"/",T[(g,kk)],f"{F[(g,kk)]/T[(g,kk)]:.0%}")
