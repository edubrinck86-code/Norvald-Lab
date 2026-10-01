from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class Dimension:
    """Unidade dimensional do Universal Document Framework.

    Dimensões são hierárquicas e extensíveis. O modelo não congela uma lista
    de dimensões: novas dimensões/subdimensões surgem conforme necessidade
    documental identificada.
    """

    id: str
    name: str
    definition: str = ""
    purpose: str = ""
    scope: str = ""
    applicability: str = "UNKNOWN"
    parent_id: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    state: str = "ACTIVE"
    version: str = "1"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("Dimension exige id.")
        if not self.name.strip():
            raise ValueError("Dimension exige name.")
        if self.applicability not in {"REQUIRED", "OPTIONAL", "CONDITIONAL", "NOT_APPLICABLE", "UNKNOWN", "PENDING"}:
            raise ValueError(f"Aplicabilidade de dimensão inválida: {self.applicability}")
        if self.state not in {"ACTIVE", "DRAFT", "DEPRECATED"}:
            raise ValueError(f"Estado de dimensão inválido: {self.state}")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "definition": self.definition,
            "purpose": self.purpose,
            "scope": self.scope,
            "applicability": self.applicability,
            "parent_id": self.parent_id,
            "dependencies": list(self.dependencies),
            "state": self.state,
            "version": self.version,
            "metadata": dict(self.metadata),
        }

