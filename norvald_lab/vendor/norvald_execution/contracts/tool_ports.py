"""Portas do mecanismo de ferramentas.

O orquestrador precisa saber *que* existe um runtime de ferramentas e um
laço que as executa — não precisa saber quais ferramentas existem nem
como elas funcionam. Estas portas são o contrato mínimo entre os dois.

Quem implementa é o domínio (ou o mecanismo de ferramentas, quando ele
vier para cá no C4). Sem implementação injetada, o orquestrador executa
sem ferramentas, que é o comportamento correto para quem não as tem.
"""

from typing import Any, List, Protocol, runtime_checkable

from norvald_lab.vendor.norvald_execution.contracts.tool_contract import ToolDefinition


@runtime_checkable
class ToolRuntimePort(Protocol):
    """O que o orquestrador usa de um runtime de ferramentas."""

    def definitions(self) -> List[ToolDefinition]:
        """As ferramentas oferecidas ao provider nesta execução."""

    def for_execution_context(self, execution_context: Any) -> "ToolRuntimePort":
        """Um runtime recortado para o contexto desta execução."""


@runtime_checkable
class ToolLoopPort(Protocol):
    """O laço que resolve chamadas de ferramenta com o provider.

    Duas estratégias, ambas do mecanismo: executar as ferramentas dentro
    do fluxo, ou resolvê-las antes e então transmitir a resposta.
    """

    async def execute_with_tools(self, *args: Any, **kwargs: Any) -> Any:
        ...

    async def resolve_tools_then_stream(self, *args: Any, **kwargs: Any) -> Any:
        ...

