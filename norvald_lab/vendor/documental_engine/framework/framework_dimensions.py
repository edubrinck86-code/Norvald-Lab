"""Baseline dimensional do Norvald Universal Document Framework.

Fonte: UDF §7, "Dimensões candidatas iniciais". O próprio documento marca
a lista como **não congelante** (§7) e define que a profundidade não é
dada pelo Framework, e sim pela necessidade documental (§4). Por isso o
baseline nasceu plano: as subdimensões nasceriam quando houver
necessidade documental real, não antes.

Essa necessidade apareceu: a decisão registrada abaixo em
`_REQUIRED_DIMENSION_IDS` e em `SECURITY_SUBDIMENSIONS` vem de decisão
explícita de Eduardo (não inferência), amarrada ao modo documental
estrito (Documental Conformance Engine) — exatamente a condição que o
comentário anterior deste arquivo dizia faltar para sair de `UNKNOWN`
sem virar invenção. `UNKNOWN`/`applicability` genérica continua correta
para as dimensões que ninguém ainda decidiu classificar; as que já
foram decididas usam o valor real.

Sem este baseline o `DimensionRegistry` nunca era instanciado em
produção — `validate_and_convert` recebia `dimension_registry=None` e
pulava a validação inteira, e nenhum especialista tinha como saber que
dimensões existiam para declarar. Todo item entrava com
`dimension_id=None`.

`layer` não vem daqui: o UDF menciona "camadas" apenas como quantidade
não predeterminada (§1) e como o modelo de engenharia de 10 camadas que
ele mesmo manda não copiar literalmente (§8). Enquanto não houver
definição, o campo não é pedido ao especialista.
"""

from __future__ import annotations

from norvald_lab.vendor.documental_engine.framework.dimension import Dimension
from norvald_lab.vendor.documental_engine.framework.dimension_registry import DimensionRegistry

# UDF §7 — na ordem do documento. Não alterar: é a lista original,
# citada por outros testes pelo próprio tamanho. Subdimensões novas
# entram em constantes separadas (ver SECURITY_SUBDIMENSIONS), nunca
# aqui dentro — isto preserva "UDF §7" como fonte exata desta tupla.
BASELINE_DIMENSIONS = (
    "Identity", "Purpose", "Scope", "Context", "Authority", "Ownership",
    "Actors", "Definitions", "Semantics", "Requirements", "Constraints",
    "Assumptions", "Dependencies", "Relationships", "References",
    "Provenance", "Evidence", "Criteria", "Validation", "State",
    "Versioning", "Change", "Impact", "Lifecycle", "Governance", "Risk",
    "Security", "Privacy", "Data", "Information", "Architecture",
    "Components", "Capabilities", "Interfaces", "Contracts", "APIs",
    "Workflows", "Processes", "Rules", "Operations", "Infrastructure",
    "Networks", "Performance", "Reliability", "Resilience",
    "Observability", "Testing", "Verification", "Deployment", "Migration",
    "Decommissioning", "Strategy", "Business", "Finance", "Legal",
    "Compliance", "Sustainability", "Human Factors", "UX", "Accessibility",
)

# Decisão de Eduardo (2026-09-13): estas, por nome de dimensão do
# baseline, são REQUIRED em qualquer Template do modo documental —
# todo documento precisa endereçar o conceito, mesmo que a subárvore
# inteira debaixo dele continue CONDITIONAL. Todas as outras 45 do
# baseline são CONDITIONAL: obrigatórias dependendo do tipo de
# documento, nunca sempre nem nunca.
_REQUIRED_DIMENSION_NAMES = frozenset({
    "Identity", "Purpose", "Scope", "Context", "Definitions", "Authority",
    "Constraints", "References", "Provenance", "Relationships", "Evidence",
    "State", "Versioning", "Lifecycle", "Security",
})


def dimension_id_of(name: str) -> str:
    """Identificador estável a partir do nome do Framework.

    "Human Factors" -> "human-factors". O nome permanece no `name`, que é
    o que aparece para o especialista.
    """
    return name.strip().lower().replace(" ", "-")


# Árvore de Segurança, aprovada por Eduardo em rodada dedicada — rascunho
# original do próprio UDF (§ exemplo de profundidade: Security ->
# Authentication -> Credential Management -> Rotation -> Frequency),
# aprofundado com justificativa real por nó, não profundidade por
# profundidade. Todas CONDITIONAL — nenhuma folha é sempre obrigatória;
# apenas o pai `security` (já no baseline acima) é REQUIRED.
#
# Formato de cada item: (id, name, parent_id).
SECURITY_SUBDIMENSIONS = (
    ("authentication", "Authentication", "security"),
    ("credential-management", "Credential Management", "authentication"),
    ("rotation", "Rotation", "credential-management"),
    ("frequency", "Frequency", "rotation"),
    ("fixed-interval", "Fixed Interval", "frequency"),
    ("adaptive-interval", "Adaptive Interval", "frequency"),
    ("trigger", "Trigger", "rotation"),
    ("compromise-detected", "Compromise Detected", "trigger"),
    ("policy-expiry", "Policy Expiry", "trigger"),
    ("manual-request", "Manual Request", "trigger"),
    ("authorization", "Authorization", "security"),
    ("role-based-access", "Role-Based Access", "authorization"),
    ("role-definition", "Role Definition", "role-based-access"),
    ("role-assignment", "Role Assignment", "role-based-access"),
    ("role-hierarchy", "Role Hierarchy", "role-based-access"),
    ("permission-scope", "Permission Scope", "authorization"),
    ("resource-scope", "Resource Scope", "permission-scope"),
    ("action-scope", "Action Scope", "permission-scope"),
    ("time-scope", "Time Scope", "permission-scope"),
    ("data-minimization", "Data Minimization", "privacy"),
    ("collection-limits", "Collection Limits", "data-minimization"),
    ("retention-limits", "Retention Limits", "data-minimization"),
    ("consent-management", "Consent Management", "privacy"),
    ("consent-capture", "Consent Capture", "consent-management"),
    ("consent-withdrawal", "Consent Withdrawal", "consent-management"),
    ("audit-trail", "Audit Trail", "security"),
    ("log-retention", "Log Retention", "audit-trail"),
    ("retention-duration", "Retention Duration", "log-retention"),
    ("retention-storage", "Retention Storage", "log-retention"),
    ("tamper-evidence", "Tamper Evidence", "audit-trail"),
    ("integrity-verification", "Integrity Verification", "tamper-evidence"),
    ("immutability-guarantee", "Immutability Guarantee", "tamper-evidence"),
)


# As 9 árvores abaixo aprofundam os segmentos aprovados por Eduardo na
# mesma rodada de Segurança — não vêm de rascunho pronto do UDF como
# Segurança veio; são construção nossa. Mesma disciplina: nós
# específicos e concretos, nunca genérico "catch-all" só para parecer
# completo — cada folha precisa responder "que necessidade documental
# isto cobre" sozinha, não em bloco.

FUNDAMENTOS_SUBDIMENSIONS = (
    ("primary-purpose", "Primary Purpose", "purpose"),
    ("secondary-purpose", "Secondary Purpose", "purpose"),
    ("in-scope", "In Scope", "scope"),
    ("out-of-scope", "Out of Scope", "scope"),
    ("scope-boundary", "Scope Boundary", "scope"),
    ("organizational-context", "Organizational Context", "context"),
    ("technical-context", "Technical Context", "context"),
    ("regulatory-context", "Regulatory Context", "context"),
    ("approval-authority", "Approval Authority", "authority"),
    ("change-authority", "Change Authority", "authority"),
    ("business-owner", "Business Owner", "ownership"),
    ("technical-owner", "Technical Owner", "ownership"),
    ("primary-actors", "Primary Actors", "actors"),
    ("secondary-actors", "Secondary Actors", "actors"),
    ("external-actors", "External Actors", "actors"),
    ("term-glossary", "Term Glossary", "definitions"),
    ("acronym-glossary", "Acronym Glossary", "definitions"),
    ("controlled-vocabulary", "Controlled Vocabulary", "semantics"),
    ("ambiguity-resolution", "Ambiguity Resolution", "semantics"),
)

NORMATIVO_SUBDIMENSIONS = (
    ("technical-constraints", "Technical Constraints", "constraints"),
    ("regulatory-constraints", "Regulatory Constraints", "constraints"),
    ("budget-constraints", "Budget Constraints", "constraints"),
    ("timeline-constraints", "Timeline Constraints", "constraints"),
    ("validated-assumptions", "Validated Assumptions", "assumptions"),
    ("unvalidated-assumptions", "Unvalidated Assumptions", "assumptions"),
    ("upstream-dependencies", "Upstream Dependencies", "dependencies"),
    ("downstream-dependencies", "Downstream Dependencies", "dependencies"),
    ("external-dependencies", "External Dependencies", "dependencies"),
    ("normative-references", "Normative References", "references"),
    ("informative-references", "Informative References", "references"),
    ("source-attribution", "Source Attribution", "provenance"),
    ("derivation-chain", "Derivation Chain", "provenance"),
    ("direct-evidence", "Direct Evidence", "evidence"),
    ("indirect-evidence", "Indirect Evidence", "evidence"),
    ("acceptance-criteria", "Acceptance Criteria", "criteria"),
    ("exit-criteria", "Exit Criteria", "criteria"),
    ("validation-method", "Validation Method", "validation"),
    ("validation-owner", "Validation Owner", "validation"),
)

GOVERNANCA_SUBDIMENSIONS = (
    ("regulatory-compliance", "Regulatory Compliance", "compliance"),
    ("internal-policy-compliance", "Internal Policy Compliance", "compliance"),
    ("audit-readiness", "Audit Readiness", "compliance"),
    ("risk-identification", "Risk Identification", "risk"),
    ("risk-assessment", "Risk Assessment", "risk"),
    ("risk-mitigation", "Risk Mitigation", "risk"),
    ("risk-acceptance", "Risk Acceptance", "risk"),
    ("residual-risk", "Residual Risk", "risk"),
)

CICLO_DE_VIDA_SUBDIMENSIONS = (
    ("draft-state", "Draft State", "state"),
    ("active-state", "Active State", "state"),
    ("deprecated-state", "Deprecated State", "state"),
    ("archived-state", "Archived State", "state"),
    ("version-scheme", "Version Scheme", "versioning"),
    ("breaking-change-policy", "Breaking Change Policy", "versioning"),
    ("change-request", "Change Request", "change"),
    ("change-approval", "Change Approval", "change"),
    ("change-log", "Change Log", "change"),
    ("impact-scope", "Impact Scope", "impact"),
    ("impact-severity", "Impact Severity", "impact"),
    ("deployment-environment", "Deployment Environment", "deployment"),
    ("rollback-plan", "Rollback Plan", "deployment"),
    ("migration-path", "Migration Path", "migration"),
    ("data-migration", "Data Migration", "migration"),
    ("decommission-trigger", "Decommission Trigger", "decommissioning"),
    ("decommission-checklist", "Decommission Checklist", "decommissioning"),
)

DADOS_SUBDIMENSIONS = (
    ("data-classification", "Data Classification", "data"),
    ("public-data", "Public Data", "data-classification"),
    ("internal-data", "Internal Data", "data-classification"),
    ("confidential-data", "Confidential Data", "data-classification"),
    ("restricted-data", "Restricted Data", "data-classification"),
    ("data-lineage", "Data Lineage", "data"),
    ("source-system", "Source System", "data-lineage"),
    ("transformation-steps", "Transformation Steps", "data-lineage"),
    ("data-quality", "Data Quality", "data"),
    ("completeness", "Completeness", "data-quality"),
    ("accuracy", "Accuracy", "data-quality"),
    ("consistency", "Consistency", "data-quality"),
    ("data-retention", "Data Retention", "data"),
    ("data-ownership", "Data Ownership", "data"),
)

ARQUITETURA_SUBDIMENSIONS = (
    ("component-boundary", "Component Boundary", "components"),
    ("component-interaction", "Component Interaction", "components"),
    ("functional-capability", "Functional Capability", "capabilities"),
    ("non-functional-capability", "Non-Functional Capability", "capabilities"),
    ("user-interface", "User Interface", "interfaces"),
    ("system-interface", "System Interface", "interfaces"),
    ("integration-interface", "Integration Interface", "interfaces"),
    ("input-contract", "Input Contract", "contracts"),
    ("output-contract", "Output Contract", "contracts"),
    ("api-versioning", "API Versioning", "apis"),
    ("api-authentication", "API Authentication", "apis"),
    ("rate-limiting", "Rate Limiting", "apis"),
    ("workflow-trigger", "Workflow Trigger", "workflows"),
    ("workflow-steps", "Workflow Steps", "workflows"),
    ("workflow-exception", "Workflow Exception", "workflows"),
    ("process-owner", "Process Owner", "processes"),
    ("process-steps", "Process Steps", "processes"),
    ("business-rule", "Business Rule", "rules"),
    ("validation-rule", "Validation Rule", "rules"),
    ("read-operation", "Read Operation", "operations"),
    ("write-operation", "Write Operation", "operations"),
    ("idempotency", "Idempotency", "operations"),
    ("compute-infrastructure", "Compute Infrastructure", "infrastructure"),
    ("storage-infrastructure", "Storage Infrastructure", "infrastructure"),
    ("network-topology", "Network Topology", "networks"),
    ("network-security-zone", "Network Security Zone", "networks"),
)

QUALIDADE_OPERACIONAL_SUBDIMENSIONS = (
    ("latency-target", "Latency Target", "performance"),
    ("throughput-target", "Throughput Target", "performance"),
    ("failure-mode", "Failure Mode", "resilience"),
    ("fallback-strategy", "Fallback Strategy", "resilience"),
    ("circuit-breaker", "Circuit Breaker", "resilience"),
    ("logging", "Logging", "observability"),
    ("metrics", "Metrics", "observability"),
    ("tracing", "Tracing", "observability"),
    ("alerting", "Alerting", "observability"),
    ("unit-testing", "Unit Testing", "testing"),
    ("integration-testing", "Integration Testing", "testing"),
    ("load-testing", "Load Testing", "testing"),
    ("manual-verification", "Manual Verification", "verification"),
    ("automated-verification", "Automated Verification", "verification"),
)

NEGOCIO_SUBDIMENSIONS = (
    ("competitive-positioning", "Competitive Positioning", "strategy"),
    ("market-fit", "Market Fit", "strategy"),
    ("cost-model", "Cost Model", "finance"),
    ("revenue-model", "Revenue Model", "finance"),
    ("budget-approval", "Budget Approval", "finance"),
    ("contract-terms", "Contract Terms", "legal"),
    ("liability", "Liability", "legal"),
    ("intellectual-property", "Intellectual Property", "legal"),
    ("environmental-impact", "Environmental Impact", "sustainability"),
    ("long-term-viability", "Long-Term Viability", "sustainability"),
)

FATORES_HUMANOS_SUBDIMENSIONS = (
    ("user-journey", "User Journey", "ux"),
    ("usability-testing", "Usability Testing", "ux"),
    ("user-feedback", "User Feedback", "ux"),
    ("wcag-compliance", "WCAG Compliance", "accessibility"),
    ("assistive-technology-support", "Assistive Technology Support", "accessibility"),
)


# ---------------------------------------------------------------------------
# Convergência dos templates Norvald (UDF §8)
#
# As subdimensões abaixo não vieram de simetria com Segurança, e sim da
# matriz de convergência entre os templates v2 e o registry: cada uma
# cobre uma necessidade documental que um tipo declara em "Deve conter"
# e que nenhuma dimensão existente representava. Das 65 necessidades
# extraídas dos 10 tipos, 43 já estavam cobertas; estas fecham as 22
# restantes.
#
# A terceira fonte prevista pelo §8 — o modelo de engenharia de 10
# camadas — não existe em forma utilizável: o próprio UDF só o menciona
# e manda não copiar literalmente (ver docs/adr/Concluidos/
# Decisoes-Orfaos-Layer-Relacoes.md §2). A convergência foi feita com as
# duas fontes que existem, e isso fica registrado em vez de suprido por
# invenção.
#
# Todas nascem CONDITIONAL: valem para o tipo documental que as exige,
# não para todo documento. Promover a REQUIRED é decisão explícita, como
# foi em Segurança.
# ---------------------------------------------------------------------------

# ADR: problema → alternativas → justificativa → decisão → consequências.
# O percurso inteiro de uma decisão, que o registry representava só pelo
# efeito (impact, risk) e nunca pelo raciocínio que levou a ela.
DECISAO_SUBDIMENSIONS = (
    ("decision", "Decision", "governance"),
    ("problem-statement", "Problem Statement", "decision"),
    ("considered-options", "Considered Options", "decision"),
    ("decision-rationale", "Decision Rationale", "decision"),
    ("decision-outcome", "Decision Outcome", "decision"),
    ("decision-consequences", "Decision Consequences", "decision"),
)

# Engineering Guideline: o único tipo cujas necessidades não tinham
# nenhuma dimensão correspondente — seis de seis eram lacuna.
PADROES_DE_ENGENHARIA_SUBDIMENSIONS = (
    ("engineering-standards", "Engineering Standards", "architecture"),
    ("coding-conventions", "Coding Conventions", "engineering-standards"),
    ("organization-patterns", "Organization Patterns", "engineering-standards"),
    ("review-guidelines", "Review Guidelines", "engineering-standards"),
    ("good-practices", "Good Practices", "engineering-standards"),
    ("antipatterns", "Antipatterns", "engineering-standards"),
    ("technical-quality-criteria", "Technical Quality Criteria", "engineering-standards"),
)

# Rule, Contract, Data Model e Specification: lacunas pontuais dentro de
# dimensões que já existiam.
CONVERGENCIA_PONTUAL_SUBDIMENSIONS = (
    ("activation-condition", "Activation Condition", "rules"),
    ("rule-exception", "Rule Exception", "rules"),
    ("rule-example", "Rule Example", "rules"),
    ("contract-exception", "Contract Exception", "contracts"),
    ("data-schema", "Data Schema", "data"),
    ("data-integrity", "Data Integrity", "data"),
    ("functional-requirement", "Functional Requirement", "requirements"),
    ("behavioral-requirement", "Behavioral Requirement", "requirements"),
)

# Test Specification: o tipo descreve o teste como documento (cenário,
# pré-condição, entrada, resultado esperado); o registry só tinha os
# modos de testar (unit, integration, load).
ESPECIFICACAO_DE_TESTE_SUBDIMENSIONS = (
    ("test-scenario", "Test Scenario", "testing"),
    ("test-precondition", "Test Precondition", "testing"),
    ("test-input-data", "Test Input Data", "testing"),
    ("expected-result", "Expected Result", "testing"),
)


# ---------------------------------------------------------------------------
# Segunda rodada de convergência: os tipos que só existem em v1
#
# API, Interface, Workflow e Constitution não têm versão v2 — não foram
# sucedidos, ficaram de fora. A primeira rodada os tratou como superados,
# o que era conclusão, não fato. Decompostos, somam 21 necessidades: 10
# já cobertas (algumas por unificação de equivalentes, como
# "compatibilidade de API" → `breaking-change-policy` e "pontos de falha
# do fluxo" → `failure-mode`), 11 descobertas — que se desdobram nas
# subdimensões abaixo.
# ---------------------------------------------------------------------------

# API: o baseline tinha versionamento, autenticação e rate limit — o que
# se supôs sobre APIs. O tipo documental exige também o que a API expõe,
# como fala e como valida o que recebe.
API_SUBDIMENSIONS = (
    ("api-operation", "API Operation", "apis"),
    ("api-protocol", "API Protocol", "apis"),
    ("api-media-type", "API Media Type", "apis"),
    ("api-payload-validation", "API Payload Validation", "apis"),
    ("api-authorization", "API Authorization", "apis"),
)

# Workflow: havia gatilho, passos e exceção. Faltava o que decide o
# caminho — condições de transição e ramificação — e os estados do
# próprio fluxo, que não se confundem com os estados do documento
# (draft/active/deprecated/archived).
FLUXO_SUBDIMENSIONS = (
    ("transition-condition", "Transition Condition", "workflows"),
    ("branching-rule", "Branching Rule", "workflows"),
    ("workflow-state", "Workflow State", "workflows"),
    ("initial-state", "Initial State", "workflow-state"),
    ("intermediate-state", "Intermediate State", "workflow-state"),
    ("final-state", "Final State", "workflow-state"),
)

# Interface: o segmento de fatores humanos tinha jornada, teste de
# usabilidade, feedback e acessibilidade — como se avalia uma interface.
# Não tinha nada sobre como ela é especificada. Os estados nomeados
# (carregando, sucesso, erro, vazio) são os que o próprio tipo lista.
INTERFACE_SUBDIMENSIONS = (
    ("interface-design", "Interface Design", "human-factors"),
    ("interaction-model", "Interaction Model", "interface-design"),
    ("design-guidelines", "Design Guidelines", "interface-design"),
    ("ui-component-pattern", "UI Component Pattern", "interface-design"),
    ("layout-pattern", "Layout Pattern", "interface-design"),
    ("usability-criteria", "Usability Criteria", "interface-design"),
    ("interface-behavior", "Interface Behavior", "interface-design"),
    ("navigation-flow", "Navigation Flow", "interface-design"),
    ("interface-state", "Interface State", "interface-design"),
    ("loading-state", "Loading State", "interface-state"),
    ("success-state", "Success State", "interface-state"),
    ("error-state", "Error State", "interface-state"),
    ("empty-state", "Empty State", "interface-state"),
)

# Constitution: o tipo de maior autoridade do Framework não tinha
# nenhuma dimensão própria. Princípio fundamental, valor permanente e
# regra que sobrevive a qualquer arquitetura não são premissa comum nem
# restrição técnica — são o que continua valendo quando tudo em volta
# muda.
CONSTITUICAO_SUBDIMENSIONS = (
    ("constitution", "Constitution", "governance"),
    ("founding-principle", "Founding Principle", "constitution"),
    ("permanent-value", "Permanent Value", "constitution"),
    ("universal-premise", "Universal Premise", "constitution"),
    ("normative-limit", "Normative Limit", "constitution"),
    ("governance-guideline", "Governance Guideline", "constitution"),
    ("invariant-rule", "Invariant Rule", "constitution"),
)

_ALL_SEGMENT_SUBDIMENSIONS = (
    FUNDAMENTOS_SUBDIMENSIONS
    + NORMATIVO_SUBDIMENSIONS
    + GOVERNANCA_SUBDIMENSIONS
    + CICLO_DE_VIDA_SUBDIMENSIONS
    + DADOS_SUBDIMENSIONS
    + ARQUITETURA_SUBDIMENSIONS
    + QUALIDADE_OPERACIONAL_SUBDIMENSIONS
    + NEGOCIO_SUBDIMENSIONS
    + FATORES_HUMANOS_SUBDIMENSIONS
    + DECISAO_SUBDIMENSIONS
    + PADROES_DE_ENGENHARIA_SUBDIMENSIONS
    + CONVERGENCIA_PONTUAL_SUBDIMENSIONS
    + ESPECIFICACAO_DE_TESTE_SUBDIMENSIONS
    + API_SUBDIMENSIONS
    + FLUXO_SUBDIMENSIONS
    + INTERFACE_SUBDIMENSIONS
    + CONSTITUICAO_SUBDIMENSIONS
)


def build_baseline_registry() -> DimensionRegistry:
    registry = DimensionRegistry()
    # "Privacy" já era uma das 60 do baseline original, sempre raiz.
    # A árvore de Segurança aprovada em 2026-09-13 a torna filha direta
    # de "security" — sem isto, data-minimization/consent-management
    # (filhas de privacy) ficam presas num galho desconectado da árvore
    # principal, mesmo com parent_id correto entre si.
    #
    # As demais entradas abaixo vêm da segmentação completa aprovada por
    # Eduardo na mesma rodada: 9 segmentos, 1 primária cada, secundárias
    # sendo dimensões que já existiam soltas no baseline (nenhuma nova
    # sendo criada aqui — só conectando o que já existia). Diferente da
    # árvore de Segurança, estas não vêm de um rascunho pronto no UDF;
    # são construção nossa, e ficaram rasas por falta de fonte naquele
    # momento, não por decisão de mantê-las assim.
    #
    # A fonte apareceu: a matriz de convergência entre os templates v2 e
    # este registry (docs/framework/Matriz_de_Convergencia_Templates_
    # Registry.md) extraiu 65 necessidades documentais e apontou 22
    # descobertas — que viraram as constantes de convergência abaixo.
    # Cresceu quem tinha lacuna, não quem parecia raso: profundidade por
    # necessidade identificável (Framework §2), nunca por simetria com
    # Segurança.
    parent_overrides = {
        "privacy": "security",
        # Fundamentos (primária: identity)
        "purpose": "identity", "scope": "identity", "context": "identity",
        "authority": "identity", "ownership": "identity", "actors": "identity",
        "definitions": "identity", "semantics": "identity",
        # Normativo (primária: requirements)
        "constraints": "requirements", "assumptions": "requirements",
        "dependencies": "requirements", "relationships": "requirements",
        "references": "requirements", "provenance": "requirements",
        "evidence": "requirements", "criteria": "requirements",
        "validation": "requirements",
        # Governança (primária: governance)
        "compliance": "governance", "risk": "governance",
        # Ciclo de vida (primária: lifecycle)
        "state": "lifecycle", "versioning": "lifecycle", "change": "lifecycle",
        "impact": "lifecycle", "deployment": "lifecycle", "migration": "lifecycle",
        "decommissioning": "lifecycle",
        # Dados (primária: information)
        "data": "information",
        # Arquitetura (primária: architecture)
        "components": "architecture", "capabilities": "architecture",
        "interfaces": "architecture", "contracts": "architecture",
        "apis": "architecture", "workflows": "architecture",
        "processes": "architecture", "rules": "architecture",
        "operations": "architecture", "infrastructure": "architecture",
        "networks": "architecture",
        # Qualidade operacional (primária: reliability)
        "performance": "reliability", "resilience": "reliability",
        "observability": "reliability", "testing": "reliability",
        "verification": "reliability",
        # Negócio (primária: business)
        "strategy": "business", "finance": "business", "legal": "business",
        "sustainability": "business",
        # Fatores humanos (primária: human-factors)
        "ux": "human-factors", "accessibility": "human-factors",
    }
    # UDF §7 não garante que toda primária apareça antes de suas
    # secundárias na ordem original do documento — "State"/"Versioning"/
    # "Change"/"Impact" vêm antes de "Lifecycle", "Data" vem antes de
    # "Information", e por aí vai. register() exige que o pai já exista;
    # sem isto, 4 dos 9 segmentos quebrariam ao tentar reparentar.
    _primary_ids = set(parent_overrides.values())
    _ordered_baseline_names = sorted(
        BASELINE_DIMENSIONS,
        key=lambda name: 0 if dimension_id_of(name) in _primary_ids else 1,
    )
    registry.register_many(
        Dimension(
            id=dimension_id_of(name),
            name=name,
            definition="",
            purpose="",
            scope="",
            applicability="REQUIRED" if name in _REQUIRED_DIMENSION_NAMES else "CONDITIONAL",
            parent_id=parent_overrides.get(dimension_id_of(name)),
            state="ACTIVE",
            metadata={"source": "UDF 7"},
        )
        for name in _ordered_baseline_names
    )
    # Registrado depois do baseline: register() exige que o pai já
    # exista, e todo pai de nível 1 aqui é "security", já registrado
    # acima. A ordem da tupla já respeita pai-antes-do-filho.
    registry.register_many(
        Dimension(
            id=dimension_id,
            name=name,
            definition="",
            purpose="",
            scope="",
            applicability="CONDITIONAL",
            parent_id=parent_id,
            state="ACTIVE",
            metadata={"source": "UDF security tree, aprovado 2026-09-13"},
        )
        for dimension_id, name, parent_id in SECURITY_SUBDIMENSIONS
    )
    # As 9 árvores de segmento seguem a mesma regra: pai já existe (seja
    # uma dimensão original do baseline, seja outra folha da própria
    # árvore, na ordem em que foi escrita).
    registry.register_many(
        Dimension(
            id=dimension_id,
            name=name,
            definition="",
            purpose="",
            scope="",
            applicability="CONDITIONAL",
            parent_id=parent_id,
            state="ACTIVE",
            metadata={"source": "segmentacao aprovada 2026-09-13, construcao propria"},
        )
        for dimension_id, name, parent_id in _ALL_SEGMENT_SUBDIMENSIONS
    )
    return registry

