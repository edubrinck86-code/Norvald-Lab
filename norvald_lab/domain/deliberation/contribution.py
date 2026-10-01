import json
import re
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


_CONTRIBUTION_RE = re.compile(
    r"<<CONTRIBUTION>>\s*(?P<body>.*?)\s*<<END_CONTRIBUTION>>",
    re.DOTALL,
)

# Bloco aberto e nunca fechado: resposta truncada, ou fechamento grafado de
# outra forma pelo especialista. O delimitador sobrevivia no texto persistido e
# o front o renderizava como tag HTML desconhecida, deixando "<>" na tela.
_DANGLING_OPEN_RE = re.compile(r"<<\s*CONTRIBUTION\s*>>.*$", re.DOTALL | re.IGNORECASE)
_DANGLING_CLOSE_RE = re.compile(r"<<\s*/?\s*END[_\s-]*CONTRIBUTION\s*>>", re.IGNORECASE)

# The specialist declares semantic knowledge; the Studio does not infer it.
DECLARABLE_KNOWLEDGE_TYPES = (
    "claim", "argument", "counterargument", "response", "inference", "option",
    "comparison", "criterion", "decision", "consequence", "condition",
    "open_question", "uncertainty", "gap", "reference",
)


def strip_contribution_block(response: str) -> str:
    """A prosa sem o bloco declarado."""
    prosa = _CONTRIBUTION_RE.sub("", response or "")
    prosa = _DANGLING_OPEN_RE.sub("", prosa)
    prosa = _DANGLING_CLOSE_RE.sub("", prosa)
    return prosa.strip()


def _strip_code_fence(body: str) -> str:
    """Remove cerca de código ao redor do JSON.

    Vários modelos envolvem o payload em ```json ... ``` mesmo dentro dos
    delimitadores. O bloco era descartado inteiro por JSONDecodeError, e a
    rodada terminava como "nenhum conhecimento declarado" com o
    conhecimento ali, a três caracteres de distância.
    """
    text = body.strip()
    if not text.startswith("```"):
        return text
    text = text[3:]
    newline = text.find("\n")
    if newline != -1 and text[:newline].strip().isalpha():
        text = text[newline + 1:]
    if text.rstrip().endswith("```"):
        text = text.rstrip()[:-3]
    return text.strip()


@dataclass(frozen=True)
class ContributionKnowledge:
    local_id: str
    type: str
    content: str
    dimension_id: Optional[str] = None
    layer: Optional[str] = None
    confidence: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ContributionRelation:
    relation_type: str
    source: str
    target: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass(frozen=True)
class Contribution:
    """Estrutura declarada pelo especialista; não interpreta a resposta."""

    id: str
    author_id: str
    round_number: int
    response: str
    knowledge: List[ContributionKnowledge] = field(default_factory=list)
    relations: List[ContributionRelation] = field(default_factory=list)

    @classmethod
    def parse(
        cls,
        response: str,
        *,
        author_id: str,
        round_number: int,
        contribution_id: Optional[str] = None,
    ) -> "Contribution":
        """Extrai somente o bloco estruturado declarado pelo especialista.

        O parsing é deliberadamente tolerante: texto sem bloco ou bloco
        inválido nunca impede o turno. Nesse caso, a resposta natural é
        preservada e nenhum conhecimento novo é declarado.
        """
        raw_response = response or ""
        match = _CONTRIBUTION_RE.search(raw_response)
        if match is None:
            return cls(
                id=contribution_id or str(uuid.uuid4()),
                author_id=author_id,
                round_number=round_number,
                response=raw_response,
            )

        try:
            payload = json.loads(_strip_code_fence(match.group("body")))
            if not isinstance(payload, dict):
                raise ValueError("Contribution payload must be an object")

            knowledge_payload = payload.get("knowledge", [])
            relation_payload = payload.get("relations", [])
            if not isinstance(knowledge_payload, list) or not isinstance(relation_payload, list):
                raise ValueError("knowledge and relations must be arrays")

            knowledge = [
                ContributionKnowledge(
                    local_id=str(item["local_id"]),
                    type=str(item["type"]),
                    content=str(item.get("content", "")),
                    dimension_id=item.get("dimension_id"),
                    layer=item.get("layer"),
                    confidence=item.get("confidence"),
                    metadata=dict(item.get("metadata", {})),
                )
                for item in knowledge_payload
            ]
            relations = [
                ContributionRelation(
                    id=str(item.get("id") or uuid.uuid4()),
                    relation_type=str(item["relation_type"]),
                    source=str(item["source"]),
                    target=str(item["target"]),
                )
                for item in relation_payload
            ]
        except (KeyError, TypeError, ValueError, json.JSONDecodeError):
            return cls(
                id=contribution_id or str(uuid.uuid4()),
                author_id=author_id,
                round_number=round_number,
                response=raw_response,
            )

        natural_response = _CONTRIBUTION_RE.sub("", raw_response).strip()
        return cls(
            id=contribution_id or str(uuid.uuid4()),
            author_id=author_id,
            round_number=round_number,
            response=natural_response,
            knowledge=knowledge,
            relations=relations,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "author_id": self.author_id,
            "round_number": self.round_number,
            "response": self.response,
            "knowledge": [
                {
                    "local_id": item.local_id,
                    "type": item.type,
                    "content": item.content,
                    "dimension_id": item.dimension_id,
                    "layer": item.layer,
                    "confidence": item.confidence,
                    "metadata": item.metadata,
                }
                for item in self.knowledge
            ],
            "relations": [
                {
                    "id": relation.id,
                    "relation_type": relation.relation_type,
                    "source": relation.source,
                    "target": relation.target,
                }
                for relation in self.relations
            ],
        }

