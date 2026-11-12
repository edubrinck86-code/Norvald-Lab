"""Sensibilidade EXPLORATÓRIA do H3: ρ̄_erro e N_eff sem as 7 chaves duvidosas do MMLU-Pro.

Não é análise registrada. As chaves não são editadas (344-79 item 3); só se
mostra quanto o ρ̄ depende delas. Mesmo bootstrap do relatório (seed 20261111,
20 000 réplicas). Uso: python studies/herd/texto2/sensibilidade_sete_chaves.py
"""

import json
import sys
from pathlib import Path

from norvald_lab.infrastructure.arof.dataset_store import arof_data_root
from norvald_lab.measures.aw9vf.dependence import Dependence
from norvald_lab.measures.bootstrap import ClusteredBootstrap
from norvald_lab.measures.command import DEFAULT_ANSWERS, DEFAULT_BANKS
from norvald_lab.measures.observation_loader import ObservationLoader
from norvald_lab.measures.observation_table import ObservationTable
from norvald_lab.measures.question_catalog import QuestionCatalog

DUVIDOSAS = ("m07756", "m07114", "m07045", "m04776", "m05049", "m02530", "m07001")


def main() -> None:
    root = arof_data_root()
    runs = ("conf2-mmlu", "conf3-contraste-mmlu", "conf2-banco")
    catalog = QuestionCatalog.from_files(root, list(runs), DEFAULT_BANKS, DEFAULT_ANSWERS)
    loader = ObservationLoader(root, catalog)
    boot = ClusteredBootstrap(reps=20000, seed=20261111)
    out = {}
    for name, run_ids, conditions in (("mmlu", ["conf2-mmlu"], ("B1", "B3", "EP", "E")), ("combinado", ["conf2-banco", "conf2-mmlu"], ("B1", "B3", "EP", "E")), ("contraste_gemma_mmlu", ["conf3-contraste-mmlu"], ("B1",))):
        table = loader.load(run_ids)
        b1 = {}
        for unit, by in table.by_question_unit.items():
            if unit[1] in DUVIDOSAS:
                b1[unit[1]] = {"gabarito": table.answer(unit[1]), "B1": dict(table.options(unit, "B1"))}
        kept = ObservationTable(tuple(r for r in table.rows if r.question_id not in DUVIDOSAS), table.questions, table.runs)
        for label, t in (("todas", table), ("sem_as_7", kept)):
            d = Dependence(boot).compute(t, conditions=conditions, behaviour=False)
            out[f"{name}|{label}"] = {"perguntas_com_gabarito": d["perguntas_com_gabarito"], "rho_erro": d["rho_erro"], "n_eff": d["n_eff"], "delta": d.get("delta_n_eff_B1_menos_E")}
        out[f"{name}|b1_nas_7"] = b1
    json.dump(out, sys.stdout, ensure_ascii=False, indent=1, default=str)


if __name__ == "__main__":
    main()
