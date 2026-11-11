from __future__ import annotations

import argparse
import asyncio
import copy
import json
import sys
from pathlib import Path

from norvald_lab.config import identifier
from norvald_lab.infrastructure.arof.dataset_store import arof_data_root
from norvald_lab.runner import ExperimentRunner
from norvald_lab.storage import read_verified_records, verify_experiment, write_once


def _read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def demo_spec(experiment_id):
    return {"schema_version": "norvald.lab.spec.v1", "experiment_id": experiment_id, "mode": "demo", "task": {"id": "pergunta-demo", "objective": "Compare as opções A e B e declare sua posição. Demonstração sintética, sem valor empírico.", "instructions": "Declare uma decision e selects para option-a ou option-b."}, "participants": [{"id": f"analista-{i}", "name": f"Analista {i}", "role": "Analista", "provider": "simulador", "model": "demo-v1"} for i in range(1, 4)], "providers": {"simulador": {"kind": "demo"}}, "documents": [{"id": "texto-demo", "title": "Material fictício", "text": "A prioriza prazo. B prioriza flexibilidade.", "source": "Demonstração sintética"}], "working_context": {"items": [{"id": "option-a", "type": "option", "content": "Opção A: prazo"}, {"id": "option-b", "type": "option", "content": "Opção B: flexibilidade"}], "relations": []}, "repetitions": 1, "condition": {"id": "B1", "exposure": "blind", "tools": "off"}}


def derive_spec(root, source_id, new_id, exposure, condition_id=None):
    identifier(source_id)
    identifier(new_id)
    read_verified_records(root, source_id)
    spec = _read(root / "experiments" / source_id / "spec.json")
    spec["experiment_id"] = new_id
    spec["condition"].update(id=condition_id or ("B3" if exposure == "self" else "E"), exposure=exposure, prior_experiment=source_id)
    return spec


def _progress(event, data):
    if event == "experiment.started":
        print(f"Iniciando {data['experiment_id']}: {data['planned']} execuções.", flush=True)
    elif event in {"execution.completed", "execution.failed"}:
        print(f"  {data['participant_id']} / {data['run_id']}: {'registrado' if data['ok'] else 'falhou (falha registrada)' }", flush=True)


async def _run(runner, spec, live=False):
    result = await runner.run(runner.prepare(spec), allow_live=live, on_event=_progress)
    print(f"Estado: {result['status']}. Pasta: {runner.root / 'experiments' / result['experiment_id']}")
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(prog="norvald-lab", description="Laboratório independente Norvald — execute, observe e confira os registros.")
    parser.add_argument("--data-dir", type=Path, default=None, help="Pasta própria de dados do laboratório")
    commands = parser.add_subparsers(dest="command", required=True)
    run = commands.add_parser("run", help="Executa uma configuração JSON")
    run.add_argument("spec", type=Path)
    run.add_argument("--live", action="store_true", help="Habilita chamadas reais aos providers configurados")
    prepare = commands.add_parser("prepare", help="Confere a configuração sem chamar modelos nem gravar experimento")
    prepare.add_argument("spec", type=Path)
    for name in ("inspect", "verify"):
        sub = commands.add_parser(name, help="Lê o resultado" if name == "inspect" else "Verifica a integridade")
        sub.add_argument("experiment_id")
    commands.add_parser("list", help="Lista os experimentos salvos")
    derive = commands.add_parser("derive", help="Prepara uma condição a partir de uma rodada cega")
    derive.add_argument("source_id")
    derive.add_argument("experiment_id")
    derive.add_argument("--exposure", choices=["self", "exposed"], required=True)
    derive.add_argument("--output", type=Path, required=True)
    herd = commands.add_parser("herd", help="Coleta do Δ_herd em lote: B1/B2 e depois B3/E, na ordem do protocolo")
    herd.add_argument("--bank", type=Path, required=True)
    herd.add_argument("--panel", type=Path, required=True)
    herd.add_argument("--run-id", required=True)
    herd.add_argument("--questions", default="", help="Ids separados por vírgula; vazio = todas as contestáveis e as com gabarito")
    herd.add_argument("--live", action="store_true")
    herd.add_argument("--pilot", action="store_true", help="Só B1 (pilotos do TESE-002 §5.3 e §5.4)")
    serve = commands.add_parser("serve", help="Inicia a bancada e o backend local")
    serve.add_argument("--port", type=int, default=8766)
    serve.add_argument("--live", action="store_true")
    serve.add_argument("--open", action="store_true", help="Abre a bancada no navegador")
    args = parser.parse_args(argv)
    root = args.data_dir.expanduser() if args.data_dir else arof_data_root()
    runner = ExperimentRunner(root)
    try:
        if args.command == "run":
            spec = _read(args.spec)
            if spec.get("mode") != "live":
                raise ValueError("O laboratório aceita somente modelos reais.")
            result = asyncio.run(_run(runner, spec, args.live))
            return 0 if result["status"] == "complete" else 1
        elif args.command == "prepare":
            prepared = runner.prepare(_read(args.spec))
            print(json.dumps({"experiment_id": prepared.spec["experiment_id"], "executions": len(prepared.requests_json), "fingerprint": prepared.condition_fingerprint}, ensure_ascii=False, indent=2))
        elif args.command in {"inspect", "verify"}:
            identifier(args.experiment_id)
            check = verify_experiment(root, args.experiment_id)
            if args.command == "verify":
                print(json.dumps(check, ensure_ascii=False, indent=2))
            else:
                result = _read(root / "experiments" / args.experiment_id / "result.json")
                print(json.dumps({"integrity": check, "result": result}, ensure_ascii=False, indent=2))
            return 0 if check["valid"] else 1
        elif args.command == "derive":
            spec = derive_spec(root, args.source_id, args.experiment_id, args.exposure)
            runner.prepare(spec)
            write_once(args.output, spec)
            print(f"Configuração pronta: {args.output}")
        elif args.command == "list":
            for path in sorted((root / "experiments").glob("*/manifest.json")):
                result = path.parent / "result.json"
                status = _read(result)["status"] if result.exists() else "não fechado"
                print(f"{path.parent.name}: {status}")
        elif args.command == "herd":
            from norvald_lab.herd.run_command import run_herd
            return run_herd(runner, bank_path=args.bank, panel_path=args.panel, run_id=args.run_id, questions=args.questions, live=args.live, progress=_progress, pilot=args.pilot)
        elif args.command == "serve":
            import uvicorn
            from norvald_lab.api import create_app
            if args.open:
                import threading
                import webbrowser
                threading.Timer(1, lambda: webbrowser.open(f"http://127.0.0.1:{args.port}")).start()
            uvicorn.run(create_app(root, allow_live=args.live, oauth_port=args.port), host="127.0.0.1", port=args.port)
        return 0
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print(f"Não foi possível concluir: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("Interrompido. Consulte os registros; uma execução não fechada não é um experimento completo.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
