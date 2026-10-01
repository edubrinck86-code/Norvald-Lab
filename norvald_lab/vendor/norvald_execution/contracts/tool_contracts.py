from dataclasses import dataclass, field

from norvald_lab.vendor.norvald_execution.contracts.tool_contract import ToolCall, ToolResult


@dataclass(frozen=True)
class ToolExchange:
    calls: list[ToolCall]
    results: list[ToolResult]
    assistant_text: str = ""
    # Estado opaco do provider que precisa sobreviver ao round-trip de tools.
    # Ex.: Anthropic exige que blocos `thinking`/`redacted_thinking` sejam
    # reenviados sem alteração junto do `tool_use` que os acompanhou.
    provider_state: dict = field(default_factory=dict)

