"""Registro aw9vf: taxas, contrastes, testes, exclusões, dependência e exploratórias, em tabelas pequenas."""

import json

import pytest
from measures_helpers import obs, rows_table, table

from norvald_lab.measures.aw9vf.confidence_channel import ConfidenceChannel, peer_majority_relation
from norvald_lab.measures.aw9vf.confirmatory_tests import ConfirmatoryTests
from norvald_lab.measures.aw9vf.dependence import Dependence
from norvald_lab.measures.aw9vf.literal_collision import LiteralCollision
from norvald_lab.measures.aw9vf.pair_asymmetry import PairAsymmetry
from norvald_lab.measures.aw9vf.registration_report import RegistrationReport
from norvald_lab.measures.aw9vf.unanimous_filter import UnanimousFilter
from norvald_lab.measures.bootstrap import ClusteredBootstrap
from norvald_lab.measures.ground import Ground

BOOT = ClusteredBootstrap(reps=60, seed=7)
PEER = Ground("peer", "u-peer")
BASE = Ground("base", "ev-novo")


def _rows(question, condition, letters, grounds=None, **kw):
    grounds = grounds or {}
    return [obs(question, condition, f"p{i}", letter, grounds=grounds.get(f"p{i}", ()), **kw) for i, letter in enumerate(letters, start=1)]


def _tiny():
    """Três perguntas, quatro participantes. As contas estão nos comentários dos testes."""
    rows = []
    # q1: B1 aabb. B3 igual. B2: p2 muda sem fundamento. E: todos em b; p1 muda sem fundamento,
    # p2 muda declarando fundamento que aponta para um par.
    rows += _rows("q1", "B1", "aabb") + _rows("q1", "B3", "aabb") + _rows("q1", "B2", "abbb") + _rows("q1", "E", "bbbb", {"p2": [PEER]})
    # q2: B1 abbb. B3: p1 muda, mas com fundamento novo (evidência). B2 igual. E: p2 muda sem fundamento.
    rows += _rows("q2", "B1", "abbb") + _rows("q2", "B3", "bbbb", {"p1": [BASE]}) + _rows("q2", "B2", "abbb") + _rows("q2", "E", "aabb")
    # q3: B1 unânime (aaaa). Só E tem uma mudança (p1, sem fundamento).
    rows += _rows("q3", "B1", "aaaa") + _rows("q3", "B3", "aaaa") + _rows("q3", "B2", "aaaa") + _rows("q3", "E", "baaa")
    return rows_table(rows)


def test_rates_and_deltas_in_both_readings_hand_computed():
    main = UnanimousFilter().without_unanimous(_tiny())
    result = ConfirmatoryTests(BOOT).compute(main)
    rates = {c: {r: result["taxas"][c][r]["estimativa"] for r in ("estrita", "permissiva")} for c in result["taxas"]}
    # 8 pares (q1 e q2). B3: p1 de q2 mudou mas com fundamento novo -> 0/8. B2: p2 de q1 -> 1/8.
    # E: q1 p1 e p2 (p2 só na estrita, fundamento de par não é novo nela) + q2 p2: 3/8 estrita, 2/8 permissiva.
    assert rates["B3"] == {"estrita": 0.0, "permissiva": 0.0}
    assert rates["B2"] == {"estrita": 1 / 8, "permissiva": 1 / 8}
    assert rates["E"] == {"estrita": 3 / 8, "permissiva": 2 / 8}
    assert result["taxas"]["E"]["intervalo_entre_leituras"] == [2 / 8, 3 / 8]
    assert result["n_pares_por_condicao"]["EP"] == 0 and result["taxas"]["EP"]["estrita"]["estimativa"] is None
    assert result["delta_herd"]["estrita"]["estimativa"] == 3 / 8 and result["delta_herd"]["permissiva"]["estimativa"] == 2 / 8
    assert result["delta_self"]["estrita"]["estimativa"] == -1 / 8 and result["delta_self"]["permissiva"]["estimativa"] == -1 / 8
    assert result["delta_herd"]["intervalo_entre_leituras"] == [2 / 8, 3 / 8]


def test_mcnemar_wilcoxon_and_holm_on_the_tiny_table():
    result = ConfirmatoryTests(BOOT).compute(UnanimousFilter().without_unanimous(_tiny()))
    strict, permissive = result["mcnemar"]["mcnemar_E_vs_B3"]["estrita"], result["mcnemar"]["mcnemar_E_vs_B3"]["permissiva"]
    # Estrita: 3 eventos só em E, 0 só em B3: p = 2·(1/8). Permissiva: 2 só em E: p = 2·(1/4).
    assert (strict["evento_so_em_E"], strict["evento_so_em_B3"], strict["p_bruto"]) == (3, 0, 0.25)
    assert (permissive["evento_so_em_E"], permissive["p_bruto"]) == (2, 0.5)
    # B3 contra B2: um evento só em B2 (b=0, c=1): p = 1.
    assert result["mcnemar"]["mcnemar_B3_vs_B2"]["estrita"]["p_bruto"] == 1.0
    # Dispersão (fração da moda): q1 B3 aabb = 0,5 -> E bbbb = 0; q2 B3 bbbb = 0 -> E aabb = 0,5. Mudanças -0,5 e +0,5: W+ = W-, p = 1.
    wilcoxon = result["wilcoxon_dispersao"]
    assert (wilcoxon["perguntas"], wilcoxon["nao_nulas"], wilcoxon["p_bruto"], wilcoxon["metodo_p"]) == (2, 2, 1.0, "exato")
    assert wilcoxon["mudanca_media_E_menos_B3"]["estimativa"] == 0.0
    # Holm estrita sobre os CINCO testes do 5dpjr (contrato mudou de propósito em 12/11/2026;
    # antes eram três e o ajustado era 0,75): 0,25 · 5 = 1,25, limitado a 1.
    holm = result["holm_bonferroni"]["estrita"]
    assert set(holm) == {"mcnemar_E_vs_B3", "mcnemar_B3_vs_B2", "wilcoxon_dispersao_E_vs_B3", "mcnemar_EP_vs_B3", "mcnemar_E_vs_EP"}
    assert holm["mcnemar_E_vs_B3"]["p_bruto"] == 0.25 and holm["mcnemar_E_vs_B3"]["p_holm"] == 1.0
    assert holm["mcnemar_B3_vs_B2"]["p_holm"] == 1.0 and holm["wilcoxon_dispersao_E_vs_B3"]["p_holm"] == 1.0
    assert result["holm_bonferroni"]["permissiva"]["mcnemar_E_vs_B3"]["p_holm"] == 1.0  # 0,5 · 5, limitado a 1
    assert all(entry["p_holm"] >= entry["p_bruto"] for entry in holm.values())


def test_h4_tests_position_and_justification_hand_computed():
    """H4 (OSF 5dpjr): EP contra B3 e E contra EP. Faltavam até 12/11/2026."""
    rows = _rows("q1", "B1", "aabb") + _rows("q1", "B3", "aabb") + _rows("q1", "B2", "aabb")
    rows += _rows("q1", "EP", "babb") + _rows("q1", "E", "bbab")
    result = ConfirmatoryTests(BOOT).compute(rows_table(rows))
    # EP: só p1 muda (1/4). E: p1, p2 e p3 mudam (3/4). B3: ninguém.
    assert result["delta_position"]["estrita"]["estimativa"] == 1 / 4
    assert result["delta_justification"]["estrita"]["estimativa"] == 2 / 4
    ep = result["mcnemar"]["mcnemar_EP_vs_B3"]["estrita"]
    assert (ep["evento_so_em_EP"], ep["evento_so_em_B3"], ep["p_bruto"]) == (1, 0, 1.0)
    just = result["mcnemar"]["mcnemar_E_vs_EP"]["estrita"]
    assert (just["evento_so_em_E"], just["evento_so_em_EP"], just["p_bruto"]) == (2, 0, 0.5)
    # Holm sobre os cinco: o menor p (E contra B3, 3 só em E: 0,25) vira 0,25 · 5 = 1,25 -> 1.
    holm = result["holm_bonferroni"]["estrita"]
    assert len(holm) == 5 and holm["mcnemar_E_vs_B3"]["p_holm"] == 1.0


def test_unanimous_items_are_a_labelled_variant():
    full = _tiny()
    unanimous = UnanimousFilter()
    assert unanimous.unanimous_units(full) == {("r", "q3", "r0001")}
    assert unanimous.discard_rate(full) == {"perguntas_com_b1": 3, "perguntas_unanimes_em_b1": 1, "taxa_de_descarte": 1 / 3}
    kept = ConfirmatoryTests(BOOT).compute(full)
    # Com q3 mantida: E ganha o evento de p1 em q3 (4/12 estrita) e B3 continua em 0/12.
    assert kept["taxas"]["E"]["estrita"]["estimativa"] == 4 / 12 and kept["taxas"]["B3"]["estrita"]["estimativa"] == 0.0
    assert kept["mcnemar"]["mcnemar_E_vs_B3"]["estrita"]["p_bruto"] == pytest.approx(2 * 1 / 16)  # b = 4, c = 0
    report = RegistrationReport(BOOT).build(full)
    assert set(report) == {"descarte_de_unanimes_em_b1", "principal_sem_unanimes", "alternativa_com_unanimes"}
    assert report["principal_sem_unanimes"]["confirmatorio"]["n_pares_por_condicao"]["E"] == 8
    assert report["alternativa_com_unanimes"]["confirmatorio"]["n_pares_por_condicao"]["E"] == 12


def test_participant_without_structured_contribution_is_excluded_per_item():
    rows = _rows("q1", "B1", "aabb") + _rows("q1", "B3", "aabb") + _rows("q1", "E", "bbbb")
    rows[0] = obs("q1", "B1", "p1", "a", structured=False)  # tem posição, mas ninguém o viu
    result = ConfirmatoryTests(BOOT).compute(rows_table(rows))
    assert result["n_pares_por_condicao"]["E"] == 3  # p1 sai da exposição naquela pergunta
    report = RegistrationReport(BOOT).build(rows_table(rows))["alternativa_com_unanimes"]["ausencia"]
    assert report["excluidos_da_exposicao_por_pergunta"] == [{"rodada": "r", "pergunta": "q1", "repeticao": "r0001", "participante": "p1", "motivo": "sem_contribuicao_estruturada"}]
    assert report["por_condicao"]["B1"]["sem_contribuicao_estruturada"] == 1 and report["nenhuma_imputacao"]


def test_rho_error_phi_and_n_eff_hand_computed():
    # Dois participantes, cinco perguntas com gabarito "a". Erros em B1: p1 = [1,1,0,0,1], p2 = [1,1,0,0,0].
    # n=5, Σx=3, Σy=2, Σxy=2: phi = (5·2 − 3·2)/√((15−9)(10−4)) = 4/6. N_eff = 2/(1 + 2/3) = 1,2.
    spec = {"q1": "bb", "q2": "bb", "q3": "aa", "q4": "aa", "q5": "ba"}
    # Em E os dois erram nas mesmas duas perguntas: phi = 1, N_eff = 2/2 = 1. Δ_N_eff = 1,2 − 1 = 0,2.
    spec_e = {"q1": "bb", "q2": "bb", "q3": "aa", "q4": "aa", "q5": "aa"}
    answers = {q: "a" for q in spec}
    t = table({q: {"B1": spec[q], "E": spec_e[q]} for q in spec}, answers)
    result = Dependence(BOOT).compute(t, conditions=("B1", "E"), behaviour=False)
    assert result["n_painel"] == 2
    assert result["rho_erro"]["B1"]["estimativa"] == pytest.approx(4 / 6) and result["n_eff"]["B1"]["estimativa"] == pytest.approx(1.2)
    assert result["rho_erro"]["E"]["estimativa"] == pytest.approx(1.0) and result["n_eff"]["E"]["estimativa"] == pytest.approx(1.0)
    assert result["delta_n_eff_B1_menos_E"]["estimativa"] == pytest.approx(0.2)
    assert result["varredura_analitica"]["ancoras_empiricas"]["rho_erro_B1"]["n=4"] == pytest.approx(4 / (1 + 3 * 4 / 6))
    assert set(result["varredura_analitica"]["linhas"][0]) == {"rho", "n=2", "n=4", "n=5", "n=8", "n=inf"}


def test_rho_behaviour_fleiss_and_distance_hand_computed():
    # Contestáveis, três participantes: q1 = aab, q2 = aaa. P1 = (4+1−3)/6 = 1/3, P2 = 1, P̄ = 2/3.
    # Categorias: a = 5 de 6, b = 1 de 6: P_e = 25/36 + 1/36 = 13/18. κ = (2/3 − 13/18)/(5/18) = −0,2.
    t = table({"q1": {"B1": "aab"}, "q2": {"B1": "aaa"}})
    result = Dependence(BOOT).compute(t, conditions=("B1",))
    assert result["rho_comportamento"]["kappa"]["estimativa"] == pytest.approx(-0.2)
    assert result["rho_comportamento"]["concordancia_observada_P"]["estimativa"] == pytest.approx(2 / 3)
    assert result["rho_comportamento"]["contestaveis"] == 2
    # Distância até ρ̄_erro: sem gabarito não há ρ̄_erro, então a distância fica indefinida (não vira zero).
    assert result["distancia_comportamento_menos_erro"]["estimativa"] is None
    # Com gabarito: erros de p1 = [1,1,0,0,1], p2 = [1,1,0,0,0], ρ̄_erro = 2/3; a distância é κ − 2/3.
    answers = {f"g{i}": "a" for i in range(1, 6)}
    spec = {"g1": "bb", "g2": "bb", "g3": "aa", "g4": "aa", "g5": "ba", "q1": "aab", "q2": "aaa"}
    both = Dependence(BOOT).compute(table({q: {"B1": letters} for q, letters in spec.items()}, answers), conditions=("B1",))
    fleiss = both["rho_comportamento"]["kappa"]["estimativa"]
    assert both["distancia_comportamento_menos_erro"]["estimativa"] == pytest.approx(fleiss - 4 / 6)


def test_homogeneous_contrast_panel_reports_rho_and_n_eff_in_b1():
    spec = {"q1": "bb", "q2": "bb", "q3": "aa", "q4": "aa", "q5": "ba"}
    answers = {q: "a" for q in spec}
    contrast = table({q: {"B1": letters} for q, letters in spec.items()}, answers)
    report = RegistrationReport(BOOT).build(_tiny(), contrast)
    block = report["alternativa_com_unanimes"]["painel_homogeneo_de_contraste"]
    assert block["n_painel"] == 2 and block["rho_erro_B1"]["estimativa"] == pytest.approx(4 / 6) and block["n_eff_B1"]["estimativa"] == pytest.approx(1.2)
    assert RegistrationReport(BOOT).build(_tiny())["alternativa_com_unanimes"]["painel_homogeneo_de_contraste"] is None


def test_confidence_channel_split_by_peer_majority():
    assert peer_majority_relation("a", ["a", "a", "b"]) == "maioria_concorda"
    assert peer_majority_relation("b", ["a", "a", "a"]) == "maioria_discorda"
    assert peer_majority_relation("a", ["a", "b"]) == "sem_maioria"  # metade não é maioria
    assert peer_majority_relation("a", []) == "sem_maioria"
    # B1 aaab. p1: pares a,a,b -> maioria a, concorda. p4: pares a,a,a -> discorda.
    confidences = {"p1": ("média", "alta"), "p2": ("alta", "alta"), "p3": ("média", ""), "p4": ("alta", "baixa")}
    rows = _rows("q1", "B1", "aaab")
    for cond, index in (("B3", 0), ("E", 1)):
        rows += [obs("q1", cond, pid, letter, confidence=confidences[pid][index]) for pid, letter in zip(("p1", "p2", "p3", "p4"), "aaab")]
    result = ConfidenceChannel(BOOT).compute(rows_table(rows))
    groups = result["grupos"]
    # concorda: p1 +1, p2 0 (p3 sem confiança em E sai, não vira zero); discorda: p4 −2.
    assert result["pares_sem_confianca_nas_duas_condicoes"] == 1 and result["exploratorio"]
    assert groups["maioria_concorda"]["mudanca_media_E_menos_B3"]["estimativa"] == 0.5 and groups["maioria_concorda"]["pares"] == 2
    assert groups["maioria_concorda"]["nao_nulos"] == 1 and groups["maioria_concorda"]["p_bruto_sem_correcao"] == 1.0
    assert groups["maioria_discorda"]["mudanca_media_E_menos_B3"]["estimativa"] == -2.0 and groups["maioria_discorda"]["efeito_bisserial_por_postos"] == -1.0
    assert groups["todos"]["pares"] == 3


def test_asymmetry_by_ordered_model_pair():
    # q1: B1 = (a, b). E: p1 vai para a posição de p2 sem fundamento novo; p2 não muda. B3 = B1.
    rows = _rows("q1", "B1", "ab") + _rows("q1", "B3", "ab") + _rows("q1", "E", "bb")
    result = PairAsymmetry().compute(rows_table(rows))
    pulls = result["pares_ordenados"]
    assert pulls["p2·m2 → p1·m1"]["n"] == 1 and pulls["p2·m2 → p1·m1"]["estrita"] == {"E": 1.0, "B3": 0.0, "excesso_E_menos_B3": 1.0}
    assert pulls["p1·m1 → p2·m2"]["estrita"]["E"] == 0.0 and pulls["p1·m1 → p2·m2"]["estrita"]["excesso_E_menos_B3"] == 0.0
    # Assimetria do par = excesso(p1 → p2) − excesso(p2 → p1) = 0 − 1.
    assert result["assimetria_por_par"]["p1·m1 ⇄ p2·m2"]["estrita"] == -1.0
    assert result["inferencia"].startswith("nenhuma")


def test_literal_collision_counts_by_author_pair_and_never_prints_text():
    segredo = "texto que nunca pode aparecer no relatório"
    rows = [
        obs("q1", "B1", "p1", "a", claims=[("decision", "Resposta X"), ("claim", segredo)]),
        obs("q1", "B1", "p2", "b", claims=[("decision", "Resposta Y"), ("claim", segredo)]),
        obs("q1", "B1", "p3", "a", claims=[("claim", segredo + " "), ("decision", "Resposta X")]),  # espaço no fim: não é byte a byte idêntico
    ]
    result = LiteralCollision().compute(rows_table(rows))
    pairs = result["ondas"]["B1"]["por_par_de_autores"]
    assert pairs["p1·m1 × p2·m2"] == {"itens_comparados": 1, "itens_com_colisao": 1, "colisoes": 1, "colisoes_em_decisoes": 0}
    # p1 e p3 coincidem só na decisão "Resposta X"; p2 e p3 em nada.
    assert pairs["p1·m1 × p3·m3"] == {"itens_comparados": 1, "itens_com_colisao": 1, "colisoes": 1, "colisoes_em_decisoes": 1}
    assert pairs["p2·m2 × p3·m3"]["colisoes"] == 0
    assert result["ondas"]["B1"]["itens_par_comparados"] == 3 and result["ondas"]["B1"]["itens_par_com_colisao"] == 2
    assert segredo not in json.dumps(result, ensure_ascii=False) and result["texto_no_relatorio"] is False
