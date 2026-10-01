"""Fumaça do C3: registry, observador e orquestrador — e a chave de
execução já generalizada."""
import pytest

from norvald_lab.vendor.norvald_execution.contracts.execution_context import ExecutionContext
from norvald_lab.vendor.norvald_execution.contracts.execution_contracts import ExecutionRequest
from norvald_lab.vendor.norvald_execution.contracts.tool_ports import ToolLoopPort, ToolRuntimePort
from norvald_lab.vendor.norvald_execution.orchestration.agent_orchestrator import AgentOrchestrator
from norvald_lab.vendor.norvald_execution.orchestration.agent_registry import AgentRegistry
from norvald_lab.vendor.norvald_execution.orchestration.execution_observer import NullExecutionObserver


def _request(metadata=None, agent_id="a1"):
    return ExecutionRequest(
        agent_id=agent_id,
        instructions="faça",
        context=ExecutionContext(objective="obj", working_context="", metadata=metadata or {}),
        user_message="oi",
    )


def _orquestrador(**kwargs):
    return AgentOrchestrator(AgentRegistry(), **kwargs)


def test_chave_usa_o_id_declarado_pelo_dominio():
    assert _orquestrador()._execution_id_of(_request({"execution_id": "x-1"})) == "x-1"


def test_chave_junta_o_escopo_declarado_sem_conhecer_as_partes():
    escopo = {"session_id": "s1", "round": 2, "participant_id": "p3"}
    assert _orquestrador()._execution_id_of(_request({"execution_scope": escopo})) == "s1:2:p3"


def test_escopo_de_outro_dominio_funciona_igual():
    """Um build não tem rodada nem participante — tem tarefa e tentativa."""
    escopo = {"build_id": "build-7", "task_id": "t1", "attempt": 2}
    assert _orquestrador()._execution_id_of(_request({"execution_scope": escopo})) == "build-7:t1:2"


def test_auditoria_recebe_as_partes_nomeadas_nao_a_chave():
    """Juntar as partes numa string mataria a consulta por parte: com
    `s1:2:p3` não se pergunta "tudo da rodada 2"."""
    escopo = {"session_id": "s1", "round": 2, "participant_id": "p3"}
    assert _orquestrador()._scope_of(_request({"execution_scope": escopo})) == escopo


def test_sem_escopo_declarado_a_auditoria_recebe_vazio_nao_invencao():
    assert _orquestrador()._scope_of(_request({})) == {}


def test_evento_guarda_o_escopo_do_dominio_que_for():
    from norvald_lab.vendor.norvald_execution.orchestration.execution_observer import ExecutionEvent

    evento = ExecutionEvent(
        event_id="e1", event_type="llm.request.completed", agent_id="a1",
        provider="p", model="m", status="ok",
        scope={"build_id": "build-7", "task_id": "t1"},
    )
    assert evento.scope["task_id"] == "t1"


def test_sem_declaracao_cai_no_agente():
    assert _orquestrador()._execution_id_of(_request({}, agent_id="revisor")) == "revisor"


def test_chave_nao_conhece_vocabulario_de_deliberacao():
    fonte = __import__("inspect").getsource(AgentOrchestrator._execution_id_of)
    corpo = fonte.split('"""')[-1]
    for termo in ("round", "participant_id", "session_id"):
        assert termo not in corpo


def test_sem_laco_de_ferramentas_nao_ha_ferramentas():
    class RuntimeQualquer:
        def definitions(self):
            return ["ferramenta"]

        def for_execution_context(self, execution_context):
            return self

    orquestrador = _orquestrador(tool_registry=RuntimeQualquer())
    assert orquestrador._tools_for(_request(), provider=object()) == []


def test_portas_sao_contratos_estruturais():
    class Runtime:
        def definitions(self):
            return []

        def for_execution_context(self, execution_context):
            return self

    assert isinstance(Runtime(), ToolRuntimePort)
    assert hasattr(ToolLoopPort, "execute_with_tools")


def test_observador_nulo_e_o_padrao():
    assert isinstance(_orquestrador().execution_observer, NullExecutionObserver)

