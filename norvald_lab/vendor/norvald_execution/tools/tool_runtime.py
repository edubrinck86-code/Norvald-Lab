"""O mecanismo de execução de ferramentas, sem catálogo de domínio.

O que está aqui vale para qualquer domínio: registrar ferramentas,
aplicar permissões, oferecer as definições ao provider, executar uma
chamada, emitir eventos e guardar o que foi executado.

O que **não** está aqui: quais ferramentas existem, o que elas fazem e
qual conhecimento elas consultam. Isso é do domínio, que registra as
suas e, se precisar, estende os ganchos abaixo.

Ganchos para o domínio, todos com padrão que não faz nada:

| Gancho | Para quê |
| :---- | :---- |
| `execute_contextual` | Ferramentas resolvidas pelo próprio runtime, fora do mapa de handlers |
| `make_preflight_call` | A chamada obrigatória antes das demais, se houver |
| `operational_tools` | Ferramentas disparadas pelo mecanismo, que não contam como iniciativa do modelo |
| `always_allowed` | Ferramentas que a permissão não pode desligar |

Quem não estende nada tem um runtime que executa o que registrou — e é
exatamente esse o caso de uso mínimo que prova que o mecanismo não
depende do domínio de onde foi extraído.
"""

import re
import time
from dataclasses import replace
from typing import Any, Callable, Dict, List, Optional, Tuple

from norvald_lab.vendor.norvald_execution.contracts.tool_contract import ToolCall, ToolDefinition, ToolProvenance, ToolResult
from norvald_lab.vendor.norvald_execution.tools.registered_tool import RegisteredTool
from norvald_lab.vendor.norvald_execution.tools.tool_execution import ToolExecution
from norvald_lab.vendor.norvald_execution.tools.tool_permission import ToolPermission

_ARTIFACT_ID = re.compile(
    r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-"
    r"[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}\b"
)


def artifact_id_from_result(result: ToolResult) -> Optional[str]:
    """Extrai a referência do artefato criado pela ferramenta."""
    if result.is_error or not result.content:
        return None
    match = _ARTIFACT_ID.search(result.content)
    return match.group(0) if match else None


class ToolRuntime:
    """Executa ferramentas registradas, respeitando permissões."""

    def __init__(
        self,
        tools: Optional[Dict[str, RegisteredTool]] = None,
        *,
        permissions: Optional[Dict[str, ToolPermission]] = None,
        denial_message: Optional[Callable[[str], str]] = None,
        on_event: Optional[Callable[[str, Dict[str, Any]], None]] = None,
        execution_context: Any = None,
    ) -> None:
        self._tools: Dict[str, RegisteredTool] = dict(tools or {})
        self._permissions: Dict[str, ToolPermission] = dict(permissions or {})
        self._denial_message = denial_message
        self._on_event = on_event
        self._execution_context = execution_context
        self.executions: List[ToolExecution] = []

    # -- composição
    def register(self, tool: RegisteredTool) -> None:
        self._tools[tool.definition.name] = tool

    def apply_permissions(self, permissions: Dict[str, ToolPermission]) -> None:
        self._permissions = dict(permissions)

    def for_execution_context(self, execution_context: Any) -> "ToolRuntime":
        """Um runtime igual, recortado para o contexto desta execução."""
        gemeo = type(self)(
            self._tools,
            permissions=self._permissions,
            denial_message=self._denial_message,
            on_event=self._on_event,
            execution_context=execution_context,
        )
        return gemeo

    # -- ganchos do domínio
    def execute_contextual(self, call: ToolCall) -> Optional[Tuple[str, List[ToolProvenance]]]:
        """Ferramentas que o próprio runtime resolve, sem handler.

        Devolver `None` — o padrão — significa "não é minha, procure no
        mapa de handlers".
        """
        return None

    def make_preflight_call(self, request: Any) -> Optional[ToolCall]:
        """A chamada obrigatória antes das demais, se este domínio tiver
        alguma. Sem preflight por padrão."""
        return None

    def operational_tools(self) -> set:
        """Ferramentas disparadas pelo mecanismo, que não contam contra o
        orçamento de chamadas do modelo."""
        return set()

    def always_allowed(self) -> set:
        """Ferramentas que a configuração de permissão não desliga."""
        return set()

    # -- permissões
    def allowed(self, name: str) -> bool:
        if name in self.always_allowed():
            return True
        permission = self._permissions.get(name)
        if permission is not None:
            return permission.enabled
        # Sem permissão declarada para ninguém, tudo que foi registrado
        # vale; havendo declaração para alguma, o silêncio nega.
        return not self._permissions

    # -- catálogo do que foi registrado
    def tool_names(self) -> List[str]:
        return [name for name in self._tools if self.allowed(name)]

    def catalog(self) -> List[tuple]:
        return [
            (tool.definition.name, tool.definition.description, self.allowed(name))
            for name, tool in self._tools.items()
        ]

    def definitions(self) -> List[ToolDefinition]:
        return [tool.definition for name, tool in self._tools.items() if self.allowed(name)]

    # -- execução
    def execute(self, call: ToolCall) -> ToolResult:
        started = time.perf_counter()
        resolved = self.resolve_name(call.name)
        if resolved != call.name:
            call = replace(call, name=resolved)

        if not self.allowed(call.name):
            return self._concluir(call, self._recusa(call), started)

        contextual = self.execute_contextual(call)
        if contextual is not None:
            return self._concluir(call, self._resultado_contextual(call, contextual), started)

        tool = self._tools.get(call.name)
        if tool is None:
            return self._concluir(call, self._recusa(call), started)

        return self._concluir(call, self._resultado_do_handler(call, tool, started), started)

    def resolve_name(self, name: str) -> str:
        """Ponto para o domínio aceitar apelidos de ferramenta."""
        return name

    # -- internos
    def _resultado_contextual(self, call: ToolCall, contextual) -> ToolResult:
        self._emit("tool.started", {"tool_name": call.name, "call_id": call.call_id, "arguments": call.arguments})
        try:
            content, provenance = contextual
            return ToolResult(call_id=call.call_id, name=call.name, content=content, provenance=provenance)
        except Exception as exc:
            return self._falha(call, exc)

    def _resultado_do_handler(self, call: ToolCall, tool: RegisteredTool, started: float) -> ToolResult:
        self._emit("tool.started", {"tool_name": call.name, "call_id": call.call_id, "arguments": call.arguments})
        try:
            content = tool.handler(call.arguments)
            provenance = tool.provenance(call.arguments, content) if tool.provenance else []
            result = ToolResult(call_id=call.call_id, name=call.name, content=content, provenance=provenance)
            self._emit(
                "tool.completed",
                {
                    "tool_name": call.name,
                    "call_id": call.call_id,
                    "result_chars": len(content or ""),
                    "duration_seconds": round(time.perf_counter() - started, 3),
                    "provenance": [item.as_dict() for item in provenance],
                },
            )
            return result
        except Exception as exc:
            return self._falha(call, exc)

    def _falha(self, call: ToolCall, exc: Exception) -> ToolResult:
        self._emit("tool.failed", {"tool_name": call.name, "call_id": call.call_id, "error": str(exc)})
        return ToolResult(
            call_id=call.call_id, name=call.name, content=f"A ferramenta falhou: {exc}", is_error=True
        )

    def _recusa(self, call: ToolCall) -> ToolResult:
        return ToolResult(call_id=call.call_id, name=call.name, content=self.denial(call.name), is_error=True)

    def denial(self, tool_name: str) -> str:
        if self._denial_message:
            return self._denial_message(tool_name)
        return f"Ferramenta '{tool_name}' não está disponível nesta execução."

    def _concluir(self, call: ToolCall, result: ToolResult, started: float) -> ToolResult:
        self._record(call, result, time.perf_counter() - started)
        return result

    def _emit(self, event: str, data: Dict[str, Any]) -> None:
        if callable(self._on_event):
            self._on_event(event, data)

    def _record(self, call: ToolCall, result: ToolResult, duration: float) -> None:
        tool = self._tools.get(call.name)
        artifact_id = artifact_id_from_result(result) if tool and tool.produces_artifact else None
        self.executions.append(
            ToolExecution(
                tool_name=call.name,
                call_id=call.call_id,
                arguments=dict(call.arguments),
                is_error=result.is_error,
                duration_seconds=duration,
                artifact_id=artifact_id,
                result_chars=len(result.content or ""),
            )
        )

