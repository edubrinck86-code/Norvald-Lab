# Lab Assistant — interface conversacional única

**Status:** implementação em PR rascunho, separada da `main`.  
**Objetivo:** operar o Norvald Lab por chat natural, com acesso flutuante e tela cheia usando um único Assistant.  
**Integração externa:** fora do escopo até os testes pessoais do proprietário.

## Superfícies de acesso

O `FloatingAssistant` é montado uma única vez em `frontend/src/App.tsx` e continua vivo quando se navega pela Bancada, Preparar, Experimentos, Registros, Notebook e Configurações. O ícone flutuante abre o mesmo chat em painel lateral; a opção **Lab Assistant** na navegação ou o botão de expansão o mostra em tela inteira, sem criar outra instância ou perder a conversa atual.

A tela inteira possui histórico de conversas, timeline de perguntas/respostas, cards de operações, área de atividades/planos e configuração do modelo operador. O painel compacto mantém as mesmas ferramentas e o mesmo histórico. A interface apresenta dicas de pedidos naturais e identifica o experimento selecionado na tela do Lab; não copia o RAW da coleta automaticamente para a LLM.

## Persistência

`norvald_lab/assistant_threads.py` guarda metadados de chats e eventos de ferramentas sob `<root>/observer/assistant_threads.sqlite3`. As mensagens continuam no banco `lab_assistant.sqlite3` existente, agora particionadas pelo ID `chat-...`. Cada conversa recebe título, contexto restrito, mensagens e eventos. Eventos incluem nome da ferramenta, operação, status, IDs de planos/experimentos e vínculo à mensagem do modelo. Falhas e execuções por botão recebem registro próprio.

O histórico geral antigo (`assistant-general`) continua acessível como **Conversa anterior**, sem migração destrutiva. Conversas de incidentes e histórico de auditoria legados permanecem armazenados nos mesmos caminhos anteriores.

## Operações por linguagem natural

O modelo operador reutiliza **somente** o catálogo tipado do Lab (validações Pydantic e serviços existentes). Não tem rota HTTP arbitrária, shell, filesystem nem chaves de credencial. As operações incluem:

- Consultar e validar Specs; propor, derivar e preparar planos B1/B3/E; iniciar um plano quando efetivamente apresentado.
- Consultar experimentos, estados, critérios, incidentes, integridade, comparações e relatórios.
- Planejar ajustes separados, consultar recuperação, ativar/desativar recuperação automática e controlar rotinas.
- Registrar ciência ou escalonamento de incidentes; consultar e criar notas e cadernos separados do RAW.
- Acionar/interromper o controle emergencial; indicar navegação para tela local.
- **Somente preparar** uma solicitação de exclusão de experimento da lista. A exclusão efetiva fica bloqueada até confirmação específica na interface.

O chat recebe contexto com campos permitidos `view`, `experiment_id` e `observation_id`. Esse contexto serve à interpretação do pedido; não substitui IDs verificáveis do Lab nem libera acesso a caminhos ou arquivos.

## Plano visível antes de execução

Os endpoints `GET /api/assistant/plans` e `GET /api/assistant/plans/{id}` **não** marcam mais um plano como apresentado. O card `PlanPreview` obtém o plano completo e, quando está realmente visível ao operador, chama `POST /api/assistant/plans/{id}/present`. Isso grava `presented_plans` no SQLite. O modelo só pode invocar `lab.plan.execute` após esse marco, em outro ciclo de conversa; a preparação por si só nunca executa o experimento.

O botão de execução chama `POST /api/assistant/threads/{thread_id}/plans/{plan_id}/execute`, revalida as condições pelo serviço anterior e registra a ação na própria conversa. A execução é idempotente; repetir o mesmo plano não inicia duplicatas.

A marca de apresentação **não é permissão individual**. Ela registra que o planejamento foi exibido. Apenas solicitações destrutivas exigem autorização específica do proprietário.

## Tela e API

- `frontend/src/components/FloatingAssistant.tsx`: chat, conversas, cards de planos e destrutivos, acessos rápidos e estado.
- `frontend/src/styles/floating-assistant.css`: layout responsivo, painel móvel e desktop, tela cheia, foco, estados e responsividade.
- `GET/POST /api/assistant/threads` e `GET /api/assistant/threads/{id}`: criar, listar e ler conversas.
- `POST /api/assistant/threads/{id}/send`: enviar pergunta e referência da tela, consultar ferramentas e retornar eventos vinculados à mensagem.
- `POST /api/assistant/plans/{id}/present`: registrar exibição de plano.
- `POST /api/assistant/threads/{id}/plans/{plan_id}/execute`: solicitar execução idempotente de plano já preparado, com auditoria na thread.
- `POST /api/assistant/threads/{id}/destructive/{request_id}/confirm`: confirmar na UI uma solicitação destrutiva já emitida, com auditoria.

Os endpoints permanecem protegidos pela política local de origem do Lab. **Não há autenticação remota.**

## Testes

`tests/test_assistant_chat.py` testa isolamento de histórico por thread, persistência após reinício, contexto de tela, proteção contra origem cruzada, plano criado por ferramenta do operador, registro de eventos, vínculo entre eventos e mensagens, execução sem duplicidade e confirmação destrutiva. A suíte anterior do Assistant e o frontend continuam no CI.

### Roteiro de aceite pessoal

1. Abrir o Lab em qualquer tela e clicar no ícone flutuante. Digitar um pedido e conferir a resposta.
2. Expandir o chat para tela cheia e voltar ao painel. Confirmar que a mesma conversa e a mensagem atual permanecem.
3. Criar uma segunda conversa e verificar que o contexto/histórico não se misturam.
4. Configurar o modelo operador usando provider real no próprio chat. Confirmar custos aplicados somente pelo provedor.
5. Pedir um experimento e verificar card do plano, participantes, objetivo e condições **antes** da execução.
6. Executar o plano pelo card ou pedir ao Assistant que execute o plano já visto; acompanhar status e RAW no Lab.
7. Pedir diagnósticos, ajustes separados, acompanhamento e relatório na conversa; conferir a ausência de mudança retroativa no experimento.
8. Testar comandos de anotação, rotina e recuperação, e confirmar a persistência.
9. Solicitar exclusão da lista, conferir pedido do modelo e verificar que **somente o checkbox e o botão de confirmação** produzem a ação.
10. Acionar a parada emergencial e conferir interrupção de novas ações, depois retomar.
11. Reiniciar a aplicação e verificar conversas, histórico de operações, planos e as rotinas.
12. Conferir comportamento em smartphone e teclado.

**Ainda não é certificação de experiência real:** testes automatizados com provedores simulados não substituem a avaliação manual do proprietário.

## Não incluído

- Conectores externos ao Assistant pessoal e APIs remotas.
- Reescrita ou exclusão irreversível do RAW, alteração direta de credenciais pelo modelo, execução de comandos arbitrários.
- Orçamento próprio de chamadas ou tokens.
