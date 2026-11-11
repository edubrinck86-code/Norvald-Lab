"""Lê os experimentos de uma ou mais rodadas do herd e devolve a tabela de observações.

Lê o RAW (raw/**/observations.jsonl), não o outcomes.csv: o CSV já guarda só
a tentativa final, e a análise precisa também da primeira, para relatar a
taxa de falha da tentativa 1 por modelo (11/11/2026: o runner está ganhando
novas tentativas, attempt_index 2). Por (pergunta, condição, repetição,
participante) vale sempre a tentativa mais recente; empate de índice, a
capturada por último.

A leitura de cada tentativa reaproveita o extrator da tabela tidy
(`row_from_payload`), para que opção declarada, opção aceita e confiança
sejam as mesmas do outcomes.csv. Nada aqui reinterpreta o validador.

Um diretório só pertence à rodada se o próprio registro confirmar o id
(`<run>-<pergunta>-<condição>`): o prefixo do nome não basta, porque a
rodada "piloto" casaria com "piloto-3-q01-b1".
"""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import replace
from pathlib import Path
from typing import Any, Iterable, Mapping

from norvald_lab.application.arof.outcome_extract import row_from_payload
from norvald_lab.herd.specs import experiment_id
from norvald_lab.measures.contribution_reader import ContributionReader
from norvald_lab.measures.justification_text import justification_from_content
from norvald_lab.measures.observation import Observation
from norvald_lab.measures.observation_table import ObservationTable
from norvald_lab.measures.position_resolver import PositionResolver
from norvald_lab.measures.question_catalog import QuestionCatalog


def _payloads(directory: Path) -> list[dict[str, Any]]:
    out = []
    for path in sorted((directory / "raw").rglob("*.jsonl")):
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                out.append(json.loads(line))
    return out


def _cost(payload: Mapping[str, Any]) -> float:
    usage = (((payload.get("result") or {}).get("metadata") or {}).get("raw_usage") or {})
    value = usage.get("cost") if isinstance(usage, Mapping) else None
    return float(value) if isinstance(value, (int, float)) else 0.0


class ObservationLoader:
    def __init__(self, root: Path, catalog: QuestionCatalog, resolver: PositionResolver | None = None):
        self.root = Path(root)
        self.catalog = catalog
        self.resolver = resolver or PositionResolver()
        self.reader = ContributionReader()

    def load(self, runs: Iterable[str]) -> ObservationTable:
        runs = tuple(runs)
        rows: list[Observation] = []
        for run in runs:
            run_rows: list[Observation] = []
            for directory in sorted((self.root / "experiments").glob(f"{run}-*")):
                payloads = _payloads(directory)
                if not payloads:
                    continue
                first = payloads[0]
                question = str(first.get("task_label") or first.get("task_id") or "")
                if experiment_id(run, question, str(first.get("condition_id") or "")) != directory.name:
                    continue
                run_rows += self._rows(run, payloads)
            rows += self._with_agents(run_rows)
        rows.sort(key=lambda r: (r.run, r.question_id, r.repetition, r.condition, r.participant_id))
        return ObservationTable(tuple(rows), self.catalog.questions, runs)

    @staticmethod
    def _with_agents(rows: list[Observation]) -> list[Observation]:
        """Modelo como identidade quando é único na rodada (ver Observation.agent)."""
        participants_by_model: dict[str, set[str]] = defaultdict(set)
        for row in rows:
            participants_by_model[row.model].add(row.participant_id)
        return [replace(row, agent_key=row.model) if len(participants_by_model[row.model]) == 1 else row for row in rows]

    def _rows(self, run: str, payloads: list[dict[str, Any]]) -> list[Observation]:
        attempts: dict[tuple, list[dict[str, Any]]] = defaultdict(list)
        for payload in payloads:
            key = (str(payload.get("task_label") or payload.get("task_id") or ""), str(payload.get("condition_id") or ""), str(payload.get("run_id") or ""), str(payload.get("participant_id") or ""))
            attempts[key].append(payload)
        rows = []
        for (question_id, condition, repetition, participant_id), group in attempts.items():
            group.sort(key=lambda p: (int(p.get("attempt_index") or 0), str(p.get("captured_at") or "")))
            resolved = [(p, row_from_payload(p)) for p in group]
            positions = [self.resolver.resolve(p, row) for p, row in resolved]
            latest_payload, latest_row = resolved[-1]
            position = positions[-1]
            info = self.catalog.get(question_id)
            correct = None if info.answer is None or position.option is None else position.option == info.answer
            metadata = ((latest_payload.get("request") or {}).get("studio_metadata") or {})
            read = self.reader.read(latest_payload, latest_row)
            content = str((latest_payload.get("result") or {}).get("content") or "")
            rows.append(Observation(
                run=run, question_id=question_id, kind=info.kind, category=info.category, condition=condition,
                repetition=repetition, participant_id=participant_id, model=str(latest_payload.get("requested_model") or ""),
                option=position.option, indirect=position.indirect, indirect_source=position.source_author, correct=correct,
                confidence=latest_row.confidence, justification=justification_from_content(content, author_id=participant_id),
                peer_order=tuple(metadata.get("peer_order") or ()), attempts=len(group),
                # Falha da tentativa 1 = ela não deu posição utilizável (erro, sem decisão,
                # seleção recusada). Seleção indireta resolvida não é falha.
                attempt1_failed=positions[0].option is None,
                cost=sum(_cost(p) for p in group), status=latest_row.status, validation_code=latest_row.validation_code,
                structured=read.structured, grounds=read.grounds, claims=read.claims,
            ))
        return rows
