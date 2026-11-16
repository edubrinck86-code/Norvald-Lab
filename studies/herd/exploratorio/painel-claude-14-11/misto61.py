import json,itertools
from norvald_lab.infrastructure.arof.dataset_store import arof_data_root
from norvald_lab.measures.command import DEFAULT_ANSWERS, DEFAULT_BANKS
from norvald_lab.measures.observation_loader import ObservationLoader
from norvald_lab.measures.question_catalog import QuestionCatalog
S='/private/tmp/claude-501/-Users-macbook-Norvald-Lab/f78a0fc3-483c-4597-a774-b93c674bb889'
qs={q['id'] for q in json.load(open(S+'/scratchpad/claude_qs.json'))}
root=arof_data_root();cat=QuestionCatalog.from_files(root,["conf2-mmlu"],DEFAULT_BANKS,DEFAULT_ANSWERS)
t=ObservationLoader(root,cat).load(["conf2-mmlu"])
rows={};mud=tot=0
for u in t.by_question_unit:
  q=u[1]
  if q not in qs: continue
  key=t.answer(q); b=dict(t.options(u,"B1")); e=dict(t.options(u,"E"))
  for m in b:
    if b[m] and e.get(m): tot+=1; mud+=b[m]!=e[m]
  rows[q]=(key,b,e)
print('perguntas',len(rows),'mudou B1->E',mud,tot,round(100*mud/tot,1))
def rho(c):
  ms=sorted({m for k,b,e in rows.values() for m in b})
  ids=[q for q,(k,b,e) in rows.items() if k and all((b if c=='B1' else e).get(m) for m in ms)]
  E=[[ (rows[q][1] if c=='B1' else rows[q][2])[m]!=rows[q][0] for q in ids] for m in ms]
  ph=[]
  for x,y in itertools.combinations(E,2):
    n=len(x);p11=sum(i and j for i,j in zip(x,y));p1=sum(x);q1=sum(y);d=(p1*(n-p1)*q1*(n-q1))**.5
    if d: ph.append((n*p11-p1*q1)/d)
  r=sum(ph)/len(ph);return len(ids),round(r,3),round(5/(1+4*r),2),round(sum(map(sum,E))/(len(ms)*len(ids)),3)
print('B1',rho('B1'),'E',rho('E'))
