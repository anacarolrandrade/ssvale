# Briefing - Adaptador Maxbot para a Sofia

Documento de trabalho para quem for implementar o canal Maxbot no backend da
Sofia. Levantamento feito em 04/08/2026, direto no painel e na documentacao
oficial da API Maxbot v1.

> **Status em 04/08/2026:** implementacao local concluida. O adaptador, webhook,
> exemplos e testes descritos neste briefing ja existem na raiz canonica.
> Resultado: 69 testes, smoke test e homologacao de 5 cenarios/31 interacoes nos
> tres caminhos. Envio real nao foi ativado e nenhuma chamada externa foi feita.

## 1. Objetivo

Permitir que a Sofia (o backend Python deste repositorio) conduza conversas
reais pelo Maxbot, que e o canal em producao hoje, antes da migracao para a
WhatsApp Business Platform da Meta.

O adaptador da Meta permanece em `channels/whatsapp.py`; o novo adaptador
Maxbot esta em `channels/maxbot.py`.

## 2. Contexto do repositorio

Raiz: `C:\ssvale-chatbot-mvp`. Leia `CLAUDE.md` antes de comecar.

O que ja existe e deve ser reaproveitado:

| Arquivo | Papel |
|---|---|
| `src/sofia_chatbot/flow.py` | Maquina de estados e regras. **Agnostico de canal.** |
| `src/sofia_chatbot/guardrails.py` | Limites comerciais (preco, frete, prazo, etc). |
| `src/sofia_chatbot/api.py` | Rotas locais, webhook Meta e webhook Maxbot. |
| `src/sofia_chatbot/channels/whatsapp.py` | Adaptador da Meta. **Use como modelo.** |
| `src/sofia_chatbot/channels/maxbot.py` | Adaptador Maxbot implementado a partir deste briefing. |
| `src/sofia_chatbot/session_store.py` | Sessao em memoria ou SQLite. |
| `src/sofia_chatbot/event_log.py` | Eventos e deduplicacao por `message_id`. |
| `tests/` | 69 testes. Devem continuar passando. |

Nao edite nem use como fonte `entrega-fable-5/` e `revisao-recebida-fable-5/`.
Sao copias historicas.

## 3. O que o Maxbot oferece

API REST ja **ativada** na conta da SS Vale. Token gerado em 19/05/2026,
visivel em Configuracao / API Maxbot. Limite de **10 requisicoes por segundo**
por token; acima disso retorna HTTP 429.

Documentacao: `https://app.maxbot.com.br/doc-api/v1/`

### 3.1 Entrada: webhook Mensagem Recebida

O Maxbot faz `POST` com JSON para a URL configurada no painel. Nao ha
assinatura, header de autenticacao nem token na requisicao.

Campos relevantes do payload:

```json
{
  "origin": "2",
  "contact": {
    "id": "1",
    "name": "Fulano",
    "surname": "Mariano",
    "whatsapp": "5531911112222",
    "city": "",
    "state": "MG",
    "external_id": "",
    "in_attendance": "",
    "current_protocol": "",
    "current_attendant": ""
  },
  "msg_id": "3EB04714F09C9DE532E2",
  "msg_timestamp": "1643129533",
  "msg_date": "2022-01-25 13:52:15",
  "msg": "Teste webhook 2",
  "type": "T"
}
```

Significados que importam:

- `origin`: 0-Chat Web, 1-MaxChat, 2-WhatsApp, 3-WhatsApp Oficial, 4-Telegram,
  5-Messenger, 6-Instagram.
- `type`: T-Texto, I-Imagem, A-Audio, F-Arquivo, L-Localizacao, V-Video,
  C-VCard.
- `msg_id`: identificador unico da mensagem. **Use para deduplicacao**, no lugar
  do `message_id` da Meta.
- `contact.whatsapp`: numero do contato. **Use como `session_id`**, mesma
  convencao ja usada no adaptador da Meta.
- `contact.in_attendance`: 0-Nao, 1-Sim. Indica que um humano ja esta atendendo.
- `contact.current_protocol` e `contact.current_attendant`: protocolo e atendente
  atuais.

Ha ainda campos `img_*`, `audio_*`, `arq_*`, `vid_*`, `map_*`, `vcard` e um
bloco `quoted_*` para mensagens respondidas. Nao sao necessarios no MVP, mas o
parser nao deve quebrar quando vierem preenchidos.

### 3.2 Segundo webhook: Mensagem Recebida em Atendimento

Evento separado, disparado quando a mensagem pertence a um protocolo ja em
atendimento humano. Hoje ambos estao configurados no painel apontando para a
mesma URL.

**Regra critica:** a Sofia nao pode responder quando ha atendente humano na
conversa. Caso contrario ela fala por cima da pessoa. Trate os dois eventos em
rotas diferentes, ou verifique `contact.in_attendance` antes de responder.

### 3.3 Saida: send_text

```
POST https://app.maxbot.com.br/api/v1.php
Content-Type: application/json
```

Corpo minimo:

```json
{
  "token": "<token da conta, via variavel de ambiente>",
  "cmd": "send_text",
  "ct_whatsapp": "554111113333",
  "msg": "Texto da mensagem"
}
```

`channel_token` e opcional. Se omitido e `ct_whatsapp` estiver preenchido, o
Maxbot usa o primeiro canal cadastrado. Para obter o token do canal existe o
endpoint `get_channel`.

Retorno:

```json
{ "status": 1, "msg": "Success" }
```

`status`: 1-Sucesso, 0-Falha, 2-Processando. Em falha, `msg` traz a descricao.

O contato **precisa existir** na base do Maxbot. A API o localiza por WhatsApp,
ID externo ou CPF, nessa ordem. Como a Sofia so responde a quem mandou
mensagem, o contato ja vai existir.

Emojis usam tags proprias no formato `[EMOJI1]`, `[EMOJI10]`, etc. Se o texto
da Sofia contiver emoji Unicode direto, avaliar se o Maxbot entrega
corretamente.

### 3.4 Endpoints uteis para o handoff

- `get_service_sector` - lista os setores.
- `get_attendant` - lista os atendentes.
- `put_protocol_annotation` - insere anotacao no protocolo. **Candidato natural
  para gravar o resumo do lead** antes de passar para o humano.
- `terminate_prot` - encerra protocolo.

Setores existentes hoje: Comercial, Compras, Compras Online, Expedicao,
Financeiro, Projetos.

## 4. O que construir

1. `src/sofia_chatbot/channels/maxbot.py`
   - Parser do payload do webhook para o formato interno que o `flow.py` ja
     consome.
   - Renderizador da resposta da Sofia para texto simples.
   - Cliente HTTP do `send_text`, com tratamento de `status` e de HTTP 429.

2. Rota nova em `src/sofia_chatbot/api.py`
   - `POST` para receber o webhook. Considere caminho com segmento secreto,
     por exemplo `/webhook/maxbot/<MAXBOT_WEBHOOK_SECRET>`, ja que o Maxbot nao
     assina a requisicao.
   - Rota separada, ou verificacao explicita, para o evento de mensagem em
     atendimento.

3. Variaveis novas em `.env.example`
   - `MAXBOT_API_TOKEN=`
   - `MAXBOT_CHANNEL_TOKEN=`
   - `MAXBOT_WEBHOOK_SECRET=`
   - `MAXBOT_SEND_MESSAGES=false`
   - `MAXBOT_API_URL=https://app.maxbot.com.br/api/v1.php`

4. Testes de regressao em `tests/test_maxbot_channel.py`, no mesmo espirito de
   `tests/test_whatsapp_channel.py`.

5. Payloads de exemplo em `examples/maxbot/`, equivalentes aos que ja existem
   em `examples/whatsapp/`.

## 5. Diferenca importante de comportamento

O adaptador da Meta renderiza **botoes e listas interativas**. O `send_text` do
Maxbot envia **apenas texto puro**.

Consequencia: as opcoes de menu da Sofia precisam virar texto numerado, e o
parser precisa aceitar tanto o numero quanto o texto da opcao. Exemplo:

```
Como posso te ajudar hoje?

1 - Procuro um equipamento especifico
2 - Vou montar ou reformar uma cozinha
3 - Suporte / Pos-venda
4 - Sou fornecedor ou representante
5 - Quero falar com um consultor
```

Isso muda a experiencia em relacao ao canal Meta. Registre a diferenca e
valide com `scripts/homologar_canais.py`, que hoje compara fluxo de referencia
e adaptador Meta e devera passar a cobrir tambem o Maxbot.

## 6. Restricoes obrigatorias

Estas regras vem de `CLAUDE.md` e da revisao de seguranca ja aplicada ao
projeto. Nao afrouxe nenhuma.

- `MAXBOT_SEND_MESSAGES=false` por padrao. Envio real so com autorizacao
  explicita.
- O token da API **nunca** entra no repositorio, em log, em captura de tela ou
  em mensagem. Somente variavel de ambiente. `.env.example` leva apenas a chave
  vazia.
- A resposta HTTP do webhook devolve **apenas um ack minimo**. Nao exponha
  texto da conversa, resumo do lead nem detalhe de excecao. Ja houve correcao
  nesse sentido no webhook da Meta; repita o padrao.
- Preserve deduplicacao por `msg_id` e o comportamento de retry: falha de
  processamento nao pode consumir a mensagem silenciosamente.
- Ao expor publicamente: `LOCAL_API_ENABLED=false` e
  `DEBUG_ENDPOINTS_ENABLED=false`.
- Nao responda quando houver atendente humano no protocolo.
- `data/*.db` pode conter dados pessoais. Nao copie nem publique.
- Para toda correcao ou mudanca de fluxo, adicione teste de regressao.

## 7. Validacao

Os tres comandos devem passar ao final:

```powershell
py -m unittest discover -s tests
py scripts/smoke_test.py
py scripts/homologar_canais.py
```

Durante a suite aparece de proposito um traceback com
`segredo interno: /caminho/sensivel`. Pertence ao teste que comprova a resposta
HTTP generica. O criterio e o resultado final `Ran NN tests ... OK`.

Atualize `MVP_STATUS.md` ao concluir.

## 8. O que NAO inventar

Sao decisoes da SS Vale. Se a tarefa depender de alguma delas, apresente a
recomendacao e pare.

1. **Convivencia com o Menu de Atendimento.** Se a Sofia responder via API e o
   menu do painel tambem responder, os dois disputam a conversa. Precisa ficar
   definido quem atende o que.
2. **Destino real do handoff humano** e o que acontece depois dele.
3. **Criterio para a Sofia voltar a atender** um numero que ja passou por
   atendente.
4. **Politica de retencao e acesso** aos logs com dados pessoais.
5. **Hospedagem.** O adaptador nao depende disso para ser escrito e testado,
   mas depende para funcionar de verdade.

## 9. Situacao do webhook atual no painel

Ha configuracao antiga apontando para
`right-alarm-peer-insight.trycloudflare.com/webhooks/maxbot/` nos eventos
Mensagem Recebida, Mensagem Recebida em Atendimento, Novo Protocolo e Protocolo
Atualizado.

E um Cloudflare Quick Tunnel, cujo endereco muda a cada reinicio. Nao ha codigo
correspondente neste repositorio. As ultimas execucoes registradas sao de
04/08/2026, 10:19 e 13:04.

Origem ainda nao confirmada. Nao reutilize esse caminho sem esclarecer, e nao
assuma que ha algo funcionando do outro lado.

## 10. Ordem sugerida

1. Parser do payload, com testes, sem tocar em rede.
2. Renderizador de texto numerado, com testes.
3. Cliente `send_text`, com envio desligado por padrao e teste com dublê.
4. Rota do webhook, com ack minimo e deduplicacao.
5. Tratamento de mensagem em atendimento humano.
6. Homologacao dos tres canais.
7. So entao discutir hospedagem e teste real.
