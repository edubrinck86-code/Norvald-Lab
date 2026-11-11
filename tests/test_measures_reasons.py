"""Mesma resposta, razões diferentes (exploratória): tokenizador, TF-IDF e agregação."""

import math

import pytest
from measures_helpers import table

from norvald_lab.measures.bootstrap import ClusteredBootstrap
from norvald_lab.measures.reasons.reason_similarity import ReasonSimilarity
from norvald_lab.measures.reasons.same_answer_reasons import SameAnswerReasons
from norvald_lab.measures.reasons.tfidf_similarity import TfidfCosineSimilarity
from norvald_lab.measures.reasons.tokenizer import tokenize


def test_tokenizer_is_documented_behaviour():
    # acentos fora, minúsculas, [a-z0-9]+, ≥ 2 caracteres, sem palavras vazias, sem o vocabulário dado
    assert tokenize("A Latência é crítica: gRPC usa HTTP/2 e x") == ["latencia", "critica", "grpc", "usa", "http"]
    assert tokenize("gRPC is faster", ignore={"grpc"}) == ["faster"]


def test_tfidf_cosine_by_hand():
    sim = TfidfCosineSimilarity(["xx yy", "xx zz"])
    # idf(xx) = ln(3/3) + 1 = 1; idf(yy) = idf(zz) = ln(3/2) + 1 = i
    # cos = 1·1 / (√(1 + i²) · √(1 + i²)) = 1 / (1 + i²)
    i = math.log(1.5) + 1
    matrix = sim.matrix(["xx yy", "xx zz", "xx yy"])
    assert matrix[0][1] == pytest.approx(1 / (1 + i * i))
    assert matrix[0][2] == pytest.approx(1.0)
    assert sim.matrix(["xx", ""])[0][1] is None  # texto sem token não compara


def test_prompt_vocabulary_is_ignored():
    # Repetir a opção escolhida não é razão em comum.
    sim = TfidfCosineSimilarity(["grpc latency", "grpc cost"])
    assert sim.matrix(["grpc latency", "grpc cost"], prompt="Which protocol? REST gRPC")[0][1] == 0


class Stub(ReasonSimilarity):
    """1 para textos iguais, 0,1 para diferentes: isola a agregação da similaridade."""
    name = "stub"

    def matrix(self, texts, *, prompt=""):
        return [[1.0 if a == b else 0.1 for b in texts] for a in texts]


def test_same_answer_aggregation_and_convergence_by_hand():
    texts = {("q1", "B1", "p1"): "r1", ("q1", "B1", "p2"): "r1", ("q1", "B1", "p3"): "r2",
             ("q1", "E", "p1"): "r1", ("q1", "E", "p2"): "r3", ("q1", "E", "p3"): "r4"}
    data = table({"q1": {"B1": "aab", "E": "aaa"}}, justifications=texts)
    out = SameAnswerReasons(Stub()).compute(data, ClusteredBootstrap(reps=50))
    b1, e = out["por_pergunta"]["r/q1/r0001"]["B1"], out["por_pergunta"]["r/q1/r0001"]["E"]
    # B1: concordantes p1,p2 (mesmo texto) → 1; discordantes (p1,p3), (p2,p3) → 0,1
    assert (b1["n_concordantes"], b1["similaridade_concordantes"], b1["similaridade_discordantes"]) == (2, 1.0, 0.1)
    assert b1["concordancia_com_razoes_diversas"] is False
    # E: os três concordam, com textos diferentes → 0,1 < 0,2 → razões diversas
    assert (e["n_concordantes"], e["concordancia_com_razoes_diversas"]) == (3, True)
    assert e["similaridade_concordantes"] == pytest.approx(0.1)
    # E − B1 entre concordantes = 0,1 − 1 = −0,9 (as razões divergiram com a exposição)
    assert out["resumo"]["similaridade_concordantes"]["contrastes"]["E_menos_B1"]["estimativa"] == pytest.approx(-0.9)
    assert out["exploratoria"] is True and out["limiar_provisorio"] == 0.2
