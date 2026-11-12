"""Coleta do estudo do formato (pré-registro em studies/formato/): B3T e B3R.

Para cada pergunta não unânime em B1 (as mesmas do B3L), deriva da B1 já
coletada em conf2-banco e conf2-mmlu:
- B3T (self_text): a própria contribuição de B1 em texto corrido;
- B3R (self): réplica do B3, coletada junto, contra a deriva no tempo.
As rodadas são próprias (f-*) e nunca se misturam às do Δ_herd. Trava de custo:
para de abrir experimentos quando o custo somado passa de US$ 2,00.
Uso: .venv/bin/python studies/formato/coleta.py ~/.norvald/lab
"""
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "herd" / "exploratorio"))
from b3l_coleta import contested  # noqa: E402  mesmas perguntas do B3L

from norvald_lab.cli import derive_spec
from norvald_lab.herd.specs import experiment_id
from norvald_lab.runner import ExperimentRunner

RUNS = {"conf2-banco": "f-banco", "conf2-mmlu": "f-mmlu"}
CONDITIONS = (("B3T", "self_text"), ("B3R", "self"))
PARALLEL = 3
LIMITE_USD = 2.00


def custo(root: Path) -> float:
    total = 0.0
    for run in RUNS.values():
        for obs_file in (root / "experiments").glob(f"{run}-*/raw/*/observations.jsonl"):
            for line in obs_file.read_text(encoding="utf-8").splitlines():
                usage = ((json.loads(line).get("result") or {}).get("metadata") or {}).get("raw_usage") or {}
                total += usage.get("cost") or 0
    return total


async def main(root: Path) -> None:
    runner = ExperimentRunner(root)
    slots = asyncio.Semaphore(PARALLEL)
    report = []

    async def one(source_run, target_run, question, cond, exposure):
        new = experiment_id(target_run, question, cond)
        if (root / "experiments" / new).exists():
            report.append((new, "já existia"))
            return
        async with slots:
            gasto = custo(root)
            if gasto > LIMITE_USD:
                report.append((new, f"parado pela trava de custo (US$ {gasto:.2f})"))
                print(report[-1], flush=True)
                return
            try:
                spec = derive_spec(root, experiment_id(source_run, question, "B1"), new, exposure, cond)
                result = await runner.run(runner.prepare(spec), allow_live=True)
                report.append((new, result["status"]))
            except ValueError as exc:
                report.append((new, "bloqueado: " + str(exc)[:200]))
            print(report[-1], flush=True)

    jobs = [one(src, dst, q, c, e) for src, dst in RUNS.items() for q in contested(root, src) for c, e in CONDITIONS]
    print(f"{len(jobs)} experimentos", flush=True)
    await asyncio.gather(*jobs)
    print("fim:", sum(s == "complete" for _, s in report), "completos de", len(report), f"custo US$ {custo(root):.4f}", flush=True)


if __name__ == "__main__":
    asyncio.run(main(Path(sys.argv[1]).expanduser()))
