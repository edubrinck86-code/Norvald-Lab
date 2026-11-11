"""Medidas de Hao et al. (§3 do protocolo) e a conferência algébrica com o nosso Δ_pares.

Mapeamento: a_0 = B1, a_sr = B3, a_so = EP, a_r = E.
"""

import random

import pytest
from measures_helpers import table

from norvald_lab.measures.bootstrap import ClusteredBootstrap
from norvald_lab.measures.cross_check import CrossCheck
from norvald_lab.measures.hao import HaoFlipRates, HaoHarmBenefit, HaoPartition, HaoStrictConformity, HaoTransitions
from norvald_lab.measures.hao.hao_unit import hao_units, subset
from norvald_lab.measures.report_builder import MeasuresReport

BOOT = ClusteredBootstrap(reps=300, seed=13)

# Gabarito "a". B1 "aabbc".
# p1: a → B3 b                         → instabilidade
# p2: a, B3 a, EP b (b é de par)        → conformidade estrita
# p3: b, B3 b, EP b, E a (a é de par)   → adoção só com raciocínio
# p4: b, B3 b, EP d (ninguém deu d)     → outros
# p5: c em tudo                         → estável
Q1 = {"B1": "aabbc", "B3": "babbc", "EP": "abbdc", "E": "abadc"}
Q2 = {"B1": "aaaaa", "B3": "aaaaa", "EP": "aaaaa", "E": "aaaaa"}  # unânime: só entra em "todas"


def _units(spec, answers):
    return hao_units(table(spec, answers))


def est(block):
    return block["estimativa"]


def test_partition_in_precedence_order_by_hand():
    units = _units({"q1": Q1}, {"q1": "a"})
    out = HaoPartition().compute(units, BOOT)
    assert out["N"] == 5
    assert out["contagens"] == {"instabilidade_reconsideracao": 1, "conformidade_estrita": 1, "adocao_so_com_raciocinio": 1, "outros": 1, "estaveis": 1}
    assert sum(out["contagens"].values()) == out["N"]


def test_flip_rates_and_strict_conformity_by_hand():
    units = _units({"q1": Q1}, {"q1": "a"})
    flips = HaoFlipRates().compute(units, BOOT)["todos"]
    # SR: p1 → 1/5. Só posição: p2, p4 → 2/5. Raciocínio: p2, p3, p4 → 3/5.
    assert [est(flips[k]) for k in ("sr", "so", "r")] == pytest.approx([0.2, 0.4, 0.6])
    strict = HaoStrictConformity().compute(units, BOOT)
    # Eq. 1: 1 estrita / 4 estáveis em SR (denominador NÃO é N)
    assert (strict["N_estrita"], strict["N_estaveis_sr"]) == (1, 4)
    assert est(strict["taxa"]) == 0.25


def test_transitions_per_cohort_by_hand():
    out = HaoTransitions().compute(_units({"q1": Q1}, {"q1": "a"}), BOOT)["coortes"]
    assert out["instabilidade_reconsideracao"]["contagens"] == {"C→W": 1, "W→C": 0, "W→W": 0}  # p1 a→b
    assert out["conformidade_estrita"]["contagens"] == {"C→W": 1, "W→C": 0, "W→W": 0}  # p2 a→b
    assert out["adocao_so_com_raciocinio"]["contagens"] == {"C→W": 0, "W→C": 1, "W→W": 0}  # p3 b→a
    assert est(out["adocao_so_com_raciocinio"]["parcelas"]["W→C"]) == 1


def test_transitions_need_gabarito():
    out = HaoTransitions().compute(_units({"q1": Q1}, {}), BOOT)["coortes"]
    assert all(cohort["n"] == 0 for cohort in out.values())


def test_harm_benefit_standardized_by_support_by_hand():
    units = _units({"q1": Q1, "q2": Q2}, {"q1": "a", "q2": "a"})
    # Estáveis em SR: q1 p2..p5 e os 5 de q2. Apoio s = pares com a mesma B1 do alvo.
    # H (a_0 certa): q1 p2 (s=1, evento em EP e em E); q2 p1..p5 (s=4, sem evento).
    # B (a_0 errada, par certo): q1 p3 (s=1), p4 (s=1), p5 (s=0).
    #   EP: nenhum vira certo. E: p3 vira certo → B_1 = 1/2, B_0 = 0/1.
    # Estratos com os dois lados: só s=1 (s=0 não tem H; s=4 não tem B) → peso 1.
    out = HaoHarmBenefit().compute(subset(units, "todas"), BOOT)
    so, r = out["so_posicao_EP"], out["raciocinio_E"]
    assert so["estratos_usados"] == [1] and so["pesos"] == {"1": 1.0}
    assert est(so["H_padronizado"]) == 1 and est(so["B_padronizado"]) == 0 and est(so["H_menos_B"]) == 1
    assert est(r["H_padronizado"]) == 1 and est(r["B_padronizado"]) == 0.5 and est(r["H_menos_B"]) == 0.5
    assert so["estratos_excluidos"] == {"0": {"n_H": 0, "n_B": 1}, "4": {"n_H": 5, "n_B": 0}}
    # sem padronização: H = 1/6 (q1 p2 entre 6 certos estáveis), B em E = 1/3
    assert est(so["H_bruto"]) == pytest.approx(1 / 6) and est(r["B_bruto"]) == pytest.approx(1 / 3)


def test_harm_benefit_weights_follow_the_strata():
    # Dois estratos com os dois lados: s=0 e s=1. Gabarito "a".
    # q1 B1 "abbcc": p1 certo, s=0 (H); p2,p3 errados s=1 com par certo (B); p4,p5 errados s=1 (B).
    # q2 B1 "aabcc": p1,p2 certos s=1 (H); p3 errado s=0 (B); p4,p5 errados s=1 (B).
    spec = {
        "q1": {"B1": "abbcc", "B3": "abbcc", "EP": "bbbcc", "E": "bbbcc"},  # p1 C→W
        "q2": {"B1": "aabcc", "B3": "aabcc", "EP": "aaacc", "E": "aaacc"},  # p3 W→C
    }
    out = HaoHarmBenefit().compute(_units(spec, {"q1": "a", "q2": "a"}), BOOT)["so_posicao_EP"]
    # s=0: H 1/1 (q1 p1), B 1/1 (q2 p3) → n=2. s=1: H 0/2 (q2 p1,p2), B 0/6 → n=8. Pesos 0,2 e 0,8.
    assert out["pesos"] == {"0": pytest.approx(0.2), "1": pytest.approx(0.8)}
    # H* = 0,2·1 + 0,8·0 = 0,2; B* = 0,2·1 + 0,8·0 = 0,2; H − B = 0
    assert est(out["H_padronizado"]) == pytest.approx(0.2) and est(out["B_padronizado"]) == pytest.approx(0.2)
    assert est(out["H_menos_B"]) == pytest.approx(0)


def test_disagreement_subset_drops_unanimous_b1():
    units = _units({"q1": Q1, "q2": Q2}, {"q1": "a", "q2": "a"})
    assert (len(subset(units, "todas")), len(subset(units, "discordancia"))) == (10, 5)
    report = MeasuresReport(BOOT).build(table({"q1": Q1, "q2": Q2}, {"q1": "a", "q2": "a"}))
    hao = report["hao"]["com_indiretas"]
    assert hao["n_pares_agente_pergunta"] == {"todas": 10, "discordancia": 5}
    assert est(hao["conformidade_estrita"]["discordancia"]["taxa"]) == 0.25
    assert est(hao["conformidade_estrita"]["todas"]["taxa"]) == pytest.approx(1 / 9)  # 1 / (4 + 5)
    assert report["hao"]["sem_indiretas"]["igual_a"] == "com_indiretas"


def test_cross_check_by_hand():
    # Estáveis em SR em q1: p2..p5. B1→E: p2 C→W, p3 W→C, p4 W→W, p5 igual → (1 − 1)/4 = 0.
    # Nosso lado: acerto E (0,1,0,0) − acerto B3 (1,0,0,0) → 0. EP: p2 C→W, p4 W→W → (0 − 1)/4.
    out = CrossCheck().compute(table({"q1": Q1}, {"q1": "a"}))["todas"]
    assert out["N_estaveis_sr"] == 4 and out["iguais"]
    assert out["nosso_lado"] == {"delta_pares": 0.0, "delta_posicao": -0.25}
    assert out["lado_hao"] == out["nosso_lado"]


def test_cross_check_holds_on_random_tables():
    # A identidade é algébrica: tem de valer em qualquer tabela, não só nas montadas à mão.
    rng = random.Random(20261111)
    for _ in range(25):
        spec, answers = {}, {}
        for q in range(12):
            letters = {c: "".join(rng.choice("abcd") for _ in range(5)) for c in ("B1", "B2", "B3", "EP", "E")}
            letters["B3"] = "".join(b if rng.random() < 0.7 else x for b, x in zip(letters["B1"], letters["B3"]))
            spec[f"g{q}"], answers[f"g{q}"] = letters, rng.choice("abcd")
        out = CrossCheck().compute(table(spec, answers))
        assert out["todas"]["iguais"] and out["discordancia"]["iguais"]
        assert out["todas"]["nosso_lado"]["delta_pares"] == pytest.approx(out["todas"]["lado_hao"]["delta_pares"], abs=1e-12)
