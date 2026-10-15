"""Assistant-facing *internal* catalogue: only explicit read-only operations in slice 1.

Inspired by Huginn's Operation / Catalogue / CatalogueTools. No generic HTTP
execution endpoint is exposed until caller authentication and permissions exist.
"""
from __future__ import annotations

from dataclasses import dataclass
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
            if op.kind != "query":
                raise ValueError("Only read-only operations are permitted in this catalogue.")
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
        return operation.handler(validated)


def build_read_catalogue(runner, template, experiment_criteria):
    """The Lab's own services are authority, not the future Assistant model."""
    return ReadCatalogue([
        Operation("lab.spec.template", "query", "Template for a new experiment.", Empty,
                  lambda _: template()),
        Operation("lab.spec.evaluate", "query", "Validate and preflight a Spec without LLM calls.", SpecInput,
                  lambda item: evaluate_spec(runner, item.spec)),
        Operation("lab.experiment.criteria", "query",
                  "Evaluate original contribution diagnostics and integrity for a stored experiment.",
                  ExperimentInput, lambda item: experiment_criteria(item.experiment_id)),
    ])
