"""EXPLORATÓRIO, fora da tese: B1 e B2 do conf2-mmlu com 5 × Sonnet via `claude -p` (cota da assinatura).

Reaproveita o pedido exato que o Lab enviou a cada analista (requests gravados em raw/),
na mesma ordem do prompt_prefix: system = shared + wave + instructions; user = user_message.
Uma pergunta por chamada, cada chamada numa sessão nova. Sem temperatura (o CLI não expõe).
Uso: python3 coleta_claude.py SAIDA.jsonl [limite]
"""
import json, re, subprocess, sys, glob, os
from concurrent.futures import ThreadPoolExecutor
EXP = os.path.expanduser('~/.norvald/lab/experiments')
VAZIO = sys.argv[3] if len(sys.argv) > 3 else '/tmp'
out = sys.argv[1]; lim = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2] else None
feito = set()
if os.path.exists(out):
    for l in open(out):
        d = json.loads(l); feito.add((d['q'], d['cond'], d['analyst']))
jobs = []
for d in sorted(glob.glob(EXP + '/conf2-mmlu-m*-b1')):
    q = d.split('-')[-2]
    reqs = {}
    for l in open(glob.glob(d + '/raw/*/observations.jsonl')[0]):
        o = json.loads(l); reqs.setdefault(o['agent_id'], o['request'])
    for cond in ('B1', 'B2'):
        for a in sorted(reqs):
            if (q, cond, a) not in feito: jobs.append((q, cond, a, reqs[a]))
if lim: jobs = jobs[:lim]
def roda(j):
    q, cond, a, r = j
    sysp = '\n\n'.join(x for x in (r.get('shared_instructions'), r.get('wave_instructions'), r.get('instructions')) if x)
    for t in range(3):
        p = subprocess.run(['claude', '-p', '--model', 'sonnet', '--effort', 'low', '--tools', '', '--strict-mcp-config',
            '--setting-sources', 'project', '--exclude-dynamic-system-prompt-sections', '--system-prompt', sysp,
            '--output-format', 'json'], input=r['user_message'], capture_output=True, text=True, cwd=VAZIO)
        try:
            d = json.loads(p.stdout); txt = d.get('result') or ''
            m = re.search(r'"relation_type"\s*:\s*"selects"[^}]*"target"\s*:\s*"(option-[a-j])"', txt)
            u = d.get('usage', {})
            return dict(q=q, cond=cond, analyst=a, option=m.group(1) if m else None, text=txt,
                        tokens_in=u.get('input_tokens', 0) + u.get('cache_creation_input_tokens', 0) + u.get('cache_read_input_tokens', 0),
                        cache_read=u.get('cache_read_input_tokens', 0), tokens_out=u.get('output_tokens', 0), attempt=t + 1)
        except Exception:
            err = (p.stderr or p.stdout)[-300:]
    return dict(q=q, cond=cond, analyst=a, option=None, error=err)
with open(out, 'a') as f, ThreadPoolExecutor(4) as ex:
    for i, res in enumerate(ex.map(roda, jobs)):
        f.write(json.dumps(res, ensure_ascii=False) + '\n'); f.flush()
        if 'error' in res and 'limit' in res['error'].lower(): print('LIMITE', res['error']); os._exit(2)
print('feito', len(jobs))
