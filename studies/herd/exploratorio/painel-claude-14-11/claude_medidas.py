import json,sys,itertools
from collections import Counter
S=sys.argv[1]
r=json.load(open(S+'/tasks/wog2rhsec.output'))['result']
key={k:v.split('-')[1].upper() for k,v in json.load(open('studies/herd/mmlu-pro/answers.json'))['answers'].items()}
qs=[q['id'] for q in json.load(open(S+'/scratchpad/claude_qs.json'))]
def tab(lst): return [{a['id']:a for a in x['answers']} for x in lst]
B1=tab([x['r'] for x in sorted(r['B1'],key=lambda x:x['i'])])
EX={c:tab([x['r'] for x in sorted([e for e in r['EX'] if e['cond']==c],key=lambda x:x['i'])]) for c in ('EP','E')}
def rho(T):
  ids=[q for q in qs if q in key and all(q in t for t in T)]
  E=[[T[m][q]['choice']!=key[q] for q in ids] for m in range(5)]
  ph=[]
  for a,b in itertools.combinations(range(5),2):
    x,y=E[a],E[b];n=len(x);p11=sum(i and j for i,j in zip(x,y));p1=sum(x);q1=sum(y)
    d=(p1*(n-p1)*q1*(n-q1))**.5
    if d: ph.append((n*p11-p1*q1)/d)
  rb=sum(ph)/len(ph);return len(ids),rb,5/(1+4*rb),sum(map(sum,E))/(5*len(ids))
print('B1 n,rho,Neff,erro',rho(B1))
for c in ('EP','E'):
  T=EX[c];ch=[(B1[m][q]['choice'],T[m][q]['choice'],q) for m in range(5) for q in qs if q in B1[m] and q in T[m]]
  mud=sum(a!=b for a,b,_ in ch);tr=Counter()
  for a,b,q in ch:
    if a!=b and q in key: tr['e->c' if b==key[q] else 'c->e' if a==key[q] else 'e->e']+=1
  print(c,'mudou',mud,len(ch),round(100*mud/len(ch),1),dict(tr),'rho',rho(T))
# pressao: colegas contra no B1
pr=Counter();pt=Counter()
for c in ('EP','E'):
 for m in range(5):
  for q in qs:
   if q not in B1[m] or q not in EX[c][m]: continue
   k=sum(B1[j][q]['choice']!=B1[m][q]['choice'] for j in range(5) if j!=m and q in B1[j])
   pt[(c,k)]+=1; pr[(c,k)]+=EX[c][m][q]['choice']!=B1[m][q]['choice']
print({f'{c}{k}':f'{pr[(c,k)]}/{pt[(c,k)]}' for (c,k) in sorted(pt)})
unan=sum(len({B1[m][q]['choice'] for m in range(5)})==1 for q in qs);print('unanimes B1',unan)
