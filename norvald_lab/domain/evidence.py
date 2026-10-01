import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from norvald_lab.domain.deliberation.document_structure import DocumentSection, DocumentStructure
from norvald_lab.domain.classification import classification_from_legacy_tags, normalize_classification


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Evidence:
    """Artefato documental usado como base verificável da deliberação.

    Evidence é a informação-fonte utilizada pelo conhecimento estruturado;
    não é, por si só, um claim, uma conclusão ou uma relação do Working
    Context. Pode existir isoladamente e mantém sua própria proveniência.

    A estrutura documental é carregada como uma camada própria. Ela organiza
    capítulos, seções, hierarquia e endereçamento, sem determinar a semântica
    dos primitives do Working Context.
    """

    kind: str
    reference: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: Optional[str] = None
    body: Optional[str] = None
    canonical_body: Optional[str] = None
    status: str = "active"
    library_id: Optional[str] = None
    classification: str = "document"
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)
    identifier: str = ""
    references: List[str] = field(default_factory=list)
    structure: Optional[DocumentStructure] = None
    structure_issues: List[str] = field(default_factory=list)
    attachment_ref: Optional[str] = None
    mime_type: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "kind": self.kind,
            "reference": self.reference,
            "name": self.name,
            "description": self.description,
            "body": self.body,
            "canonical_body": self.canonical_body,
            "status": self.status,
            "library_id": self.library_id,
            "classification": self.classification,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "identifier": self.identifier,
            "references": self.references,
            "structure": self.structure.to_dict() if self.structure else None,
            "structure_issues": self.structure_issues,
            "attachment_ref": self.attachment_ref,
            "mime_type": self.mime_type,
        }

    @classmethod
    def _load_structure(cls, raw: Any, document_id: str, document_type: str) -> Optional[DocumentStructure]:
        if not raw:
            return None
        if isinstance(raw, dict) and "document_id" in raw and "document_type" in raw:
            return DocumentStructure.from_dict(raw)

        # Compatibilidade de leitura para evidências persistidas antes da
        # consolidação do contrato DocumentStructure. O legado não é
        # reintroduzido: ele é normalizado para o contrato canônico ao ser
        # carregado e será persistido novamente pelo próximo write.
        if isinstance(raw, dict):
            raw_sections = raw.get("sections", [])
        elif isinstance(raw, list):
            raw_sections = raw
        else:
            return None

        sections: List[DocumentSection] = []
        for index, item in enumerate(raw_sections, start=1):
            if not isinstance(item, dict):
                continue
            section_id = str(item.get("id") or item.get("number") or index)
            sections.append(
                DocumentSection(
                    id=section_id,
                    title=str(item.get("title", "")),
                    level=int(item.get("level", 1)),
                    order=int(item.get("order", index)),
                    parent_id=item.get("parent_id"),
                    role=item.get("role"),
                    content=str(item.get("content", "")),
                    children=[str(v) for v in item.get("children", [])],
                    semantic_ids=[str(v) for v in item.get("semantic_ids", [])],
                    metadata=dict(item.get("metadata", {})),
                )
            )

        baseline = raw.get("baseline", {}) if isinstance(raw, dict) else {}
        allowed_baseline = {
            key: value
            for key, value in baseline.items()
            if key in {
                "identity", "purpose", "scope", "context", "definitions", "content",
                "applicability", "authority", "constraints", "references", "provenance",
                "relations", "evidence", "state", "version", "lifecycle",
            }
        }
        return DocumentStructure(
            document_id=str(raw.get("document_id") or document_id) if isinstance(raw, dict) else document_id,
            document_type=str(raw.get("document_type") or document_type) if isinstance(raw, dict) else document_type,
            sections=sections,
            baseline=allowed_baseline,
            version=str(raw.get("version", "1")) if isinstance(raw, dict) else "1",
            state=str(raw.get("state", "DRAFT")) if isinstance(raw, dict) else "DRAFT",
        )

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Evidence":
        evidence_id = data.get("id", str(uuid.uuid4()))
        kind = data["kind"]
        reference = data["reference"]
        identifier = data.get("identifier", "")
        raw_structure = data.get("structure")
        structure = cls._load_structure(
            raw_structure,
            document_id=identifier or reference or evidence_id,
            document_type=kind,
        )
        return cls(
            id=evidence_id,
            kind=kind, reference=reference,
            name=data.get("name", ""), description=data.get("description"),
            body=data.get("body"), canonical_body=data.get("canonical_body"),
            status=data.get("status", "active"), library_id=data.get("library_id"),
            classification=normalize_classification(data.get("classification")) if data.get("classification") else classification_from_legacy_tags(data.get("tags", []), kind=kind), metadata=data.get("metadata", {}),
            created_at=data.get("created_at") or _now_iso(),
            updated_at=data.get("updated_at") or _now_iso(),
            identifier=identifier, references=data.get("references", []),
            structure=structure, structure_issues=data.get("structure_issues", []),
            attachment_ref=data.get("attachment_ref"), mime_type=data.get("mime_type"),
        )

