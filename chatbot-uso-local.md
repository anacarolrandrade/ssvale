# Uso Local do Chatbot Sofia

Este e o primeiro chatbot real da Sofia, com o fluxo do MVP e uma camada separada para trocar o modelo de LLM.

## Como rodar

Na pasta do projeto:

```powershell
python run_sofia.py
```

Por padrao, a API sobe em:

`http://127.0.0.1:8000`

## Teste rapido

### Verificar se esta rodando

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/health"
```

### Enviar mensagem

```powershell
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/chat" -ContentType "application/json" -Body '{"session_id":"teste-1","message":"Comecar"}'
```

## Camada de LLM

A Sofia usa uma interface independente chamada `LLMClient`.

Hoje existem dois provedores:

- `mock`: usado para testes locais, sem chamar API externa.
- `openai_compatible`: adaptador generico para APIs com formato `/chat/completions`.

## Configuracao

Copie `.env.example` como referencia e configure as variaveis no ambiente.

Exemplo local sem modelo externo:

```powershell
$env:LLM_PROVIDER="mock"
$env:SESSION_STORE="sqlite"
$env:SQLITE_PATH="data/sofia_sessions.db"
python run_sofia.py
```

As conversas ficam salvas em SQLite por padrao, no arquivo:

`data/sofia_sessions.db`

Para testes rapidos sem persistencia:

```powershell
$env:SESSION_STORE="memory"
python run_sofia.py
```

Exemplo com provedor compativel:

```powershell
$env:LLM_PROVIDER="openai_compatible"
$env:LLM_BASE_URL="https://api.openai.com/v1"
$env:LLM_API_KEY="sua-chave"
$env:LLM_MODEL="modelo-escolhido"
python run_sofia.py
```

## Regras mantidas no chatbot

A Sofia nao deve:

- Informar preco.
- Calcular frete.
- Processar pagamento.
- Emitir orcamento formal.
- Confirmar estoque.
- Prometer prazo de entrega.
- Prometer desconto.
- Fazer diagnostico tecnico.

Quando o cliente pedir algo sensivel, o chatbot coleta dados e encaminha para atendimento humano.

## Validacao atual

A suite de testes cobre:

- Todos os equipamentos do MVP.
- Projeto de cozinha.
- Suporte / Pos-venda.
- Fornecedor / Representante.
- Falar com consultor.
- Pedido de preco ou frete.
- Termos comerciais comuns como "quanto custa", "pix", "cartao", "pronta entrega" e "prazo".
- Resposta fora das opcoes.
- Opcoes numericas no menu.
- Equipamento digitado diretamente no menu inicial.
- Bloqueio de novas interacoes do bot depois do encaminhamento humano.
- Persistencia de sessao em SQLite.
- Parser e renderizador do WhatsApp Business Platform.
- Webhook da Meta em modo `dry_run`.
- Logs de eventos em SQLite.
- Controle de mensagens duplicadas do WhatsApp.
- Verificacao opcional de assinatura do webhook.

## Simulador WhatsApp

Para testar uma conversa sem depender da Meta:

```powershell
py scripts/simular_whatsapp.py
```

## WhatsApp Business Platform

A direcao atual do projeto e integrar a Sofia ao WhatsApp Business oficial da Meta.

Veja o guia em:

`whatsapp-meta.md`
