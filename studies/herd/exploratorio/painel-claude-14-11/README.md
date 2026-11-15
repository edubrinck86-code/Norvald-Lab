# Painel de 5 Claude Sonnet (14/11/2026): parâmetro pessoal, FORA da tese

Exploratório, não pré-registrado, não entra em nenhum texto. Serve só de referência para decidir o que coletar depois.

- 61 perguntas contestadas do MMLU-Pro (as não unânimes do painel misto no conf2-mmlu).
- 5 × Sonnet via Workflow do Claude Code, raciocínio baixo, sem ferramentas. Todas as 61 perguntas numa só chamada por agente (o painel misto respondia uma por chamada).
- B1 cego; EP (letras dos pares); E (letra, confiança e justificativa). Custo: cerca de 1,3 M tokens.

| | 5 × Sonnet | Painel misto (as mesmas 61) |
|---|---|---|
| Erro B1 | 43% | 52% |
| Unânimes no B1 | 42 de 61 | 0 (por construção) |
| ρ̄_erro B1 | 0,81 | 0,32 (viés de seleção: só contestadas) |
| N_eff B1 | 1,18 | 2,2 |
| ρ̄_erro E | 0,97 | 0,71 |
| Mudou B1→EP | 11,8% (36/305) | n/d |
| Mudou B1→E | 13,1% (40/305) | 21,6% (61/283) |
| E: errado→certo / certo→errado / errado→errado | 17 / 7 / 16 | |

Curva de pressão (colegas contra no B1 → mudou), em E: 0 → 2% (5/210); 2 → 21%; 3 → 44%; 4 → 85% (23/27). Em EP: 4 → 96% (26/27).

Referências: 5 × Gemma, ρ̄_erro B1 0,848 (140 perguntas, texto 2). Hao et al. (2026): 5 × GPT-4o.
Ressalvas: as perguntas foram escolhidas por dividirem o painel misto, não o Claude; o lote de 61 numa chamada muda o contexto; um dia, uma rodada.
Arquivos: `respostas.json` (saída do workflow), `claude_medidas.py`, `misto61.py`, `painel-5-sonnet-mmlu.js`.

## B1 e B2 sem lote (15/11, `metodo/`), 60 perguntas completas

Coleta via `claude -p` (cota da assinatura), uma pergunta por chamada, prompt exato do Lab. Parou em 603 de 1.400: a cota acabou e o aviso veio como resposta (797 descartadas).
Nas mesmas 60: erro B1 21% (misto 34%); ρ̄_erro B1 0,75 [0,61; 0,87] (misto 0,71 [0,58; 0,82]); B1→B2 10%.
Confiança × acerto: alta 87% (429), média 62% (158), baixa 25% (16). Por quartil de tamanho da resposta: 90/77/79/70%.
Erro unânime do Sonnet: 7 perguntas, confiança alta em 50 de 60. Em 5 delas (m02085, m02530, m03165, m04683, m05018) a maioria do painel misto errou na MESMA opção. Indício (não prova) de memória compartilhada entre empresas, para a tese 4.
