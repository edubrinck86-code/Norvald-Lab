"""Fumaça do C4: o laço executa ferramentas sem saber quais são.

Cada generalização tem um teste que mostra o mesmo mecanismo servindo
dois domínios diferentes.
"""
from norvald_lab.vendor.norvald_execution.contracts.execution_context import ExecutionContext
from norvald_lab.vendor.norvald_execution.contracts.execution_contracts import ExecutionRequest
from norvald_lab.vendor.norvald_execution.contracts.tool_contract import ToolCall
from norvald_lab.vendor.norvald_execution.tools import tool_loop
from norvald_lab.vendor.norvald_execution.tools.registered_tool import RegisteredTool
from norvald_lab.vendor.norvald_execution.tools.tool_permission import AVAILABILITY_LEVELS, ToolPermission
from norvald_lab.vendor.norvald_execution.tools.tool_execution import ToolExecution


def _request(metadata=None, agent_id="a1"):
    return ExecutionRequest(
        agent_id=agent_id,
        instructions="faça",
        context=ExecutionContext(objective="obj", working_context="", metadata=metadata or {}),
        user_message="oi",
    )


class RuntimeDeDominio:
    """Runtime mínimo: declara preflight e ferramentas operacionais."""

    def __init__(self, preflight=None, operacionais=()):
        self._preflight = preflight
        self._operacionais = operacionais

    def make_preflight_call(self, request):
        return self._preflight

    def operational_tools(self):
        return self._operacionais


class RuntimeSemNada:
    """Runtime que não declara nada — o caso de quem só tem ferramentas."""


def test_preflight_e_declarado_pelo_dominio():
    chamada = ToolCall(call_id="p1", name="consultar-base", arguments={})
    runtime = RuntimeDeDominio(preflight=chamada)
    assert tool_loop._preflight_call(_request(), runtime) is chamada


def test_quem_nao_declara_preflight_nao_tem_preflight():
    assert tool_loop._preflight_call(_request(), RuntimeSemNada()) is None


def test_ferramentas_operacionais_vem_do_runtime():
    runtime = RuntimeDeDominio(operacionais={"varredura"})
    chamadas = [
        ToolCall(call_id="1", name="varredura", arguments={}),
        ToolCall(call_id="2", name="pesquisa-web", arguments={}),
    ]
    assert tool_loop._chargeable_tool_calls(chamadas, runtime) == 1


def test_sem_runtime_toda_chamada_conta():
    chamadas = [ToolCall(call_id="1", name="qualquer", arguments={})]
    assert tool_loop._chargeable_tool_calls(chamadas) == 1


def test_varredura_so_existe_para_quem_a_tem():
    assert tool_loop._usa_varredura(RuntimeSemNada()) is False


def test_perfil_de_paciencia_vem_do_metadata_nao_do_nome_do_agente():
    assert tool_loop._stall_profile(_request()) == tool_loop.DEFAULT_STALL_PROFILE
    assert tool_loop._stall_profile(_request({"stall_profile": "assistant"})) == "assistant"
    assert tool_loop._stall_profile(_request(agent_id="studio-assistant")) == tool_loop.DEFAULT_STALL_PROFILE


def test_motivo_de_parada_segue_o_perfil():
    assert tool_loop._stall_reason(_request({"stall_profile": "build"})) == "build_no_progress"


def test_teto_de_paciencia_tem_padrao_para_perfil_nao_declarado():
    assert tool_loop._stall_limit(_request({"stall_profile": "inexistente"})) == tool_loop.DEFAULT_MAX_NO_PROGRESS_CYCLES


def test_permissao_tem_tres_niveis():
    assert AVAILABILITY_LEVELS == ("disabled", "available", "required")
    assert ToolPermission("x", "disabled").enabled is False


def test_ferramenta_registrada_guarda_definicao_e_handler():
    from norvald_lab.vendor.norvald_execution.contracts.tool_contract import ToolDefinition

    tool = RegisteredTool(
        definition=ToolDefinition(name="somar", description="d", parameters={"type": "object"}),
        handler=lambda args: "3",
    )
    assert tool.handler({}) == "3"
    assert tool.produces_artifact is False


def test_execucao_vira_registro_serializavel():
    registro = ToolExecution(
        tool_name="somar", call_id="c1", arguments={}, is_error=False, duration_seconds=0.12
    )
    assert registro.to_dict()["duration_seconds"] == 0.12

