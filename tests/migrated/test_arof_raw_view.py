import json

from norvald_lab.infrastructure.arof.dataset_store import (
    experiment_dir,
    load_experiment_raw_view,
)


def test_raw_view_preserva_tentativas_separadas(tmp_path):
    directory = experiment_dir("exp-raw", root=tmp_path)
    raw_path = directory / "raw" / "r001" / "observations.jsonl"
    raw_path.parent.mkdir(parents=True, exist_ok=True)

    base = {
        "schema_version": "arof.raw.v4",
        "experiment_id": "exp-raw",
        "logical_execution_id": "logical-1",
        "participant_id": "p1",
        "participant_name": "Modelo A",
        "requested_model": "model-a",
        "result": {
            "content": "resposta",
            "reasoning": "reasoning bruto",
            "metadata": {},
        },
    }
    first = {
        **base,
        "observation_id": "obs-1",
        "attempt_index": 1,
    }
    second = {
        **base,
        "observation_id": "obs-2",
        "attempt_index": 2,
    }
    raw_path.write_text(
        json.dumps(first) + "\n" + json.dumps(second) + "\n",
        encoding="utf-8",
    )

    view = load_experiment_raw_view("exp-raw", root=tmp_path)

    assert [item["payload"]["attempt_index"] for item in view["records"]] == [1, 2]
    assert view["records"][0]["payload"]["result"]["reasoning"] == "reasoning bruto"
    assert view["issues"] == []



def test_raw_view_uses_completion_file_as_authority(tmp_path):
    directory = experiment_dir("exp-certified", root=tmp_path)
    actual_raw = directory / "certified" / "capture.jsonl"
    actual_raw.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "schema_version": "arof.raw.v4",
        "experiment_id": "exp-certified",
        "observation_id": "obs-certified",
        "logical_execution_id": "logical-certified",
        "attempt_index": 1,
        "result": {
            "content": "ok",
            "reasoning": "raw reasoning",
            "metadata": {},
        },
    }
    actual_raw.write_text(json.dumps(payload) + "\n", encoding="utf-8")
    (directory / "completion.json").write_text(
        json.dumps(
            {
                "experiment_id": "exp-certified",
                "status": "complete",
                "files": [
                    {
                        "path": str(
                            actual_raw.resolve().relative_to(
                                tmp_path.resolve()
                            )
                        )
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    view = load_experiment_raw_view(
        "exp-certified",
        root=tmp_path,
    )

    assert len(view["records"]) == 1
    assert (
        view["records"][0]["payload"]["observation_id"]
        == "obs-certified"
    )

