---
id: TESE-README
type: Índice
status: Vigente
version: 5.0.0
references:
  - docs/pesquisa/PESQUISA-1000_Correlacao_Entre_Especialistas_e_Efeito_Manada.md
  - docs/analise/Analise_Critica_da_Tese.md
---

# Tese — efeito manada e tamanho amostral efetivo

Esta pasta contém **a tese** e nada além dela. O que saiu do caderno `PESQUISA-1000` e não é tese foi para pasta própria.

## A tese

| Arquivo | O que é |
|---|---|
| `01_Protocolo_Experimental.md` | Pergunta, afirmação a defender, três condições, definições operacionais, análise, ameaças à validade, estrutura do texto |
| `02_Mapa_de_Teste.md` | Operacionalização: painel, configuração congelada, banco de perguntas, matriz de execução, checklist |
| `03_Posicionamento_e_Procedencia.md` | Literatura vigente, a lacuna, e de onde veio o CC |
| `04_Confronto_com_Kohli_2026.md` | Comparação linha a linha com o precedente direto, e o que a tese não pode mais reivindicar |
| `05_Adendo_Escopo_Descritivo_e_Alteracao_Sob_Exposicao.md` | Delimitação descritiva, vocabulário, contraste principal e pendências metodológicas |
| `06_Pre_Registros_2_e_3.md` | Campos prontos dos registros 2 (cruzamento AROF) e 3 (trajetória de N_eff) |

## Pré-registro

    registro 1     https://osf.io/5vy6e
                   submetido em 29/09/2026 · público, sem embargo
                   objeto: efeito da exposição ao par sobre N_eff, duas levas

    registro 2     redigido, não submetido · docs/tese/06 §Registro 2
                   objeto: similaridade estrutural de traço prediz co-falha

    registro 3     redigido, não submetido · docs/tese/06 §Registro 3
                   objeto: trajetória de N_eff por rodada de exposição

O registro é **imutável** depois de submetido. Por isso o reposicionamento
perante Kohli (`03` §3 e `04`) foi aplicado antes: congelar uma reivindicação
já sabida falsa seria pior do que não registrar.

Pela mesma razão, 2 e 3 são registros próprios e não emendas do primeiro. O
registro 1 permanece como está.

O que entra no registro: hipótese, condições, estimador, plano de análise e
critério de fracasso, todos já escritos em `01`. O fingerprint do banco de
perguntas entra depois, pelo recurso de *update*, quando o banco for
congelado — o que a data protege é a decisão da análise, não o instrumento.

Custo estimado do experimento: ordem de **dois dólares** com providers hospedados. Zero em camada gratuita.

Os três primeiros documentos estão na versão 2, revisada em 27/09/2026 contra a análise crítica em `docs/analise/Analise_Critica_da_Tese.md`. O que mudou: quarta condição (B3), painel de contraste homogêneo, remoção do piso de ρ̄, tabela de `N_eff` restrita ao subconjunto binário, canal de confiança, e pilotos obrigatórios antes do congelamento do banco.

Em 28/09/2026 entrou `04`, e `01` e `03` foram reposicionados perante o precedente direto de Kohli. A reivindicação deixou de ser "aplicar ESS a painel de LLM correlacionado" e passou a ser o efeito da exposição sobre esse número. Decisões em `docs/pesquisa/PESQUISA-NEFF-02_Exposicao_Estimador_e_Colisao_Literal.md`.

## O que não é tese, e onde está

    docs/paper/PAPER-001_Observar_Nao_Autoriza_Governar.md
      position paper sobre observabilidade × controle · sem experimento

    docs/pesquisa/PESQUISA-AROF_Observabilidade_do_Raciocinio.md
      anotação de pesquisa · linha aberta, fora do caminho crítico

    docs/pesquisa/PESQUISA-1000_Correlacao_Entre_Especialistas_e_Efeito_Manada.md
      o caderno de origem · append-only, intacto

    docs/analise/Revisao_Critica_ADR-1000.md
      revisão crítica do caderno e verificação de citações

    docs/analise/Analise_Critica_da_Tese.md
      benefício, impacto, gaps e as correções aplicadas à tese

## De onde cada um veio

    PESQUISA-1000
      ├── §47–49, §68, §73          → tese
      ├── §78–89                     → paper
      └── §17–34, §51–64, §91–102    → anotação de pesquisa

    docs/AROF_Glossary.md                          canônico para a anotação
    docs/AROF_Execution_Readiness.md               o Runner serve à tese
    docs/AROF_Experimental_Implementation_Plan.md  escopo da anotação

## Correções que atravessam os documentos

**`C_adj` não será estimado.** Parâmetro não observável sob análise de sensibilidade em [0, 1]. Resolve a §71 do caderno sem o programa da §74.

**Não há piso de ρ̄.** Retratação da versão 1: o acordo observado não limita ρ̄ por baixo, porque inclui acordo produzido por pergunta fácil — dependência sem erro. A varredura cobre o intervalo inteiro e o argumento fica mais forte sem o piso. Detalhe em `TESE-001` §7.2.

**A leva 1 não é independência.** É cegueira ao par sob contexto compartilhado. O Δ continua válido; o nível absoluto, não. Correção da §49.

**Exposição ao par e ancoragem na própria resposta são coisas distintas.** A condição B3 separa as duas; sem ela o Δ principal vinha enviesado para zero. `TESE-001` §4.1.

**A taxonomia funcional não precisa ser inventada.** Adotar uma existente e citada dissolve a tensão da §41 e desbloqueia a Fase A. Aplica-se à anotação de pesquisa.
