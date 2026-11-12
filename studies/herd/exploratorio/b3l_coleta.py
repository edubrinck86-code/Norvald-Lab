"""Coleta exploratória B3L (12/11/2026): controle "só a letra", fora do registro.

Para cada pergunta em que o painel não foi unânime em B1 (conf2-banco e
conf2-mmlu), deriva da B1 já coletada uma condição B3L: o participante vê só a
opção que escolheu, mais a mesma instrução de reconsiderar. Reproduz o controle
de Hao et al. (2026, Tabela 30) no nosso painel. Rodada própria (x-b3l-*), para
nunca se misturar aos dados confirmatórios. Uso:

    .venv/bin/python studies/herd/exploratorio/b3l_coleta.py ~/.norvald/lab
"""
import asyncio
import sys
from pathlib import Path

from norvald_lab.cli import derive_spec
from norvald_lab.herd.specs import experiment_id
from norvald_lab.measures.aw9vf.unanimous_filter import UnanimousFilter
from norvald_lab.measures.command import DEFAULT_ANSWERS, DEFAULT_BANKS
from norvald_lab.measures.observation_loader import ObservationLoader
from norvald_lab.measures.question_catalog import QuestionCatalog
from norvald_lab.runner import ExperimentRunner

RUNS = {"conf2-banco": "x-b3l-banco", "conf2-mmlu": "x-b3l-mmlu"}
PARALLEL = 4


def contested(root: Path, run: str) -> list[str]:
    catalog = QuestionCatalog.from_files(root, [run], DEFAULT_BANKS, DEFAULT_ANSWERS)
    table = ObservationLoader(root, catalog).load([run])
    unanimous = UnanimousFilter().unanimous_units(table)
    return sorted({unit[1] for unit in table.by_question_unit if unit not in unanimous and "B1" in table.by_question_unit[unit]})


async def main(root: Path) -> None:
    runner = ExperimentRunner(root)
    slots = asyncio.Semaphore(PARALLEL)
    report = []

    async def one(source_run, target_run, question):
        new = experiment_id(target_run, question, "B3L")
        if (root / "experiments" / new).exists():
            report.append((new, "já existia"))
            return
        async with slots:
            try:
                spec = derive_spec(root, experiment_id(source_run, question, "B1"), new, "self_letter")
                result = await runner.run(runner.prepare(spec), allow_live=True)
                report.append((new, result["status"]))
            except ValueError as exc:
                report.append((new, "bloqueado: " + str(exc)[:200]))
            print(report[-1], flush=True)

    jobs = [one(src, dst, q) for src, dst in RUNS.items() for q in contested(root, src)]
    print(f"{len(jobs)} experimentos B3L", flush=True)
    await asyncio.gather(*jobs)
    print("fim:", sum(s == "complete" for _, s in report), "completos de", len(report), flush=True)


if __name__ == "__main__":
    asyncio.run(main(Path(sys.argv[1]).expanduser()))
