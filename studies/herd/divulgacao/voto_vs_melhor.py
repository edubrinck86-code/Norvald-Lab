"""EXPLORATÓRIO (15/11/2026, para o post de divulgação): a votação do painel acerta mais
do que o melhor modelo sozinho? E quanto acertaria se os erros fossem independentes?
Maioria simples entre as posições válidas (empate = erro). Teórico: binomial com a
acurácia média de cada modelo, supondo independência.
Uso: .venv/bin/python studies/herd/divulgacao/voto_vs_melhor.py
"""
import json, sys
from collections import Counter, defaultdict
from itertools import product
from norvald_lab.infrastructure.arof.dataset_store import arof_data_root
from norvald_lab.measures.command import DEFAULT_ANSWERS, DEFAULT_BANKS
from norvald_lab.measures.observation_loader import ObservationLoader
from norvald_lab.measures.question_catalog import QuestionCatalog


def maioria_independente(ps):
    tot = 0.0
    for v in product([0, 1], repeat=len(ps)):
        if sum(v) * 2 > len(ps):
            p = 1.0
            for a, q in zip(v, ps):
                p *= q if a else 1 - q
            tot += p
    return tot


def bloco(table, cond):
    acertos, n_mod = defaultdict(int), defaultdict(int)
    voto_ok = n = 0
    for unit in table.by_question_unit:
        key = table.answer(unit[1])
        if not key:
            continue
        o = {m: x for m, x in dict(table.options(unit, cond)).items() if x is not None}
        if len(o) < 3:
            continue
        n += 1
        for m, x in o.items():
            n_mod[m] += 1; acertos[m] += x == key
        top, c = Counter(o.values()).most_common(1)[0]
        tie = sum(1 for v in Counter(o.values()).values() if v == c) > 1
        voto_ok += (top == key and not tie)
    acc = {m: acertos[m] / n_mod[m] for m in n_mod}
    return {"perguntas": n, "acerto_por_modelo": acc, "melhor": max(acc.values()),
            "voto_real": voto_ok / n, "voto_se_independentes": maioria_independente(list(acc.values()))}


def main():
    root = arof_data_root()
    catalog = QuestionCatalog.from_files(root, ["conf2-mmlu"], DEFAULT_BANKS, DEFAULT_ANSWERS)
    t = ObservationLoader(root, catalog).load(["conf2-mmlu"])
    json.dump({c: bloco(t, c) for c in ("B1", "E")}, sys.stdout, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
