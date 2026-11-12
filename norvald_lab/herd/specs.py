"""Monta os specs cegos (B1, B2) de uma pergunta do banco para um painel.

O Lab aceita uma pergunta por experimento (Preenchimento do Lab, 15/10/2026);
cada pergunta vira B1 e B2 aqui e B3 e E por derivação de B1 (cli.derive_spec).
Os participantes recebem ids e nomes neutros e iguais em formato
("analista-1", "Analista 1"), para que o rótulo visto em E não revele modelo
nem família (Ajustes necessários, item 1).
"""

from __future__ import annotations

import copy
from typing import Any, Mapping

BLIND_CONDITIONS = ("B1", "B2")

# Rótulos neutros por idioma. Em inglês (decisão de 11/11/2026), um "Analista" em
# português dentro do prompt seria o único texto em outra língua visto pelos pares.
LABELS = {"pt-BR": ("analista", "Analista"), "en": ("analyst", "Analyst")}


def experiment_id(run_id: str, question_id: str, condition_id: str) -> str:
    return f"{run_id}-{question_id}-{condition_id.lower()}"


def participants_for(panel: Mapping[str, Any]) -> list[dict[str, Any]]:
    slug, label = LABELS[panel.get("language", "pt-BR")]
    out = []
    for position, slot in enumerate(panel["participants"], start=1):
        out.append({
            "id": f"{slug}-{position}", "name": f"{label} {position}", "role": label,
            "provider": slot["provider"], "model": slot["model"],
            "reasoning_effort": panel.get("reasoning_effort", "default"),
            "sampling_with_reasoning": bool(panel.get("sampling_with_reasoning", False)),
            "sampling": copy.deepcopy(panel["sampling"]),
            # Só entra quando o painel fixa: specs antigos seguem idênticos.
            **({"upstream_provider": slot["upstream_provider"]} if slot.get("upstream_provider") else {}),
        })
    return out


def blind_spec(question: Mapping[str, Any], panel: Mapping[str, Any], *, run_id: str, condition_id: str) -> dict[str, Any]:
    if condition_id not in BLIND_CONDITIONS:
        raise ValueError("Só B1 e B2 nascem aqui; B3 e E derivam de B1.")
    participants = participants_for(panel)
    language = {"language": panel["language"]} if "language" in panel else {}
    # Só entra quando o painel declara: painéis anteriores seguem gerando o mesmo spec.
    attempts = {"max_agent_attempts": panel["max_agent_attempts"]} if "max_agent_attempts" in panel else {}
    return language | {
        "schema_version": "norvald.lab.spec.v1",
        "experiment_id": experiment_id(run_id, question["id"], condition_id),
        "mode": panel.get("mode", "live"),
        "task": {"id": question["id"], "objective": question["question"], "instructions": panel["instructions"]},
        "participants": participants,
        "providers": copy.deepcopy(panel["providers"]),
        "documents": [],
        "working_context": {"question": "", "items": [{"id": o["id"], "type": "option", "content": o["content"]} for o in question["options"]], "relations": []},
        "repetitions": 1,
        "condition": {"id": condition_id, "exposure": "blind", "tools": "off"},
        "budget": {"max_concurrency": len(participants), "max_concurrency_per_provider": panel.get("max_concurrency_per_provider", 2), "timeout_seconds": panel.get("timeout_seconds", 300)} | attempts,
    }
