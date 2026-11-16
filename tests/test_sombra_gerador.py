"""Tese 4: o gerador de pares clássico × sorteado (15/11/2026)."""

import json
import os
import re
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
GER = os.path.join(AQUI, "..", "studies", "sombra", "gerador")
sys.path.insert(0, GER)

from moldes import MOLDES  # noqa: E402
import gerador  # noqa: E402

MMLU = os.path.join(AQUI, "..", "studies", "herd", "mmlu-pro")


def _numero(texto):
    t = texto.replace(",", "").replace("$", "")
    # ".306" (sem zero antes do ponto) aparece nas opções do MMLU-Pro
    m = re.search(r"-?\s?(\d+(\.\d+)?|\.\d+)(\s*(×|x)\s*10\^(-?\d+)|e(-?\d+))?", t)
    base = float(re.search(r"-?\s?(\d+(\.\d+)?|\.\d+)", m.group(0)).group(0).replace(" ", ""))
    exp = m.group(5) or m.group(6)
    return base * 10 ** int(exp) if exp else base


def test_moldes_reproduzem_o_gabarito():
    """Com os números publicados, a fórmula cai na opção que o MMLU-Pro dá como certa."""
    banco = {q["id"]: q for q in json.load(open(os.path.join(MMLU, "bank.json")))["questions"]}
    gab = json.load(open(os.path.join(MMLU, "answers.json")))["answers"]
    for m in MOLDES:
        q = banco[m.classico_id]
        valores = {o["id"]: _numero(o["content"]) for o in q["options"]}
        calc = m.resposta(dict(m.originais))
        perto = min(valores, key=lambda k: abs(valores[k] - calc))
        assert perto == gab[m.classico_id], (m.classico_id, calc, valores[gab[m.classico_id]])


def test_sorteado_tem_dez_opcoes_distintas_e_o_gabarito_calculado():
    banco, chaves = gerador.gerar(20261115)
    sorteados = [q for q in banco["questions"] if q["versao"] == "sorteado"]
    assert len(sorteados) == len(MOLDES)
    moldes = {m.classico_id: m for m in MOLDES}
    for q in sorteados:
        textos = [o["content"] for o in q["options"]]
        assert len(textos) == 10 and len(set(textos)) == 10, q["id"]
        m = moldes[q["par"]]
        certo = m.formato.format(m.resposta(q["parametros"]))
        chave = chaves["answers"][q["id"]]
        assert next(o["content"] for o in q["options"] if o["id"] == chave) == certo


def test_mesma_seed_mesmo_banco():
    assert gerador.gerar(7) == gerador.gerar(7)
