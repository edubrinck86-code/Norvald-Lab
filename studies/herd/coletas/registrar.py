"""Registro de coleta do Δ_herd: data, hora, duração, chamadas, falhas e custo por rodada.

Pedido do Eduardo (11/11/2026): "não esquece de registrar o tempo de coleta, data e
hora". O OSF pede que se declare quando cada dado nasceu, e o piloto coletado antes
do registro precisa dessa prova de data.

Lê só o que o Lab já grava (manifest.json, completion.json, observations.jsonl);
não chama modelo. Horários em UTC e em Brasília (UTC−3, sem horário de verão).

Uso: python registrar.py <raiz do lab> <run_id> [<run_id> ...]
Grava coletas/<run_id>.json e reescreve a tabela de coletas/README.md.
"""

import json
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
BRT = timezone(timedelta(hours=-3))


def _ts(text):
    return datetime.fromisoformat(text)


def summarize(root, run_id):
    experiments = sorted(p for p in (root / "experiments").glob(f"{run_id}-*") if p.is_dir())
    starts, ends, calls, cost, out_tokens = [], [], 0, 0.0, 0
    by_condition, first_fail, attempts2, incomplete = Counter(), Counter(), 0, []
    for exp in experiments:
        manifest = json.loads((exp / "manifest.json").read_text(encoding="utf-8"))
        starts.append(_ts(manifest["created_at"]))
        completion = exp / "completion.json"
        if completion.exists():
            ends.append(_ts(json.loads(completion.read_text(encoding="utf-8"))["closed_at"]))
            by_condition[exp.name.rsplit("-", 1)[1].upper()] += 1
        else:
            incomplete.append(exp.name)
        for obs_file in exp.glob("raw/*/observations.jsonl"):
            for line in obs_file.read_text(encoding="utf-8").splitlines():
                obs = json.loads(line)
                calls += 1
                result = obs.get("result") or {}
                usage = (result.get("metadata") or {}).get("raw_usage") or {}
                cost += usage.get("cost") or 0
                out_tokens += result.get("output_tokens") or 0
                if obs.get("attempt_index", 1) > 1:
                    attempts2 += 1
                    first_fail[(obs.get("requested_model") or "?").split("/")[-1]] += 1
    start, end = min(starts), max(ends) if ends else None
    return {
        "run_id": run_id,
        "inicio_utc": start.isoformat(), "inicio_brasilia": start.astimezone(BRT).strftime("%d/%m/%Y %H:%M:%S"),
        "fim_utc": end.isoformat() if end else None, "fim_brasilia": end.astimezone(BRT).strftime("%d/%m/%Y %H:%M:%S") if end else None,
        "duracao_min": round((end - start).total_seconds() / 60, 1) if end else None,
        "experimentos_fechados": dict(sorted(by_condition.items())), "experimentos_abertos": incomplete,
        "chamadas": calls, "segundas_tentativas": attempts2, "falhas_da_1a_tentativa_por_modelo": dict(first_fail),
        "tokens_de_saida": out_tokens, "custo_usd": round(cost, 4),
        "registrado_em_utc": datetime.now(timezone.utc).isoformat(),
    }


def main(root, run_ids):
    for run_id in run_ids:
        data = summarize(Path(root).expanduser(), run_id)
        (HERE / f"{run_id}.json").write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    rows = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(HERE.glob("*.json"), key=lambda p: json.loads(p.read_text(encoding="utf-8"))["inicio_utc"])]
    lines = ["# Registro de coletas do Δ_herd", "", "Gerado por `registrar.py` a partir dos arquivos do Lab. Horário de Brasília (UTC−3).", "",
             "| Rodada | Início | Fim | Duração (min) | Experimentos | Chamadas | 2ª tentativa | Custo (US$) |", "|---|---|---|---|---|---|---|---|"]
    for r in rows:
        exps = ", ".join(f"{k} {v}" for k, v in r["experimentos_fechados"].items()) + (f"; abertos {len(r['experimentos_abertos'])}" if r["experimentos_abertos"] else "")
        lines.append(f"| {r['run_id']} | {r['inicio_brasilia']} | {r['fim_brasilia'] or 'em andamento'} | {r['duracao_min'] if r['duracao_min'] is not None else '—'} | {exps} | {r['chamadas']} | {r['segundas_tentativas']} | {r['custo_usd']:.4f} |")
    (HERE / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2:])
