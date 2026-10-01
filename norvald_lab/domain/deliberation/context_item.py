from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


CONTEXT_ITEM_TYPES = (
    "context", "evidence", "claim", "argument", "counterargument", "response",
    "inference", "option", "comparison", "criterion", "decision", "consequence",
    "condition", "open_question", "uncertainty", "gap", "reference", "relation",
)

SOURCE_TYPES = (
    "document", "library", "attachment", "deliberation_message", "specialist",
)

ITEM_STATUSES = (
    "active", "superseded", "rejected", "resolved", "accepted", "unresolved",
    "contested", "unknown",
)


@dataclass
class ContextItem:
    """Unidade semântica do WC com referências estruturais opcionais."""

    id: str
    type: str
    content: str
    dimension_id: Optional[str] = None
    # CONGELADO — não pedir ao especialista, não preencher, não remover.
    # O Universal Document Framework cita "camadas" apenas como
    # quantidade não predeterminada (§1) e no modelo de 10 camadas que
    # ele mesmo manda não copiar literalmente (§8): não há tipo, não há
    # registro, não há valores válidos — ao contrário das dimensões, que
    # o §7 lista. Pedir que alguém preencha um campo sem dizer quais
    # valores existem produz invenção, e invenção contamina todo item
    # declarado dali em diante, de forma difícil de desfazer. O campo
    # permanece na estrutura, vazio, até haver definição.
    # Ver docs/adr/Processando/Decisoes-Pendentes-Orfaos-Layer-Relacoes.md §2.
    layer: Optional[str] = None
    document_id: Optional[str] = None
    section_id: Optional[str] = None
    source_type: Optional[str] = None
    source_id: Optional[str] = None
    source_location: Optional[str] = None
    origin: Optional[str] = None
    author_id: Optional[str] = None
    round_number: Optional[int] = None
    status: str = "active"
    confidence: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.type not in CONTEXT_ITEM_TYPES:
            raise ValueError(f"Tipo de ContextItem inválido: {self.type}")
        if self.source_type is not None and self.source_type not in SOURCE_TYPES:
            raise ValueError(f"Tipo de origem inválido: {self.source_type}")
        if self.status not in ITEM_STATUSES:
            raise ValueError(f"Status de ContextItem inválido: {self.status}")
        if self.section_id is not None and self.document_id is None:
            raise ValueError("section_id exige document_id.")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id, "type": self.type, "content": self.content,
            "dimension_id": self.dimension_id, "layer": self.layer,
            "document_id": self.document_id, "section_id": self.section_id,
            "source_type": self.source_type, "source_id": self.source_id,
            "source_location": self.source_location, "origin": self.origin,
            "author_id": self.author_id, "round_number": self.round_number,
            "status": self.status, "confidence": self.confidence,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ContextItem":
        return cls(
            id=data["id"], type=data["type"], content=data.get("content", ""),
            dimension_id=data.get("dimension_id"), layer=data.get("layer"),
            document_id=data.get("document_id"), section_id=data.get("section_id"),
            source_type=data.get("source_type"), source_id=data.get("source_id"),
            source_location=data.get("source_location"), origin=data.get("origin"),
            author_id=data.get("author_id"), round_number=data.get("round_number"),
            status=data.get("status", "active"), confidence=data.get("confidence"),
            metadata=dict(data.get("metadata", {})),
        )

