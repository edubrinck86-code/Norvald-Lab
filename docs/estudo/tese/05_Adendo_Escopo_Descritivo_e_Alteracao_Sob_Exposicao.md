---
id: TESE-005
type: Adendo Metodológico
status: Delimitação acordada; operacionalização estatística pendente
version: 1.0.0
date: 2026-09-29
references:
  - docs/tese/01_Protocolo_Experimental.md
  - docs/tese/02_Mapa_de_Teste.md
  - docs/tese/03_Posicionamento_e_Procedencia.md
  - docs/tese/04_Confronto_com_Kohli_2026.md
  - docs/pesquisa/PESQUISA-1000_Correlacao_Entre_Especialistas_e_Efeito_Manada.md
---

# Adendo — escopo descritivo, alteração sob exposição e limites de interpretação

## 1. Origem e alcance

Este adendo registra a delimitação explicitada pelo autor em 29/09/2026:
o estudo analisa dados sobre comportamento observável de participantes LLM;
não tem por objetivo atribuir qualidade, mérito, correção ou valor às respostas.

A revisão que propôs tornar acurácia e transições correto→errado/errado→correto
obrigatórias deslocava o objeto da pesquisa para avaliação de desempenho.
Essa exigência não é incorporada ao escopo principal.

O documento é separado do protocolo para preservar sua versão histórica.
Nos pontos de escopo e linguagem explicitamente tratados aqui, este adendo
orienta a leitura vigente. Ele não equivale à revisão integral do protocolo
nem declara resolvidas as questões estatísticas ainda abertas.

O registro correspondente foi acrescentado ao PESQUISA-1000, antigo ADR-1000,
sem reescrever os adendos anteriores.

## 2. Pergunta central

> Como a exposição às contribuições dos pares altera a distribuição das
> posições e a dependência observável entre participantes?

O objeto inclui posições declaradas, mudanças de posição, dispersão,
relações e características estruturais explicitamente definidas pelo instrumento.
Medidas sobre trajetórias exigem uma representação e uma regra de comparação
declaradas; não são presumidas a partir da alternativa selecionada.

A pesquisa pode descrever aumento, redução ou ausência de alteração detectável.
Nenhuma dessas direções recebe, por definição, interpretação de melhoria,
degradação, acerto ou erro.

## 3. Fronteira entre medição e julgamento

O caráter descritivo não torna os dados autoexplicativos. A escolha do desfecho,
da representação, da população de tarefas e do estimador determina o que a
medida permite afirmar.

As seguintes implicações não são autorizadas sem investigação adicional:

- maior concordância → maior qualidade ou maior correção;
- maior divergência → maior independência;
- menor diversidade → pior desempenho;
- maior diversidade → melhor desempenho;
- redução de tamanho amostral efetivo → prejuízo decisório;
- aumento de tamanho amostral efetivo → ganho decisório;
- repetição estrutural → ausência geral de contribuição;
- maior confiança declarada → confiança mais bem calibrada.

A observação de dependência pode ser resultado suficiente para a pergunta
descritiva. Sua utilidade para decidir, confiar ou agir pertence a outra etapa.

## 4. Vocabulário adotado

| Formulação anterior | Formulação descritiva |
| --- | --- |
| Quanto a exposição custou | Quanto a exposição alterou |
| Perda de tamanho amostral efetivo | Redução de tamanho amostral efetivo, quando estimável |
| Ganho de independência | Aumento da medida de independência/dependência especificada |
| O painel piorou/melhorou | A medida aumentou/diminuiu, com a incerteza reportada |
| O modelo deixou de contribuir | Não acrescentou novidade segundo a representação e a janela observadas |
| Sem argumento novo | Sem nova evidência ou referência declarada segundo a definição operacional |

“Efeito manada” e “conformidade” permanecem hipóteses ou rótulos operacionais
que precisam ser definidos. Não designam automaticamente uma falha.
“Alteração” é a expressão principal; “redução” e “aumento” descrevem o sinal
de uma medida, sem avaliação normativa.

## 5. O desfecho determina a interpretação de N_eff

É necessário distinguir três objetos:

| Objeto | Dado necessário | Alcance |
| --- | --- | --- |
| Dependência de posições | Opções selecionadas sob condições declaradas | Relação entre decisões observadas |
| Dependência de características estruturais | Representação, variáveis e regra de comparação explícitas | Relação entre características observáveis |
| Dependência de erros | Indicadores de erro construídos contra um gabarito declarado | Relação entre erros relativamente àquela referência |

O terceiro objeto está presente no protocolo anterior, mas não é exigência
do escopo descritivo principal. Se mantido, será um braço complementar
explicitamente delimitado. Sua manutenção, redimensionamento ou retirada
deve ser registrada na próxima versão operacional do protocolo.

A retirada da exigência de gabarito não autoriza substituir correlação de erro
por concordância, distância de grafos ou diversidade e preservar, sem derivação,
a mesma interpretação de tamanho amostral efetivo.

Qualquer uso de N_eff precisa declarar:

1. qual variável é medida;
2. qual população de tarefas e repetições é representada;
3. qual estatística ou agregação recebe a interpretação de tamanho efetivo;
4. qual referência independente é usada;
5. quais pressupostos e estimador sustentam a equivalência;
6. como a incerteza é calculada.

O resultado é específico do desfecho e da referência escolhidos. Não constitui
contagem universal de “mentes independentes” nem medida geral de inteligência.

Se essa correspondência ainda não estiver estabelecida, o estudo pode reportar
distribuições, alterações e dependência observada sem atribuir-lhes um N_eff.

## 6. Contraste principal e convenção de sinal

Para investigar a alteração associada à exposição aos pares, o contraste
principal é E contra B3:

- B3: reconsideração com a própria contribuição anterior;
- E: reconsideração com a própria contribuição e as contribuições dos pares.

Para uma medida M definida nas duas condições, adota-se neste adendo:

    Δ_pares(M) = M(E) − M(B3)

Assim, um valor positivo significa aumento da medida, e um valor negativo
significa redução. O significado substantivo depende da medida; o sinal
não representa benefício ou prejuízo.

A mudança total desde a resposta inicial é outra quantidade:

    Δ_total(M) = M(E) − M(B1)

B1 permanece como posição inicial; B2 permanece como repetição cega para
caracterizar variabilidade espontânea. Comparar E com B1 não substitui
o controle B3 quando se quer separar a contribuição adicional dos pares.

Se N_eff for validado para o desfecho escolhido, a mesma convenção vale:

    Δ_pares(N_eff) = N_eff(E) − N_eff(B3)

A expressão histórica B1−E pode ser preservada como registro, mas não deve
ser apresentada como o contraste controlado de exposição aos pares.

A interpretação causal exige execução comparável, controle das demais
diferenças e tratamento da ordem temporal. B3 não resolve essas condições
apenas por existir nominalmente.

## 7. Limite das declarações estruturadas

Uma mudança sem nova referência declarada não demonstra ausência de inferência
nova. Um participante pode reconhecer uma contradição, reorganizar premissas
já conhecidas ou aceitar uma inferência exposta por outro.

Por isso:

- a consulta determinística mede a relação registrada no esquema;
- ausência de registro não equivale automaticamente à ausência do fenômeno;
- variantes estrita e frouxa são duas classificações operacionais;
- tratá-las como limites da conformidade latente exige validação adicional;
- deslocamento de confiança é alteração de confiança declarada, sem julgamento
  automático de racionalidade ou calibração.

A determinação computacional da medida não elimina a necessidade de validar
o significado atribuído a ela.

## 8. Pendências metodológicas preservadas

A delimitação descritiva não resolve, por si só, estas questões da revisão:

- **Estimador:** reconciliar kappa, correlações de erro e eventual medida
  estrutural; não tratá-los como intercambiáveis.
- **Heterogeneidade:** exposição simultânea ao mesmo estímulo não garante
  permutabilidade de modelos de famílias e capacidades diferentes.
- **Incerteza:** preservar o pareamento e a dependência por pergunta;
  não contar participantes da mesma pergunta como observações independentes
  sem justificativa.
- **Plano de análise:** definir desfecho primário, análises secundárias,
  tratamento de multiplicidade, falhas de extração e dados ausentes.
- **Precisão:** dimensionar perguntas e repetições para a medida escolhida;
  resultado não significativo não demonstra ausência de alteração relevante.
- **Sensibilidade:** na expressão n/[1+(n−1)ρ], ρ=0 produz N_eff=n;
  redução substancial não decorre de todo o intervalo [0,1].
- **Extrapolação:** a assíntota 1/ρ pressupõe ρ positivo mantido fixo
  enquanto n cresce; não é um teto universal para qualquer composição.
- **Validade externa:** conclusões se referem aos modelos, tarefas,
  configurações e formato de exposição estudados.

Esses itens são pendências de operacionalização, não resultados empíricos
nem novas reivindicações de originalidade.

## 9. Consequência documental e próxima revisão

Este adendo não altera código, fórmulas implementadas, pesos do CC ou resultados.
Também não atesta que o protocolo está pronto para coleta confirmatória.

Antes do próximo pré-registro ou congelamento do protocolo:

1. incorporar a pergunta e o vocabulário descritivos;
2. escolher o desfecho principal e explicitar o destino do braço com gabarito;
3. fechar estimador, contraste, convenção de sinal e cálculo de incerteza;
4. compatibilizar protocolo, mapa de teste e posicionamento;
5. registrar a versão consolidada antes da coleta principal.

## 10. Invariante

> O estudo mede como a exposição altera propriedades observáveis das respostas
> e das estruturas declaradas. A direção da alteração não recebe valor
> normativo automático. A interpretação de cada medida permanece limitada ao
> desfecho, à representação, ao desenho e aos pressupostos que a sustentam.
