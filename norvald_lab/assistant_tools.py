"""Typed query and plan-staging tools for the native Lab Assistant.

The LLM may discover and invoke only the Lab's whitelisted query or plan-creation catalogue.
It cannot access arbitrary routes, filesystem paths, credentials, deletion,
destructive changes or unplanned execution through this interface.
"""
from __future__ import annotations

from norvald_lab.vendor.norvald_execution.contracts.tool_contract import ToolDefinition


def definitions():
    return [
        ToolDefinition(
            name="list_operations",
            description="List permitted safe Norvald Lab operations and their purposes.",
            parameters={"type": "object", "properties": {}, "additionalProperties": False}),
        ToolDefinition(
            name="describe_operation",
            description="Read the Pydantic JSON input schema of a specific Lab operation.",
            parameters={"type": "object", "properties": {
                "name": {"type": "string"}}, "required": ["name"], "additionalProperties": False}),
        ToolDefinition(
            name="call_operation",
            description="Call one whitelisted Lab operation; execution requires a previously displayed plan.",
            parameters={"type": "object", "properties": {
                "name": {"type": "string"},
                "input": {"type": "object", "additionalProperties": True}},
                "required": ["name", "input"], "additionalProperties": False}),
    ]


def dispatch(catalogue, name, args):
    if not isinstance(args, dict):
        raise ValueError("Argumentos de ferramenta inválidos.")
    if name == "list_operations":
        if args:
            raise ValueError("list_operations não recebe argumentos.")
        return {"operations": [{"name": item["name"], "summary": item["summary"]}
                                for item in catalogue.describe()]}
    if name == "describe_operation":
        if set(args) != {"name"} or not isinstance(args["name"], str):
            raise ValueError("Informe apenas o nome da operação.")
        item = next((item for item in catalogue.describe()
                     if item["name"] == args["name"]), None)
        if item is None:
            raise ValueError("Operação não autorizada ou desconhecida.")
        return item
    if name == "call_operation":
        if set(args) != {"name", "input"} or not isinstance(args["name"], str):
            raise ValueError("Informe nome e entrada estruturada.")
        return {"operation": args["name"], "result": catalogue.call(args["name"], args["input"])}
    raise ValueError("Ferramenta não autorizada.")


async def dispatch_async(catalogue, name, args):
    """Async dispatch adds plan execution while retaining typed server policy."""
    if name != "call_operation":
        return dispatch(catalogue, name, args)
    if not isinstance(args, dict) or set(args) != {"name", "input"}:
        raise ValueError("Informe nome e entrada estruturada.")
    operation = args["name"]
    if not isinstance(operation, str):
        raise ValueError("Nome de operação inválido.")
    return {"operation": operation,
            "result": await catalogue.call_async(operation, args["input"])}
