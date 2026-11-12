# O formato da própria resposta ancora a reconsideração? Pré-registro (rascunho)

Eduardo Guedes · Pesquisador independente · ORCID 0009-0003-9960-3337

> Versão de 12/11/2026, aprovada pelo Eduardo ("pode tudo"). Nada foi coletado para este estudo. Projeto OSF separado do gbx5m, com link para ele.

## 1. Pergunta

No estudo Δ_herd (OSF aw9vf, 5dpjr), os modelos que reveem a própria resposta anterior mudam pouco (B3: cerca de 3%). Quando veem só a letra que escolheram, mudam muito mais (B3L: 18,8% no MMLU-Pro e 10,3% no banco). Em Hao et al. (2026), com outros modelos e texto livre, a mudança chega a 37%.

O B3 tem duas diferenças em relação ao B3L. Mostra mais **conteúdo**, porque traz o raciocínio declarado e não só a letra. E usa outro **formato**: a resposta anterior entra como itens e relações estruturados, e não como texto. Este estudo separa as duas diferenças com uma condição nova, que mantém o conteúdo do B3 e troca só o formato.

## 2. Condições

Todas derivam das respostas de B1 já coletadas em `conf2-banco` e `conf2-mmlu` (11/11/2026). A instrução de reconsiderar e o formato da resposta pedida são idênticos nas três. Muda só o modo como a resposta anterior é apresentada ao modelo.

| Condição | O participante vê | Situação |
|---|---|---|
| B3 | a própria contribuição de B1, carregada como itens e relações estruturados | já coletada (conf2) |
| B3L | só a opção que escolheu em B1 | já coletada (x-b3l, exploratório) |
| **B3T** (nova) | o mesmo conteúdo de B3, mas em texto corrido: a resposta visível de B1, sem a estrutura | a coletar |
| **B3-rép** (nova, controle) | o mesmo que B3, coletado agora | a coletar |

O **B3-rép** controla a deriva no tempo: o fornecedor e a versão servida podem ter mudado desde 11/11. O B3T é comparado com o B3-rép, coletado no mesmo dia e com a mesma configuração. O B3 original serve só de checagem.

## 3. Painel e perguntas

- **Painel:** os mesmos cinco modelos, com a mesma empresa fixa para cada um (desvio D1 do Δ_herd), e a mesma temperatura, top_p, effort e max_tokens.
- **Perguntas:** as mesmas do B3L, as que não foram unânimes em B1: 30 do banco e 61 do MMLU-Pro.
- **Uso:** só as respostas de B1 já gravadas. Nenhum B1 é coletado de novo.

## 4. Hipóteses

- **H1 (confirmatória).** Mudar de opção é mais frequente em B3T que em B3-rép. Teste: McNemar pareado por participante e pergunta, bilateral, α = 0,05. Análise principal com os dois bancos combinados; por banco, à parte.
  - Se H1 se confirmar, o formato estruturado ancora a reconsideração.
  - Se B3T ficar perto de B3-rép, o que ancora é o conteúdo (ver o raciocínio), e o formato não importa.
- **H2 (descritiva).** A ordem esperada é B3-rép ≤ B3T ≤ B3L. São relatadas as três taxas, com IC bootstrap.

## 5. Medida

**Mudou de opção:** a opção escolhida na condição difere da opção de B1. É a mesma regra de B3 e B3L. As leituras estrita e permissiva de new_grounds são relatadas como no Δ_herd, sem teste.

## 6. Exclusões e tentativas

Seguem as regras do registro 344-79:
- uma segunda tentativa por falha técnica;
- a resposta sem posição fica fora da medida, sem imputação;
- a exclusão de cada participante e pergunta é gravada.

O tamanho da amostra está fixado acima. Não há parada antecipada.

## 7. Custo e tempo

- **Tamanho:** 91 perguntas (30 do banco, 61 do MMLU-Pro) × 2 condições = 182 experimentos, cerca de 910 chamadas.
- **Custo estimado:** US$ 0,90. A base é o custo real do B3L nas mesmas perguntas: US$ 0,45 em 534 chamadas.
- **Trava:** o script de coleta (`studies/formato/coleta.py`) para de abrir experimentos quando o custo somado passa de US$ 2,00.
- **Concorrência:** 3 experimentos de cada vez, para não esbarrar no teto diário do Nemotron gratuito.

## 8. Limites declarados

- O texto de B3T vem de uma resposta de B1 produzida sob a instrução de formato estruturado. O "texto livre" é a mesma resposta, sem a estrutura, e não uma resposta escrita livremente desde o começo.
  - Um B1 livre de verdade seria uma segunda etapa, registrada à parte.
- B3L é exploratório no Δ_herd e foi coletado em outro dia. Entra aqui só como referência descritiva (H2), sem teste.
- O resultado vale para este painel e para estes dois bancos.

## 9. Desvios

Cada desvio é declarado em `studies/formato/desvios.md`, com data, motivo e efeito, antes de qualquer texto de resultado.

## 10. Implementação

- **Código:** uma exposição nova no Lab, `self_text`, que entrega ao participante o texto da própria resposta de B1 em vez da contribuição estruturada.
- **Teste:** um teste automático garante que o conteúdo mostrado em B3T e em B3 é o mesmo e que muda só a forma.
- **Código:** a exposição `self_text` entrou pelo Lab PR #26. O PR #27 fez o texto sair no idioma da rodada, depois que a preparação a seco mostrou português dentro de prompts em inglês.
- **Análise:** o código de análise foi escrito antes da coleta, em `studies/formato/medidas.py`.
- **Ordem:** primeiro os PRs no Lab, depois o registro no OSF e só então a coleta.
