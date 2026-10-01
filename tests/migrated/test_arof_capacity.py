import asyncio
import json

import pytest

from norvald_lab.application.arof.capacity import CapacityMonitor
from norvald_lab.application.arof.dataset import ExperimentManifest
from norvald_lab.infrastructure.arof.dataset_store import (
    write_capacity_report,
    write_manifest,
)


@pytest.mark.asyncio
async def test_capacity_monitor_mede_sem_definir_threshold(tmp_path):
    dataset = tmp_path / "dataset"
    dataset.mkdir()

    monitor = CapacityMonitor(
        disk_path=tmp_path,
        dataset_path=dataset,
        sample_interval_seconds=0.01,
    )
    await monitor.start()
    (dataset / "raw.bin").write_bytes(b"x" * 128)
    await asyncio.sleep(0.03)
    report = await monitor.stop(
        logical_executions=3,
        attempts=4,
        failures=1,
    )

    assert report.sample_count >= 2
    assert report.elapsed_seconds >= 0
    assert report.process_rss_peak_bytes > 0
    assert report.disk_free_min_bytes > 0
    assert report.dataset_growth_bytes >= 128
    assert report.logical_executions == 3
    assert report.attempts == 4
    assert report.failures == 1


@pytest.mark.asyncio
async def test_capacity_report_e_write_once_e_exige_manifesto(tmp_path):
    dataset = tmp_path / "dataset"
    dataset.mkdir()
    monitor = CapacityMonitor(disk_path=tmp_path, dataset_path=dataset)
    await monitor.start()
    report = await monitor.stop()

    with pytest.raises(FileNotFoundError):
        write_capacity_report("exp-001", report, root=tmp_path)

    manifest = ExperimentManifest(
        experiment_id="exp-001",
        framework_version="test",
        task={"label": "t"},
        conditions=({"condition_id": "blind"},),
        models=({"provider": "stub", "model": "m"},),
        budget={
            "max_logical_executions": 3,
            "max_attempts": 6,
            "max_concurrency": 3,
        },
    )
    write_manifest(manifest, root=tmp_path)
    path = write_capacity_report("exp-001", report, root=tmp_path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["sample_count"] >= 2

    with pytest.raises(FileExistsError):
        write_capacity_report("exp-001", report, root=tmp_path)

