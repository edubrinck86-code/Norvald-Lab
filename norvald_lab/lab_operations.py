"""Assistant-facing *internal* catalogue: only explicit read-only operations in slice 1.

Inspired by Huginn's Operation / Catalogue / CatalogueTools. No generic HTTP
execution endpoint is exposed until caller authentication and permissions exist.
"""
from __future__ import annotations

from dataclasses import dataclass
from inspect import isawaitable
from typing import Callable

from pydantic import BaseModel, ConfigDict, Field

from norvald_lab.criteria import evaluate_spec


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Empty(Input):
    pass


class SpecInput(Input):
    spec: dict = Field(description="Portable Norvald Lab experiment specification.")


class ExperimentInput(Input):
    experiment_id: str = Field(min_length=1, max_length=120)


class PlanInput(Input):
    plan_id: str = Field(pattern=r"^plan-[a-f0-9]{32}$")


class ComparisonInput(Input):
    left: str = Field(min_length=1)
    right: str = Field(min_length=1)


class DeriveInput(Input):
    source_id: str = Field(min_length=1)
    new_id: str = Field(min_length=1)
    exposure: str = Field(pattern=r"^(self|exposed)$")


class IncidentInput(Input):
    incident_id: str = Field(pattern=r"^ci-[0-9a-f]{32}$")


class IncidentListInput(Input):
    experiment_id: str | None = Field(default=None, min_length=1, max_length=120)
    status: str | None = None
    limit: int = Field(default=100, ge=1, le=500)


@dataclass(frozen=True)
class Operation:
    name: str
    kind: str
    description: str
    input_type: type[Input]
    handler: Callable


class ReadCatalogue:
    """Whitelist with validated JSON inputs, not an open dispatcher over Python."""

    def __init__(self, operations):
        self._operations = {}
        for op in operations:
            if op.kind not in {"query", "organize", "execute"}:
                raise ValueError("Only explicit non-destructive operations are permitted.")
            if op.kind == "execute" and op.name != "lab.plan.execute":
                raise ValueError("No generic execution or destructive operations permitted.")
            if op.name in self._operations:
                raise ValueError("Duplicate operation: " + op.name)
            self._operations[op.name] = op

    def describe(self):
        return [{"name": op.name, "kind": op.kind, "summary": op.description,
                 "input": op.input_type.model_json_schema()}
                for op in self._operations.values()]

    def call(self, name, payload=None):
        try:
            operation = self._operations[name]
        except KeyError as exc:
            raise ValueError("Unknown or unauthorized operation.") from exc
        validated = operation.input_type.model_validate(payload if payload is not None else {})
        if operation.kind == "execute":
            raise ValueError("Execução exige caminho assíncrono e plano apresentado.")
        return operation.handler(validated)

    async def call_async(self, name, payload=None):
        try:
            operation = self._operations[name]
        except KeyError as exc:
            raise ValueError("Unknown or unauthorized operation.") from exc
        validated = operation.input_type.model_validate(payload if payload is not None else {})
        result = operation.handler(validated)
        if isawaitable(result):
            return await result
        return result


def build_read_catalogue(runner, template, experiment_criteria, *,
                         list_incidents=None, get_incident=None,
                         list_experiments=None, get_experiment_status=None,
                         plan_experiment=None, plan_adjustment=None, derive=None,
                         compare=None, execute_plan=None, presented=None):
    """The Lab's own services are authority, not the future Assistant model."""
    operations = [
        Operation("lab.spec.template", "query", "Template for a new experiment.", Empty,
                  lambda _: template()),
        Operation("lab.spec.evaluate", "query", "Validate and preflight a Spec without LLM calls.", SpecInput,
                  lambda item: evaluate_spec(runner, item.spec)),
        Operation("lab.experiment.criteria", "query",
                  "Evaluate original contribution diagnostics and integrity for a stored experiment.",
                  ExperimentInput, lambda item: experiment_criteria(item.experiment_id)),
    ]
    if list_incidents is not None:
        operations.append(Operation(
            "lab.incidents.list", "query", "List durable unmet framework criteria.",
            IncidentListInput, lambda item: list_incidents(
                experiment_id=item.experiment_id, status=item.status, limit=item.limit)))
    if get_incident is not None:
        operations.append(Operation(
            "lab.incident.get", "query", "Read incident, audit history and recovery proposal.",
            IncidentInput, lambda item: get_incident(item.incident_id)))
    if list_experiments is not None:
        operations.append(Operation(
            "lab.experiments.list", "query", "List available experiments and their statuses.",
            Empty, lambda item: list_experiments()))
    if get_experiment_status is not None:
        operations.append(Operation(
            "lab.experiment.status", "query", "Read current status or outcome of an experiment.",
            ExperimentInput, lambda item: get_experiment_status(item.experiment_id)))
    if plan_experiment is not None:
        operations.append(Operation(
            "lab.experiment.plan", "organize",
            "Prepare and persist a visible experiment plan without executing it.",
            SpecInput, lambda item: plan_experiment(item.spec)))
    if plan_adjustment is not None:
        operations.append(Operation(
            "lab.adjustment.plan", "organize",
            "Prepare and persist a separate adjustment plan without invoking a provider.",
            IncidentInput, lambda item: plan_adjustment(item.incident_id)))
    if derive is not None:
        operations.append(Operation(
            "lab.spec.derive", "query",
            "Draft a derived condition from an existing complete and verified B1.",
            DeriveInput, lambda item: derive(
                item.source_id, item.new_id, item.exposure)))
    if compare is not None:
        operations.append(Operation(
            "lab.experiments.compare", "query",
            "Descriptive comparison of two sealed experimental datasets.",
            ComparisonInput, lambda item: compare(item.left, item.right)))
    if execute_plan is not None and presented is not None:
        async def run_presented(item):
            if not presented(item.plan_id):
                raise ValueError(
                    "Plano ainda não apresentado ao operador. Consulte-o na interface antes de executar.")
            return await execute_plan(item.plan_id)
        operations.append(Operation(
            "lab.plan.execute", "execute",
            "Execute a previously displayed non-destructive plan, with no extra approval.",
            PlanInput, run_presented))
    return ReadCatalogue(operations)
