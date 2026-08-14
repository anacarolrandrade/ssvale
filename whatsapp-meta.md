# Integracao WhatsApp Business Platform - Meta

Este arquivo descreve a nova abordagem do projeto Sofia para operar com o WhatsApp Business oficial da Meta.

O Maxbot deixa de ser a prioridade de implementacao. Os documentos do Maxbot continuam como referencia de fluxo, mas o chatbot real passa a funcionar assim:

```text
WhatsApp / Meta
  -> Webhook da Sofia
  -> SofiaFlow
  -> Resposta renderizada para WhatsApp
  -> Cloud API da Meta
```

## O que ja esta implementado

- Parser de webhook da Meta.
- Renderizador de resposta para WhatsApp.
- Suporte a mensagem de texto.
- Suporte a botoes quando ha ate 3 opcoes.
- Suporte a lista quando ha mais de 3 opcoes.
- Endpoint de verificacao do webhook.
- Endpoint de recebimento do webhook.
- Modo `dry_run` por padrao, sem enviar mensagem real.
- Sessao por numero de WhatsApp do cliente.
- Logs de atendimento em SQLite.
- Bloqueio de mensagens duplicadas por `message_id`.
- Verificacao opcional de assinatura do webhook.
- Simulador local de webhook.
- Testes automatizados com payload simulado da Meta.

## Endpoints

### Verificacao do webhook

`GET /webhook/whatsapp`

Usado pela Meta para validar o webhook.

Parametros esperados:

- `hub.mode`
- `hub.verify_token`
- `hub.challenge`

Se o token estiver correto, a API responde com o valor de `hub.challenge`.

### Recebimento de mensagens

`POST /webhook/whatsapp`

Recebe eventos do WhatsApp. O projeto processa apenas mensagens recebidas de clientes. Eventos de status, como entrega ou leitura, sao ignorados por enquanto.

## Variaveis de ambiente

```powershell
$env:WHATSAPP_VERIFY_TOKEN="crie-um-token-de-verificacao"
$env:WHATSAPP_ACCESS_TOKEN="token-da-meta"
$env:WHATSAPP_APP_SECRET="app-secret-da-meta"
$env:WHATSAPP_PHONE_NUMBER_ID="id-do-numero"
$env:WHATSAPP_API_VERSION="v20.0"
$env:WHATSAPP_SEND_MESSAGES="false"
```

Por seguranca, `WHATSAPP_SEND_MESSAGES` deve ficar como `false` enquanto estiver testando. Assim a Sofia processa o webhook e monta o payload de resposta, mas nao envia mensagem real ao cliente.

Se `WHATSAPP_APP_SECRET` estiver configurado, o endpoint valida o cabecalho `X-Hub-Signature-256`. Se nao estiver configurado, a verificacao fica desativada para facilitar testes locais.

Para enviar mensagens reais:

```powershell
$env:WHATSAPP_SEND_MESSAGES="true"
```

Antes disso, confirme que:

- o token da Meta esta correto;
- o phone number ID esta correto;
- o webhook esta validado;
- o numero esta em ambiente de teste ou aprovado para uso;
- a equipe sabe como assumir o atendimento humano.

## Como rodar localmente

```powershell
python run_sofia.py
```

## Simulador local

Para testar uma conversa sem depender da Meta:

```powershell
py scripts/simular_whatsapp.py
```

O simulador monta payloads parecidos com o webhook oficial, chama a Sofia em memoria e mostra a resposta que seria enviada ao WhatsApp.

Para receber webhook da Meta em ambiente local, sera necessario expor a porta local com uma URL publica segura, por exemplo via ferramenta de tunel. Configure essa URL no painel da Meta apontando para:

```text
https://sua-url-publica/webhook/whatsapp
```

## Formato de resposta

Quando o webhook recebe uma mensagem, a API retorna um resumo interno em JSON com:

- mensagem recebida;
- resposta da Sofia;
- tags;
- status;
- bloco atual;
- payload que seria enviado para a Meta;
- modo de envio, que pode ser `dry_run`.

## Handoff humano

O projeto ja identifica o destino:

- `encaminhar_comercial`
- `encaminhar_pos_venda`
- `encaminhar_fornecedor`

Ainda falta definir operacionalmente onde o humano vai atender:

- inbox oficial da Meta;
- CRM;
- ferramenta de atendimento;
- sistema proprio;
- outro provedor conectado ao WhatsApp Business Platform.

Enquanto isso nao estiver definido, a Sofia consegue qualificar e encerrar o fluxo, mas o repasse humano real ainda precisa de decisao operacional.

## Logs

Quando `EVENT_LOG_ENABLED=true`, os eventos sao registrados em SQLite:

```powershell
$env:EVENT_LOG_ENABLED="true"
$env:EVENT_LOG_PATH="data/sofia_events.db"
```

Os logs incluem:

- mensagem recebida;
- resposta enviada;
- tags;
- bloco atual;
- status da conversa;
- payload de envio em `dry_run`;
- mensagens duplicadas ignoradas.

## O que ainda depende da empresa

- Criar ou confirmar a conta WhatsApp Business Platform.
- Confirmar WABA, numero e phone number ID.
- Criar token de acesso adequado.
- Definir token de verificacao do webhook.
- Configurar URL publica do webhook.
- Definir onde o vendedor/atendente humano vai receber o lead.
- Validar templates oficiais para mensagens iniciadas pela empresa.
- Validar regras de opt-in e politica de atendimento.

## Comando de teste

Rodar todos os testes:

```powershell
python -m unittest discover -s tests
```

Os testes incluem payloads simulados do webhook da Meta e garantem que a Sofia responde em modo seguro.
