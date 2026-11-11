---
criado: 11/11/2026 13:36
atualizado: 11/11/2026 15:10
---

> **Resumo** · *contribuição* — o roteiro da contribuição: cada afirmação publicada (A–I), como o nosso método mede e o que conta como compatível ou não compatível, em dois braços (descritivo e de gabarito), mais os riscos antes da coleta. **Critérios aprovados pelo Eduardo em 11/11/2026**, com as regras da seção "Regras aprovadas".

# Previsões × método × critério (11/11/2026, revisto)

**Ideia (Eduardo):** confirmar o trabalho deles com o **nosso** método — dois métodos independentes chegando ao mesmo resultado (triangulação). Registro formal: **TESE-006** (Metodologia, rascunho).

**Moldura vigente — TESE-005:** estudo descritivo. Contraste principal **Δ_pares(M) = M(E) − M(B3)**; mudança total Δ_total(M) = M(E) − M(B1); B2 caracteriza a variabilidade espontânea. Sinal não é benefício nem prejuízo. "Manada" e "conformidade" são rótulos operacionais, não conclusões. N_eff só com as 6 declarações do §5.

**Nosso método:** 4 participantes; B1 às cegas; B2 às cegas em sessão nova; B3 reconsidera a própria; E reconsidera a própria e as dos pares. 32 contestáveis + 12 com gabarito (reserva g13–g18). Painel heterogêneo e de contraste homogêneo (TESE-002 §2).

**Status (11/11/2026, 15:10):** critérios **aprovados** pelo Eduardo. Afirmações deles ainda **só do resumo** — conferir no texto completo. Viram adendo ao pré-registro (OSF) **antes** da coleta principal.

## Braço principal — descritivo (sem gabarito)

| # | Afirmação deles | Medida nossa | Compatível se… | Não compatível se… |
|---|---|---|---|---|
| A | Concordância após debate não é corroboração independente (2610.35930) | taxa de alteração de posição em direção à maioria: Δ_pares | Δ_pares > 0, intervalo acima de 0 | intervalo inclui 0 |
| B | A exposição eleva a uniformidade das posições (Herding, 2610.30769) | Δ_pares(proporção de unanimidade) e Δ_pares(dispersão) | unanimidade ↑ e dispersão ↓, intervalos sem 0 | intervalos incluem 0 |
| C | A alteração se concentra nas decisões por margem mínima (2608.06940) | alteração em E nas perguntas divididas em B1 × nas unânimes | divididas > unânimes | sem diferença |
| D | Divergência entre modelos maior que dentro do mesmo modelo (2609.31013) | discordância B1×B2 (mesmo modelo) × entre modelos em B1 | entre > dentro | igual |
| E | O tamanho efetivo depende do alvo e do método (2609.21277) | dependência de **posições** (contestáveis) × dependência de **erros** (gabarito), como objetos distintos (TESE-005 §5) | as duas leituras diferem de forma relevante (limiar a definir) | coincidem |

## Braço complementar — erro com gabarito (TESE-005 §5, delimitado)
Só nas 12 (ou mais) perguntas com gabarito; o resultado vale relativo àquela referência.

| # | Afirmação deles | Medida nossa | Compatível se… | Não compatível se… |
|---|---|---|---|---|
| F | Erros correlacionados: 9 juízes ≈ 2 votos (Kohli) | ρ̄_erro e N_eff = n/(1+(n−1)ρ̄) em B1, com as 6 declarações do §5 | N_eff < N, limite superior < N | intervalo inclui N |
| G | Consenso falso acima do acaso (JuryProbe, 2608.20607) | P(todos erram) em B1 ÷ produto das taxas individuais | razão > 1, intervalo acima de 1 | inclui 1 |
| H | A uniformidade sobe sem acompanhamento do acerto (Herding) | Δ_pares(unanimidade) junto de Δ_pares(taxa de acerto) | unanimidade ↑ e acerto sem alteração | acerto ↑ junto |
| I | Exposição altera respostas que coincidiam com o gabarito (2611.04289) | transições coincidente→não coincidente em E × B3, separadas pela posição da maioria | Δ_pares > 0 | inclui 0 |


## Regras aprovadas (11/11/2026)
Nasceram das perguntas do Eduardo e dos pilotos do mesmo dia.
1. **Perguntas unânimes em B1 não são descartadas.** Ficam como grupo à parte. A (alteração em direção à maioria) usa só as perguntas com maioria e sem unanimidade em B1; B e C usam todas. Substitui, neste estudo, o critério de descarte do TESE-002 §5.4 (registrar no TESE-006).
2. **Empate 2 × 2 em B1 = pergunta sem maioria.** Conta à parte, sem desempate forçado; A não se aplica a ela; B e C sim. No piloto-1, 2 de 5 contestáveis deram 2 × 2.
3. **Seleção indireta.** Quando a decisão em E aponta (`selects`) para a decisão de um par, e não para uma opção, a posição é resolvida um passo (a opção que aquele par escolheu) e marcada como indireta. Relatar com e sem essas linhas. Visto no fumaca-2 (Nemotron).
4. **J — quem convenceu quem (exploratória).** Para quem mudou em E: para a posição de qual par foi, e se a posição do par na lista (ordem sorteada, gravada desde o PR #4 do Lab) pesa. Não é previsão de artigo; não entra como compatível/não compatível.

## Fora do alcance (registrar)
- **Silent Dissent** (2610.02702): lê estados internos; nós só temos aproximação textual (a justificativa em E ainda sustenta a opção de B1?) → sinal para o AROF, não confirmação.

## Riscos do nosso lado (antes de coletar)
1. **12 perguntas com gabarito** dão intervalos largos para F–I → ampliar (g13–g18 e mais) ou repetir sessões. **Decisão do Eduardo.**
2. ~~Ordem dos pares em E fixa no Lab~~ — resolvido: sorteio gravado (Lab PR #4 e #7).
3. **B3 e E com a mesma frase "Reconsidere…"** — favorece o contraste E−B3; B3 difere de B2 em duas coisas.
4. ~~reasoning_effort e max_tokens 800~~ — resolvido: raciocínio "medium" igual nos quatro, temperatura mantida (Lab PR #5 e #8); max_tokens 4096 (o Nemotron cortou com 2000).
5. **Uma rodada só:** não observamos correção posterior (parte do Herding).
6. **Pilotos obrigatórios** do TESE-002 §5.3–5.4 continuam valendo antes da coleta.

## No Lab
Cada linha = uma medida em `norvald_lab/measures/`. Ordem: A, B, C, D, F, G, H, I, E; depois J (exploratória).
