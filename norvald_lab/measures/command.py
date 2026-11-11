"""Comando `norvald-lab measures`: lê as rodadas, calcula tudo, grava o JSON e o resumo .md.

Só lê: nenhuma chamada a modelo, nenhuma escrita na pasta de dados do Lab.
Os gabaritos padrão são os do repositório (studies/herd); em instalação sem
o repositório, passe --answers.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Sequence

from norvald_lab.measures.bootstrap import ClusteredBootstrap
from norvald_lab.measures.markdown_summary import render_markdown
from norvald_lab.measures.observation_loader import ObservationLoader
from norvald_lab.measures.question_catalog import QuestionCatalog
from norvald_lab.measures.reasons.same_answer_reasons import SameAnswerReasons
from norvald_lab.measures.report_builder import MeasuresReport

STUDY = Path(__file__).resolve().parents[2] / "studies" / "herd"
DEFAULT_BANKS = (STUDY / "bank.en.json", STUDY / "mmlu-pro" / "bank.json")
DEFAULT_ANSWERS = (STUDY / "answers.json", STUDY / "mmlu-pro" / "answers.json")


def run_measures(root: Path, *, runs: Sequence[str], out: Path, seed: int, reps: int, bank_paths: Sequence[Path] = (), answer_paths: Sequence[Path] = (), threshold: float | None = None) -> int:
    catalog = QuestionCatalog.from_files(root, runs, bank_paths or DEFAULT_BANKS, answer_paths or DEFAULT_ANSWERS)
    table = ObservationLoader(root, catalog).load(runs)
    if not table.rows:
        raise ValueError("Nenhuma observação encontrada para as rodadas: " + ", ".join(runs))
    reasons = SameAnswerReasons(threshold=threshold) if threshold is not None else None
    report = MeasuresReport(ClusteredBootstrap(reps=reps, seed=seed), reasons).build(table)
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    summary = out.with_suffix(".md")
    summary.write_text(render_markdown(report), encoding="utf-8")
    print(f"{len(table.rows)} observações. Relatório: {out}. Resumo: {summary}")
    return 0
