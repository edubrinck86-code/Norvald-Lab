"""O mecanismo do runtime: executa o que foi registrado, sem saber de
domínio nenhum. Os ganchos existem para quem precisar; quem não precisa
tem um runtime que funciona sem estender nada."""
from norvald_lab.vendor.norvald_execution.contracts.tool_contract import ToolCall, ToolDefinition, ToolProvenance
from norvald_lab.vendor.norvald_execution.tools.registered_tool import RegisteredTool
from norvald_lab.vendor.norvald_execution.tools.tool_permission import ToolPermission
from norvald_lab.vendor.norvald_execution.tools.tool_runtime import ToolRuntime


def _ferramenta(nome="somar", handler=None, **kwargs):
    return RegisteredTool(
        definition=ToolDefinition(name=nome, description="d", parameters={"type": "object"}),
        handler=handler or (lambda args: "pronto"),
        **kwargs,
    )


def _runtime(**kwargs):
    runtime = ToolRuntime(**kwargs)
    runtime.register(_ferramenta())
    return runtime


def _chamada(nome="somar", **argumentos):
    return ToolCall(call_id="c1", name=nome, arguments=argumentos)


def test_executa_o_que_foi_registrado():
    runtime = _runtime()
    assert runtime.execute(_chamada()).content == "pronto"


def test_ferramenta_desconhecida_e_recusada_com_motivo():
    resultado = _runtime().execute(_chamada("inexistente"))
    assert resultado.is_error is True
    assert "não está disponível" in resultado.content


def test_falha_da_ferramenta_vira_resultado_de_erro_nao_excecao():
    def explode(args):
        raise RuntimeError("quebrou")

    runtime = ToolRuntime()
    runtime.register(_ferramenta(handler=explode))
    resultado = runtime.execute(_chamada())
    assert (resultado.is_error, "quebrou" in resultado.content) == (True, True)


def test_permissao_declarada_para_outra_ferramenta_nega_o_silencio():
    runtime = _runtime(permissions={"outra": ToolPermission("outra")})
    assert runtime.execute(_chamada()).is_error is True


def test_sem_permissao_declarada_tudo_que_foi_registrado_vale():
    assert _runtime().allowed("somar") is True


def test_permissao_desligada_bloqueia():
    runtime = _runtime(permissions={"somar": ToolPermission("somar", "disabled")})
    assert runtime.allowed("somar") is False
    assert "somar" not in runtime.tool_names()


def test_definicoes_so_oferecem_o_permitido():
    runtime = _runtime(permissions={"somar": ToolPermission("somar", "disabled")})
    assert runtime.definitions() == []


def test_toda_execucao_fica_registrada_inclusive_a_recusada():
    runtime = _runtime()
    runtime.execute(_chamada())
    runtime.execute(_chamada("inexistente"))
    assert [(e.tool_name, e.is_error) for e in runtime.executions] == [("somar", False), ("inexistente", True)]


def test_artefato_so_e_extraido_de_ferramenta_que_produz_artefato():
    uuid = "3f2504e0-4f89-11d3-9a0c-0305e82c3301"
    runtime = ToolRuntime()
    runtime.register(_ferramenta(nome="criar", handler=lambda a: f"criado {uuid}", produces_artifact=True))
    runtime.register(_ferramenta(nome="ler", handler=lambda a: f"contém {uuid}"))
    runtime.execute(_chamada("criar"))
    runtime.execute(_chamada("ler"))
    assert [e.artifact_id for e in runtime.executions] == [uuid, None]


def test_eventos_sao_emitidos_para_quem_escuta():
    eventos = []
    runtime = _runtime(on_event=lambda nome, dados: eventos.append(nome))
    runtime.execute(_chamada())
    assert eventos == ["tool.started", "tool.completed"]


def test_ganchos_nao_fazem_nada_por_padrao():
    runtime = ToolRuntime()
    assert runtime.execute_contextual(_chamada()) is None
    assert runtime.make_preflight_call(object()) is None
    assert runtime.operational_tools() == set()
    assert runtime.always_allowed() == set()


def test_dominio_pode_resolver_ferramenta_sem_handler():
    class RuntimeDeDominio(ToolRuntime):
        def execute_contextual(self, call):
            if call.name == "consultar-base":
                return "resposta da base", [ToolProvenance(source_id="base", source_type="documento")]
            return None

    resultado = RuntimeDeDominio().execute(_chamada("consultar-base"))
    assert resultado.content == "resposta da base"
    assert resultado.provenance[0].source_id == "base"


def test_dominio_pode_declarar_ferramenta_que_a_permissao_nao_desliga():
    class RuntimeComObrigatoria(ToolRuntime):
        def always_allowed(self):
            return {"varredura"}

    runtime = RuntimeComObrigatoria(permissions={"varredura": ToolPermission("varredura", "disabled")})
    assert runtime.allowed("varredura") is True


def test_recorte_por_contexto_preserva_ferramentas_e_permissoes():
    runtime = _runtime(permissions={"somar": ToolPermission("somar")})
    recortado = runtime.for_execution_context({"qualquer": "coisa"})
    assert recortado.tool_names() == ["somar"]
    assert recortado.executions == []

