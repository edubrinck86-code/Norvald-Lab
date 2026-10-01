import json
from concurrent.futures import ThreadPoolExecutor

from norvald_lab.application.arof.raw_observation import (
    AROF_RAW_SCHEMA_VERSION,
    build_raw_observation,
)
from norvald_lab.infrastructure.arof.raw_observation_store import (
    JsonlRawObservationStore,
    arof_capture_enabled,
)
from norvald_lab.vendor.norvald_execution.contracts.execution_context import ExecutionContext
from norvald_lab.vendor.norvald_execution.contracts.execution_contracts import ExecutionRequest, ExecutionResult
from norvald_lab.vendor.norvald_execution.contracts.sampling import ResolvedSampling


def _request() -> ExecutionRequest:
    return ExecutionRequest(
        agent_id="agent-1",
        instructions="cauda específica",
        shared_instructions="instrução compartilhada",
        wave_instructions="working context da leva",
        context=ExecutionContext(
            objective="testar captura",
            working_context="WC exato",
            working_context_id="session-1",
            metadata={
                "session_id": "session-1",
                "round": 2,
                "participant_id": "participant-1",
                "participant_name": "Especialista A",
                "participant_role": "analista",
                "task_id": "task-1",
                "peer_exposure_mode": "blind",
                "reasoning_exposure_mode": "summarized",
                "research_anchor_ids": ["evidence-a"],
                "attached_evidence_mode": "inline_selected",
                "tool_phase": "n_plus_0",
                "library_corpus_fingerprint": "abc123",
                "library_corpus_item_count": 7,
                "library_corpus_algorithm": "sha256-canonical-json-v1",
                "tool_limits_explicit": False,
                # Deve ser excluído do metadata selecionado: já existe em
                # shared_instructions e duplicaria volume no RAW.
                "repository_material": "x" * 1000,
            },
        ),
        user_message="mensagem do usuário",
        reasoning_effort="high",
        sampling=ResolvedSampling(max_tokens=500),
        allow_tools=False,
    )


def _result() -> ExecutionResult:
    return ExecutionResult(
        content="resposta final",
        reasoning="raciocínio exposto",
        tokens=12,
        input_tokens=7,
        output_tokens=5,
        duration_seconds=1.25,
        provider="stub-provider",
        model="stub-model",
        metadata={
            "raw_usage": {"input_tokens": 7, "output_tokens": 5},
            "tool_loop_reason": "natural_completion",
            "tool_loop_truncated": False,
            "advertised_tool_names": ["search_library", "web_search"],
        },
    )


def test_raw_observation_preserva_request_resultado_e_granularidade():
    record = build_raw_observation(
        request=_request(),
        attempt_index=2,
        requested_provider_kind="openai",
        requested_model="requested-model",
        result=_result(),
    )

    payload = record.to_dict()
    assert payload["schema_version"] == AROF_RAW_SCHEMA_VERSION
    assert payload["logical_execution_id"] == "session-1:2:participant-1"
    assert payload["attempt_index"] == 2
    assert payload["attempt_outcome"] == "returned"
    assert payload["started_at"]
    assert payload["captured_at"]
    assert payload["peer_exposure_mode"] == "blind"
    assert payload["reasoning_exposure_mode"] == "summarized"
    assert payload["research_anchor_ids"] == ["evidence-a"]
    assert payload["attached_evidence_mode"] == "inline_selected"
    assert payload["tool_phase"] == "n_plus_0"
    assert payload["library_corpus_fingerprint"] == "abc123"
    assert payload["library_corpus_item_count"] == 7
    assert payload["library_corpus_algorithm"] == "sha256-canonical-json-v1"
    assert payload["termination_reason"] == "natural_completion"
    assert payload["tool_loop_truncated"] is False
    assert payload["provider_advertised_tool_names"] == [
        "search_library",
        "web_search",
    ]
    assert payload["tool_limits_explicit"] is False
    assert payload["request"]["context"]["working_context"] == "WC exato"
    assert payload["request"]["sampling"]["max_tokens"] == 500
    assert payload["result"]["reasoning"] == "raciocínio exposto"
    assert payload["result"]["input_tokens"] == 7
    assert "repository_material" not in payload["request"]["studio_metadata"]


def test_raw_separa_reasoning_de_metadata_de_apresentacao():
    # A propriedade de UI do Studio não pertence ao pacote Execution.
    result = _result()
    result.reasoning = "trace completo"
    result.metadata["display_reasoning"] = "summary"
    raw = build_raw_observation(request=_request(), attempt_index=1,
        requested_provider_kind="openrouter", requested_model="m", result=result)
    assert raw.result["reasoning"] == "trace completo"
    assert raw.result["metadata"]["display_reasoning"] == "summary"


def test_raw_observation_preserva_reasoning_details_do_openrouter():
    result = _result()
    details = [{
        "type": "reasoning.summary",
        "summary": "Resumo nativo.",
        "id": "sum-1",
        "format": "openai-responses-v1",
        "index": 0,
    }]
    result.reasoning = "trace completo"
    result.metadata.update({
        "display_reasoning": "Resumo nativo.",
        "reasoning_exposure_mode": "mixed",
        "provider_state": {
            "openrouter_reasoning_details": details,
            "openrouter_legacy_reasoning": "trace completo",
        },
    })

    record = build_raw_observation(
        request=_request(),
        attempt_index=1,
        requested_provider_kind="openrouter",
        requested_model="openai/gpt-6-astra",
        result=result,
    )
    payload = record.to_dict()

    assert payload["result"]["reasoning"] == "trace completo"
    assert payload["result"]["metadata"]["display_reasoning"] == "Resumo nativo."
    assert payload["result"]["metadata"]["provider_state"]["openrouter_reasoning_details"] == details
    assert payload["result"]["metadata"]["provider_state"]["openrouter_legacy_reasoning"] == "trace completo"


def test_raw_observation_prefere_modo_de_exposicao_declarado_pelo_provider():
    request = _request()
    request.context.metadata["reasoning_exposure_mode"] = "unknown"
    result = _result()
    result.metadata["reasoning_exposure_mode"] = "summarized"

    record = build_raw_observation(
        request=request,
        attempt_index=1,
        requested_provider_kind="anthropic",
        requested_model="claude-test",
        result=result,
    )

    payload = record.to_dict()
    assert payload["reasoning_exposure_mode"] == "summarized"
    # A proveniência muda; o texto observado na fronteira não.
    assert payload["result"]["reasoning"] == "raciocínio exposto"


def test_raw_observation_registra_falha_sem_inventar_resultado():
    error = RuntimeError("provider indisponível")
    record = build_raw_observation(
        request=_request(),
        attempt_index=1,
        requested_provider_kind="anthropic",
        requested_model="requested-model",
        error=error,
    )

    payload = record.to_dict()
    assert payload["attempt_outcome"] == "raised"
    assert payload["result"] is None
    assert payload["error"]["type"] == "RuntimeError"
    assert payload["error"]["message"] == "provider indisponível"


def test_jsonl_store_suporta_escritas_concorrentes(tmp_path):
    store = JsonlRawObservationStore(tmp_path)
    records = [
        build_raw_observation(
            request=_request(),
            attempt_index=index + 1,
            requested_provider_kind="test",
            requested_model="test-model",
            result=_result(),
        )
        for index in range(12)
    ]

    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(store.record, records))

    path = tmp_path / "sessions" / "session-1" / "raw" / "observations.jsonl"
    lines = path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 12
    decoded = [json.loads(line) for line in lines]
    assert {item["observation_id"] for item in decoded} == {
        item.observation_id for item in records
    }


def test_capture_raw_e_opt_in(monkeypatch):
    monkeypatch.delenv("NORVALD_LAB_CAPTURE", raising=False)
    assert arof_capture_enabled() is False
    monkeypatch.setenv("NORVALD_LAB_CAPTURE", "1")
    assert arof_capture_enabled() is True

