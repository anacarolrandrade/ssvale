# MVP Status - Sofia SS Vale

Status do backend MVP da Sofia para primeiro teste controlado.

## Preparacao para deploy - 14/08/2026

Diagnostico completo em `DIAGNOSTICO-DEPLOY.md` (itens B1 a B13) e plano
faseado em `PLANO-PILOTO-PRODUCAO.md`.

**Decisoes tomadas:** segundo numero liberado pela SS Vale; hospedagem na conta
da SS Vale; handoff de ponta a ponta faz parte do criterio de sucesso (e, por
isso, depende de resposta do suporte Maxbot).

**Correcoes aplicadas nesta etapa** (as que nao dependem de terceiros):

- **B2** - `.env` e os bancos deixaram de depender do diretorio de onde o
  processo foi iniciado. Antes, subir o servico de outra pasta carregava
  configuracao vazia: o webhook respondia 404 a tudo, o `/health` continuava
  `ok` e a Sofia ficava muda sem registrar erro. Agora a raiz do projeto e
  deduzida do proprio arquivo, `SOFIA_ENV_FILE` permite apontar o arquivo em
  producao e o boot imprime de onde a configuracao veio.
- **B4** - a variavel `PORT` (convencao de plataforma gerenciada) passa a ser
  aceita, com `SOFIA_PORT` mantendo precedencia. O padrao `127.0.0.1`
  permanece, porque esta correto atras do Caddy na mesma maquina; ha aviso no
  boot se `PORT` existir e o bind for de loopback.
- **B7** - `SIGTERM` e `SIGINT` sao tratados. O servidor para de aceitar
  conexoes e conclui as requisicoes em voo antes de sair. Sem isso, um deploy
  podia matar o processo entre marcar a mensagem como processada e envia-la,
  descartando-a em silencio.
- **B9** - timeout do envio ao Maxbot caiu de 30s para 10s, configuravel por
  `MAXBOT_TIMEOUT_SECONDS`. O envio ocorre dentro do handler do webhook.
- **B10** - `msg_date_sql` passa a usar horario de Brasilia fixo (UTC-3) em vez
  do fuso do servidor. Deslocamento fixo, e nao `zoneinfo`, para nao introduzir
  a dependencia `tzdata` no Windows; o Brasil nao adota horario de verao desde
  2019 e nao adotara em 2026.
- **Extra, descoberto na verificacao** - sob systemd/Docker o `stdout` vira
  pipe com buffer de bloco e o log so aparecia quando o processo morria. O
  servico parecia nao registrar nada justamente enquanto estava no ar. Agora a
  saida e por linha.

**Artefatos de deploy criados:** `requirements.txt` (vazio de proposito, sem
dependencias externas), `deploy/sofia.service` e `deploy/Caddyfile`. O log de
acesso do Caddy fica desligado de proposito: o segredo do webhook faz parte do
caminho da URL e iria para o disco em texto plano a cada mensagem.

**Controle de versao:** `.gitignore` revisado e validado (76 arquivos, 860 KB,
nenhum segredo, dado com PII ou copia historica entra no repositorio). O
`git init` precisa ser executado por voce no Windows.

**Validacao:** 112 testes, smoke test, homologacao de 5 cenarios/26 interacoes
e ensaio da janela aprovados. Verificado tambem fora da pasta do projeto: o
servico sobe a partir de outro diretorio, carrega a configuracao, o webhook
responde 200 com o segredo certo e 404 com o errado, o log aparece ao vivo e o
`SIGTERM` encerra em 1 segundo.

**Continua desligado:** `MAXBOT_SEND_MESSAGES=false` e
`MAXBOT_PILOT_ALLOW_ATTENDANCE=false`.

**Ainda pendente:** B1 (git init), B3 (disco persistente), B5 (log operacional
e `/status` remoto), B6 (expiracao do handoff), B12 (URL estavel), e o handoff
real, que depende do chamado ao suporte Maxbot.

## Preparacao da segunda janela - 11/08/2026

- Roteiro operacional da proxima janela em `ROTEIRO-JANELA-2.md`.
- Os quatro cenarios que faltavam validar no ar (guardrail comercial,
  duplicidade, telefone nao autorizado e retorno seguro) agora passam offline:
  `py scripts/ensaio_janela_maxbot.py`, 16 checagens aprovadas.
- Go/no-go pre-janela em um comando: `py scripts/checar_janela.py`, que roda
  suite, smoke test, homologacao, ensaio e preflight e devolve um veredito
  unico com o motivo de qualquer reprovacao.
- Novo apoio operacional `py scripts/janela_teste.py` com `preflight`,
  `baseline`, `status` e `encerrar`. Os contadores da janela passam a ser
  contados a partir de um marco, sem apagar o log (que contem PII e depende da
  politica de retencao).
- Correcao: as mensagens de limite comercial e de suporte estavam sem acento e
  chegavam assim ao cliente, justamente no cenario de guardrail. Regressao em
  `tests/test_textos_cliente.py`.
- Correcao: a suite gravava eventos `chat` de teste no banco real
  `data/sofia_events.db`, que contem PII do piloto, e poluia a contagem das
  janelas. Regressao em `IsolamentoDeDadosTest`.
- `mensagens.json` nao e carregado por nenhum codigo e esta defasado em relacao
  ao fluxo. A fonte de verdade dos textos e `src/sofia_chatbot/flow.py` com
  `src/sofia_chatbot/guardrails.py`.
- Pendencia detectada pelo preflight: a sessao do telefone piloto continua em
  `handoff` desde 04/08. Precisa de reset confirmado antes da janela, senao a
  Sofia fica silenciosa com o proprio telefone de teste.
- Validacao atual: **93 testes**, smoke test, homologacao de 5 cenarios/26
  interacoes e ensaio offline aprovados.
- Envio real continua desligado: `MAXBOT_SEND_MESSAGES=false` e
  `MAXBOT_PILOT_ALLOW_ATTENDANCE=false`.

## Resultado do primeiro teste real - 04/08/2026

- Conversa real completa aprovada no numero oficial pelo telefone piloto:
  inicio, menu, equipamento, perguntas especificas, nome, cidade e confirmacao
  final.
- Telefone nao autorizado permaneceu silencioso e foi filtrado.
- Configuracao correta do painel descoberta: manter `Interacao` ativada, pois
  desativa-la tambem corta os webhooks; silenciar o Maxbot esvaziando a saudacao
  e ocultando temporariamente os tres itens publicados do menu principal.
- Protocolo automatico tratado por excecao explicita, desligada por padrao e
  restrita ao telefone piloto.
- Backend real precisa de permissao de rede externa para acessar a API Maxbot.
- Resposta dentro do protocolo sem atendente usa `send_text`; `send_chat_msg`
  retornou recusa do Maxbot nesse contexto.
- Telefone agora e obtido automaticamente do remetente no WhatsApp/Maxbot; a
  pergunta redundante foi removida nesses canais.
- Textos e opcoes do fluxo foram revisados com acentuacao.
- Estado seguro atual: `MAXBOT_SEND_MESSAGES=false` e
  `MAXBOT_PILOT_ALLOW_ATTENDANCE=false`.
- Validacao atual: **75 testes aprovados**, smoke test aprovado e homologacao
  de 5 cenarios/26 interacoes aprovada.
- Repetir teste limpo no fim de semana antes de homologar para clientes reais.
- Handoff real para um setor/atendente continua pendente.

## Atualizacao adicional de 04/08/2026 - adaptador Maxbot

- Adaptador Maxbot implementado em `src/sofia_chatbot/channels/maxbot.py`.
- Webhook protegido por segredo no caminho, com ACK minimo e limite de corpo
  compartilhado com a API existente.
- Parser de texto, renderizacao de menus numerados e cliente `send_text`
  implementados.
- Envio real continua desligado por padrao: `MAXBOT_SEND_MESSAGES=false`.
- Deduplicacao por `msg_id`, falha reprocessavel e preservacao da sessao em
  erro de envio foram validadas.
- Mensagens com atendimento humano ativo sao ignoradas sem resposta da Sofia.
- HTTP 429 do Maxbot e tratado como falha transitoria, sem retry interno que
  pudesse duplicar mensagens.
- Criados 7 payloads locais em `examples/maxbot/`.
- Piloto restrito por telefone ou segmentacao; contatos nao autorizados recebem
  somente ACK e permanecem sob o menu atual.
- O contrato oficial separado de `Mensagem Recebida em Atendimento` e
  reconhecido explicitamente. Por padrao nao dispara resposta; a unica excecao
  exige modo piloto, telefone autorizado, protocolo identificado e chave da
  janela supervisionada.
- Sessoes em handoff ficam em silencio ate reset manual confirmado.
- Script de reset individual criado em modo de simulacao por padrao.
- Suite principal: **75 testes aprovados**.
- Smoke test: aprovado para fluxo, Meta e Maxbot.
- Homologacao: 5 cenarios e 26 interacoes equivalentes no fluxo direto e nos
  dois adaptadores.
- Entrada e saida reais do Maxbot foram validadas no numero oficial durante
  janela controlada.
- A abertura/transferencia automatica do protocolo ainda nao foi ativada. O uso
  de `open_followup` em conversa iniciada pelo cliente precisa ser confirmado
  com o suporte Maxbot antes de implementar o handoff real.
- Decisao operacional: enquanto nao houver segundo numero, o teste sera feito
  no numero atual em janela curta. O menu devera ser desativado antes de ligar
  o envio da Sofia e restaurado somente depois de desligar o envio.

## Atualizacao de 04/08/2026

- Foi configurada no painel do Maxbot uma versao reduzida da Sofia, para lancar
  no canal atual antes da migracao para a Meta. Detalhes em
  `SOFIA-NO-MAXBOT.md`.
- Foram criados 9 registros novos, todos com `Exibir: Nao`. Nenhum registro em
  producao foi editado.
- A arvore nova cobre: menu de equipamento com 6 opcoes sob
  `1 - Falar com um vendedor`, mais `Suporte / Pos-venda` e
  `Falar com um consultor` no menu principal.
- A inspecao do painel confirmou que o Maxbot possui apenas quatro tipos de
  registro: Menu, Encaminhamento, Informativo e Integracao. Nao ha variavel,
  resposta livre, ramificacao condicional nem resumo consolidado.
- Por isso, os 37 blocos de `roteiro-maxbot.md` nao sao transponiveis para o
  Maxbot. A qualificacao no canal atual vem do caminho percorrido no menu.
- O painel possui 6 setores, e nao 3: Comercial, Compras, Compras Online,
  Expedicao, Financeiro e Projetos. Nao existe setor de pos-venda.
- Ativacao pendente de aprovacao: basta trocar `Exibir` para `Sim`.
- O backend em `src/sofia_chatbot` nao foi alterado nesta etapa.

## Atualizacao de 28/07/2026

- A versao revisada foi consolidada na raiz principal do projeto.
- Suite principal: 52 testes aprovados.
- Smoke test: aprovado.
- Materiais do Maxbot foram preservados como canal atual.
- Plano de convivencia e migracao para a Meta documentado em
  `PLANO-DOIS-CANAIS.md`.
- Checklist nao tecnico para criacao da conta Meta documentado em
  `CHECKLIST-CONTA-META.md`.
- Envio real para o WhatsApp continua desativado ate a disponibilizacao das
  credenciais e do numero de teste.
- Primeira mensagem do cliente processada sem exigir repeticao.
- Falso bloqueio contextual de "entrega" corrigido.
- Homologacao automatizada: 5 cenarios e 31 interacoes equivalentes nos dois
  canais.
- Destinos confirmados no Maxbot incorporados: Comercial, Compras e Compras
  Online.
- Levantamento essencial do Maxbot concluido; configuracoes secundarias e
  legado foram adiados sem bloquear o MVP.
- Ferramenta de expurgo criada em modo de simulacao; a remocao permanece
  pendente da aprovacao da politica de retencao.

## Pronto no projeto

- Fluxo principal da Sofia.
- Guardrails contra preco, frete, pagamento, orcamento, estoque, desconto e prazo.
- Camada independente de LLM.
- Provedor mock para testes.
- Adaptador openai-compatible.
- Persistencia de sessao em SQLite.
- Logs de eventos em SQLite.
- Controle de mensagens duplicadas por `message_id`.
- Webhook WhatsApp / Meta em modo `dry_run`.
- Webhook Maxbot em modo `dry_run`.
- Renderizacao para texto, botoes e listas do WhatsApp.
- Renderizacao de opcoes numeradas em texto para o Maxbot.
- Verificacao opcional de assinatura `X-Hub-Signature-256`.
- Simulador local de WhatsApp.
- Smoke test.
- Payloads simulados da Meta.
- Payloads simulados do Maxbot.
- Testes automatizados.

## Ainda depende de decisao/acesso externo

- Conta WhatsApp Business Platform / WABA.
- Numero oficial.
- `WHATSAPP_PHONE_NUMBER_ID`.
- `WHATSAPP_ACCESS_TOKEN`.
- `WHATSAPP_APP_SECRET`.
- URL publica do webhook.
- Destino real do atendimento humano.
- Templates oficiais aprovados na Meta.
- Regras comerciais finais da SS Vale.
- Decisao de convivencia entre o menu atual do Maxbot e a Sofia via API.
- Segredo de webhook, token da API e URL publica para um teste controlado do
  Maxbot.

## Criterios minimos para primeiro teste controlado

- Suite automatizada passando.
- Smoke test passando.
- `WHATSAPP_SEND_MESSAGES=false` durante teste local.
- `MAXBOT_SEND_MESSAGES=false` durante teste local.
- Webhook validado em ambiente de teste.
- Humano responsavel acompanhando as conversas.
- Plano de pausa/desligamento definido.
- Nenhum envio real ativado sem revisao.

## Riscos conhecidos

- Handoff humano real ainda nao definido.
- Templates oficiais ainda nao cadastrados/aprovados.
- O bot ainda nao foi testado com payload real da Meta.
- O envio real pela Cloud API ainda nao foi validado com credenciais.
- O adaptador Maxbot ainda nao recebeu payload real nem fez envio real.
- Se o menu do painel e a Sofia via API forem ativados juntos sem separacao,
  podem disputar a mesma conversa.
- SQLite e suficiente para MVP, mas nao e a escolha final para alto volume.

## Comandos de validacao

```powershell
py scripts/smoke_test.py
py -m unittest discover -s tests
py scripts/homologar_canais.py
py scripts/ensaio_janela_maxbot.py
py scripts/janela_teste.py preflight
```

## Decisao recomendada

Antes de testar o adaptador Maxbot com envio real, decidir como ele convive com
o menu atual. Depois, usar uma URL HTTPS estavel, segredo no caminho,
`LOCAL_API_ENABLED=false`, `DEBUG_ENDPOINTS_ENABLED=false` e acompanhamento
humano. A ativacao deve ocorrer somente em ambiente controlado.
