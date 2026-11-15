# Engine documental: o que os dados mostram

Rascunho para cliente, 15/11/2026. Leitura pendente — proprietário. Todos os números saem de dados registrados; a fonte de cada um está no fim.

## O que é
Uma engine que entrega a informação ao modelo de IA estruturada, rastreável e na medida certa, em vez de despejar contexto e esperar que o modelo descubra o que importa. Funciona com qualquer modelo (testada em 11 modelos de empresas diferentes).

## Em uso
- **Norvald Lab:** 1.995 experimentos, 9.814 respostas de modelos registradas, 33,8 milhões de tokens processados (out.–nov. 2026). Toda a base de três pesquisas pré-registradas no OSF rodou sobre ela.
- **Norvald Huginn:** em produção desde 14/11/2026 (peças de tendências: 81 chamadas, 99% concluídas).
- **Norvald Studio:** deliberação entre modelos com rastreabilidade de cada contribuição.

## Efeito medido (experimento controlado, mesmos modelos e mesmas perguntas, ~450 chamadas por lado)
| | Sem a engine (texto corrido) | Com a engine (estruturado) |
|---|---|---|
| Mudanças de resposta sem motivo | 10,3% | **3,9%** (−62%) |
| Troca de um erro por outro erro | 20 casos | **4 casos** |
| Acerto | igual | igual |
| Custo por chamada (bônus) | US$ 0,00100 | US$ 0,00094 (−6,6%) |

**Em uma frase:** o modelo fica estável e previsível: muda de resposta 62% menos, sem perder acerto. E ainda sai um pouco mais barato.

## Por que importa
Sistemas em que a IA revisa o próprio trabalho em várias etapas (atendimento, análise de documentos, produção de conteúdo, agentes) sofrem com respostas que mudam sem motivo. Cada mudança à toa é retrabalho, inconsistência e perda de confiança do usuário.

## Fontes
- Experimento controlado: pesquisa "O formato da própria resposta anterior ancora a reconsideração?", OSF gzvk5 (custos do registro de cada chamada, 12/11/2026).
- Volume: registros do Norvald Lab (~/.norvald/lab/experiments) e ledger do Huginn (model_calls).

Eduardo Guedes · Norvald · ORCID 0009-0003-9960-3337
