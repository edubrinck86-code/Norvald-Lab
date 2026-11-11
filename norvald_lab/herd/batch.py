"""Executa a coleta do Δ_herd em lote, na ordem do protocolo, retomável.

Um experimento que já existe não é refeito: o Lab proíbe reutilizar id.
Se B1 de uma pergunta não terminou completo, B3 e E dela são pulados e
registrados como bloqueados, porque a exposição exige resposta válida de
todos (runner.prepare recusa). Nada é descartado em silêncio: o resumo
diz o que rodou, o que já existia e o que ficou bloqueado, e por quê.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from norvald_lab.cli import derive_spec
from norvald_lab.herd.schedule import Step, protocol_order
from norvald_lab.herd.specs import blind_spec, experiment_id
from norvald_lab.runner import ExperimentRunner


@dataclass
class BatchReport:
    ran: list[tuple[str, str]] = field(default_factory=list)  # (experiment_id, status)
    existing: list[tuple[str, str]] = field(default_factory=list)
    blocked: list[tuple[str, str]] = field(default_factory=list)  # (experiment_id, motivo)

    def to_dict(self) -> dict[str, Any]:
        return {"ran": self.ran, "existing": self.existing, "blocked": self.blocked}


class HerdBatch:
    def __init__(self, runner: ExperimentRunner, bank: Mapping[str, Any], panel: Mapping[str, Any], *, run_id: str):
        self.runner = runner
        self.questions = {q["id"]: q for q in bank["questions"]}
        self.panel = panel
        self.run_id = run_id

    def _status(self, expid: str) -> str | None:
        result = self.runner.root / "experiments" / expid / "result.json"
        if result.exists():
            return json.loads(result.read_text(encoding="utf-8"))["status"]
        if (self.runner.root / "experiments" / expid).exists():
            return "unfinished"
        return None

    def _spec(self, step: Step) -> dict[str, Any]:
        if not step.derived:
            return blind_spec(self.questions[step.question_id], self.panel, run_id=self.run_id, condition_id=step.condition_id)
        source = experiment_id(self.run_id, step.question_id, "B1")
        exposure = "self" if step.condition_id == "B3" else "exposed"
        return derive_spec(self.runner.root, source, experiment_id(self.run_id, step.question_id, step.condition_id), exposure, condition_id=step.condition_id)

    async def run(self, question_ids: Sequence[str], *, allow_live: bool, on_event: Callable | None = None, on_step: Callable | None = None) -> BatchReport:
        unknown = [q for q in question_ids if q not in self.questions]
        if unknown:
            raise ValueError("Perguntas fora do banco: " + ", ".join(unknown))
        report = BatchReport()
        for step in protocol_order(question_ids):
            expid = experiment_id(self.run_id, step.question_id, step.condition_id)
            status = self._status(expid)
            if status is not None:
                report.existing.append((expid, status))
                continue
            if step.derived:
                origin = self._status(experiment_id(self.run_id, step.question_id, "B1"))
                if origin != "complete":
                    report.blocked.append((expid, f"B1 {origin or 'ausente'}"))
                    continue
            if on_step:
                on_step(step, expid)
            try:
                result = await self.runner.run(self.runner.prepare(self._spec(step)), allow_live=allow_live, on_event=on_event)
                report.ran.append((expid, result["status"]))
            except ValueError as exc:  # recusa antes de chamar modelos (ex.: exposição incompleta)
                report.blocked.append((expid, str(exc)[:300]))
        return report
