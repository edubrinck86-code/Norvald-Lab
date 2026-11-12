"""EXPLORATÓRIO (fora do registro): o banco novo tem erros quase independentes
porque as perguntas são novas ou porque são mais fáceis?

Proxy de novidade dentro do MMLU-Pro: perguntas herdadas do MMLU original
(`ori_mmlu`, mais expostas em dados de treino) contra as acrescentadas pelo
MMLU-Pro (stemez, theoremQA, scibench). Para cada grupo: taxa de erro por
modelo em B1, distribuição de quantos dos cinco erram, e ρ̄_erro(B1).
Uso: python studies/herd/texto2/novidade_ou_facilidade.py
"""

import json
import sys
from collections import Counter
from pathlib import Path

from norvald_lab.infrastructure.arof.dataset_store import arof_data_root
from norvald_lab.measures.aw9vf.dependence import Dependence
from norvald_lab.measures.bootstrap import ClusteredBootstrap
from norvald_lab.measures.command import DEFAULT_ANSWERS, DEFAULT_BANKS
from norvald_lab.measures.observation_loader import ObservationLoader
from norvald_lab.measures.observation_table import ObservationTable
from norvald_lab.measures.question_catalog import QuestionCatalog

BANK = Path(__file__).resolve().parents[1] / "mmlu-pro" / "bank.json"


def origem():
    data = json.loads(BANK.read_text())
    items = data if isinstance(data, list) else data["questions"]
    return {q["id"]: ("mmlu_original" if q["src"].startswith("ori_mmlu") else "acrescentada_pro") for q in items}


def perfil(table, boot):
    erros, por_pergunta = Counter(), Counter()
    totais = Counter()
    for unit in table.by_question_unit:
        key = table.answer(unit[1])
        if not key:
            continue
        opts = dict(table.options(unit, "B1"))
        k = 0
        for model, opt in opts.items():
            if opt is None:
                continue
            totais[model] += 1
            if opt != key:
                erros[model] += 1
                k += 1
        por_pergunta[k] += 1
    taxa = {m: round(erros[m] / totais[m], 3) for m in sorted(totais)}
    d = Dependence(boot).compute(table, conditions=("B1",), behaviour=False)
    return {"perguntas": sum(por_pergunta.values()), "taxa_erro_por_modelo": taxa,
            "taxa_erro_media": round(sum(erros.values()) / sum(totais.values()), 3),
            "quantos_erram_dos_5": dict(sorted(por_pergunta.items())),
            "rho_erro_B1": d["rho_erro"], "n_eff_B1": d["n_eff"]}


def main():
    root = arof_data_root()
    catalog = QuestionCatalog.from_files(root, ["conf2-mmlu", "conf2-banco"], DEFAULT_BANKS, DEFAULT_ANSWERS)
    loader = ObservationLoader(root, catalog)
    boot = ClusteredBootstrap(reps=20000, seed=20261111)
    src = origem()
    mmlu = loader.load(["conf2-mmlu"])
    out = {"banco": perfil(loader.load(["conf2-banco"]), boot), "mmlu_todas": perfil(mmlu, boot)}
    for grupo in ("mmlu_original", "acrescentada_pro"):
        t = ObservationTable(tuple(r for r in mmlu.rows if src.get(r.question_id) == grupo), mmlu.questions, mmlu.runs)
        out[grupo] = perfil(t, boot)
    json.dump(out, sys.stdout, ensure_ascii=False, indent=1, default=str)


if __name__ == "__main__":
    main()
