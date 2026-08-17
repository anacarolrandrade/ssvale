# Handoff para continuidade no Claude

## Estado mais recente - Fase 3 concluida, 14/08/2026

- **B6 aplicado:** sessoes em handoff se liberam sozinhas apos
  `HANDOFF_EXPIRA_HORAS` (padrao 24h, `0` desliga). O estado agora carrega
  `handoff_since`. A expiracao nunca sobrepoe atendimento humano — o
  `in_attendance` e checado antes. Sessoes antigas sem o campo sao tratadas
  como expiradas de proposito. Regressao em `tests/test_handoff_expiracao.py`.
- **B5 aplicado:** log de uma linha por acontecimento em `stdout`
  (`[sofia] respondida de=***2222 bloco=... envio=dry_run`) e endpoint
  `GET /status` autenticado por `STATUS_TOKEN` no cabecalho `X-Status-Token`,
  devolvendo **somente contagens**. Regressao em
  `tests/test_observabilidade.py`, incluindo teste que falha se telefone
  completo ou texto de conversa vazarem para o log.
- **Validacao atual: 143 testes**, smoke, homologacao e ensaio aprovados.
- **Decisao pendente da SS Vale:** o prazo de 24h para expirar o handoff.
- Nao confunda `/status` com `/debug/*`: o primeiro so devolve numeros e pode
  ficar exposto; os segundos devolvem PII e continuam desligados em producao.

## Estado anterior - preparacao para deploy, 14/08/2026

- Leia `DIAGNOSTICO-DEPLOY.md` (o que impede de rodar fora da maquina local,
  itens B1 a B13) e `PLANO-PILOTO-PRODUCAO.md` (plano faseado, ~17h em 5
  semanas) antes de mexer em infraestrutura.
- Decisoes ja tomadas: segundo numero liberado; hospedagem em VPS na conta da
  SS Vale; handoff de ponta a ponta dentro do criterio de sucesso.
- Cinco correcoes aplicadas, todas com regressao em
  `tests/test_prontidao_deploy.py`: B2 (caminhos independentes do diretorio de
  execucao), B4 (`PORT` aceita), B7 (`SIGTERM` com parada limpa), B9 (timeout
  de 10s), B10 (horario de Brasilia). Mais uma correcao extra: saida sem buffer
  de bloco, senao o log nao aparece sob systemd.
- **Validacao atual: 112 testes**, smoke test, homologacao e ensaio aprovados.
- Artefatos novos: `requirements.txt`, `deploy/sofia.service`,
  `deploy/Caddyfile`.
- **Pendencia de infraestrutura:** o `git init` ainda nao foi feito. O
  `.gitignore` ja esta revisado e validado.
- Duas peculiaridades de producao que valem lembrar: o `.env` agora e
  localizado pela raiz do projeto (ou por `SOFIA_ENV_FILE`), nunca pelo
  diretorio atual; e o log de acesso do Caddy fica desligado de proposito,
  porque o segredo do webhook esta no caminho da URL.

## Estado anterior - preparacao da 2a janela, 11/08/2026

- Roteiro da proxima janela: `ROTEIRO-JANELA-2.md`.
- Os quatro cenarios que faltavam validar no ar ja passam offline:
  `py scripts/ensaio_janela_maxbot.py` (16 checagens).
- Go/no-go pre-janela em um comando: `py scripts/checar_janela.py` (suite,
  smoke, homologacao, ensaio e preflight, com veredito unico).
- Apoio operacional novo: `py scripts/janela_teste.py`
  (`preflight`, `baseline`, `status`, `encerrar`). O "contador limpo" da janela
  e um marco no log, nao um expurgo: o log tem PII e a politica de retencao
  continua pendente.
- Corrigido: mensagens de limite comercial e de suporte estavam sem acento
  (chegaram assim ao cliente em 04/08). Regressao em
  `tests/test_textos_cliente.py`.
- Corrigido: a suite gravava eventos de teste no banco real
  `data/sofia_events.db`, com PII do piloto. Regressao em `IsolamentoDeDadosTest`
  dentro de `tests/test_flow.py`.
- **Bloqueio para a proxima janela:** a sessao do telefone piloto esta em
  `handoff` desde 04/08. Sem `py scripts/resetar_sessao.py --session-id <tel>
  --confirmar`, a Sofia fica silenciosa com o proprio telefone de teste. O
  `preflight` acusa isso.
- `mensagens.json` nao e lido por nenhum codigo e esta defasado; os textos reais
  vivem em `flow.py` e `guardrails.py`.
- Validacao atual: **93 testes**, smoke test, homologacao e ensaio aprovados.
- Envio real desligado: `MAXBOT_SEND_MESSAGES=false` e
  `MAXBOT_PILOT_ALLOW_ATTENDANCE=false`.

## Estado anterior - teste real Maxbot de 04/08/2026

- O numero oficial recebeu e respondeu uma conversa real completa da Sofia:
  menu, equipamento, tres perguntas, nome, cidade e confirmacao final.
- O envio real esta **desligado** ao encerrar:
  `MAXBOT_SEND_MESSAGES=false` e
  `MAXBOT_PILOT_ALLOW_ATTENDANCE=false`.
- No painel, a chave global `Interacao` precisa permanecer
  `Ativada - Direcionando Atendimentos`; desativa-la tambem corta os webhooks.
- Para uma janela da Sofia no numero atual: esvaziar temporariamente a mensagem
  de boas-vindas e ocultar os tres itens publicados do menu principal.
- O Maxbot cria protocolo automatico. A excecao de protocolo so pode ser ligada
  durante janela supervisionada e continua restrita ao telefone piloto.
- O backend de envio real deve ser iniciado com permissao de rede externa. Sem
  isso, a API falha com `URLError/PermissionError` mesmo com token valido.
- `send_chat_msg` foi recusado no protocolo sem atendente; o piloto usa
  `send_text` para o contato autorizado.
- O fluxo agora preenche o telefone pelo remetente no WhatsApp/Maxbot e pula a
  pergunta redundante. Os textos e opcoes do fluxo foram revisados com acentos.
- Validacao atual: **75 testes**, smoke test e homologacao de 5 cenarios/26
  interacoes aprovados.
- Proximo teste: repetir no fim de semana com contadores limpos, testar
  guardrail comercial, duplicidade, telefone nao autorizado e retorno seguro.
- Handoff real ao setor ainda nao esta implementado; a Sofia apenas confirma,
  gera o resumo e fica silenciosa em `human_pending`.

## Missao do projeto

Continuar o MVP da **Sofia**, assistente virtual da SS Vale para triagem de
pre-venda, qualificacao de leads e encaminhamento humano. O backend local em
Python prepara a integracao com o WhatsApp Business Platform (Cloud API da
Meta), mantendo em paralelo o fluxo atual do Maxbot.

A Sofia pode coletar dados, identificar o tipo de atendimento e encaminhar um
resumo para uma pessoa. Ela **nao pode** informar preco, calcular frete,
processar pagamento, emitir orcamento formal, confirmar estoque, prometer prazo
ou desconto, nem fazer diagnostico tecnico.

## Comece por aqui

1. Trabalhe na raiz `C:\ssvale-chatbot-mvp`.
2. Leia, nesta ordem:
   - `README.md`
   - `MVP_STATUS.md`
   - `PLANO-DOIS-CANAIS.md`
   - `regras-negocio.md`
   - `CHECKLIST-CONTA-META.md`
   - `INVENTARIO-MAXBOT-ATUAL.md`
3. Considere os arquivos da raiz e `src/`, `tests/`, `scripts/` como a versao
   canonica.
4. Nao edite nem use como fonte principal as copias historicas em
   `entrega-fable-5/` e `revisao-recebida-fable-5/`, salvo para consulta.

Esta pasta nao esta atualmente em um repositorio Git reconhecido. Antes de
assumir que existe branch, historico ou diff, confirme o ambiente. Preserve os
arquivos existentes e nao inclua bases de dados ou segredos em commits/pacotes.

## Estado validado em 04/08/2026

- Suite: **69 testes aprovados**.
- Smoke test: aprovado.
- Homologacao: **5 cenarios e 31 interacoes equivalentes** entre o fluxo
  direto e os adaptadores Meta e Maxbot.
- Envio real de WhatsApp permanece desligado por padrao.
- A raiz ja contem as correcoes da revisao Fable 5 e melhorias posteriores.
- A primeira mensagem util do cliente e processada sem exigir repeticao.
- O falso bloqueio de `entrega` em contexto como `lanches para entrega` foi
  corrigido.
- Ha ferramenta de expurgo de eventos em modo de simulacao por padrao.

Comandos de validacao esperados em Windows:

```powershell
py -m unittest discover -s tests
py scripts/smoke_test.py
py scripts/homologar_canais.py
py scripts/ensaio_janela_maxbot.py
```

O criterio atual e `Ran 143 tests ... OK`.

Se o launcher `py` nao existir, use o executavel Python disponivel no ambiente.
Durante a suite aparece intencionalmente um traceback com
`segredo interno: /caminho/sensivel`; ele pertence ao teste que comprova a
resposta HTTP generica. O criterio e o resultado final `Ran 93 tests ... OK`.

## Arquitetura essencial

- `src/sofia_chatbot/flow.py`: maquina de estados e regras da conversa.
- `src/sofia_chatbot/guardrails.py`: limites comerciais.
- `src/sofia_chatbot/api.py`: `/chat`, `/reset`, `/health`, tester e webhooks.
- `src/sofia_chatbot/channels/whatsapp.py`: parse/render da Cloud API.
- `src/sofia_chatbot/channels/maxbot.py`: parser, texto numerado e cliente
  `send_text` do Maxbot.
- `src/sofia_chatbot/session_store.py`: sessao em memoria ou SQLite.
- `src/sofia_chatbot/event_log.py`: eventos e deduplicacao por `message_id`.
- `src/sofia_chatbot/llm/`: contrato, mock e provedor OpenAI-compatible.
- `mensagens.json`: textos-base.
- `equipamentos.json` e `matriz-equipamentos.md`: catalogo/regras de produtos.
- `tests/`: regressao executavel.
- `scripts/`: smoke test, simulacao, homologacao, monitoramento e expurgo.

## Fontes de verdade

| Assunto | Fonte principal |
|---|---|
| Limites comerciais | `regras-negocio.md` |
| Equipamentos | `equipamentos.json` e `matriz-equipamentos.md` |
| Textos enviados ao cliente | `src/sofia_chatbot/flow.py` e `guardrails.py` |
| Textos-base (referencia historica, nao carregada) | `mensagens.json` |
| Fluxo atual no Maxbot | `roteiro-maxbot.md` |
| Fluxo executavel da Meta | `src/sofia_chatbot/flow.py` |
| Cenarios de aceite | `testes-mvp.md` e `tests/` |

Qualquer mudanca compartilhada de regra ou mensagem deve ser refletida nos dois
canais e validada com `scripts/homologar_canais.py`.

## Restricoes de seguranca

- Nunca habilite envio real sem autorizacao explicita e credenciais do ambiente
  de teste.
- Mantenha `WHATSAPP_SEND_MESSAGES=false` no desenvolvimento local.
- Mantenha `MAXBOT_SEND_MESSAGES=false` no desenvolvimento local.
- O webhook Maxbot exige `MAXBOT_WEBHOOK_SECRET` no caminho. Nunca grave ou
  exponha o token da API.
- Mantenha `MAXBOT_PILOT_MODE=true`. Somente telefones em
  `MAXBOT_PILOT_PHONES` ou contatos no segmento configurado podem receber
  resposta.
- Mensagem de atendimento humano e sessao em handoff sao sempre silenciosas.
- Ao expor o webhook, use `LOCAL_API_ENABLED=false` e
  `DEBUG_ENDPOINTS_ENABLED=false`.
- Nao grave tokens no repositorio. Use `.env.example` apenas como referencia.
- Nao exponha texto da conversa, resumo do lead ou detalhes de excecao no ACK
  HTTP do webhook.
- Preserve a deduplicacao e o comportamento de retry: falhas de processamento
  devem permitir que a Meta reenvie a mensagem.
- `data/*.db` pode conter PII. Nao copie, publique ou inspecione dados reais sem
  necessidade e autorizacao.
- O expurgo so deve remover registros com `--confirmar`, depois de aprovada a
  politica de retencao da empresa.

## Pendencias reais (dependem da SS Vale ou acesso externo)

1. Conta WABA, numero de teste/oficial e credenciais da Meta.
2. URL publica HTTPS para o webhook.
3. Destino real do handoff humano (CRM, painel, grupo, e-mail etc.).
4. Comportamento depois do handoff e criterio para reiniciar uma conversa.
5. Templates oficiais aprovados pela Meta.
6. Politica de retencao, expurgo e acesso a logs com PII/LGPD.
7. Regras comerciais finais e aceite do time da SS Vale.
8. Convivencia entre o menu atual do Maxbot e a Sofia via API.
9. Confirmacao do suporte Maxbot sobre abertura/encaminhamento de protocolo em
   conversa iniciada pelo cliente. Nao ativar `open_followup` por suposicao.

Decisao provisoria de convivencia: usar o numero atual em janela curta e
controlada. A ordem obrigatoria e: desativar menu, confirmar, ativar Sofia;
depois desligar Sofia, confirmar e restaurar menu. Nunca deixar ambos ativos.

Nao invente essas decisoes. Quando uma tarefa depender delas, apresente a
recomendacao e solicite a decisao necessaria.

## Proximo objetivo recomendado

O adaptador Maxbot e o controle de piloto ja estao implementados e validados
localmente. A convivencia aprovada e: menu para contatos comuns, Sofia somente
para a lista/segmento do piloto e silencio durante handoff/atendimento humano.
Antes do teste real:

1. Obter uma URL HTTPS estavel e configurar um segredo URL-safe no caminho.
2. Configurar o token somente por variavel de ambiente.
3. Expor somente o webhook, com `MAXBOT_SEND_MESSAGES=false`,
   `LOCAL_API_ENABLED=false` e `DEBUG_ENDPOINTS_ENABLED=false`.
4. Garantir no painel que o menu nao responda aos mesmos contatos do piloto;
   preferir numero/canal de teste separado.
5. Validar payload real, deduplicacao e bloqueio durante atendimento humano.
6. Ativar o envio apenas no ambiente controlado, com acompanhamento e plano de
   desligamento.
7. Confirmar que `maxbot_error` permanece em zero e executar novamente suite,
   smoke test e homologacao.

Antes de clientes reais, o handoff humano, o pos-handoff, os templates e a
politica de dados precisam estar resolvidos.

## Forma de trabalhar

- Antes de alterar codigo, reproduza o comportamento e leia os testes
  relacionados.
- Para toda correcao ou mudanca de fluxo, adicione teste de regressao.
- Depois de alteracoes em regras compartilhadas, execute os tres comandos de
  validacao.
- Atualize `MVP_STATUS.md` e os documentos afetados quando o estado mudar.
- Prefira mudancas pequenas e mantenha o envio real desligado durante testes.
- Ao encerrar uma etapa, registre o que mudou, o que foi validado e quais
  decisoes externas continuam pendentes.
