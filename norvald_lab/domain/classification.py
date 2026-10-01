from __future__ import annotations

from typing import Iterable

CLASSIFICATIONS = (
    "document",
    "analysis",
    "evidence",
    "data",
    "code",
    "diagram",
    "draft",
)

_CLASSIFICATION_ALIASES = {
    "documento": "document",
    "document": "document",
    "análise": "analysis",
    "analise": "analysis",
    "analysis": "analysis",
    "evidência": "evidence",
    "evidencia": "evidence",
    "evidence": "evidence",
    "dados": "data",
    "data": "data",
    "código": "code",
    "codigo": "code",
    "code": "code",
    "diagrama": "diagram",
    "diagram": "diagram",
    "rascunho": "draft",
    "draft": "draft",
}

_CODE_EXTENSIONS = {
    "py", "js", "jsx", "ts", "tsx", "java", "go", "rs", "c", "h", "cpp",
    "hpp", "cs", "rb", "php", "sh", "sql", "css", "scss", "html", "vue", "svelte",
}
_DATA_EXTENSIONS = {"csv", "tsv", "xls", "xlsx", "json", "xml", "parquet"}


def normalize_classification(value: str | None, *, fallback: str = "document") -> str:
    raw = str(value or "").strip().lower()
    normalized = _CLASSIFICATION_ALIASES.get(raw, raw)
    return normalized if normalized in CLASSIFICATIONS else fallback


def classification_from_kind(kind: str | None) -> str:
    value = str(kind or "").strip().lower()
    if value in {"analysis", "analise", "análise", "research", "pesquisa", "diagnostic", "diagnóstico"}:
        return "analysis"
    if value in {"evidence", "evidencia", "evidência"}:
        return "evidence"
    if value in {"data", "dataset", "data_model"}:
        return "data"
    if value in {"code", "codigo", "código"}:
        return "code"
    if value in {"diagram", "diagrama"}:
        return "diagram"
    if value in {"draft", "rascunho", "notebook"}:
        return "draft"
    return "document"


def classification_for_artifact(
    *,
    filename: str = "",
    content_type: str = "",
    tool_name: str = "",
) -> str:
    tool = str(tool_name or "").strip().lower()
    if tool in {"create_diagram"}:
        return "diagram"
    if tool in {"create_spreadsheet"}:
        return "data"

    suffix = str(filename or "").rsplit(".", 1)[-1].lower() if "." in str(filename or "") else ""
    if suffix in _CODE_EXTENSIONS:
        return "code"
    if suffix in _DATA_EXTENSIONS:
        return "data"
    if str(content_type or "").startswith("image/"):
        return "evidence"
    return "document"


def classification_from_legacy_tags(tags: Iterable[str] | None, *, kind: str | None = None) -> str:
    """Compatibilidade de leitura. Tags antigas nunca voltam a ser gravadas.

    Só migra quando uma tag antiga já nomeia inequivocamente uma das sete
    classificações. Caso contrário, o subtipo documental (kind) fornece
    um fallback determinístico.
    """
    for tag in tags or ():
        raw = str(tag or "").strip().lower()
        if raw in _CLASSIFICATION_ALIASES:
            return normalize_classification(raw)
    return classification_from_kind(kind)

