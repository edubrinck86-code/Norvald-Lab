"""Medidas A–J do bloco 1.2 sobre tabelas pequenas com resposta conhecida.

Notação das tabelas: cada letra é a opção de p1, p2, p3...; "-" é sem posição.
As contas esperadas estão feitas à mão nos comentários.
"""

import pytest
from measures_helpers import obs, table

from norvald_lab.measures.b1_grouping import B1Grouping
from norvald_lab.measures.bootstrap import ClusteredBootstrap
from norvald_lab.measures.criteria import CriterionA, CriterionB, CriterionC, CriterionD, CriterionE, CriterionF, CriterionG, CriterionH, CriterionI, CriterionJ
from norvald_lab.measures.observation_table import ObservationTable
from norvald_lab.measures.panel_agreement import discordance, unanimity
from norvald_lab.measures.verdict import A_DEFINIR, COMPATIVEL, NAO_COMPATIVEL

BOOT = ClusteredBootstrap(reps=300, seed=11)


def est(block):
    return block["estimativa"]


# --- regras 1 e 2 ---------------------------------------------------------------------

@pytest.mark.parametrize("letters,group,majority", [
    ("aaaaa", "unanime", "a"),
    ("aaabb", "maioria", "a"),   # 3 × 2: maioria por margem mínima
    ("aabb", "sem_maioria", None),  # regra 2: 2 × 2 é sem maioria, sem desempate
    ("aabbc", "sem_maioria", None),  # 2-2-1: nenhuma passa da metade
    ("aabcd", "sem_maioria", None),  # pluralidade não é maioria
    ("a", "insuficiente", None),
])
def test_b1_grouping(letters, group, majority):
    grouping = B1Grouping.classify(list(letters))
    assert (grouping.group, grouping.majority) == (group, majority)


def test_panel_agreement():
    # "aabbb": Σ n_k(n_k−1) = 2·1 + 3·2 = 8; m(m−1) = 20; dispersão = 1 − 8/20 = 0,6
    assert discordance(list("aabbb")) == pytest.approx(0.6)
    assert discordance(list("aaaaa")) == 0 and unanimity(list("aaaaa")) == 1
    assert unanimity(list("a")) is None and discordance(["a"]) is None


# --- A --------------------------------------------------------------------------------

A_SPEC = {
    "q1": {"B1": "aaabb", "B2": "aaaba", "B3": "aaabb", "EP": "aaaab", "E": "aaaaa"},  # maioria a; fora: p4, p5
    "q2": {"B1": "aaaaa", "B2": "aaaaa", "B3": "aaaaa", "EP": "aaaaa", "E": "aaaaa"},  # unânime: fora de A (regra 1)
    "q3": {"B1": "aabbc", "B2": "aabbc", "B3": "aabbc", "EP": "aaaaa", "E": "aaaaa"},  # sem maioria: fora de A (regra 2)
    "q4": {"B1": "bbbba", "B2": "bbbba", "B3": "bbbba", "EP": "bbbbb", "E": "bbbba"},  # maioria b; fora: p5
}


def test_a_toward_majority_by_hand():
    out = CriterionA().compute(table(A_SPEC), BOOT)
    # Unidades: (q1,p4), (q1,p5), (q4,p5).
    # B2: p4 b→b 0, p5 b→a 1, q4 p5 0 → 1/3.  B3: 0.  EP: p4 a 1, p5 b 0, q4 p5 b 1 → 2/3.
    # E: 1, 1, 0 → 2/3.
    levels = out["resultado"]["todas"]["niveis"]
    assert [est(levels[c]) for c in ("B1", "B2", "B3", "EP", "E")] == pytest.approx([0, 1 / 3, 0, 2 / 3, 2 / 3])
    contrasts = out["resultado"]["todas"]["contrastes"]
    assert est(contrasts["delta_pares"]) == pytest.approx(2 / 3)
    assert est(contrasts["delta_total"]) == pytest.approx(2 / 3)
    assert est(contrasts["delta_posicao"]) == pytest.approx(2 / 3)
    assert est(contrasts["delta_justificativa"]) == pytest.approx(0)
    assert est(contrasts["delta_espontanea"]) == pytest.approx(1 / 3)
    assert contrasts["delta_pares"]["n"] == 3
    assert out["perguntas_por_grupo_b1"] == {"unanime": 1, "maioria": 2, "sem_maioria": 1, "insuficiente": 0}
    # q4 contribui Δ = 0; réplica só com q4 tem Δ = 0 → o intervalo toca 0.
    assert out["veredito"] == NAO_COMPATIVEL


def test_a_compatible_when_every_question_moves():
    spec = {q: A_SPEC["q1"] for q in ("q1", "q5", "q6")}
    out = CriterionA().compute(table(spec), BOOT)
    assert out["resultado"]["todas"]["contrastes"]["delta_pares"]["ic"] == [1.0, 1.0]
    assert out["veredito"] == COMPATIVEL


def test_a_with_and_without_indirect_rows():
    # Regra 3: a linha de E de p4 é indireta. Com ela: p4 foi à maioria. Sem ela: p4 sai do par E−B3.
    base = table({"q1": A_SPEC["q1"]})
    rows = tuple(r if not (r.condition == "E" and r.participant_id == "p4") else obs("q1", "E", "p4", "a", indirect=True) for r in base.rows)
    with_indirect = ObservationTable(rows, base.questions, base.runs)
    out_with = CriterionA().compute(with_indirect, BOOT)["resultado"]["todas"]["contrastes"]["delta_pares"]
    out_without = CriterionA().compute(with_indirect.without_indirect(), BOOT)["resultado"]["todas"]["contrastes"]["delta_pares"]
    assert (est(out_with), out_with["n"]) == (1.0, 2)
    assert (est(out_without), out_without["n"]) == (1.0, 1)


# --- B --------------------------------------------------------------------------------

def test_b_uniformity_by_hand():
    spec = {
        "q1": {"B1": "aabbb", "B2": "aabbb", "B3": "aabbb", "EP": "abbbb", "E": "bbbbb"},
        "q2": {"B1": "aaaaa", "B2": "aaaaa", "B3": "aaaaa", "EP": "aaaaa", "E": "aaaaa"},
    }
    out = CriterionB().compute(table(spec), BOOT)["resultado"]
    unan, disp = out["unanimidade"], out["dispersao"]
    # unanimidade: q1 E=1, B3=0; q2 1 em tudo → M(E)=1, M(B3)=1/2, Δ_pares = média(1, 0) = 1/2
    assert est(unan["todas"]["niveis"]["E"]) == 1 and est(unan["todas"]["niveis"]["B3"]) == 0.5
    assert est(unan["todas"]["contrastes"]["delta_pares"]) == 0.5
    # dispersão: q1 B3 "aabbb" = 0,6; EP "abbbb" = 1 − 12/20 = 0,4; E 0. q2 0.
    # Δ_pares = média(−0,6, 0) = −0,3; Δ_posição = média(0,4 − 0,6, 0) = −0,1
    assert est(disp["todas"]["contrastes"]["delta_pares"]) == pytest.approx(-0.3)
    assert est(disp["todas"]["contrastes"]["delta_posicao"]) == pytest.approx(-0.1)
    # regra 1: unânimes em B1 ficam num grupo à parte (q2), q1 é "maioria"
    assert est(unan["maioria"]["contrastes"]["delta_pares"]) == 1 and est(unan["unanime"]["contrastes"]["delta_pares"]) == 0


def test_b_pairs_by_participant():
    # Em E falta p1. No par E−B3 só entram p2..p5: B3 "abbb" (não unânime, dispersão 1 − 6/12 = 0,5), E "bbbb".
    out = CriterionB().compute(table({"q1": {"B1": "aabbb", "B3": "aabbb", "E": "-bbbb"}}), BOOT)["resultado"]
    assert est(out["unanimidade"]["todas"]["contrastes"]["delta_pares"]) == 1
    assert est(out["dispersao"]["todas"]["contrastes"]["delta_pares"]) == pytest.approx(-0.5)


# --- C --------------------------------------------------------------------------------

def test_c_divided_versus_unanimous_by_hand():
    spec = {
        "q1": {"B1": "aaabb", "B3": "aaabb", "E": "aaaaa"},  # maioria: 2 de 5 mudam em E
        "q2": {"B1": "aaaaa", "B3": "aaaaa", "E": "aaaab"},  # unânime: 1 de 5
        "q3": {"B1": "aabbc", "B3": "aabbc", "E": "aabbb"},  # sem maioria: 1 de 5
    }
    out = CriterionC().compute(table(spec), BOOT)
    groups = out["resultado"]
    # divididas = q1 + q3 = 3/10; unânimes = 1/5; diferença em E = 0,1
    assert est(groups["divididas"]["niveis"]["E"]) == pytest.approx(0.3)
    assert est(groups["unanimes"]["niveis"]["E"]) == pytest.approx(0.2)
    assert est(groups["maioria"]["niveis"]["E"]) == pytest.approx(0.4) and est(groups["sem_maioria"]["niveis"]["E"]) == pytest.approx(0.2)
    assert est(out["divididas_menos_unanimes"]["niveis"]["E"]) == pytest.approx(0.1)
    # B3 não muda ninguém: a diferença em Δ_pares é a mesma 0,1
    assert est(out["divididas_menos_unanimes"]["contrastes"]["delta_pares"]) == pytest.approx(0.1)


# --- D --------------------------------------------------------------------------------

def test_d_between_versus_within_by_hand():
    spec = {"q1": {"B1": "aabbb", "B2": "aabba"}, "q2": {"B1": "aaaaa", "B2": "aaaaa"}}
    out = CriterionD().compute(table(spec), BOOT)["resultado"]
    # dentro: q1 1/5, q2 0 → 0,1. entre: q1 0,6, q2 0 → 0,3. entre − dentro = média(0,4, 0) = 0,2
    assert est(out["dentro"]) == pytest.approx(0.1)
    assert est(out["entre"]) == pytest.approx(0.3)
    assert est(out["entre_menos_dentro"]) == pytest.approx(0.2)


# --- F, G, E --------------------------------------------------------------------------

# Gabarito "a". Erros em B1: p1 [1,1,0,0], p2 [1,1,0,0], p3 [1,0,1,0].
ERR_SPEC = {"g1": {"B1": "bbb"}, "g2": {"B1": "bba"}, "g3": {"B1": "aab"}, "g4": {"B1": "aaa"}}
ERR_ANSWERS = {q: "a" for q in ERR_SPEC}
# Contestáveis: p1 a,a,b,a; p2 a,a,b,b; p3 b,b,a,b.
POS_SPEC = {"c1": {"B1": "aab"}, "c2": {"B1": "aab"}, "c3": {"B1": "bba"}, "c4": {"B1": "abb"}}


def test_f_error_correlation_and_n_eff_by_hand():
    out = CriterionF().compute(table(ERR_SPEC, ERR_ANSWERS), BOOT)
    # phi(p1,p2) = 1; phi(p1,p3): n=4, Σx=Σy=2, Σxy=1 → (4 − 4)/√(4·4) = 0; phi(p2,p3) = 0
    # ρ̄ = 1/3; N_eff = 3/(1 + 2/3) = 1,8
    assert est(out["rho_erro"]) == pytest.approx(1 / 3)
    assert est(out["n_eff"]) == pytest.approx(1.8)
    assert out["n_participantes"] == 3
    assert est(out["taxa_erro_por_participante"]["p3·m3"]) == 0.5


def test_g_false_consensus_ratio_by_hand():
    out = CriterionG().compute(table(ERR_SPEC, ERR_ANSWERS), BOOT)["resultado"]
    # todos erram só em g1 → 1/4; taxas 1/2, 1/2, 1/2 → produto 1/8; razão 2
    assert est(out["p_todos_erram"]) == 0.25
    assert est(out["produto_taxas"]) == 0.125
    assert est(out["razao"]) == pytest.approx(2.0)


def test_g_excludes_incomplete_panel():
    spec = dict(ERR_SPEC, g5={"B1": "bb-"})
    out = CriterionG().compute(table(spec, {q: "a" for q in spec}), BOOT)
    assert out["perguntas_excluidas_painel_incompleto"] == 1 and out["resultado"]["p_todos_erram"]["n"] == 4


def test_e_positions_versus_errors_by_hand():
    spec = dict(ERR_SPEC, **POS_SPEC)
    out = CriterionE().compute(table(spec, ERR_ANSWERS), BOOT)
    r = out["resultado"]
    # kappa(p1,p2): P_o = 3/4, P_e = 3/4·1/2 + 1/4·1/2 = 1/2 → 0,5
    # kappa(p1,p3): P_o = 0, P_e = 3/4·1/4 + 1/4·3/4 = 3/8 → −0,6
    # kappa(p2,p3): P_o = 1/4, P_e = 1/2 → −0,5        ρ̄_pos = −0,2; N_eff_pos = 3/(1 − 0,4) = 5
    assert est(r["rho_posicoes_kappa"]) == pytest.approx(-0.2)
    assert est(r["n_eff_posicoes"]) == pytest.approx(5.0)
    # erros: phi como em F (1/3); kappa certo/errado: 1, 0, 0 → 1/3; N_eff 1,8
    assert est(r["rho_erros_phi"]) == pytest.approx(1 / 3) and est(r["rho_erros_kappa"]) == pytest.approx(1 / 3)
    assert est(r["dif_n_eff_posicoes_menos_erros_phi"]) == pytest.approx(3.2)
    assert est(r["dif_rho_kappa_posicoes_menos_erros"]) == pytest.approx(-0.2 - 1 / 3)
    assert out["perguntas"] == {"contestaveis": 4, "gabarito": 4}
    assert out["veredito"] == A_DEFINIR  # "limiar a definir" no critério


# --- H --------------------------------------------------------------------------------

def test_h_uniformity_with_accuracy_by_hand():
    spec = {
        "g1": {"B1": "aab", "B3": "aab", "EP": "aab", "E": "aaa"},  # p3 W→C em E
        "g2": {"B1": "abb", "B3": "abb", "EP": "abb", "E": "bbb"},  # p1 C→W em E
    }
    out = CriterionH().compute(table(spec, {"g1": "a", "g2": "a"}), BOOT)
    r = out["resultado"]
    # unanimidade: E 1 nas duas, B3 0 → Δ_pares = 1. acerto: B3 3/6, E 3/6 → Δ_pares = 0
    assert est(r["unanimidade"]["todas"]["contrastes"]["delta_pares"]) == 1
    assert est(r["acerto"]["todas"]["contrastes"]["delta_pares"]) == 0
    # réplicas: (g1,g1) +1/3, (g2,g2) −1/3 → intervalo do acerto inclui 0; unanimidade [1,1]
    assert out["veredito"] == COMPATIVEL


# --- I --------------------------------------------------------------------------------

def test_i_correct_to_incorrect_by_majority_by_hand():
    spec = {
        "g1": {"B1": "aab", "B3": "aab", "EP": "aab", "E": "abb"},  # maioria certa; acertaram p1, p2; p2 C→W em E
        "g2": {"B1": "abb", "B3": "abb", "EP": "abb", "E": "bbb"},  # maioria errada; acertou p1; C→W em E
    }
    out = CriterionI().compute(table(spec, {"g1": "a", "g2": "a"}), BOOT)["resultado"]
    # 3 unidades: E 2/3, B3 0 → Δ_pares 2/3; Δ_posição 0; Δ_justificativa 2/3
    assert est(out["todas"]["contrastes"]["delta_pares"]) == pytest.approx(2 / 3)
    assert est(out["todas"]["contrastes"]["delta_posicao"]) == 0
    assert est(out["todas"]["contrastes"]["delta_justificativa"]) == pytest.approx(2 / 3)
    assert est(out["maioria_certa"]["niveis"]["E"]) == 0.5 and est(out["maioria_errada"]["niveis"]["E"]) == 1


# --- J --------------------------------------------------------------------------------

def test_j_who_moved_whom_and_list_position_by_hand():
    spec = {"q1": {"B1": "aabc", "E": "aaad"}}  # p3 b→a (portadores p1, p2); p4 c→d (nenhum par tinha d)
    orders = {("q1", "E", "p3"): ("p2", "p4", "p3", "p1")}  # sem o próprio: [p2, p4, p1], m = 3
    out = CriterionJ().compute(table(spec, peer_orders=orders), BOOT)["por_condicao"]["E"]
    assert (out["mudancas"], out["para_opcao_de_nenhum_par"], out["sem_ordem_gravada"]) == (2, 1, 0)
    assert out["credito_destino_origem"] == {"m3": {"m1": 0.5, "m2": 0.5}}
    # esperado sem efeito de ordem: k/m = 2/3 em cada posição; observado: 1, 0, 1
    ranks = out["portador_por_posicao_na_lista"]
    assert [ranks[r]["observado"] for r in ("1", "2", "3")] == [1, 0, 1]
    assert ranks["1"]["esperado_sem_efeito"] == pytest.approx(2 / 3)
    # excesso no primeiro e no último: (1 − 2/3)/1 = 1/3; metade das mudanças foi para posição de par
    assert est(out["resultado"]["excesso_primeiro"]) == pytest.approx(1 / 3)
    assert est(out["resultado"]["excesso_ultimo"]) == pytest.approx(1 / 3)
    assert est(out["resultado"]["fracao_para_posicao_de_par"]) == 0.5
