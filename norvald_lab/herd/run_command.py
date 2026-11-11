"""Comando `norvald-lab herd`: congela o plano da rodada e executa o lote.

O plano (banco + painel) é gravado uma vez por rodada, com impressão digital.
Uma segunda chamada com outro painel ou outro banco para o mesmo run_id é
recusada: a configuração congelada do TESE-002 §3 não muda no meio da coleta.
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path

from norvald_lab.application.arof.corpus import fingerprint_payload
from norvald_lab.config import identifier
from norvald_lab.herd.batch import HerdBatch


def _read(path: Path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def default_questions(bank) -> list[str]:
    return [q["id"] for q in bank["questions"] if q["kind"] in {"contestavel", "gabarito"}]


def freeze_plan(root: Path, run_id: str, bank, panel) -> Path:
    identifier(run_id)
    directory = root / "studies" / run_id
    directory.mkdir(parents=True, exist_ok=True)
    plan = {"run_id": run_id, "bank_fingerprint": fingerprint_payload(bank), "panel_fingerprint": fingerprint_payload(panel), "bank": bank, "panel": panel}
    path = directory / "plan.json"
    if path.exists():
        frozen = _read(path)
        if (frozen["bank_fingerprint"], frozen["panel_fingerprint"]) != (plan["bank_fingerprint"], plan["panel_fingerprint"]):
            raise ValueError(f"A rodada {run_id} já foi congelada com outro banco ou painel. Use outro run_id.")
        return path
    path.write_text(json.dumps(plan, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return path


def run_herd(runner, *, bank_path: Path, panel_path: Path, run_id: str, questions: str, live: bool, progress=None) -> int:
    bank, panel = _read(bank_path), _read(panel_path)
    plan_path = freeze_plan(runner.root, run_id, bank, panel)
    ids = [q.strip() for q in questions.split(",") if q.strip()] or default_questions(bank)
    batch = HerdBatch(runner, bank, panel, run_id=run_id)
    report = asyncio.run(batch.run(ids, allow_live=live, on_event=progress, on_step=lambda step, expid: print(f"== {expid}", flush=True)))
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = plan_path.parent / f"report-{stamp}.json"
    out.write_text(json.dumps(report.to_dict(), ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"Rodou {len(report.ran)}, já existiam {len(report.existing)}, bloqueados {len(report.blocked)}. Relatório: {out}")
    return 0 if not report.blocked and all(status == "complete" for _, status in report.ran) else 1
