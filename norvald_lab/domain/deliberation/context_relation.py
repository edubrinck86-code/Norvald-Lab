from dataclasses import dataclass
from typing import Any, Dict, Optional


# Canonical semantic relations from Framework Documental 02.
# The graph remains responsible for validating source/target type pairs.
RELATION_TYPES = (
    "documents",
    "supports",
    "addresses",
    "challenges",
    "contradicts",
    "derived_from",
    "evaluated_by",
    "compares",
    "selects",
    "produces",
    "constrains",
    "resolves",
    "answers",
    "supersedes",
    "motivates",
)


@dataclass(frozen=True)
class ContextRelation:
    """Relação semântica explícita entre duas unidades do Working Context.

    `author_id` e `round_number` registram quem declarou a relação e em
    qual leva. Sem eles não é possível distinguir uma contestação entre
    autores de uma relação que o próprio autor declarou sobre os itens
    dele, e o encadeamento de levas depende exatamente dessa distinção.

    `None` significa não declarado — relação persistida antes desta
    mudança, ou origem que não informou proveniência. Nunca deve ser
    lido como "autor desconhecido, logo diferente de todos": quem
    consome a proveniência ignora a relação em vez de supor.
    """

    source_id: str
    relation_type: str
    target_id: str
    author_id: Optional[str] = None
    round_number: Optional[int] = None

    def __post_init__(self) -> None:
        if self.relation_type not in RELATION_TYPES:
            raise ValueError(f"Relação de contexto inválida: {self.relation_type}")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_id": self.source_id,
            "relation_type": self.relation_type,
            "target_id": self.target_id,
            "author_id": self.author_id,
            "round_number": self.round_number,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ContextRelation":
        round_number = data.get("round_number")
        return cls(
            source_id=data["source_id"],
            relation_type=data["relation_type"],
            target_id=data["target_id"],
            author_id=data.get("author_id") or None,
            round_number=int(round_number) if round_number is not None else None,
        )

