from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


BASELINE_FIELDS = (
    "identity", "purpose", "scope", "context", "definitions", "content",
    "applicability", "authority", "constraints", "references", "provenance",
    "relations", "evidence", "state", "version", "lifecycle",
)

DOCUMENT_APPLICABILITY = (
    "REQUIRED", "OPTIONAL", "CONDITIONAL", "NOT_APPLICABLE", "UNKNOWN", "PENDING",
)


@dataclass(frozen=True)
class DocumentAddress:
    """Endereço estrutural estável: documento + capítulo + seção."""
    document_id: str
    chapter: str
    section: str

    @property
    def value(self) -> str:
        return f"{self.document_id} {self.chapter}.{self.section}"


@dataclass
class DocumentSection:
    """Unidade estrutural; não define semântica por si só."""
    id: str
    title: str
    level: int = 1
    order: int = 0
    parent_id: Optional[str] = None
    role: Optional[str] = None
    content: str = ""
    children: List[str] = field(default_factory=list)
    semantic_ids: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def address(self, document_id: str) -> DocumentAddress:
        chapter, _, section = self.id.partition(".")
        return DocumentAddress(document_id, chapter, section or chapter)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id, "title": self.title, "level": self.level,
            "order": self.order, "parent_id": self.parent_id, "role": self.role,
            "content": self.content, "children": list(self.children),
            "semantic_ids": list(self.semantic_ids), "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DocumentSection":
        return cls(
            id=str(data["id"]), title=str(data.get("title", "")),
            level=int(data.get("level", 1)), order=int(data.get("order", 0)),
            parent_id=data.get("parent_id"), role=data.get("role"),
            content=str(data.get("content", "")),
            children=[str(v) for v in data.get("children", [])],
            semantic_ids=[str(v) for v in data.get("semantic_ids", [])],
            metadata=dict(data.get("metadata", {})),
        )


@dataclass
class DocumentStructure:
    """Estrutura documental canônica, separada da camada semântica."""
    document_id: str
    document_type: str
    sections: List[DocumentSection] = field(default_factory=list)
    baseline: Dict[str, Any] = field(default_factory=dict)
    version: str = "1"
    state: str = "DRAFT"

    def __post_init__(self) -> None:
        if not self.document_id.strip():
            raise ValueError("DocumentStructure exige document_id.")
        if not self.document_type.strip():
            raise ValueError("DocumentStructure exige document_type.")
        unknown = set(self.baseline) - set(BASELINE_FIELDS)
        if unknown:
            raise ValueError(f"Campos de baseline desconhecidos: {sorted(unknown)}")
        self.validate()

    def validate(self) -> None:
        ids = {section.id for section in self.sections}
        if len(ids) != len(self.sections):
            raise ValueError("Seção documental duplicada.")
        for section in self.sections:
            if section.level < 1:
                raise ValueError(f"Nível de seção inválido: {section.id}")
            if section.parent_id is not None and section.parent_id not in ids:
                raise ValueError(f"Pai de seção não encontrado: {section.parent_id}")
            if section.id in section.children:
                raise ValueError(f"Seção não pode ser filha de si mesma: {section.id}")
            for child_id in section.children:
                if child_id not in ids:
                    raise ValueError(f"Filho de seção não encontrado: {child_id}")

    def get_section(self, section_id: str) -> Optional[DocumentSection]:
        return next((section for section in self.sections if section.id == section_id), None)

    def address(self, section_id: str) -> DocumentAddress:
        section = self.get_section(section_id)
        if section is None:
            raise ValueError(f"Seção documental não encontrada: {section_id}")
        return section.address(self.document_id)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "document_id": self.document_id,
            "document_type": self.document_type,
            "sections": [s.to_dict() for s in self.sections],
            "baseline": dict(self.baseline), "version": self.version, "state": self.state,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DocumentStructure":
        return cls(
            document_id=str(data["document_id"]), document_type=str(data["document_type"]),
            sections=[DocumentSection.from_dict(item) for item in data.get("sections", [])],
            baseline=dict(data.get("baseline", {})), version=str(data.get("version", "1")),
            state=str(data.get("state", "DRAFT")),
        )

