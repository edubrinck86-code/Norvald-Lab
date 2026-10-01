from abc import ABC, abstractmethod
from typing import Callable, List

from norvald_lab.vendor.norvald_execution.contracts.attachment_contracts import AttachmentPayload, AttachmentResult, classify_attachment_kind
from norvald_lab.vendor.norvald_execution.contracts.execution_contracts import ExecutionRequest, ExecutionResult
from norvald_lab.vendor.norvald_execution.contracts.model_contracts import ModelInfo


class LLMProvider(ABC):
    ATTACHMENT_CAPABILITIES: frozenset = frozenset()
    SUPPORTS_REASONING_OUTPUT: bool = False
    SUPPORTS_TOOL_USE: bool = False

    def classify_attachments(self, attachments: List[AttachmentPayload]):
        supported: List[AttachmentPayload] = []
        unsupported: List[AttachmentResult] = []
        for att in attachments:
            kind = classify_attachment_kind(att.mime_type)
            if kind in self.ATTACHMENT_CAPABILITIES:
                supported.append(att)
            else:
                unsupported.append(
                    AttachmentResult(
                        identifier=att.identifier,
                        filename=att.filename,
                        mime_type=att.mime_type,
                        status="unsupported",
                        reason=(
                            f"Provider '{self.__class__.__name__}' não declara suporte a anexos "
                            f"do tipo '{kind}' ({att.mime_type})."
                        ),
                    )
                )
        return supported, unsupported

    @abstractmethod
    async def execute(self, request: ExecutionRequest, model: str) -> ExecutionResult:
        ...

    @abstractmethod
    async def list_models(self) -> List[ModelInfo]:
        ...

    async def test_connection(self) -> bool:
        await self.list_models()
        return True

    async def account_intelligence(self) -> dict:
        """Dados operacionais da conta/chave sem executar inferência.

        Providers que não oferecem endpoint apropriado devolvem vazio.
        """
        return {}

    async def model_intelligence(self, model: str) -> dict:
        """Dados operacionais por modelo/rota sem executar inferência."""
        return {}

    async def generation_intelligence(self, generation_id: str) -> dict:
        """Metadados pós-execução quando o provider oferece consulta própria."""
        return {}

    async def execute_stream(
        self,
        request: ExecutionRequest,
        model: str,
        on_delta: Callable[[str], None],
        on_reasoning_delta: Callable[[str], None] | None = None,
    ) -> ExecutionResult:
        """Fallback de streaming para providers que não implementam stream real."""
        import logging
        import time

        logger = logging.getLogger(__name__)
        started = time.monotonic()
        logger.info("[LLM] provider=%s model=%s path=execute_stream(fallback) request_started", self.__class__.__name__, model)
        result = await self.execute(request, model)
        elapsed = time.monotonic() - started
        logger.info("[LLM] provider=%s model=%s path=execute_stream(fallback) completed duration=%.3fs", self.__class__.__name__, model, elapsed)
        if result.reasoning and on_reasoning_delta:
            on_reasoning_delta(result.reasoning)
        if result.content:
            on_delta(result.content)
        return result

