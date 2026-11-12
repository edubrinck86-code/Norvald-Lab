from dataclasses import dataclass, field
from norvald_lab.vendor.norvald_execution.contracts.sampling import ResolvedSampling
from typing import Any, Dict, List, Optional

from norvald_lab.vendor.norvald_execution.contracts.execution_context import ExecutionContext
from norvald_lab.vendor.norvald_execution.contracts.tool_contract import ToolCall


@dataclass
class ExecutionRequest:
    agent_id: str
    instructions: str
    context: ExecutionContext
    # Prefixo estável do prompt, idêntico entre participantes e rodadas
    # (evidências, formato da Contribution, instruções de ferramenta).
    # Fica separado porque o cache dos providers é por PREFIXO: com o
    # trecho variável na frente, o prefixo nunca casa e o bloco grande é
    # recobrado inteiro a cada turno.
    shared_instructions: str = ""
    # Estável dentro da leva: o Working Context é idêntico para todos os
    # especialistas de uma mesma leva, mas muda a cada rodada.
    #
    # Existe como campo próprio porque o cache dos providers é por
    # prefixo e precisa de três faixas, não duas: o que não muda entre
    # rodadas, o que não muda dentro da leva, e o que varia por
    # participante. Sem a faixa do meio, o WC ficava na mensagem do
    # usuário e era cobrado cheio nas cinco requisições da leva.
    wave_instructions: str = ""
    user_message: Optional[str] = None
    attachments: List["AttachmentPayload"] = field(default_factory=list)
    reasoning_effort: str = "off"
    # Empresa que serve o modelo atrás de um roteador (OpenRouter). 11/11/2026: na
    # coleta confirmatória do Δ_herd, as "5 cópias" do Gemma vieram de KT e NextBit
    # na mesma pergunta; sem fixar, cópias deixam de ser cópias. None = roteamento livre.
    upstream_provider: Optional[str] = None
    # Modelo opcionalmente resolvido pela camada de apresentação.
    # Quando ausente, o AgentRegistry continua sendo a fonte padrão.
    model: Optional[str] = None
    # Já resolvida para este provider/modelo: o orquestrador não decide
    # o que é aceitável, só entrega o que a política aprovou.
    sampling: Optional["ResolvedSampling"] = None
    allow_tools: bool = False
    tools: List["ToolDefinition"] = field(default_factory=list)
    #: Teto de chamadas de ferramenta neste turno.
    #:
    #: Viaja no contrato em vez de o laço importar a regra: o
    #: AgentOrchestrator não deve conhecer rodadas nem fases do Studio, e
    #: quem sabe quanto o turno permite é quem o montou. `None` significa conclusão natural; qualquer número é um limite
    #: explícito aplicado pela configuração/experimento.
    max_tool_calls: Optional[int] = None
    #: Teto de ciclos de decisão ferramenta -> resultado -> nova decisão.
    #:
    #: `None` significa conclusão natural.
    max_tool_iterations: Optional[int] = None
    tool_exchanges: List["ToolExchange"] = field(default_factory=list)


@dataclass
class ExecutionResult:
    content: str
    tokens: int
    duration_seconds: float
    provider: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    reasoning: Optional[str] = None
    tool_calls: List["ToolCall"] = field(default_factory=list)

