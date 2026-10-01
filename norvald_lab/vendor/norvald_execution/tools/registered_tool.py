"""Uma ferramenta registrada: a definição que o provider enxerga e o
handler que a executa.

Quem registra é o domínio — o mecanismo só conhece esta forma.
"""

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

from norvald_lab.vendor.norvald_execution.contracts.tool_contract import ToolDefinition, ToolProvenance


@dataclass
class RegisteredTool:
    definition: ToolDefinition
    handler: Callable[[Dict[str, Any]], str]
    produces_artifact: bool = False
    provenance: Optional[
        Callable[[Dict[str, Any], str], List[ToolProvenance]]
    ] = None

