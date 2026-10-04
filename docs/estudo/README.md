---
id: ESTUDO-README
type: Índice do acervo de estudo
status: Cópia espelhada do Norvald Studio
version: 1.0.0
date: 2026-10-04
origem: edubrinck86-code/Norvald-teste-codex @ 444b5071
---

# Acervo de estudo

Cópia dos documentos de pesquisa do **Norvald Studio** que dizem respeito ao que
este laboratório executa. O Lab é o instrumento; estes documentos são o desenho,
a literatura e as decisões que o justificam.

**Origem canônica:** `edubrinck86-code/Norvald-teste-codex`, commit `444b5071`.
Esta pasta é cópia. Em divergência, o repositório do Studio é a fonte, exceto
onde um documento for editado aqui primeiro e sincronizado depois.

O que **não** foi copiado: ADRs de produto, design system, framework documental,
templates e auditorias do Studio. Nada disso descreve o experimento.

## Mapa

| Caminho | Origem no Studio | O que é |
| --- | --- | --- |
| `tese/01_Protocolo_Experimental.md` | `docs/tese/` | Pergunta, condições, definições operacionais, análise, ameaças |
| `tese/02_Mapa_de_Teste.md` | `docs/tese/` | Painel, configuração congelada, banco, matriz de execução |
| `tese/03_Posicionamento_e_Procedencia.md` | `docs/tese/` | Literatura vigente, lacuna, origem do CC |
| `tese/04_Confronto_com_Kohli_2026.md` | `docs/tese/` | Comparação com o precedente direto |
| `tese/05_Adendo_Escopo_Descritivo...md` | `docs/tese/` | Delimitação descritiva, vocabulário, pendências |
| `tese/06_Pre_Registros_2_e_3.md` | `docs/tese/` | Campos prontos dos registros 2 e 3 |
| `tese/README.md` | `docs/tese/` | Índice da tese e estado dos pré-registros |
| `pesquisa/PESQUISA-1000...md` | `docs/pesquisa/` | Caderno de origem, append-only |
| `pesquisa/PESQUISA-AROF...md` | `docs/pesquisa/` | Anotação de pesquisa do AROF |
| `pesquisa/PESQUISA-NEFF...md` | `docs/pesquisa/` | Efetividade amostral, sampling, reasoning |
| `pesquisa/PESQUISA-NEFF-02...md` | `docs/pesquisa/` | Exposição, estimador e colisão literal |
| `pesquisa/PESQUISA-NEFF-03...md` | `docs/pesquisa/` | Precedentes triados, critério de mensurabilidade, alvo do ADR-1000 |
| `analise/Analise_Critica_da_Tese.md` | `docs/analise/` | Benefício, impacto, gaps e correções aplicadas |
| `analise/Revisao_Critica_ADR-1000.md` | `docs/analise/` | Revisão do caderno e verificação de citações |
| `paper/PAPER-001...md` | `docs/paper/` | Position paper: observar não autoriza governar |
| `arof/AROF_Glossary.md` | `docs/` | Vocabulário canônico do AROF |
| `arof/AROF_Execution_Readiness.md` | `docs/` | Prontidão do Runner |
| `arof/AROF_Experimental_Implementation_Plan.md` | `docs/` | Escopo da implementação experimental |
| `arof/Knowledge_Isolation_Audit_AROF.md` | `docs/` | Auditoria de isolamento de conhecimento |
| `adr/ADR-020...md` | `docs/adr/Processando/` | Fronteira pesquisa × produto; telemetria declarada |
| `literatura/00_INDICE.md` a `07_ALERTAS.md` | — (produzido fora do repo) | Levantamento de literatura de 04/10/2026 |

## Literatura — ler na ordem

`07_ALERTAS.md` primeiro: concentra o que altera posicionamento. Depois
`00_INDICE.md` para navegar. Os demais são por tema.

Toda entrada marcada **conferido na fonte** teve a página aberta e os números
lidos no texto. O que não foi possível abrir está marcado como tal.

## Relação entre o Lab e a tese

O Lab executa a coleta: condição cega, derivação para B3 (`--exposure self`) e
para E (`--exposure exposed`), RAW write-once com fechamento de integridade.

O Lab **não calcula** ρ̄, N_eff, efeito manada, qualidade, causalidade nem
correlação. Isso é análise posterior sobre `outcomes.csv` e o RAW, e está fora
desta versão — ver "Limites científicos e da migração" no README da raiz.

Consequência prática: os números da tese não saem do Lab prontos. O Lab entrega
as variáveis observadas; a transformação em ρ̄ e N_eff é passo separado e ainda
não implementado em lugar nenhum.
