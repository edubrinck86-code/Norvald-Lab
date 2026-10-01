"""Camada de preparação de anexos multimodais do request.

Responsabilidade única: resolver referências leves de anexo
(`attachment_ref`, guardadas na Session/Evidence) em bytes reais via
WorkspaceAttachmentStore, produzindo `AttachmentPayload` prontos para o
`ExecutionRequest`.

Deliberadamente separado da montagem de prompt (que só conhece texto/
instruções e nunca deve importar storage) e do Provider (que só conhece
tradução de AttachmentPayload -> formato nativo da API). Esta camada é
o único ponto que sabe ler bytes do disco/armazenamento.
"""

import base64
from dataclasses import dataclass
from typing import List, Sequence, Tuple

from norvald_lab.vendor.norvald_execution.contracts.attachment_contracts import AttachmentPayload, AttachmentResult


@dataclass
class AttachmentRef:
    """Referência leve e serializável — o que fica guardado na Session
    entre o fechamento do Working Context e o momento em que cada
    participante de fato executa. Nunca carrega bytes."""

    identifier: str
    filename: str
    mime_type: str
    attachment_ref: str

    def to_dict(self) -> dict:
        return {"identifier": self.identifier, "filename": self.filename, "mime_type": self.mime_type, "attachment_ref": self.attachment_ref}

    @classmethod
    def from_dict(cls, data: dict) -> "AttachmentRef":
        return cls(identifier=data["identifier"], filename=data.get("filename", ""), mime_type=data.get("mime_type", "application/octet-stream"), attachment_ref=data["attachment_ref"])


def refs_from_evidence(evidence: Sequence) -> List[AttachmentRef]:
    return [AttachmentRef(identifier=e.identifier or e.id, filename=e.name or e.reference, mime_type=e.mime_type or "application/octet-stream", attachment_ref=e.attachment_ref) for e in evidence if getattr(e, "attachment_ref", None)]


def resolve_attachments(refs: Sequence[AttachmentRef], attachment_store) -> Tuple[List[AttachmentPayload], List[AttachmentResult]]:
    payloads: List[AttachmentPayload] = []
    failures: List[AttachmentResult] = []
    for ref in refs:
        attachment = attachment_store.get(ref.attachment_ref)
        if not attachment:
            failures.append(AttachmentResult(identifier=ref.identifier, filename=ref.filename, mime_type=ref.mime_type, status="failed", reason="Anexo não encontrado no Repository (attachment_ref inválido)."))
            continue
        try:
            raw = attachment_store.read_bytes(attachment)
        except FileNotFoundError:
            failures.append(AttachmentResult(identifier=ref.identifier, filename=ref.filename, mime_type=ref.mime_type, status="failed", reason="Arquivo bruto ausente no disco do Repository."))
            continue
        payloads.append(AttachmentPayload(identifier=ref.identifier, filename=ref.filename, mime_type=ref.mime_type, data_base64=base64.b64encode(raw).decode("ascii")))
    return payloads, failures

