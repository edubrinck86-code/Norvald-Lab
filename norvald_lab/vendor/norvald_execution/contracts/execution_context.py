from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class ExecutionContext:
    """Representação de transporte do contexto para uma execução.

    O Working Context continua sendo a fonte estruturada de verdade. Este
    objeto não o substitui; carrega sua representação preparada para o
    participante/provider e metadados da execução.
    """

    objective: str
    working_context: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    working_context_id: Optional[str] = None
    working_context_format: str = "text"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "objective": self.objective,
            "working_context": self.working_context,
            "metadata": dict(self.metadata),
            "working_context_id": self.working_context_id,
            "working_context_format": self.working_context_format,
        }

