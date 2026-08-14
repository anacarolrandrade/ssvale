# Sofia - Chatbot SS Vale

Backend MVP da Sofia, assistente virtual da SS Vale para triagem de pre-venda, qualificacao de leads e encaminhamento humano.

O projeto comecou como apoio para configuracao no Maxbot e agora possui uma
implementacao local em Python com adaptadores para o Maxbot e para o WhatsApp
Business Platform da Meta. Os dois envios reais ficam desligados por padrao.

## Papel da Sofia

A Sofia pode:

- Fazer triagem inicial.
- Identificar interesse em equipamentos.
- Qualificar leads comerciais.
- Separar suporte/pos-venda.
- Separar fornecedor/representante.
- Coletar dados basicos.
- Encaminhar para humano com resumo.

A Sofia nao pode:

- Informar preco.
- Calcular frete.
- Processar pagamento.
- Emitir orcamento formal.
- Confirmar estoque.
- Prometer prazo de entrega.
- Prometer desconto.
- Fazer diagnostico tecnico.

## Estrutura principal

- `src/sofia_chatbot/flow.py`: fluxo da Sofia e regras de conversa.
- `src/sofia_chatbot/api.py`: API local, `/chat`, `/reset`, `/health` e webhooks.
- `src/sofia_chatbot/channels/whatsapp.py`: adaptador WhatsApp Business Platform.
- `src/sofia_chatbot/channels/maxbot.py`: adaptador de webhook e API Maxbot.
- `src/sofia_chatbot/llm/`: camada independente para testar provedores de LLM.
- `src/sofia_chatbot/session_store.py`: persistencia de sessoes.
- `src/sofia_chatbot/event_log.py`: logs de eventos e controle de duplicidade.
- `tests/`: testes automatizados.
- `scripts/`: simuladores e smoke test.
- `examples/whatsapp/`: payloads simulados da Meta.
- `examples/maxbot/`: payloads simulados do Maxbot.

## Como rodar

```powershell
py run_sofia.py
```

Por padrao:

- API local: `http://127.0.0.1:8000`
- sessoes em SQLite: `data/sofia_sessions.db`
- eventos em SQLite: `data/sofia_events.db`
- envios reais Meta e Maxbot desativados.

Para uma conversa individual no navegador, abra:

```text
http://127.0.0.1:8000/tester
```

Essa tela usa apenas a API local e nao se conecta ao Maxbot.

## Testar sem servicos externos

Simular conversa WhatsApp:

```powershell
py scripts/simular_whatsapp.py
```

Rodar smoke test:

```powershell
py scripts/smoke_test.py
```

Rodar suite completa:

```powershell
py -m unittest discover -s tests
```

Comparar automaticamente o fluxo direto e os adaptadores Meta e Maxbot:

```powershell
py scripts/homologar_canais.py
```

Simular a politica de retencao dos logs, sem remover dados:

```powershell
py scripts/expurgar_eventos.py --dias 90
```

O expurgo somente remove registros quando executado deliberadamente com
`--confirmar`, depois da aprovacao da politica de retencao da empresa.

## Endpoints

### API local

- `GET /health`
- `POST /chat` (somente com `LOCAL_API_ENABLED=true`)
- `POST /reset` (somente com `LOCAL_API_ENABLED=true`)

Ao expor o webhook publicamente (tunel/proxy), use `LOCAL_API_ENABLED=false` para nao expor `/chat` e `/reset` junto.

### WhatsApp / Meta

- `GET /webhook/whatsapp`
- `POST /webhook/whatsapp` (responde apenas um ack minimo: contagens de processadas, duplicadas e erros)

### Maxbot

- `POST /webhook/maxbot/<MAXBOT_WEBHOOK_SECRET>`

O Maxbot nao assina a requisicao. Por isso, a rota so existe quando um segredo
URL-safe esta configurado e o valor correto aparece no caminho. O ACK contem
apenas contagens. Mensagens com `contact.in_attendance=1` sao registradas como
ignoradas e nunca recebem resposta da Sofia. O contrato separado de
`Mensagem Recebida em Atendimento`, com `whatsapp` e `prot_id` no nivel
principal, tambem e reconhecido e silenciado.

Por padrao, o piloto fica restrito. O contato precisa estar no segmento
`SOFIA_API_PILOTO` ou ter o telefone em `MAXBOT_PILOT_PHONES`. Depois que o
fluxo chega ao handoff, mensagens futuras ficam silenciosas ate um reset manual.

### Debug local

Disponivel somente quando `DEBUG_ENDPOINTS_ENABLED=true`:

- `GET /debug/session?session_id=...`
- `GET /debug/events?session_id=...&limit=20`

Nao habilitar debug em endpoint publico.

## Configuracao

Use `.env.example` como referencia.

Variaveis principais:

```powershell
$env:LLM_PROVIDER="mock"
$env:SESSION_STORE="sqlite"
$env:SQLITE_PATH="data/sofia_sessions.db"
$env:EVENT_LOG_ENABLED="true"
$env:EVENT_LOG_PATH="data/sofia_events.db"
$env:WHATSAPP_SEND_MESSAGES="false"
$env:MAXBOT_SEND_MESSAGES="false"
```

Para Meta:

```powershell
$env:WHATSAPP_VERIFY_TOKEN="token-de-verificacao"
$env:WHATSAPP_ACCESS_TOKEN="token-da-meta"
$env:WHATSAPP_APP_SECRET="app-secret-da-meta"
$env:WHATSAPP_PHONE_NUMBER_ID="id-do-numero"
```

Para Maxbot, ainda sem ativar envio real:

```powershell
$env:MAXBOT_WEBHOOK_SECRET="segredo-url-safe"
$env:MAXBOT_API_TOKEN="token-fornecido-pelo-maxbot"
$env:MAXBOT_CHANNEL_TOKEN="token-opcional-do-canal"
$env:MAXBOT_PILOT_MODE="true"
$env:MAXBOT_PILOT_SEGMENT="SOFIA_API_PILOTO"
$env:MAXBOT_PILOT_PHONES="5531999990001,5531999990002"
$env:MAXBOT_SEND_MESSAGES="false"
```

O token nunca deve ser gravado no repositorio, nos logs ou em capturas de tela.

Para reiniciar uma unica conversa depois que o atendimento humano terminar:

```powershell
py scripts/resetar_sessao.py --session-id 5531999990001
py scripts/resetar_sessao.py --session-id 5531999990001 --confirmar
```

O primeiro comando somente simula. Consulte `OPERACAO-PILOTO-MAXBOT.md` antes
de conectar o webhook ao painel.

## Estado atual

Consulte:

- `MVP_STATUS.md`
- `PLANO-DOIS-CANAIS.md`
- `CHECKLIST-CONTA-META.md`
- `INVENTARIO-MAXBOT-ATUAL.md`
- `whatsapp-meta.md`
- `chatbot-uso-local.md`
- `BRIEFING-ADAPTADOR-MAXBOT.md`

## Maxbot e WhatsApp Business

Durante a transicao, a SS Vale pode manter o menu atual do Maxbot e homologar
em paralelo os adaptadores de API do Maxbot e da Meta. As regras comerciais sao
compartilhadas; cada canal possui apenas sua propria entrada e saida. A
convivencia entre o menu do painel e a Sofia via API precisa ser decidida antes
de qualquer ativacao real, para evitar duas respostas na mesma conversa.

## Melhorias internas concluidas

- A primeira mensagem util do cliente e processada junto com a saudacao.
- O termo contextual "entrega" em respostas como "lanches para entrega" nao
  interrompe mais a qualificacao.
- Perguntas comerciais reais sobre entrega continuam protegidas pelo guardrail.
- Existe homologacao automatizada do fluxo direto e dos adaptadores Meta e
  Maxbot.
- Existe ferramenta segura, com simulacao por padrao, para futura retencao dos
  logs com dados pessoais.
