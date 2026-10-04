---
id: PESQUISA-AROF
type: Anotação de Pesquisa
status: Linha aberta
version: 1.0.0
references:
  - docs/pesquisa/PESQUISA-1000_Correlacao_Entre_Especialistas_e_Efeito_Manada.md
  - docs/AROF_Glossary.md
  - docs/AROF_Experimental_Implementation_Plan.md
---

# AROF — observabilidade do raciocínio agêntico

Anotação de pesquisa. Condensado das seções §17–34, §51–64 e §91–102 do caderno `PESQUISA-1000`. O detalhe completo permanece lá; esta seção é o que entra num texto de tese como direção futura, mais as correções de rota que a revisão produziu.

## A hipótese

> O reasoning parcialmente exposto por providers comerciais contém estrutura suficiente para derivar métricas reprodutíveis da dinâmica agêntica observável — distintas de entropia textual e potencialmente informativas sobre padrões de modelo, família e provider.

Status: não sustentada no sentido forte. O piloto Atlas produziu evidência preliminar de viabilidade da representação; o teste de identificabilidade `D_intra < D_inter` não foi executado.

## Posição honesta quanto à novidade

Os componentes do AROF têm precedentes publicados:

| Componente | Precedente |
|---|---|
| Taxonomia funcional sobre reasoning traces | ThinkARM — Li et al., ACL 2026 |
| Cadeia de Markov sobre estados de raciocínio | Yu et al., Findings EMNLP 2025 |
| Entropia de transição como objeto distinto | Baram et al., UAI 2021 (RL) |
| Forma temporal da entropia ao longo da cadeia | Zhao, arXiv 2026 |
| Sinal suficiente em summaries expostos | Zhang, Morris & Shmatikov, arXiv 2026 |
| Diversidade em ensemble de LLM | LLM-TOPLA — Tekin et al., 2024 |

O que permanece sem precedente localizado é a **junção**: trajetória de processo, normalizada de forma provider-agnostic sobre reasoning comercial exposto, vinculada à trajetória de resultado num grafo deliberativo persistente, e usada para **estimar dependência** em vez de avaliar qualidade.

Junção estreita é o tamanho certo de contribuição. Reivindicar framework novo, não.

## Correção de rota: adotar taxonomia existente

A tensão da §41 — *como normalizar função sem um classificador que decide o que é função* — não precisa ser resolvida por este trabalho.

O ThinkARM já enfrentou o problema, escolheu um annotator automático e documentou o ruído de rotulagem nas limitações. Adotar a taxonomia dele em lugar das nove Reasoning Functions v1:

- remove a obrigação de defender taxonomia própria;
- substitui gold set manual por replicação de anotação já validada em venue;
- dissolve a Fase A como bloqueio;
- torna o `assisted_reference` (§90) desnecessário como contorno.

Custo: perder o alinhamento fino com o vocabulário do Working Context. Benefício: a Fase A deixa de exigir meses de anotação. Para um trabalho sem financiamento, a troca é claramente favorável.

## Reasoning como estimador — a formulação que a intuição pede

Há uma armadilha de definição a evitar. Pela §71 do caderno, `C_adj` é o **resíduo**: o que sobra depois de medir tudo o que é mensurável. Logo, por construção, nada que se extraia do reasoning *é* `C_adj` — no instante em que se mede, aquilo sai do resíduo.

A formulação correta não é "extrair `C_adj` do reasoning". É:

> O reasoning aperta o limite inferior de ρ̄, transferindo massa do não medido para o medido. `C_adj` encolhe pela diferença.

É o que a §77 já afirma — "medição melhor encolhe `C_adj`; nenhuma medição o elimina" — dito de forma operacional. E respeita a §68: o reasoning só pode **elevar** a estimativa de dependência, nunca reduzi-la.

### O que só o processo enxerga

Medidas no nível da conclusão só detectam dependência quando os modelos concordam. O reasoning vê um caso que elas perdem inteiramente:

```
conclusões diferentes + estrutura de raciocínio convergente
  → dependência latente visível
```

Dois modelos que chegam a respostas opostas percorrendo a mesma topologia — mesmo enquadramento, mesmos critérios na mesma ordem, mesma forma de descartar alternativa — compartilham prior de treinamento mesmo discordando. Nenhuma métrica de concordância detecta isso.

É o argumento mais forte a favor do AROF, e está implícito nos quatro estados da §5 do caderno sem a consequência declarada: **divergência de conclusão sob convergência estrutural é a única evidência de dependência que só o processo oferece.**

### Dois obstáculos, de tamanhos diferentes

**Exposição desigual — contornável.** O provider não mente, mas filtra, e com intensidade diferente entre providers. O observável é o raciocínio depois de um filtro com perda específico de cada um. Isso inviabiliza comparação estrutural **entre** providers antes de normalizar exposição, mas não **dentro** do mesmo provider, onde o filtro é constante. Daí o desenho: estabelecer o método intra-provider, onde é limpo, antes de atacar o cruzamento.

**Ausência de gabarito — o duro.** Mesmo com observação perfeita, mede-se comportamento correlacionado, não erro correlacionado. Dois modelos podem raciocinar igual e ambos acertarem.

O contorno barato está na tese: o subconjunto com gabarito (`TESE-001` §5.1, banco em `TESE-002` §5.2) dá erro correlacionado observado. Daí sai o critério de aceitação empírico do AROF:

> A convergência estrutural medida nas perguntas sem gabarito prevê o erro correlacionado observado nas perguntas com gabarito?

Se prevê, a hipótese está demonstrada e o aparato se justifica. Se não prevê, descobriu-se barato que estrutura de raciocínio não carrega a informação suposta — e o AROF não precisa ser construído para ser recusado.

## Questões definicionais a resolver antes de coletar

Três pontos que a ADR-1000 registrou como testes empíricos e que são, na verdade, escolhas de definição. Resolvê-los custa uma frase cada e evita gastar execuções descobrindo álgebra.

**Conjunta ou condicional.** Se `D_transition` comparar a matriz condicional `P(j|i)`, então `S` carrega informação que `M` não tem e as dimensões são distintas. Se comparar a conjunta `C[i,j]`, `S` é a marginal de `M` e `D_function` é redundante por construção. Escolher e declarar.

**REVISE conta uma vez.** Hoje aparece como classe funcional em `S`, como `revision_distribution` em `H_A` e dentro de `G` na OAD. Reservar cada estado a uma dimensão. O mesmo vale para branching.

**`orientation=peer` provavelmente duplica R.** Descreve operacionalmente o que `measure_cross_engagement` já mede. Se `D_orientation` for dominado por `peer`, R entra no CC duas vezes por caminhos diferentes. Verificar antes de compor.

## O que fica pendente no CC

Independente do AROF:

- **`E` e `H` nunca foram definidos.** Somam 0,40 do peso da fórmula e não aparecem definidos nem na ADR-1000 nem no glossário canônico. Enquanto isso não for resolvido, discutir a forma da fórmula é discutir o que não se sabe o que é.
- **Colisão de notação.** A convenção canônica fixa `H / h → entropia`; o `H` do CC vem do CDD-017 e não se sabe se é entropia.
- **Os pesos nunca foram calibrados.** Vieram de uma deliberação. Dez adendos atacaram a forma aditiva; nenhum atacou os números.

## Ordem experimental, unificada

A ADR-1000 contém pelo menos cinco ordens concorrentes (§34, §E, §49, §63, §74, §101), nenhuma revogando a anterior. Ordem única, do barato ao caro:

    1. Δ_herd pelo caminho observável         ← é a tese 01
    2. variabilidade intra-modelo por repetição — curva K(n)
    3. identificabilidade: D_intra < D_inter
    4. relação entre OAD e o Δ já medido no passo 1
    5. só então, papel no CC

O passo 4 é o critério de aceitação do AROF: se a OAD não prevê o Δ que o passo 1 mediu, o aparato não precisa ser construído para ser recusado. Isso inverte deliberadamente a ordem original — o caminho barato produz o ground truth que valida o caro.

## Custo, que a ADR-1000 nunca estimou

Antes de retomar esta linha, produzir uma tabela com: execuções por experimento, horas de anotação, custo de API, e espaço em disco de traces. Três programas de pesquisa concorrentes sem orçamento declarado não se priorizam sozinhos, e a priorização é a decisão que falta.

## O que permanece válido sem ressalva

Independente do destino do AROF, três invariantes se sustentam e devem sobreviver a qualquer reformulação:

**Assimetria da evidência.** Convergência observada é evidência de dependência; divergência observada não é evidência de independência.

**Estrutura presente, nunca ausência.** Estimadores derivados de trace se constroem sobre o que está lá. Ausência de transição no trace não prova ausência no processo. O viés resultante subestima dependência — falha conservadora.

**`H(texto) ≠ H(raciocínio agêntico).`** Diversidade linguística lida como diversidade de raciocínio infla `N_eff`.
