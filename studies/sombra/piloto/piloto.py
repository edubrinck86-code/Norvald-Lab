"""Piloto da tese 4 (não é dado; só calibra a dificuldade): B1 de 5 pares, clássico e sorteado.

Reaproveita o spec B1 do conf2-mmlu (mesmo painel, provedores, idioma e
amostragem) e troca só a pergunta. Rodada própria (sp-), separada do Δ_herd.
Trava: para se o custo somado da rodada passar de US$ 0,30.
Uso: .venv/bin/python studies/sombra/piloto/piloto.py ~/.norvald/lab
"""
import asyncio, copy, json, sys
from pathlib import Path
from norvald_lab.runner import ExperimentRunner

RUN, LIMITE = "sp-piloto", 0.30
PARES = ["m00119", "m04546", "m08838", "m10189", "m09455"]
AQUI = Path(__file__).resolve().parent

def custo(root):
    t = 0.0
    for f in (root / "experiments").glob(f"{RUN}-*/raw/*/observations.jsonl"):
        for l in f.read_text().splitlines():
            t += ((((json.loads(l).get("result") or {}).get("metadata") or {}).get("raw_usage") or {}).get("cost") or 0)
    return t

async def main(root):
    banco = {q["id"]: q for q in json.load(open(AQUI.parent / "banco" / "bank.json"))["questions"]}
    base = json.load(open(root / "experiments" / "conf2-mmlu-m00119-b1" / "spec.json"))
    runner = ExperimentRunner(root)
    for par in PARES:
        for v in ("c", "s"):
            q = banco[f"{v}-{par}"]
            eid = f"{RUN}-{q['id']}-b1"
            if (root / "experiments" / eid).exists() or custo(root) > LIMITE:
                print(eid, "pulado"); continue
            spec = copy.deepcopy(base)
            spec["experiment_id"] = eid
            spec["task"]["id"] = q["id"]; spec["task"]["objective"] = q["question"]
            spec["working_context"]["items"] = [{"id": o["id"], "type": "option", "content": o["content"]} for o in q["options"]]
            r = await runner.run(runner.prepare(spec), allow_live=True)
            print(eid, r["status"], f"US$ {custo(root):.4f}", flush=True)

asyncio.run(main(Path(sys.argv[1]).expanduser()))
