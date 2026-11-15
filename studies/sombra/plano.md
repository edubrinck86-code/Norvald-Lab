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

1. De onde vem o bloco novo e difícil: criar nós mesmos ou usar um banco publicado depois do corte de treino dos modelos.
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
