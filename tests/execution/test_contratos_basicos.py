"""Fumaça do C1: os contratos existem, são independentes de domínio e
o pacote não conhece o Studio."""
import pathlib

from norvald_lab.vendor.norvald_execution.contracts.execution_contracts import ExecutionRequest, ExecutionResult
from norvald_lab.vendor.norvald_execution.contracts.execution_context import ExecutionContext
from norvald_lab.vendor.norvald_execution.contracts.provider_contract import LLMProvider
from norvald_lab.vendor.norvald_execution.contracts.tool_contract import ToolCall, ToolDefinition, ToolResult, clamp_limit


def test_pacote_nao_importa_o_studio():
    """Procura import, não menção: a palavra pode aparecer em prosa
    ("reiniciar o backend"), mas nenhum módulo daqui pode depender do
    Studio."""
    raiz = pathlib.Path(__file__).resolve().parent.parent / "src"
    ofensores = [
        f"{arquivo}:{numero}"
        for arquivo in raiz.rglob("*.py")
        for numero, linha in enumerate(arquivo.read_text(encoding="utf-8").splitlines(), 1)
        if linha.lstrip().startswith(("import backend", "from backend"))
    ]
    assert ofensores == []


def test_contrato_de_ferramenta_nao_carrega_catalogo():
    import norvald_lab.vendor.norvald_execution.contracts.tool_contract as contrato
    nomes = [n for n in dir(contrato) if n.isupper()]
    assert "SEARCH_CONTEXT" not in nomes
    assert "READ_CONTRIBUTION" not in nomes
    assert "MAX_DOCUMENT_CHARS" in nomes


def test_requisicao_de_execucao_se_monta():
    request = ExecutionRequest(
        agent_id="a1",
        instructions="faça",
        context=ExecutionContext(objective="obj", working_context=""),
        user_message="oi",
    )
    assert request.agent_id == "a1"
    assert request.context.to_dict()["objective"] == "obj"


def test_resultado_de_execucao_se_monta():
    resultado = ExecutionResult(
        content="saída", tokens=10, duration_seconds=0.5, provider="p", model="m"
    )
    assert (resultado.content, resultado.tool_calls) == ("saída", [])


def test_provider_e_um_contrato():
    assert hasattr(LLMProvider, "execute")


def test_ferramenta_ida_e_volta():
    call = ToolCall(call_id="c1", name="qualquer", arguments={"x": 1})
    result = ToolResult(call_id=call.call_id, name=call.name, content="pronto")
    definicao = ToolDefinition(name="qualquer", description="d", parameters={"type": "object"})
    assert (definicao.name, result.call_id, result.is_error) == ("qualquer", "c1", False)


def test_limite_de_resultados_e_contido():
    assert clamp_limit("99") == 10
    assert clamp_limit(None) == 5

