"""Medidas exploratórias do B3L (12/11/2026), fora do registro.

Junta cada rodada confirmatória (conf2-*) com a sua B3L (x-b3l-*), nas perguntas
em que o painel não foi unânime em B1, e reporta por condição (B2, B3, B3L):
- evento registrado: mudou de opção sem fundamento novo (344-66, leitura estrita);
- qualquer mudança de opção (a régua de Hao et al. 2026, "reconsideration instability").
O contraste B3L − B3 vem com bootstrap por pergunta e McNemar exato pareado. Uso:

    .venv/bin/python studies/herd/exploratorio/b3l_medidas.py ~/.norvald/lab studies/herd/resultados/b3l-exploratorio.md
"""
import random
import sys
from dataclasses import replace
from pathlib import Path

from norvald_lab.measures.aw9vf.mcnemar_exact import McNemarExact
from norvald_lab.measures.aw9vf.pair_outcome_index import PairOutcomeIndex
from norvald_lab.measures.aw9vf.unanimous_filter import UnanimousFilter
from norvald_lab.measures.command import DEFAULT_ANSWERS, DEFAULT_BANKS
from norvald_lab.measures.observation_loader import ObservationLoader
from norvald_lab.measures.observation_table import ObservationTable
from norvald_lab.measures.question_catalog import QuestionCatalog

RUNS = {"conf2-mmlu": "x-b3l-mmlu", "conf2-banco": "x-b3l-banco"}
CONDITIONS = ("B2", "B3", "B3L")
REPS, SEED = 20000, 20261112


def table_for(root: Path, run: str, letter_run: str) -> ObservationTable:
    catalog = QuestionCatalog.from_files(root, [run, letter_run], DEFAULT_BANKS, DEFAULT_ANSWERS)
    loader = ObservationLoader(root, catalog)
    main, letter = loader.load([run]), loader.load([letter_run])
    # As linhas B3L entram na unidade da pergunta de origem, como uma condição a mais.
    rows = main.rows + tuple(replace(r, run=run) for r in letter.rows)
    return UnanimousFilter().without_unanimous(ObservationTable(rows, main.questions, (run,)))


def rate_ci(pairs, value):
    clusters = {}
    for p in pairs:
        clusters.setdefault(p.unit, []).append(value(p))
    keys = sorted(clusters)
    est = sum(sum(v) for v in clusters.values()) / max(1, sum(len(v) for v in clusters.values()))
    rng, stats = random.Random(SEED), []
    for _ in range(REPS):
        pick = [clusters[rng.choice(keys)] for _ in keys]
        n = sum(len(v) for v in pick)
        stats.append(sum(sum(v) for v in pick) / n if n else 0.0)
    stats.sort()
    return est, stats[int(0.025 * REPS)], stats[int(0.975 * REPS) - 1], len(pairs), len(keys)


def diff_ci(paired, value):
    clusters = {}
    for a, b in paired:
        clusters.setdefault(a.unit, []).append((value(a), value(b)))
    keys = sorted(clusters)
    def d(groups):
        items = [x for g in groups for x in g]
        return (sum(a for a, _ in items) - sum(b for _, b in items)) / len(items) if items else 0.0
    est = d(clusters.values())
    rng, stats = random.Random(SEED), []
    for _ in range(REPS):
        stats.append(d([clusters[rng.choice(keys)] for _ in keys]))
    stats.sort()
    return est, stats[int(0.025 * REPS)], stats[int(0.975 * REPS) - 1], len(paired), len(keys)


def fmt(e, lo, hi, n, k):
    return f"{e:.3f} [{lo:.3f}; {hi:.3f}] (n={n}, {k} perguntas)"


def main(root: Path, out: Path) -> None:
    lines = ["# B3L — controle \"só a letra\" (exploratório, fora do registro)", "",
             "Gerado por `studies/herd/exploratorio/b3l_medidas.py`. Perguntas não unânimes em B1. Bootstrap por pergunta, "
             f"{REPS} réplicas, seed {SEED}, IC 95% percentil. McNemar exato pareado, sem correção (exploratório).", ""]
    event = lambda p: p.event("estrita")
    changed = lambda p: p.changed
    for run, letter_run in RUNS.items():
        index = PairOutcomeIndex(table_for(root, run, letter_run), conditions=CONDITIONS)
        lines += [f"## {run} + {letter_run}", "",
                  "| Condição | Mudou sem fundamento novo | Qualquer mudança |", "|---|---|---|"]
        for c in CONDITIONS:
            pairs = index.of_condition(c)
            lines.append(f"| {c} | {fmt(*rate_ci(pairs, event)) if pairs else '—'} | {fmt(*rate_ci(pairs, changed)) if pairs else '—'} |")
        paired = index.paired("B3L", "B3")
        if paired:
            mc_e = McNemarExact().test([(event(a), event(b)) for a, b in paired])
            mc_c = McNemarExact().test([(changed(a), changed(b)) for a, b in paired])
            lines += ["", "| Contraste B3L − B3 | Estimativa | McNemar p |", "|---|---|---|",
                      f"| sem fundamento novo | {fmt(*diff_ci(paired, event))} | {mc_e.p:.4g} |",
                      f"| qualquer mudança | {fmt(*diff_ci(paired, changed))} | {mc_c.p:.4g} |"]
        lines.append("")
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main(Path(sys.argv[1]).expanduser(), Path(sys.argv[2]))
