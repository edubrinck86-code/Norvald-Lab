import json

from norvald_lab.application.arof.reference_normalization import (
    prepare_reference_normalization,
    segment_reasoning_blocks,
    update_reference_event,
)
from norvald_lab.infrastructure.arof.dataset_store import experiment_dir


def _write_raw(tmp_path, experiment_id: str, reasoning: str | None):
    directory = experiment_dir(experiment_id, root=tmp_path)
    raw_path = directory / "raw" / "r001" / "observations.jsonl"
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": "arof.raw.v4",
        "experiment_id": experiment_id,
        "observation_id": "obs-1",
        "logical_execution_id": "logical-1",
        "attempt_index": 1,
        "participant_id": "p1",
        "participant_name": "Modelo A",
        "requested_provider_kind": "provider-a",
        "requested_model": "model-a",
        "reasoning_exposure_mode": "unknown",
        "result": {
            "content": "resposta",
            "reasoning": reasoning,
            "provider": "provider-a",
            "model": "model-a",
            "metadata": {},
        },
    }
    raw_path.write_text(json.dumps(payload) + "\n", encoding="utf-8")


def test_segmentacao_preserva_spans_e_nao_classifica():
    reasoning = "Primeiro bloco.\n\nSegundo bloco com\nduas linhas."
    events = segment_reasoning_blocks(reasoning)

    assert [event["raw_span"] for event in events] == [
        "Primeiro bloco.",
        "Segundo bloco com\nduas linhas.",
    ]
    for event in events:
        assert reasoning[event["start_char"]:event["end_char"]] == event["raw_span"]
        assert event["macro_function"] is None
        assert event["scope"] == "unknown"
        assert event["ambiguous"] is True
        assert event["support_status"] is None


def test_prepare_e_anotar_l1_sem_alterar_raw(tmp_path):
    _write_raw(tmp_path, "exp-l1", "Frame inicial.\n\nReconsiderando.")
    document = prepare_reference_normalization("exp-l1", root=tmp_path)

    assert document["classification_policy"] == "manual_reference"
    trace = document["traces"][0]
    assert trace["reasoning_observation_status"] == "observed"
    assert trace["process_trajectory_status"] == "available_for_annotation"
    assert trace["reasoning_exposure_mode_declared"] == "unknown"
    assert trace["reasoning_exposure_character_observed"] == "unknown"
    assert len(trace["events"]) == 2

    updated = update_reference_event(
        "exp-l1",
        observation_id="obs-1",
        event_id="e0002",
        macro_function="REVISE",
        scope="problem_reasoning",
        ambiguous=False,
        annotation_note="  reconsideração explícita  ",
        root=tmp_path,
    )

    event = updated["traces"][0]["events"][1]
    assert event["macro_function"] == "REVISE"
    assert event["scope"] == "problem_reasoning"
    assert event["ambiguous"] is False
    assert event["annotation_note"] == "reconsideração explícita"
    assert event["annotation_origin"] == "human"
    assert event["reference_tier"] == "human_reviewed"
    assert event["assistant_assignment"] is None

    raw_path = (
        experiment_dir("exp-l1", root=tmp_path)
        / "raw"
        / "r001"
        / "observations.jsonl"
    )
    raw_payload = json.loads(raw_path.read_text(encoding="utf-8"))
    assert raw_payload["result"]["reasoning"] == "Frame inicial.\n\nReconsiderando."


def test_reasoning_nao_exposto_cria_trace_sem_eventos(tmp_path):
    _write_raw(tmp_path, "exp-no-reasoning", None)
    document = prepare_reference_normalization(
        "exp-no-reasoning",
        root=tmp_path,
    )

    trace = document["traces"][0]
    assert trace["reasoning_observed"] is False
    assert trace["reasoning_observation_status"] == "not_exposed"
    assert trace["reasoning_exposure_character_observed"] == "not_observed"
    assert (
        trace["process_trajectory_status"]
        == "unavailable_reasoning_not_exposed"
    )
    assert trace["events"] == []



def test_load_legacy_reference_completa_semantica_sem_perder_anotacao(tmp_path):
    _write_raw(tmp_path, "exp-legacy", "Bloco.")
    document = prepare_reference_normalization("exp-legacy", root=tmp_path)
    path = (
        experiment_dir("exp-legacy", root=tmp_path)
        / "normalized"
        / "reference-v0.json"
    )
    legacy = json.loads(path.read_text(encoding="utf-8"))
    trace = legacy["traces"][0]
    for key in (
        "reasoning_exposure_mode_declared",
        "reasoning_observation_status",
        "reasoning_exposure_character_observed",
        "process_trajectory_status",
    ):
        trace.pop(key, None)
    for key in (
        "support_status",
        "alternative_function",
        "annotation_origin",
        "reference_tier",
        "assistant_assignment",
    ):
        trace["events"][0].pop(key, None)
    trace["events"][0]["macro_function"] = "FRAME"
    path.write_text(json.dumps(legacy), encoding="utf-8")

    loaded = prepare_reference_normalization("exp-legacy", root=tmp_path)
    upgraded = loaded["traces"][0]
    assert upgraded["events"][0]["macro_function"] == "FRAME"
    assert upgraded["events"][0]["support_status"] is None
    assert upgraded["events"][0]["annotation_origin"] == "human"
    assert upgraded["events"][0]["reference_tier"] == "human_reviewed"
    assert upgraded["reasoning_observation_status"] == "observed"
    assert upgraded["process_trajectory_status"] == "available_for_annotation"

