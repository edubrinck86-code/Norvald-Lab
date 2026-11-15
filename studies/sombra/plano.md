# A sombra da memória: o raciocínio revela a memória de treino?

Rascunho de plano, 15/11/2026. Leitura pendente — proprietário. Ainda sem OSF: o pré-registro vem depois deste plano aprovado, e a coleta só depois do registro.

## Ideia

O raciocínio de um LLM não cria o erro em comum entre modelos; ele mostra a memória em comum (os pesos, os dados de treino) que causa esse erro (reenquadramento do AROF, 12/11). Se isso vale, o raciocínio deve ter outra cara quando a pergunta está na memória e quando não está.

## Hipóteses (a registrar)

Contraste entre dois blocos: **antigas** (MMLU herdado pelo MMLU-Pro, muito publicado) e **novas e difíceis** (fora da internet).

- **H1, tamanho.** Nas antigas, o raciocínio é mais curto do que nas novas, dentro de cada modelo.
- **H2, confiança.** Nas antigas, a confiança "alta" é mais frequente.
- **H3, caminho comum.** Nas antigas, os fundamentos declarados por modelos de empresas diferentes se sobrepõem mais, inclusive quando erram na mesma opção.
- **Resultado nulo:** se não houver diferença entre os blocos, a resposta à pergunta é "não". Isso também é resultado.

Controle de dificuldade: comparar perguntas com taxa de acerto parecida nos dois blocos (estratificação). Sem isso, "antiga" e "fácil" se confundem (limite do texto 2, §5).

## Desenho principal: clássico × sorteado (decidido em 15/11)

O mesmo problema em duas versões:
- **Clássico:** o enunciado publicado (livro, MMLU, GPQA), com os números originais. Está na internet e, provavelmente, no treino.
- **Sorteado:** a mesma estrutura, com números, nomes e contexto sorteados por programa. A pergunta exata nunca existiu.

Se o raciocínio revela a memória, ele é curto e "alto" no clássico e longo no sorteado, com a mesma estrutura. A diferença dentro do par isola a memória da dificuldade.

**Gerador por programa, não por memória.** O Opus escreve o gerador (estrutura, faixas dos parâmetros, regras dos distratores). O conteúdo concreto vem do sorteio, com seed registrada, e o gabarito vem do cálculo. Nenhuma pergunta é escrita à mão pelo Opus: uma pergunta "inventada" por um LLM sairia da memória de treino, que é o que a tese mede (conversa de 15/11).
- **Distratores por regra:** erros típicos calculados (sinal trocado, fórmula vizinha, unidade errada).
- **Dois níveis de dificuldade** por um botão: mais etapas, mais variáveis, mais restrições.
- **Áreas:** física, química, finanças, probabilidade, lógica e combinatória (problemas com solução única, verificada por programa).
- **Limite:** não cobre humanas nem direito, onde não há gabarito calculável. Essas áreas ficam fora do desenho principal; se entrarem, será com banco externo (HLE privado) ou especialista.
- **Piloto:** uma amostra pequena antes, para calibrar a faixa em que o painel erra entre 30% e 60%. Entra no registro como piloto e não vira dado.

Os blocos externos (SuperGPQA, GPQA Diamond) passam a ser opcionais, como réplica.

## Filtro de gabarito, decidido antes de ver os dados

Ficam fora do bloco antigo:
- as que o MMLU-Redux marca como erro de gabarito, pergunta ambígua ou mais de uma resposta certa;
- o resíduo do MMLU-Pro já documentado (texto 2, §4.1b; Hugging Face #57).

Motivo: sem o filtro, "memória em comum" pode ser só "todos acertaram e o gabarito errou".

## Desenho

- **Painel:** o misto, de cinco empresas, com os mesmos provedores fixos. O Claude não entra (na tese eu administro e não participo).
- **Condições:** B1 (às cegas) e B2 (às cegas, sessão nova, para medir a variação espontânea). Sem exposição: aqui o que está em jogo é a memória, não a manada.
- **Medidas, todas sem juiz:**
  - tamanho do raciocínio (tokens de saída e de raciocínio, quando o provedor informa);
  - confiança declarada no bloco do Lab;
  - sobreposição dos fundamentos (Jaccard das palavras de conteúdo, base em `studies/herd/texto2/caminho_dos_fundamentos.py`);
  - ρ̄_erro e "mesma opção errada" por bloco.
- **Estatística:** bootstrap por pergunta; modelos mistos ou estratificação por modelo para H1 e H2.

## Decisões em aberto (do Eduardo)

1. ~~De onde vem o bloco novo e difícil~~: gerador por programa, pares clássico × sorteado (15/11). Falta escolher os problemas clássicos de origem.
2. Bloco antigo: reaproveitar o conf2-mmlu (mais barato, já visto, vira análise de dados existentes) ou coletar de novo.
3. Se o Hao entra como comparação.

Recomendação do Opus: reaproveitar o conf2-mmlu como bloco antigo, declarando no registro que os dados já existem e quais análises já foram vistas (as exploratórias de 12/11), e gastar só no bloco novo e difícil.

## Indícios que motivaram (exploratórios, não confirmatórios)

- Painel misto, conf2-mmlu: confiança alta acerta 82%; acerto por quartil de raciocínio 91/91/74/58% (`studies/herd/exploratorio/especulacao-12-11/`).
- 5 × Sonnet, fora da tese (`studies/herd/exploratorio/painel-claude-14-11/`): alta acerta 87%; em 5 dos 7 erros unânimes, a mesma opção errada do painel misto, com confiança alta em 50 de 60 respostas.

## Ordem

1. Eduardo lê e decide os três pontos abertos.
2. Filtro do Redux aplicado e congelado (lista de perguntas no repositório).
3. Pré-registro no OSF.
4. Coleta do bloco novo; análise com o script escrito antes da coleta.

## Literatura próxima (busca de 15/11/2026; ler os textos completos antes do registro)

- **O método do par não é nosso:** GSM-Symbolic (arXiv 2410.05229), Functional MATH (2402.19450), Putnam-AXIOM (2508.08292), MATH-Perturb (2502.06453). Todos medem a queda de **acerto**.
- **Erro correlacionado:** Kim et al., "Correlated Errors in LLMs" (2506.07962), com 350 modelos e mais correlação dentro da mesma empresa; "The Oracle's Fingerprint" (2605.00844) cita a sobreposição de treino como causa possível, **sem testar**.
- **Estrutura parecida no raciocínio:** ReasoningFlow (2606.05402): traços estruturalmente parecidos entre modelos de bases diferentes. "Same Answer, Different Reasons" (2610.29092): divergência no nível do traço.
- **Memória e raciocínio:**
  - ZCP (2605.21856): corta o CoT e compara com versões isomórficas;
  - 2601.04301: memória não se sustenta em soluções longas;
  - MemLens (2509.20909): amostras contaminadas travam na resposta cedo e com confiança alta, um sinal medido por dentro do modelo.

**Lacuna, pela busca:** ninguém isola a memória de treino como causa do erro e do caminho em comum **entre empresas**, medido por fora (sem pesos, sem juiz), com pares clássico × sorteado. É a contribuição a declarar. O MemLens é o paralelo interno da hipótese "alta = memória" e deve ser citado como tal.
