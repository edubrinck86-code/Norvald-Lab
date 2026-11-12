"""EXPLORATÓRIO: de onde vem o aumento do ρ̄ com a exposição — acerto coletivo ou erro coletivo?

Por pergunta com gabarito: quantos dos participantes acertam em B1, B3 e E.
Conta perguntas com todos certos / todos errados em cada condição, e as
transições por resposta (certo→errado, errado→certo) de B3 para E e de B1 para E.
Uso: .venv/bin/python studies/herd/texto2/acerto_e_erro_coletivo.py
"""

import json
import sys
from collections import Counter

from norvald_lab.infrastructure.arof.dataset_store import arof_data_root
from norvald_lab.measures.command import DEFAULT_ANSWERS, DEFAULT_BANKS
from norvald_lab.measures.observation_loader import ObservationLoader
from norvald_lab.measures.question_catalog import QuestionCatalog


def bloco(table):
    todos = {c: Counter() for c in ("B1", "B3", "E")}
    trans = {"B3->E": Counter(), "B1->E": Counter()}
    for unit in table.by_question_unit:
        key = table.answer(unit[1])
        if not key:
            continue
        opts = {c: dict(table.options(unit, c)) for c in ("B1", "B3", "E")}
        for c, o in opts.items():
            v = [x for x in o.values() if x is not None]
            if not v:
                continue
            k = sum(x == key for x in v)
            todos[c]["todos_certos" if k == len(v) else "todos_errados" if k == 0 else "divididos"] += 1
        for nome, a in (("B3->E", "B3"), ("B1->E", "B1")):
            for m, x in opts[a].items():
                y = opts["E"].get(m)
                if x is None or y is None:
                    continue
                trans[nome][("certo" if x == key else "errado") + "->" + ("certo" if y == key else "errado")] += 1
    return {"perguntas_por_condicao": {c: dict(v) for c, v in todos.items()}, "transicoes": {k: dict(v) for k, v in trans.items()}}


def main():
    root = arof_data_root()
    catalog = QuestionCatalog.from_files(root, ["conf2-mmlu", "conf2-banco"], DEFAULT_BANKS, DEFAULT_ANSWERS)
    loader = ObservationLoader(root, catalog)
    out = {n: bloco(loader.load([r])) for n, r in (("mmlu", "conf2-mmlu"), ("banco", "conf2-banco"))}
    json.dump(out, sys.stdout, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
