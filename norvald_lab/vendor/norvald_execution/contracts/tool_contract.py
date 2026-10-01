"""Contrato de ferramenta — o que um agente pode chamar durante a sua vez.

Aqui está apenas a forma: como uma ferramenta é descrita ao provider,
como uma chamada chega e como um resultado volta. Quais ferramentas
existem é do domínio que as expõe, não daqui.

A LLM decide *quando* chamar; este módulo só descreve o contrato que o
runtime executa.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

MAX_DOCUMENT_CHARS = 60000


@dataclass(frozen=True)
class ToolDefinition:
    """Descrição de uma ferramenta, independente de Provider.

    Os campos abaixo de `parameters` são metadados do domínio: descrevem a
    ferramenta para quem decide o que oferecer, e **não** viajam para a
    LLM. O provider recebe só nome, descrição e schema.
    """

    name: str
    description: str
    parameters: Dict[str, Any]
    capabilities: frozenset = field(default_factory=frozenset)
    cost: str = "local"
    depends_on: tuple = ()
    effect: str = "read"


@dataclass(frozen=True)
class ToolCall:
    """Pedido de execução emitido pela LLM."""

    call_id: str
    name: str
    arguments: Dict[str, Any]
    thought_signature: Optional[str] = None


@dataclass(frozen=True)
class ToolProvenance:
    """Origem navegável de um resultado produzido por uma ferramenta."""

    source_type: str
    source_id: str
    title: Optional[str] = None
    evidence_id: Optional[str] = None
    locator: Optional[str] = None
    query: Optional[str] = None
    url: Optional[str] = None

    def as_dict(self) -> Dict[str, Any]:
        return {"source_type": self.source_type, "source_id": self.source_id, "title": self.title, "evidence_id": self.evidence_id, "locator": self.locator, "query": self.query, "url": self.url}


@dataclass(frozen=True)
class ToolResult:
    """Resposta a um ToolCall, incluindo sua proveniência."""

    call_id: str
    name: str
    content: str
    is_error: bool = False
    provenance: List[ToolProvenance] = field(default_factory=list)

    def provenance_dicts(self) -> List[Dict[str, Any]]:
        return [item.as_dict() for item in self.provenance]


def clamp_limit(raw: Optional[Any], default: int = 5, maximum: int = 10) -> int:
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return default
    return max(1, min(value, maximum))

