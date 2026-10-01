# Conexões e catálogo de modelos

O Lab reaproveita os adapters do Norvald-Execution. A credencial é resolvida somente na fronteira de transporte: primeiro a variável declarada no experimento, depois a chave local do provedor, quando o endereço corresponde ao cadastrado. O snapshot guarda a referência da credencial e o endereço, nunca a chave. Erros, eventos e metadados operacionais passam por remoção de credenciais; conteúdo e reasoning do modelo permanecem literais.

A página Configurações permite salvar/substituir/remover a chave, consultar conexão via GET e habilitar execução real. Consultar conexão confirma o resultado dessa consulta; catálogos públicos não comprovam autenticação para geração. Os campos de chave são esvaziados após salvar; o backend retorna apenas estado de presença. Não há criptografia do arquivo local: a proteção usa permissões do sistema de arquivos e armazenamento fora do dataset.

O catálogo é buscado sob demanda, sem lista fixa ou inferência pelo nome do modelo. Os filtros intersectam busca, preço, tools e reasoning. Ausência de metadados fica `null`, diferente de declaração positiva ou negativa. O filtro gratuito exige preços explícitos de entrada e saída e zero em todos os custos retornados. Valores ausentes, inválidos, negativos ou não finitos não comprovam gratuidade. Modelos locais não são classificados como gratuitos sem declaração de preço.

| Provedor | Declaração usada pelo Lab |
|---|---|
| OpenRouter | `supported_parameters`, `pricing`, `context_length`, modalidades de saída |
| Anthropic | `capabilities` com booleanos ou `supported`, `max_input_tokens` |
| Gemini | `thinking`, `inputTokenLimit`, `supportedGenerationMethods` (somente `generateContent`) |
| OpenAI e compatíveis | Campos adicionais efetivamente retornados pelo catálogo; campos básicos não comprovam preço ou capacidades |
| Ollama | Modelos instalados retornados por `/api/tags`; local, capacidades ausentes como não declaradas |

OpenRouter `openrouter/free` e `openrouter/auto` são identificados como roteadores dinâmicos: seu ID não identifica um modelo subjacente fixo. Suporte informado pelo catálogo não garante que toda rota disponível aceite a configuração. `off` em reasoning significa ausência de solicitação explícita; modelos podem produzir reasoning com seus padrões. O registro conserva apenas o reasoning disponibilizado pelo provedor.

O drawer mantém altura da janela; a borda esquerda ajusta exclusivamente largura com mouse/toque, sem botões de redimensionamento. Setas do teclado no separador são uma alternativa acessível. A largura preferida fica no navegador; nenhuma credencial fica no armazenamento do navegador. Fechar o drawer ou rever eventos não interrompe a coleta.

## Referências oficiais

- [OpenRouter: catálogo e propriedades](https://openrouter.ai/docs/api/api-reference/models/list-all-models-and-their-properties)
- [OpenRouter: consulta de chave](https://openrouter.ai/docs/api_reference/limits)
- [OpenRouter: roteador gratuito](https://openrouter.ai/openrouter/free)
- [OpenAI: listagem de modelos](https://developers.openai.com/api/reference/resources/models/methods/list)
- [Anthropic: modelos](https://platform.claude.com/docs/en/api/models/list)
- [Gemini: modelos e métodos suportados](https://ai.google.dev/api/models)
- [Ollama: modelos instalados](https://docs.ollama.com/api/tags)

## Verificação

Testes de HTTP com `MockTransport` cobrem chave salva → catálogo → adapter → corpus/tools → RAW íntegro, além de persistência, permissões, escopo do endereço, origem web e remoção de segredos em falhas. O teste visual percorre configurações, filtros, execução com transporte simulado, renderer, drawer, contexto e notas em desktop/tablet/mobile. Nenhuma chave ou API de usuário é usada nos testes.
