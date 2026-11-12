import json,glob,re,sys
from itertools import combinations
from statistics import mean, median
sys.path.insert(0,'studies/herd/texto2')
from caminho_dos_fundamentos import words, contribution, STUDY
from norvald_lab.infrastructure.arof.dataset_store import arof_data_root
FMT=words("contribution end json relation relations selects select selected source target decision option options block knowledge local_id type confidence high medium low justification justify sentences sentence prose output produce answer final format ensure check need declare working context analyst lines line break spaces delimiters string content item items unit units choose chosen good fine yes okay let maybe also correct best")
res={}
for name,bp,ap,pre in (("mmlu",STUDY/"mmlu-pro"/"bank.json",STUDY/"mmlu-pro"/"answers.json","conf2-mmlu"),("banco",STUDY/"bank.en.json",STUDY/"answers.json","conf2-banco")):
  bank=json.load(open(bp))["questions"]; ans=json.load(open(ap))["answers"]
  for cond in ("b1","e"):
    g={}; per_model={}
    for q in bank:
      key=ans.get(q["id"])
      if not key: continue
      f=glob.glob(str(arof_data_root()/"experiments"/f"{pre}-{q['id']}-{cond}"/"raw"/"r0001"/"observations.jsonl"))
      if not f: continue
      noise=words(q["question"])|set().union(*(words(o["content"]) for o in q["options"]))|FMT
      bm={}
      for l in open(f[0]):
        r=json.loads(l)
        if r["attempt_outcome"]!="returned" or not r.get("result"): continue
        c=contribution(r["result"].get("content")) or {}
        p=[x["target"] for x in c.get("relations",[]) if x.get("relation_type")=="selects" and str(x.get("target","")).startswith("option-")]
        rs=r["result"].get("reasoning") or ""
        if not p or not rs: continue
        bm[r["requested_model"].split("/")[1][:7]]=(p[0],words(rs)-noise)
      for a,b in combinations(sorted(bm),2):
        (oa,wa),(ob,wb)=bm[a],bm[b]
        if not (wa|wb): continue
        j=len(wa&wb)/len(wa|wb)
        k="acerto_em_comum" if oa==ob==key else "erro_em_comum" if oa==ob else "um_certo_outro_errado" if key in (oa,ob) else "erros_diferentes"
        g.setdefault(k,[]).append(j); per_model.setdefault(k,{}).setdefault(f"{a}×{b}",[]).append(j)
    res[f"{name}|{cond.upper()}"]={k:{"pares":len(v),"jaccard_medio":round(mean(v),3),"mediana":round(median(v),3)} for k,v in sorted(g.items())}
    if name=="mmlu" and cond=="b1":
      res["mmlu|B1|por_par"]={k:{p:round(mean(v),3) for p,v in sorted(d.items())} for k,d in per_model.items() if k in("acerto_em_comum","erro_em_comum")}
json.dump(res,sys.stdout,ensure_ascii=False,indent=1)
