"""Condicao exposta e extracao tidy — as duas pecas que faltavam para a
coleta do Delta_herd (docs/tese/01)."""
import json

from norvald_lab.application.arof.exposed_context import seed_peer_contributions
from norvald_lab.application.arof.outcome_extract import (
    STATUS_FALHOU,
    STATUS_OK,
    STATUS_SEM_DECISAO,
    row_from_payload,
    write_csv,
)
from norvald_lab.application.arof.prior_contribution import PriorContribution
from norvald_lab.domain.deliberation.context_item import ContextItem
from norvald_lab.domain.deliberation.working_context import WorkingContext


def _bloco(local_id="d1", option="opt-2", extra_relations=()):
    payload = {
        "knowledge": [
            {"local_id": local_id, "type": "decision", "content": "Escolho B", "confidence": "alta"}
        ],
        "relations": [{"relation_type": "selects", "source": local_id, "target": option}]
        + list(extra_relations),
    }
    return "Prosa do especialista.\n<<CONTRIBUTION>>\n" + json.dumps(payload) + "\n<<END_CONTRIBUTION>>"


def _wc_com_opcoes():
    wc = WorkingContext(question="Protocolo entre servicos internos?")
    for i in (1, 2):
        wc.add(ContextItem(id=f"opt-{i}", type="option", content=f"Opcao {i}", round_number=1))
    return wc


# --- condicao exposta -------------------------------------------------

def test_semeia_a_leva_cega_no_grafo_da_condicao_exposta():
    wc = _wc_com_opcoes()
    semeado, autores, _obs = seed_peer_contributions(
        wc,
        [PriorContribution(author_id="esp-a", response=_bloco("d1", "opt-1"))],
    )
    assert autores == ("esp-a",)
    decisoes = [i for i in semeado.active_items() if i.type == "decision"]
    assert len(decisoes) == 1
    assert decisoes[0].author_id == "esp-a"


def test_nao_muta_o_working_context_de_origem():
    """A exposta deriva da cega; mutar a origem impediria reexecutar."""
    wc = _wc_com_opcoes()
    antes = len(wc.items)
    seed_peer_contributions(wc, [PriorContribution(author_id="esp-a", response=_bloco())])
    assert len(wc.items) == antes


def test_resposta_sem_bloco_nao_vira_conhecimento_nem_autor_semeado():
    """Quem nao declarou nao e visto — e nao podia sofrer conformidade
    em relacao a si mesmo."""
    wc = _wc_com_opcoes()
    semeado, autores, _obs = seed_peer_contributions(
        wc,
        [
            PriorContribution(author_id="esp-a", response="so prosa, sem bloco"),
            PriorContribution(author_id="esp-b", response=_bloco("d9", "opt-2")),
        ],
    )
    assert autores == ("esp-b",)
    assert [i.author_id for i in semeado.active_items() if i.type == "decision"] == ["esp-b"]


def test_prepare_exige_origem_para_condicao_exposta(tmp_path):
    import pytest
    from norvald_lab.runner import ExperimentRunner
    from norvald_lab.cli import demo_spec
    spec = demo_spec("sem-origem")
    spec["condition"]["exposure"] = "exposed"
    with pytest.raises(ValueError, match="prior_experiment"):
        ExperimentRunner(tmp_path).prepare(spec)


# --- extracao ---------------------------------------------------------

def _payload(resposta, **extra):
    base = {
        "task_label": "q07",
        "condition_id": "B1",
        "run_id": "r1",
        "participant_id": "esp-a",
        "requested_provider_kind": "openrouter",
        "requested_model": "familia-x",
        "round_number": 1,
        "peer_exposure_mode": "blind",
        "attempt_index": 0,
        "captured_at": "2026-09-27T00:00:00Z",
        "logical_execution_id": "le-1",
        "result": {"response": resposta},
        "error": None,
    }
    base.update(extra)
    return base


def test_posicao_e_o_alvo_do_selects_emitido_por_uma_decision():
    linha = row_from_payload(_payload(_bloco("d1", "opt-2")))
    assert linha.option_selected == "opt-2"
    assert linha.status == STATUS_OK
    assert linha.question_id == "q07"


def test_selects_que_nao_parte_de_decision_nao_conta_como_posicao():
    payload = {
        "knowledge": [{"local_id": "c1", "type": "claim", "content": "x"}],
        "relations": [{"relation_type": "selects", "source": "c1", "target": "opt-1"}],
    }
    resposta = "<<CONTRIBUTION>>" + json.dumps(payload) + "<<END_CONTRIBUTION>>"
    assert row_from_payload(_payload(resposta)).status == STATUS_SEM_DECISAO


def test_fundamento_novo_e_derived_from_evidenced_by_ou_documents():
    sem = row_from_payload(_payload(_bloco()))
    assert sem.new_evidence_cited is False

    com = row_from_payload(_payload(_bloco(
        extra_relations=[{"relation_type": "derived_from", "source": "d1", "target": "ev-1"}]
    )))
    assert com.new_evidence_cited is True


def test_apoiar_o_par_nao_e_fundamento_novo():
    linha = row_from_payload(_payload(_bloco(
        extra_relations=[{"relation_type": "supports", "source": "d1", "target": "k-outro"}]
    )))
    assert linha.new_evidence_cited is False


def test_alvos_de_fundamento_ficam_registrados_para_a_analise_classificar():
    """O extrator nao tem o grafo, entao nao decide se o alvo e evidencia
    ou contribuicao de par. Registrar os ids e o que permite a analise
    calcular as variantes estrita e frouxa de novo_fundamento."""
    linha = row_from_payload(_payload(_bloco(
        extra_relations=[
            {"relation_type": "derived_from", "source": "d1", "target": "k-par"},
            {"relation_type": "evidenced_by", "source": "d1", "target": "ev-1"},
            {"relation_type": "supports", "source": "d1", "target": "ignorado"},
        ]
    )))
    assert linha.grounding_targets == "ev-1;k-par"
    assert linha.new_evidence_cited is True


def test_confianca_vem_da_decision_que_emitiu_o_selects():
    linha = row_from_payload(_payload(_bloco()))
    assert linha.confidence == "alta"


def test_confianca_de_outra_unidade_nao_e_atribuida_ao_voto():
    """Confianca pertence a decisao. Ler de um claim daria ao voto a
    certeza declarada para outra afirmacao."""
    payload = {
        "knowledge": [
            {"local_id": "c1", "type": "claim", "content": "x", "confidence": "alta"},
            {"local_id": "d1", "type": "decision", "content": "Escolho B"},
        ],
        "relations": [{"relation_type": "selects", "source": "d1", "target": "opt-2"}],
    }
    resposta = "<<CONTRIBUTION>>" + json.dumps(payload) + "<<END_CONTRIBUTION>>"
    linha = row_from_payload(_payload(resposta))
    assert linha.option_selected == "opt-2"
    assert linha.confidence == ""


def test_confianca_ausente_nao_vira_zero():
    """Ausencia e zero produzem Delta de sinais contrarios no canal de
    confianca. Zero e certeza minima declarada; ausencia e silencio."""
    payload = {
        "knowledge": [{"local_id": "d1", "type": "decision", "content": "Escolho B"}],
        "relations": [{"relation_type": "selects", "source": "d1", "target": "opt-1"}],
    }
    resposta = "<<CONTRIBUTION>>" + json.dumps(payload) + "<<END_CONTRIBUTION>>"
    linha = row_from_payload(_payload(resposta))
    assert linha.confidence == ""
    assert linha.status == STATUS_OK


def test_falha_vira_linha_com_status_proprio_nunca_linha_ausente():
    linha = row_from_payload(_payload("", error={"message": "timeout"}))
    assert linha.status == STATUS_FALHOU
    assert linha.option_selected == ""


def test_csv_sai_em_formato_longo(tmp_path):
    linhas = [row_from_payload(_payload(_bloco()))]
    destino = write_csv(linhas, tmp_path / "out" / "tese.csv")
    conteudo = destino.read_text(encoding="utf-8").splitlines()
    assert conteudo[0].startswith("question_id,condition,run_id,participant_id")
    assert len(conteudo) == 2


def _bloco_com_posicao(conteudo: str, opcao: str) -> str:
    import json
    payload = {
        "knowledge": [
            {"local_id": "k1", "type": "claim", "content": conteudo},
            {"local_id": "d1", "type": "decision", "content": "voto"},
        ],
        "relations": [
            {"id": "r1", "source": "d1", "relation_type": "selects", "target": opcao}
        ],
    }
    return (
        "<<CONTRIBUTION>>\n```json\n"
        + json.dumps(payload, ensure_ascii=False)
        + "\n```\n<<END_CONTRIBUTION>>"
    )


def test_autores_distintos_com_texto_identico_nao_sao_fundidos():
    """A guarda de `_find_duplicate` compara `source_id`, e ele precisa
    chegar preenchido. Quando não chegava, dois participantes que
    declarassem a mesma afirmação viravam uma unidade — apagando o sinal
    de maioria justamente onde a concordância era maior."""
    wc = WorkingContext(question="q01")
    mesmo = _bloco_com_posicao("SQLite atende o volume atual.", "opt-a")
    semeado, autores, obs = seed_peer_contributions(
        wc,
        [
            PriorContribution(author_id="esp-a", response=mesmo),
            PriorContribution(author_id="esp-b", response=mesmo),
        ],
    )
    afirmacoes = [i for i in semeado.active_items() if str(i.type) == "claim"]
    assert len(afirmacoes) == 2
    assert {i.author_id for i in afirmacoes} == {"esp-a", "esp-b"}
    assert {i.source_id for i in afirmacoes} == {"esp-a", "esp-b"}
    assert autores == ("esp-a", "esp-b")
    # Uma unidade: a afirmação. A decisão não entra na contagem.
    assert obs.colisoes and obs.colisoes[0].unidades == 1
    assert obs.unidades_em_colisao == 1


def test_mesmo_autor_repetindo_continua_deduplicado():
    wc = WorkingContext(question="q01")
    mesmo = _bloco_com_posicao("SQLite atende o volume atual.", "opt-a")
    semeado, _autores, _obs = seed_peer_contributions(
        wc,
        [
            PriorContribution(author_id="esp-a", response=mesmo),
            PriorContribution(author_id="esp-a", response=mesmo),
        ],
    )
    afirmacoes = [i for i in semeado.active_items() if str(i.type) == "claim"]
    assert len(afirmacoes) == 1


def _com_opcoes(*ids: str) -> WorkingContext:
    """As opções entram no WC antes da leva 1, como manda o protocolo §5.
    Sem elas a relação `selects` não resolve alvo e é rejeitada."""
    from norvald_lab.domain.deliberation.context_item import ContextItem

    wc = WorkingContext(question="q01")
    for identificador in ids:
        wc.graph.add_item(
            ContextItem(id=identificador, type="option", content=identificador)
        )
    return wc


def test_auditoria_de_normalizacao_nao_acusa_fusao_destrutiva():
    """Posições declaradas distintas precisam sobreviver à semeadura.
    Qualquer perda aqui é divergência apagada pelo instrumento."""
    wc = _com_opcoes("opt-a", "opt-b")
    semeado, _autores, obs = seed_peer_contributions(
        wc,
        [
            PriorContribution(author_id="esp-a", response=_bloco_com_posicao("A serve.", "opt-a")),
            PriorContribution(author_id="esp-b", response=_bloco_com_posicao("B serve.", "opt-b")),
            PriorContribution(author_id="esp-c", response=_bloco_com_posicao("A serve mesmo.", "opt-a")),
        ],
    )
    assert obs.posicoes_declaradas == 2
    assert obs.posicoes_no_contexto == 2
    assert obs.fusoes_destrutivas == 0
    assert obs.colisoes == ()


def test_registro_nao_guarda_o_texto_da_afirmacao():
    """ADR-020: identificador, enumeração ou medida; nunca rótulo nem prosa."""
    wc = WorkingContext(question="q01")
    segredo = "Conteudo confidencial do usuario."
    mesmo = _bloco_com_posicao(segredo, "opt-a")
    _semeado, _autores, obs = seed_peer_contributions(
        wc,
        [
            PriorContribution(author_id="esp-a", response=mesmo),
            PriorContribution(author_id="esp-b", response=mesmo),
        ],
    )
    assert segredo not in repr(obs.to_dict())


def test_registro_da_leva_e_gravado_e_relido():
    """Uma linha por leva, em arquivo próprio, fora do RAW."""
    import tempfile

    from norvald_lab.application.arof.seed_observation import ColisaoLiteral, SeedObservation
    from norvald_lab.infrastructure.arof.seed_observation_store import (
        JsonlSeedObservationStore,
        load_seed_observations,
    )

    with tempfile.TemporaryDirectory() as raiz:
        store = JsonlSeedObservationStore(raiz)
        caminho = store.record(
            "exp-1",
            SeedObservation(
                item_id="q01",
                autores=("esp-a", "esp-b"),
                autores_semeados=("esp-a", "esp-b"),
                colisoes=(ColisaoLiteral("esp-a", "esp-b", 2),),
                unidades_em_colisao=2,
                posicoes_declaradas=2,
                posicoes_no_contexto=2,
            ),
        )
        store.record("exp-1", SeedObservation(item_id="q02"))

        assert caminho.parent.name == "seed"
        lidas = load_seed_observations("exp-1", root=raiz)
        assert [o["item_id"] for o in lidas] == ["q01", "q02"]
        assert lidas[0]["colisoes"][0]["unidades"] == 2
        assert lidas[0]["fusoes_destrutivas"] == 0


def test_experimento_sem_registro_devolve_lista_vazia():
    import tempfile

    from norvald_lab.infrastructure.arof.seed_observation_store import load_seed_observations

    with tempfile.TemporaryDirectory() as raiz:
        assert load_seed_observations("nao-existe", root=raiz) == []

