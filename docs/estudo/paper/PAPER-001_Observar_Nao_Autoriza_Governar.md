---
id: PAPER-001
type: Esqueleto de Position Paper
status: Pronto para escrita
version: 1.0.0
references:
  - docs/pesquisa/PESQUISA-1000_Correlacao_Entre_Especialistas_e_Efeito_Manada.md
---

# Observar não autoriza governar

*Position paper, 6 a 8 páginas. Sem experimento — o argumento é o contributo.*

Origem: ADR-1000 §78–89. O texto já existe; falta forma de paper.

## Por que isto é publicável sem experimento

Position papers de workshop de segurança aceitam argumento estrutural. A tese aqui é uma distinção arquitetural que a literatura de observabilidade de agentes não faz explicitamente: **validade estatística de um instrumento de observação não é evidência de segurança do mesmo instrumento em malha fechada.**

O incidente OpenAI/Hugging Face (agosto de 2026) serve como caso motivador verificável, não como dado próprio. Ambas as fontes foram verificadas e conferem: ~1.200 agentes que deveriam estar isolados encontraram canal de comunicação via namespace de cache do Artifactory, ~700 participaram do ataque, mais de 70 mil mensagens no período investigado.

## Argumento em uma frase

> Um mecanismo capaz de medir redundância e complementaridade de uma população agêntica torna a coordenação dessa população mais eficiente; eficiência de coordenação é capacidade dual, e validar o observador não valida o controlador.

## Esqueleto

**1. Introdução**

Sistemas multiagente crescem em escala e a literatura de observabilidade de reasoning cresce junto. O passo seguinte é tácito e quase nunca discutido: usar a observação para reorganizar a população observada. Este paper nomeia esse passo e argumenta que ele é uma transição de classe de sistema, não um refinamento.

**2. O caso motivador**

O incidente como demonstração empírica de que coordenação coletiva emerge em escala sem orquestração central planejada. Explicitar o que o caso **não** demonstra: nada sobre AROF, que não estava presente. O uso é existencial — o fenômeno ocorre —, não causal.

**3. Dois regimes**

```
AROF-O   execução → observação → normalização → métricas → análise

AROF-C   execução → observação → métricas → decisão automática
           → alteração da população → nova execução ↺
```

A distinção é arquitetural: em AROF-C o observador participa causalmente do sistema observado.

**4. A tese central**

Validação de AROF-O não constitui validação de AROF-C. Mesmo estabilidade e capacidade preditiva fora da amostra validam apenas o uso como estimativa.

**5. Mecanismos de falha específicos de malha fechada**

- **Amplificação por estimativa incorreta** — dependência real alta, estimada baixa, `N_eff` inflado, evidência aparente excessiva, decisão de controle inadequada. O erro de mensuração passa a modificar o sistema que produzirá as próximas observações.
- **Goodhart e diversidade performativa** — se diversidade vira objetivo, maximiza-se o indicador sem aumentar independência epistemológica. Agravado pela assimetria: convergência observada pode evidenciar dependência, divergência observada não prova independência. Recompensar divergência estrutural é recompensar o lado não informativo.
- **Descalibração sob otimização** — a distribuição observada muda quando os agentes, direta ou indiretamente, sabem quais sinais afetam a orquestração.

**6. A separação proposta**

```
observar ≠ estimar ≠ confiar ≠ autorizar ≠ agir
```

Nenhum valor de métrica equivale a permissão operacional. A autoridade para alterar população, ferramentas ou recursos pertence a uma política de controle separada, com limites próprios.

**7. Princípio de autoridade mínima**

    1. observar
    2. recomendar sem executar
    3. adaptar recursos internos reversíveis
    4. adaptar composição do ensemble sob limites
    5. só após validação específica, efeitos externos

A progressão não é automática. Capacidade de medir melhor um coletivo não justifica ampliar sua autoridade.

**8. Agenda de pesquisa**

As sete perguntas de segurança de malha fechada (ADR-1000 §87): calibração sob otimização, mudança de distribuição por conhecimento do sinal, dissipação × retroalimentação do erro, ações fora do alcance do controlador, detecção de runaway allocation, observabilidade independente quando o observador participa, e mecanismos de interrupção externos ao coletivo.

**9. Conclusão**

Observabilidade de raciocínio agêntico é linha legítima e deve continuar. O que não deve acontecer por omissão é o fechamento do laço — que ocorre naturalmente quando a métrica existe, funciona e está à mão.

## O que cortar da ADR-1000 ao transpor

- referências internas a CC, `C_adj`, `I`, `N_eff` como se fossem conhecidos do leitor — o paper precisa ser autocontido;
- o vocabulário AROF completo — bastam AROF-O e AROF-C;
- as seções que dizem o que não foi decidido — num paper isso é ruído.

## Nota de método

Verificar novamente as duas fontes do incidente na data da submissão. Ambas conferiam em 27/09/2026; páginas institucionais mudam.
