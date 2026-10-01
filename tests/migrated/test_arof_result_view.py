import json

from norvald_lab.application.arof.dataset import ExperimentResultView
from norvald_lab.infrastructure.arof.dataset_store import (
    experiment_dir,
    latest_experiment_result_for_source,
    write_experiment_result,
)


def test_latest_result_retorna_view_mais_recente(tmp_path):
    for exp, completed in [
        ("exp-old", "2026-09-21T10:00:00+00:00"),
        ("exp-new", "2026-09-21T11:00:00+00:00"),
    ]:
        directory = experiment_dir(exp, root=tmp_path)
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "completion.json").write_text(
            json.dumps({"experiment_id": exp}),
            encoding="utf-8",
        )
        write_experiment_result(
            ExperimentResultView(
                experiment_id=exp,
                condition_id="n0-native",
                source_session_id="source-x",
                status="complete",
                failures=0,
                executions=(),
                condition_fingerprint="c",
                library_corpus_fingerprint="l",
                completed_at=completed,
            ),
            root=tmp_path,
        )

    latest = latest_experiment_result_for_source(
        "source-x", root=tmp_path
    )

    assert latest is not None
    assert latest["experiment_id"] == "exp-new"

