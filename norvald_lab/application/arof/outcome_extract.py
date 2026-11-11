"""Extrai do RAW a tabela tidy da tese: uma linha por (pergunta, participante, condição).

Opera sobre o RAW, não sobre o grafo. O RAW é o artefato durável — o
grafo de uma condição experimental é descartado depois da execução, e
reconstruí-lo para analisar amarraria a análise ao runtime. Reprocessar
com critério novo precisa ser possível sem chamar provider nenhum.

As três derivadas da tese — mudou, mudou sem fundamento novo,
convergência — **não** são calculadas aqui. Aqui só se extrai o fato por
execução; a comparação entre condições acontece na análise, sobre a
tabela. Calcular a derivada na extração congelaria o critério dentro do
dado e impediria revisá-lo depois.
"""

from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from norvald_lab.application.arof.outcome_validation import validation_from_payload
from norvald_lab.domain.deliberation.contribution import Contribution

# Relações que declaram fundamento novo. Não inclui `selects`, que é a
# própria posição, nem `supports`/`challenges`, que apontam para
# afirmação de par — apoiar o outro não é trazer fundamento.
RELACOES_DE_FUNDAMENTO = frozenset({"derived_from", "evidenced_by", "documents"})

STATUS_OK = "ok"
STATUS_SEM_DECISAO = "no_decision"
STATUS_FALHOU = "failed"


@dataclass(frozen=True)
class OutcomeRow:
    """Uma execução observada, reduzida ao que a análise precisa."""

    question_id: str
    condition: str
    run_id: str
    participant_id: str
    provider: str
    model: str
    round_number: int
    peer_exposure_mode: str
    status: str
    option_selected: str
    confidence: str
    new_evidence_cited: bool
    grounding_targets: str
    relations_out: str
    attempt_index: int
    captured_at: str
    # Leitura do validador, ao lado da leitura do bloco declarado acima.
    # Acréscimo do Lab (docs/MIGRACAO.md, 2026-10-04); as colunas
    # anteriores não mudam de definição. Vazio é ausência de leitura — o
    # RAW não trazia o contexto da execução —, nunca zero. Ver
    # `outcome_validation.OutcomeValidation`.
    validation_code: str = ""
    items_declared: str = ""
    items_accepted: str = ""
    relations_declared: str = ""
    relations_accepted: str = ""
    option_accepted: str = ""
    grounding_targets_accepted: str = ""
    rejected_reasons: str = ""


def _texto_da_resposta(payload: Mapping[str, Any]) -> str:
    resultado = payload.get("result")
    if not isinstance(resultado, Mapping):
        return ""
    for chave in ("response", "content", "text", "output"):
        valor = resultado.get(chave)
        if isinstance(valor, str) and valor.strip():
            return valor
    return ""


def _decisao_selecionadora(contribuicao: Contribution) -> tuple[Any | None, str]:
    """A unidade `decision` que emitiu `selects`, e o alvo dela.

    Posição é isso e só isso. Ler a opção do texto seria julgamento
    semântico — exatamente o que o desenho evita.

    Devolve a unidade junto com o alvo porque a confiança declarada
    pertence à decisão, e lê-la de qualquer outra unidade seria atribuir
    ao voto a certeza de outra afirmação.
    """
    decisoes = {
        item.local_id: item
        for item in contribuicao.knowledge
        if str(item.type) == "decision"
    }
    for relacao in contribuicao.relations:
        if str(relacao.relation_type) != "selects":
            continue
        unidade = decisoes.get(str(relacao.source))
        if unidade is not None:
            return unidade, str(relacao.target)
    return None, ""


CONFIANCA_EM_INGLES = {"high": "alta", "medium": "média", "low": "baixa"}


def _confianca_declarada(decisao: Any | None) -> str:
    """A confiança da decisão, como texto, ou vazio quando não declarada.

    Ausência não vira zero. `confidence` é campo opcional da
    contribuição, e zero significaria certeza mínima declarada — o
    oposto de não ter dito nada. Os dois produzem Δ de sinais contrários
    na análise do canal de confiança.
    """
    if decisao is None:
        return ""
    valor = getattr(decisao, "confidence", None)
    if valor is None:
        return ""
    texto = str(valor).strip()
    # Coleta em inglês (11/11/2026) pede high/medium/low. Normalizar para os
    # valores canônicos em português mantém uma única escala na análise;
    # qualquer outro texto passa como veio, como sempre foi.
    return CONFIANCA_EM_INGLES.get(texto.lower(), texto)


def _alvos_de_fundamento(contribuicao: Contribution) -> tuple[str, ...]:
    """Os alvos das relações de fundamento declaradas na contribuição.

    O extrator lê o RAW e não tem o grafo, então não classifica o alvo.
    Registrar os ids é o que permite à análise decidir depois, contra o
    Working Context, se o fundamento aponta para evidência ou para a
    contribuição de um par — que é a diferença entre as variantes
    estrita e frouxa de `novo_fundamento` (`TESE-001` §6).
    """
    return tuple(
        sorted(
            {
                str(relacao.target)
                for relacao in contribuicao.relations
                if str(relacao.relation_type) in RELACOES_DE_FUNDAMENTO
            }
        )
    )


def row_from_payload(payload: Mapping[str, Any], *, condition: str = "") -> OutcomeRow:
    """Converte um registro RAW numa linha da tabela.

    Falha de execução vira linha com status próprio, nunca linha
    ausente: descartar quem não respondeu enviesa o Δ na direção de quem
    responde sempre.
    """
    erro = payload.get("error")
    resposta = _texto_da_resposta(payload)
    contribuicao = Contribution.parse(
        resposta,
        author_id=str(payload.get("participant_id") or ""),
        round_number=int(payload.get("round_number") or 1),
    )
    decisao, opcao = _decisao_selecionadora(contribuicao)
    alvos = _alvos_de_fundamento(contribuicao)

    if erro or not resposta.strip():
        status = STATUS_FALHOU
    elif not opcao:
        status = STATUS_SEM_DECISAO
    else:
        status = STATUS_OK

    validacao = validation_from_payload(
        payload, response=resposta, grounding_relations=RELACOES_DE_FUNDAMENTO
    )

    return OutcomeRow(
        # A pergunta é a tarefa do experimento: uma task_label por
        # pergunta é o que torna a tabela pareável entre condições.
        question_id=str(payload.get("task_label") or payload.get("task_id") or ""),
        condition=condition or str(payload.get("condition_id") or ""),
        run_id=str(payload.get("run_id") or ""),
        participant_id=str(payload.get("participant_id") or ""),
        provider=str(payload.get("requested_provider_kind") or ""),
        model=str(payload.get("requested_model") or ""),
        round_number=int(payload.get("round_number") or 1),
        peer_exposure_mode=str(payload.get("peer_exposure_mode") or ""),
        status=status,
        option_selected=opcao,
        confidence=_confianca_declarada(decisao),
        new_evidence_cited=bool(alvos),
        grounding_targets=";".join(alvos),
        relations_out=";".join(
            sorted({str(r.relation_type) for r in contribuicao.relations})
        ),
        attempt_index=int(payload.get("attempt_index") or 0),
        captured_at=str(payload.get("captured_at") or ""),
        **asdict(validacao),
    )


def rows_from_raw(
    paths: Sequence[str | Path],
    *,
    experiment_id: str | None = None,
) -> tuple[OutcomeRow, ...]:
    """Lê os JSONL do RAW e devolve as linhas, na ordem dos arquivos.

    Só a tentativa final de cada execução lógica entra: um replan não é
    um especialista independente, e contá-lo duplicaria a observação.
    """
    from norvald_lab.application.arof.dataset import ReplayFilter
    from norvald_lab.infrastructure.arof.dataset_store import replay_jsonl

    resultado = replay_jsonl(
        [Path(p) for p in paths],
        filters=ReplayFilter(experiment_id=experiment_id) if experiment_id else None,
    )

    ultima_por_execucao: dict[str, Mapping[str, Any]] = {}
    for registro in resultado.records:
        payload = registro.payload
        chave = str(payload.get("logical_execution_id") or registro.line_number)
        anterior = ultima_por_execucao.get(chave)
        if anterior is None or int(payload.get("attempt_index") or 0) >= int(
            anterior.get("attempt_index") or 0
        ):
            ultima_por_execucao[chave] = payload

    return tuple(row_from_payload(payload) for payload in ultima_por_execucao.values())


def write_csv(rows: Iterable[OutcomeRow], destination: str | Path) -> Path:
    """Grava a tabela tidy. Formato longo, uma linha por observação —
    é o que pandas, R e planilha leem sem transformação."""
    caminho = Path(destination)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    linhas = list(rows)
    with caminho.open("w", encoding="utf-8", newline="") as arquivo:
        escritor = csv.DictWriter(
            arquivo, fieldnames=list(OutcomeRow.__dataclass_fields__)
        )
        escritor.writeheader()
        for linha in linhas:
            escritor.writerow(asdict(linha))
    return caminho

