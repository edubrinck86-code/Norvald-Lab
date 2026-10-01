import json

import pytest

from norvald_lab.application.arof.dataset import (
    ExperimentManifest,
    ReplayFilter,
)
from norvald_lab.application.arof.raw_observation import build_raw_observation
from norvald_lab.vendor.norvald_execution.contracts.sampling import ResolvedSampling
from norvald_lab.infrastructure.arof.dataset_store import (
    close_experiment,
    file_integrity,
    load_manifest,
    replay_jsonl,
    write_manifest,
)
from norvald_lab.infrastructure.arof.raw_observation_store import JsonlRawObservationStore
from norvald_lab.vendor.norvald_execution.contracts.execution_context import ExecutionContext
from norvald_lab.vendor.norvald_execution.contracts.execution_contracts import ExecutionRequest, ExecutionResult


def _manifest(experiment_id="exp-001"):
    return ExperimentManifest(
        experiment_id=experiment_id,
        framework_version="test-framework",
        task={"label": "task-a", "prompt": "Avalie A"},
        conditions=(
            {"condition_id": "blind", "peer_exposure_mode": "blind"},
        ),
        models=(
            {"provider": "stub", "model": "model-a"},
        ),
        budget={
            "max_logical_executions": 3,
            "max_attempts": 6,
            "max_concurrency": 3,
            "planned_logical_executions": 1,
        },
        corpus={
            "library": {
                "algorithm": "sha256-canonical-json-v1",
                "fingerprint": "abc",
                "item_count": 1,
            }
        },
    )


def _record(*, experiment_id="exp-001", run_id="run-1", task_label="task-a", model="model-a"):
    request = ExecutionRequest(
        agent_id="agent-1",
        instructions="instrução",
        context=ExecutionContext(
            objective="avaliar",
            working_context="snapshot",
            working_context_id="wc-1",
            metadata={
                "session_id": "session-1",
                "round": 1,
                "participant_id": "p1",
                "task_id": "task-1",
                "experiment_id": experiment_id,
                "condition_id": "blind",
                "run_id": run_id,
                "task_label": task_label,
                "peer_exposure_mode": "blind",
                "reasoning_exposure_mode": "unknown",
            },
        ),
        sampling=ResolvedSampling(),
        allow_tools=False,
    )
    result = ExecutionResult(
        content="resposta",
        tokens=2,
        duration_seconds=0.1,
        provider="stub",
        model=model,
        input_tokens=1,
        output_tokens=1,
        metadata={},
    )
    return build_raw_observation(
        request=request,
        attempt_index=1,
        requested_provider_kind="stub",
        requested_model=model,
        result=result,
    )


def test_manifesto_e_write_once(tmp_path):
    manifest = _manifest()
    path = write_manifest(manifest, root=tmp_path)

    loaded = load_manifest("exp-001", root=tmp_path)
    assert loaded["experiment_id"] == "exp-001"
    assert loaded["raw_schema_version"] == "arof.raw.v4"
    assert path.name == "manifest.json"

    with pytest.raises(FileExistsError):
        write_manifest(manifest, root=tmp_path)


def test_raw_de_experimento_fica_ao_lado_logico_do_manifesto(tmp_path):
    write_manifest(_manifest(), root=tmp_path)
    store = JsonlRawObservationStore(tmp_path)
    record = _record()

    store.record(record)
    path = (
        tmp_path
        / "experiments"
        / "exp-001"
        / "raw"
        / "run-1"
        / "observations.jsonl"
    )
    assert path.exists()


def test_replay_preserva_ordem_e_filtra_sem_chamar_provider(tmp_path):
    store = JsonlRawObservationStore(tmp_path)
    first = _record(run_id="run-1", model="model-a")
    second = _record(run_id="run-2", model="model-b")
    store.record(first)
    store.record(second)

    paths = [
        tmp_path / "experiments" / "exp-001" / "raw" / "run-1" / "observations.jsonl",
        tmp_path / "experiments" / "exp-001" / "raw" / "run-2" / "observations.jsonl",
    ]
    replay = replay_jsonl(paths, filters=ReplayFilter(model="model-b"))

    assert replay.valid
    assert len(replay.records) == 1
    assert replay.records[0].payload["run_id"] == "run-2"


def test_replay_reporta_linha_invalida_sem_perder_as_validas(tmp_path):
    path = tmp_path / "observations.jsonl"
    valid = _record().to_dict()
    path.write_text(
        json.dumps(valid, ensure_ascii=False) + "\n" + "{quebrado}\n",
        encoding="utf-8",
    )

    replay = replay_jsonl([path])

    assert len(replay.records) == 1
    assert len(replay.issues) == 1
    assert replay.issues[0].line_number == 2
    assert replay.issues[0].code == "invalid_json"


def test_integridade_hash_e_fechamento_sao_imutaveis(tmp_path):
    write_manifest(_manifest(), root=tmp_path)
    store = JsonlRawObservationStore(tmp_path)
    store.record(_record())
    raw_path = (
        tmp_path
        / "experiments"
        / "exp-001"
        / "raw"
        / "run-1"
        / "observations.jsonl"
    )

    integrity = file_integrity(raw_path)
    assert len(integrity.sha256) == 64
    assert integrity.valid_records == 1
    assert integrity.invalid_records == 0

    completion_path = close_experiment(
        "exp-001",
        [raw_path],
        status="complete",
        root=tmp_path,
    )
    completion = json.loads(completion_path.read_text(encoding="utf-8"))
    assert completion["logical_executions"] == 1
    assert completion["attempts"] == 1
    assert completion["files"][0]["sha256"] == integrity.sha256

    with pytest.raises(FileExistsError):
        close_experiment(
            "exp-001",
            [raw_path],
            status="complete",
            root=tmp_path,
        )


def test_fechamento_exige_manifesto(tmp_path):
    with pytest.raises(FileNotFoundError):
        close_experiment(
            "exp-ausente",
            [],
            status="aborted",
            root=tmp_path,
        )


def test_complete_recusa_raw_invalido(tmp_path):
    write_manifest(_manifest(), root=tmp_path)
    raw_path = (
        tmp_path
        / "experiments"
        / "exp-001"
        / "raw"
        / "run-1"
        / "observations.jsonl"
    )
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    raw_path.write_text("{quebrado}\n", encoding="utf-8")

    with pytest.raises(ValueError, match="não pode ser fechado como complete"):
        close_experiment(
            "exp-001",
            [raw_path],
            status="complete",
            root=tmp_path,
        )


def test_complete_recusa_raw_de_outro_experimento(tmp_path):
    write_manifest(_manifest("exp-001"), root=tmp_path)
    store = JsonlRawObservationStore(tmp_path)
    foreign = _record(experiment_id="exp-002")
    store.record(foreign)
    raw_path = (
        tmp_path
        / "experiments"
        / "exp-002"
        / "raw"
        / "run-1"
        / "observations.jsonl"
    )

    with pytest.raises(ValueError, match="outro experiment_id"):
        close_experiment(
            "exp-001",
            [raw_path],
            status="complete",
            root=tmp_path,
        )


def test_completion_guarda_caminho_portavel_relativo_ao_arof_root(tmp_path):
    write_manifest(_manifest(), root=tmp_path)
    store = JsonlRawObservationStore(tmp_path)
    store.record(_record())
    raw_path = (
        tmp_path
        / "experiments"
        / "exp-001"
        / "raw"
        / "run-1"
        / "observations.jsonl"
    )

    completion_path = close_experiment(
        "exp-001",
        [raw_path],
        status="complete",
        root=tmp_path,
    )
    completion = json.loads(completion_path.read_text(encoding="utf-8"))
    assert completion["files"][0]["path"] == (
        "experiments/exp-001/raw/run-1/observations.jsonl"
    )

