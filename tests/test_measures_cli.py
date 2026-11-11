"""Ponta a ponta: rodada herd no simulador → `norvald-lab measures` → JSON e resumo .md."""

import json
from pathlib import Path

import pytest

from norvald_lab.cli import main
from norvald_lab.herd.batch import HerdBatch
from norvald_lab.herd.run_command import freeze_plan
from norvald_lab.runner import ExperimentRunner

STUDY = Path(__file__).resolve().parents[1] / "studies" / "herd"
BANK_EN = json.loads((STUDY / "bank.en.json").read_text(encoding="utf-8"))
PANEL = {
    "mode": "demo", "language": "en",
    "providers": {"simulador": {"kind": "demo"}},
    "participants": [{"provider": "simulador", "model": "demo-v1"} for _ in range(3)],
    "reasoning_effort": "default",
    "sampling": {"temperature": 0.7, "top_p": 1.0, "max_tokens": 800},
    "instructions": "Choose exactly one option.",
}
QUESTIONS = ["q01", "q02", "g01", "h01"]


def _without_timestamp(report):
    return {k: v for k, v in report.items() if k != "gerado_em"}


@pytest.mark.asyncio
async def test_demo_herd_run_to_measures_report(tmp_path):
    bank = {"questions": [q for q in BANK_EN["questions"] if q["id"] in QUESTIONS]}
    freeze_plan(tmp_path, "demo", bank, PANEL)
    report = await HerdBatch(ExperimentRunner(tmp_path), bank, PANEL, run_id="demo").run(QUESTIONS, allow_live=False)
    assert len(report.ran) == 20 and not report.blocked
    before = sorted(p.relative_to(tmp_path) for p in tmp_path.rglob("*"))

    out = tmp_path / "saida" / "medidas.json"
    assert main(["--data-dir", str(tmp_path), "measures", "--run", "demo", "--out", str(out), "--reps", "200", "--seed", "42"]) == 0
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["bootstrap"]["seed"] == 42 and data["bootstrap"]["reps"] == 200
    assert data["tabela"]["linhas"] == 4 * 5 * 3
    assert data["tabela"]["perguntas_por_tipo"] == {"contestavel": 2, "gabarito": 2}
    assert data["tabela"]["perguntas_com_gabarito"] == 2
    assert set(data["criterios"]) == set("ABCDEFGHIJ")
    assert set(data["hao"]["com_indiretas"]["particao"]) == {"todas", "discordancia"}
    assert data["conferencia_algebrica"]["com_indiretas"]["todas"]["iguais"]
    assert set(data["tentativas_e_custo"]["por_modelo"]) == {"demo-v1"}
    # O simulador escolhe sempre a mesma opção por participante: ninguém muda de posição.
    assert data["hao"]["com_indiretas"]["particao"]["todas"]["contagens"]["estaveis"] == data["hao"]["com_indiretas"]["n_pares_agente_pergunta"]["todas"]
    summary = out.with_suffix(".md").read_text(encoding="utf-8")
    assert summary.startswith("# Medidas do Δ_herd — demo") and "Hao et al." in summary
    # Registro aw9vf: primeira chave do JSON e primeira seção do resumo.
    assert next(iter(data)) == "registro_aw9vf"
    assert summary.index("## Registro aw9vf (confirmatório)") < summary.index("## Tentativas e custo")
    registro = data["registro_aw9vf"]["com_indiretas"]
    assert set(registro) >= {"descarte_de_unanimes_em_b1", "principal_sem_unanimes", "alternativa_com_unanimes"}
    assert registro["alternativa_com_unanimes"]["painel_homogeneo_de_contraste"] is None

    # Só lê: a pasta de dados do Lab não ganhou nem perdeu arquivo (a saída foi em saida/).
    after = sorted(p.relative_to(tmp_path) for p in tmp_path.rglob("*") if "saida" not in p.parts)
    assert after == before

    # --contrast-run: painel homogêneo de contraste (aqui a mesma rodada, só para exercitar o caminho).
    contrasted = tmp_path / "saida" / "contraste.json"
    assert main(["--data-dir", str(tmp_path), "measures", "--run", "demo", "--contrast-run", "demo", "--out", str(contrasted), "--reps", "50", "--seed", "42"]) == 0
    block = json.loads(contrasted.read_text(encoding="utf-8"))["registro_aw9vf"]["com_indiretas"]["alternativa_com_unanimes"]["painel_homogeneo_de_contraste"]
    assert block["n_painel"] == 3 and set(block) >= {"rho_erro_B1", "n_eff_B1"}

    # Determinístico: mesma tabela, mesma seed, mesmo relatório.
    again = tmp_path / "saida" / "de-novo.json"
    assert main(["--data-dir", str(tmp_path), "measures", "--run", "demo", "--out", str(again), "--reps", "200", "--seed", "42"]) == 0
    assert _without_timestamp(json.loads(again.read_text(encoding="utf-8"))) == _without_timestamp(data)


def test_measures_without_observations_fails_cleanly(tmp_path, capsys):
    assert main(["--data-dir", str(tmp_path), "measures", "--run", "nada", "--out", str(tmp_path / "x.json")]) == 1
    assert "Nenhuma observação" in capsys.readouterr().err
