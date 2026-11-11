"""Registro aw9vf: as estatísticas, com tabelas pequenas e contas feitas à mão."""

import math

import pytest

from norvald_lab.measures.aw9vf.confidence_scale import ConfidenceScale
from norvald_lab.measures.aw9vf.holm_bonferroni import HolmBonferroni
from norvald_lab.measures.aw9vf.mcnemar_exact import McNemarExact
from norvald_lab.measures.aw9vf.modal_dispersion import ModalDispersion
from norvald_lab.measures.aw9vf.neff_sweep import NeffSweep, n_eff
from norvald_lab.measures.aw9vf.new_grounds import NewGrounds, PERMISSIVE, STRICT
from norvald_lab.measures.aw9vf.wilcoxon_signed_rank import WilcoxonSignedRank, midranks
from norvald_lab.measures.ground import Ground


def _pairs(only_x, only_y, both=0, neither=0):
    return [(True, False)] * only_x + [(False, True)] * only_y + [(True, True)] * both + [(False, False)] * neither


def test_mcnemar_exact_hand_computed():
    # b=1, c=5: n=6, P(Bin(6,.5) <= 1) = (1+6)/64 -> p = 2*7/64.
    assert McNemarExact().test(_pairs(1, 5, both=9, neither=4)).p == pytest.approx(0.21875)
    # b=0, c=5: P = 1/32 -> p = 2/32.
    assert McNemarExact().test(_pairs(0, 5)).p == pytest.approx(0.0625)
    # b=c=3: caudas somam mais que 1 -> p = 1.
    assert McNemarExact().test(_pairs(3, 3)).p == 1.0
    # Sem discordantes: nada a observar.
    assert McNemarExact().test(_pairs(0, 0, both=5, neither=5)).p == 1.0
    result = McNemarExact().test(_pairs(0, 10))
    assert (result.b, result.c) == (0, 10) and result.p == pytest.approx(2 / 1024)


def test_wilcoxon_exact_hand_computed():
    # |d| = 1..5, W+ = 1+2+3+4 = 10, W- = 5. P(W <= 5 ou W >= 10) = 20/32.
    result = WilcoxonSignedRank().test([1, 2, 3, 4, -5])
    assert (result.w_plus, result.w_minus, result.n_nonzero, result.method) == (10, 5, 5, "exato")
    assert result.p == pytest.approx(0.625) and result.rank_biserial == pytest.approx(1 / 3)
    # Todos positivos: só os dois extremos, 2/32.
    assert WilcoxonSignedRank().test([1, 2, 3, 4, 5]).p == pytest.approx(0.0625)
    # Zeros saem: sobram 1, 2, 3 (todos positivos), p = 2/8.
    zeros = WilcoxonSignedRank().test([0, 0, 1, 2, 3])
    assert (zeros.n_zero, zeros.n_nonzero) == (2, 3) and zeros.p == pytest.approx(0.25)


def test_wilcoxon_exact_with_ties_uses_midranks():
    # [2, 2, 1, -1]: postos médios 3,5 3,5 1,5 1,5; W+ = 8,5. Em dobro: pesos 7, 7, 3, 3 (total 20);
    # |2s - 20| >= 14 só para s <= 3 (1 + 2 subconjuntos) ou s >= 17 (3): 6/16.
    assert midranks([2, 2, 1, 1]) == [3.5, 3.5, 1.5, 1.5]
    result = WilcoxonSignedRank().test([2, 2, 1, -1])
    assert result.w_plus == 8.5 and result.p == pytest.approx(0.375)
    # Simétrico: W+ = W-, p = 1.
    assert WilcoxonSignedRank().test([1, -1, 2, -2]).p == pytest.approx(1.0)


def test_wilcoxon_without_differences_and_normal_approximation():
    none = WilcoxonSignedRank().test([0, 0, 0])
    assert none.p is None and none.method == "sem_diferencas"
    # 60 diferenças positivas distintas: z = (1830 - 915 - 0,5)/sqrt(60·61·121/24) = 6,73.
    big = WilcoxonSignedRank().test(list(range(1, 61)))
    assert big.method == "normal"
    z = 914.5 / math.sqrt(60 * 61 * 121 / 24)
    assert big.p == pytest.approx(math.erfc(z / math.sqrt(2)))


def test_holm_bonferroni_hand_computed():
    adjusted = HolmBonferroni().adjust({"a": 0.01, "b": 0.04, "c": 0.03})
    # ordem 0,01 · 3 = 0,03; 0,03 · 2 = 0,06; 0,04 · 1 = 0,04 -> sobe para 0,06 (monotonia).
    assert adjusted == {"a": pytest.approx(0.03), "c": pytest.approx(0.06), "b": pytest.approx(0.06)}
    assert HolmBonferroni().adjust({"a": 0.5, "b": 0.6, "c": 0.9}) == {"a": 1.0, "b": 1.0, "c": 1.0}
    assert all(adjusted[k] >= p for k, p in {"a": 0.01, "b": 0.04, "c": 0.03}.items())


def test_new_grounds_strict_and_permissive():
    base_e1, base_e2 = Ground("base", "ev1"), Ground("base", "ev2")
    peer, own, local = Ground("peer", "u-peer"), Ground("own", "u-own"), Ground("local", "um argumento")
    rule = NewGrounds()
    first = [base_e1]
    # Repete o fundamento da B1: não é novo em nenhuma leitura.
    assert not rule.has_new(first, [base_e1], STRICT) and not rule.has_new(first, [base_e1], PERMISSIVE)
    # Aponta para a contribuição de um par: novo só na permissiva.
    assert not rule.has_new(first, [base_e1, peer], STRICT) and rule.has_new(first, [base_e1, peer], PERMISSIVE)
    # Aponta para a própria contribuição anterior: nunca é novo.
    assert not rule.has_new(first, [own], STRICT) and not rule.has_new(first, [own], PERMISSIVE)
    # Evidência que a B1 não tinha, ou unidade própria que a B1 não tinha: novo nas duas.
    assert rule.has_new(first, [base_e2], STRICT) and rule.has_new(first, [base_e2], PERMISSIVE)
    assert rule.has_new(first, [local], STRICT) and not rule.has_new(first + [local], [local], STRICT)
    # Sem fundamento nenhum: não há fundamento novo.
    assert not rule.has_new(first, [], PERMISSIVE)


def test_modal_dispersion_and_confidence_scale():
    assert ModalDispersion().of(["a", "a", "b", "c"]) == 0.5
    assert ModalDispersion().of(["a"] * 5) == 0.0
    assert ModalDispersion().of(["a", "a", "a", "b", "c"]) == pytest.approx(0.4)
    assert ModalDispersion().of(["a"]) is None
    scale = ConfidenceScale()
    assert [scale.rank(c) for c in ("baixa", "média", "media", "alta", "Alta ")] == [1, 2, 2, 3, 3]
    assert scale.rank("") is None and scale.rank("certeza") is None


def test_neff_sweep_is_analytic():
    assert n_eff(4, 0.5) == pytest.approx(1.6)  # 4 / (1 + 3·0,5)
    assert n_eff(5, 1.0) == pytest.approx(1.0)
    assert n_eff(None, 0.25) == pytest.approx(4.0)  # 1/ρ̄
    assert n_eff(8, 0.1) == pytest.approx(8 / 1.7)
    table = NeffSweep().table(5, {"rho_erro_B1": 0.5, "rho_erro_E": None})
    rows = {row["rho"]: row for row in table["linhas"]}
    assert set(rows[0.5]) == {"rho", "n=4", "n=5", "n=8", "n=inf"} and rows[0.5]["n=inf"] == pytest.approx(2.0)
    assert all(0 < row["rho"] <= 1 for row in table["linhas"]) and "analitica" in table["natureza"]
    assert table["ancoras_empiricas"]["rho_erro_B1"]["n=4"] == pytest.approx(1.6) and table["ancoras_empiricas"]["rho_erro_E"] is None
