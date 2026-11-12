"""Medidas do estudo do formato (pré-registro: studies/formato/preregistration-en.md).

H1 (confirmatória): "qualquer mudança de opção" em B3T contra B3R, McNemar
exato pareado por participante e pergunta, bilateral, α = 0,05. A análise
principal combina os dois bancos; cada banco também sai à parte.
H2 (descritiva): taxas de B3R, B3T e B3L (e do B3 original), com IC bootstrap.
H3 (descritiva, acrescentada antes do registro em 12/11/2026): nas perguntas com
gabarito, quantas mudanças vão do errado para o certo e quantas do certo para o
errado em cada condição. Mudar pouco só é bom se o modelo mantém o que está certo
e ainda corrige o que está errado.
A leitura estrita de new_grounds é relatada sem teste. Escrito antes da coleta.
Uso: .venv/bin/python studies/formato/medidas.py ~/.norvald/lab studies/formato/resultados.md
"""
import sys
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "herd" / "exploratorio"))
from b3l_medidas import REPS, SEED, diff_ci, fmt, rate_ci  # noqa: E402  mesmo bootstrap do B3L

from norvald_lab.measures.aw9vf.mcnemar_exact import McNemarExact
from norvald_lab.measures.aw9vf.pair_outcome_index import PairOutcomeIndex
from norvald_lab.measures.aw9vf.unanimous_filter import UnanimousFilter
from norvald_lab.measures.command import DEFAULT_ANSWERS, DEFAULT_BANKS
from norvald_lab.measures.observation_loader import ObservationLoader
from norvald_lab.measures.observation_table import ObservationTable
from norvald_lab.measures.question_catalog import QuestionCatalog

BANKS = {"banco": ("conf2-banco", "f-banco", "x-b3l-banco"), "mmlu": ("conf2-mmlu", "f-mmlu", "x-b3l-mmlu")}
CONDITIONS = ("B3", "B3R", "B3T", "B3L")


def index_for(root: Path, run: str, extra: tuple) -> PairOutcomeIndex:
    catalog = QuestionCatalog.from_files(root, [run, *extra], DEFAULT_BANKS, DEFAULT_ANSWERS)
    loader = ObservationLoader(root, catalog)
    main = loader.load([run])
    rows = main.rows
    for other in extra:
        # As derivadas entram na unidade da pergunta de origem, como condições a mais.
        rows += tuple(replace(r, run=run) for r in loader.load([other]).rows)
    table = UnanimousFilter().without_unanimous(ObservationTable(rows, main.questions, (run,)))
    return PairOutcomeIndex(table, conditions=CONDITIONS)


def main(root: Path, out: Path) -> None:
    changed = lambda p: p.changed
    strict = lambda p: p.event("estrita")
    indexes = {name: index_for(root, run, (f, letter)) for name, (run, f, letter) in BANKS.items()}
    lines = ["# Estudo do formato: resultados", "",
             f"Gerado por `studies/formato/medidas.py`. Perguntas não unânimes em B1. Bootstrap por pergunta, {REPS} réplicas, "
             f"seed {SEED}, IC 95% percentil. H1: McNemar exato pareado, bilateral, α = 0,05.", ""]
    groups = {"combinado": list(indexes.values()), **{k: [v] for k, v in indexes.items()}}
    for name, idxs in groups.items():
        lines += [f"## {name}", "", "| Condição | Qualquer mudança | Mudou sem fundamento novo (estrita) |", "|---|---|---|"]
        for c in CONDITIONS:
            pairs = [p for i in idxs for p in i.of_condition(c)]
            lines.append(f"| {c} | {fmt(*rate_ci(pairs, changed)) if pairs else '—'} | {fmt(*rate_ci(pairs, strict)) if pairs else '—'} |")
        paired = [x for i in idxs for x in i.paired("B3T", "B3R")]
        if paired:
            mc = McNemarExact().test([(changed(a), changed(b)) for a, b in paired])
            tag = "H1 (confirmatória)" if name == "combinado" else "por banco"
            lines += ["", "| Contraste B3T − B3R | Estimativa | McNemar p |", "|---|---|---|",
                      f"| qualquer mudança, {tag} | {fmt(*diff_ci(paired, changed))} | {mc.p:.4g} |"]
        lines += ["", "| Condição (com gabarito) | Errado → certo | Certo → errado | Errado → outro errado | Pares |", "|---|---|---|---|---|"]
        for c in CONDITIONS:
            n = {"wc": 0, "cw": 0, "ww": 0, "pares": 0}
            for i in idxs:
                for p in i.of_condition(c):
                    key = i.table.answer(p.unit[1])
                    if not key:
                        continue
                    n["pares"] += 1
                    if p.changed:
                        before, after = p.b1_option == key, p.option == key
                        n["wc" if after else "cw" if before else "ww"] += 1
            lines.append(f"| {c} | {n['wc']} | {n['cw']} | {n['ww']} | {n['pares']} |" if n["pares"] else f"| {c} | — | — | — | 0 |")
        lines.append("")
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main(Path(sys.argv[1]).expanduser(), Path(sys.argv[2]))
