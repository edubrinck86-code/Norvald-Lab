"""Registro de uma execução de ferramenta: o que foi chamado, o que
voltou, quanto demorou.

`participant_id` e `round_number` são campos que o consumidor preenche
se fizerem sentido para ele — ficaram do formato do Studio e serão
generalizados quando o segundo consumidor disser com o quê.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional
import uuid


@dataclass(frozen=True)
class ToolExecution:
    tool_name: str
    call_id: str
    arguments: Dict[str, Any]
    is_error: bool
    duration_seconds: float
    participant_id: str = ""
    round_number: Optional[int] = None
    artifact_id: Optional[str] = None
    result_chars: int = 0
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "tool_name": self.tool_name,
            "call_id": self.call_id,
            "arguments": self.arguments,
            "is_error": self.is_error,
            "duration_seconds": round(self.duration_seconds, 3),
            "participant_id": self.participant_id,
            "round_number": self.round_number,
            "artifact_id": self.artifact_id,
            "result_chars": self.result_chars,
        }

