from dataclasses import dataclass
from typing import List

ATTACHMENT_KIND_IMAGE = "image"
ATTACHMENT_KIND_DOCUMENT = "document"


def classify_attachment_kind(mime_type: str) -> str:
    mime_type = (mime_type or "").lower()
    if mime_type.startswith("image/"):
        return ATTACHMENT_KIND_IMAGE
    if mime_type == "application/pdf":
        return ATTACHMENT_KIND_DOCUMENT
    return "other"


@dataclass
class AttachmentPayload:
    identifier: str
    filename: str
    mime_type: str
    data_base64: str


@dataclass
class AttachmentResult:
    identifier: str
    filename: str
    mime_type: str
    status: str
    reason: str = ""

    def to_dict(self) -> dict:
        return {
            "identifier": self.identifier,
            "filename": self.filename,
            "mime_type": self.mime_type,
            "status": self.status,
            "reason": self.reason,
        }

