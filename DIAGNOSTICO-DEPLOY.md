# Diagnostico de prontidao para deploy - Sofia / SS Vale

Levantamento em 13/08/2026. Somente leitura: nenhum arquivo do projeto foi
alterado, nenhuma chamada externa foi feita, nenhum envio foi ligado.

Este documento e a etapa 1 de tres: **diagnostico -> plano -> implementacao**.
Nao contem plano de hospedagem nem codigo.

---

## a) Como o projeto esta estruturado hoje

### Numeros

- 2.304 linhas de Python em `src/`, mais scripts e testes.
- **Zero dependencias de terceiros.** So biblioteca padrao
  (`http.server`, `sqlite3`, `urllib`, `hmac`, `json`).
- 93 testes, executados nesta sessao em Linux/Python 3.10: `Ran 93 tests ... OK`.
- `pyproject.toml` declara `requires-python >=3.11`, mas o codigo roda em 3.10.

### Desenho

```
webhook Maxbot  ->  api.py  ->  flow.py  ->  session_store (SQLite)
                      |            |
                      |            +-> guardrails.py
                      +-> event_log (SQLite)
                      +-> channels/maxbot.py -> POST app.maxbot.com.br
```

Tres camadas bem separadas, e essa separacao e a maior qualidade do projeto:

| Camada | Arquivos | Papel |
|---|---|---|
| Regra de negocio | `flow.py`, `guardrails.py`, `domain.py` | Agnostica de canal |
| Canal | `channels/maxbot.py`, `channels/whatsapp.py` | Traduz payload |
| Transporte | `api.py` | HTTP, dedup, ACK |

A camada de LLM existe (`llm/`) mas o provedor ativo e o `mock`. O fluxo e
100% deterministico, como voce descreveu. Isso e uma vantagem para deploy:
sem chave de LLM, sem custo por mensagem, sem latencia de inferencia.

### O que o codigo ja faz bem

- Deduplicacao por `msg_id`, com desmarcacao em caso de falha.
- ACK minimo no webhook (nao vaza conversa nem lead).
- Segredo no caminho do webhook, comparado com `hmac.compare_digest`.
- Allowlist de piloto por telefone ou segmento.
- Silencio obrigatorio em atendimento humano e em `handoff`.
- Limite de corpo (1 MB) com drain antes de responder 413.
- Envio real desligado por padrao (`dry_run`).

Isso e mais disciplina de seguranca do que a maioria dos MVPs tem. O problema
nao e o codigo. E tudo que esta em volta dele.

---

## b) O que impede de rodar fora da sua maquina

Ordenado por gravidade real, nao por dificuldade.

### B1. Nao existe controle de versao — BLOQUEANTE

`.git/` existe mas esta **vazia**. `git log` responde
`not a git repository`. Nao ha historico, branch, tag nem remoto.

Consequencias diretas:

- Toda plataforma de hospedagem moderna faz deploy a partir de um repositorio.
  Sem repo, so resta upload manual ou copia por SSH.
- Nao ha como saber o que mudou entre a janela de 04/08 e a de 11/08 alem do
  que voce escreveu a mao no `MVP_STATUS.md`.
- Nao ha rollback. Se o piloto quebrar, nao existe "volta pra versao anterior".
- O projeto so existe em um HD. Um disco perdido = cliente sem sistema.

Isso precisa ser resolvido antes de qualquer discussao de hospedagem.

### B2. Falha silenciosa por diretorio de trabalho — BLOQUEANTE

`config.py` carrega `load_settings(".env")` e `session_store` usa
`data/sofia_sessions.db`. Ambos **relativos ao diretorio de onde o processo foi
iniciado**, nao ao codigo.

Verificado nesta sessao: iniciando o processo de outro diretorio,
`maxbot_webhook_secret` volta vazio. E `verify_maxbot_webhook_path` retorna
`False` quando o segredo esta vazio.

Resultado pratico no ar: **o Maxbot posta, recebe 404, e a Sofia nunca
responde — sem nenhum erro, sem nenhum log.** O sistema sobe, o `/health`
responde `ok`, e nada funciona. E o modo de falha mais caro de diagnosticar
que existe, e ele so aparece fora da sua maquina.

Junto com isso, um segundo efeito: o SQLite e criado vazio no novo caminho.
Sessoes e dedup sao perdidos sem aviso.

### B3. Persistencia em disco efemero — BLOQUEANTE

Dois bancos SQLite em `data/`: sessoes e eventos. Em quase toda hospedagem
gerenciada, o disco do container e apagado a cada deploy e a cada reinicio.

Se isso acontecer no meio do piloto:

- Conversas em andamento voltam ao inicio do menu, do nada, para o cliente.
- A tabela `processed_messages` zera. Se o Maxbot reenviar uma mensagem depois
  do restart, ela e tratada como nova e **o cliente recebe a resposta duas
  vezes**. Duplicidade e um dos seus criterios de interrupcao imediata.
- O log de eventos, que e sua unica evidencia do que aconteceu na janela,
  desaparece.

Ha ainda uma restricao tecnica: SQLite com WAL nao funciona de forma confiavel
em sistema de arquivos de rede. Precisa de disco de bloco de verdade.

### B4. `host` padrao `127.0.0.1` — impede o container de receber trafego

`config.py` linha 33 e 95. Dentro de um container, `127.0.0.1` significa
"so eu mesmo": o roteador da plataforma nao alcanca o processo. Precisa ser
`0.0.0.0`.

Alem disso, a maioria das plataformas injeta a porta na variavel `PORT`, e o
codigo le `SOFIA_PORT`. Sem tratar isso, o processo escuta na porta errada e o
health check da plataforma derruba o servico em loop.

### B5. Voce fica cega — o processo nao gera log nenhum

`api.py` sobrescreve `log_message` para retornar sem imprimir. Nao ha log de
acesso, nao ha log de aplicacao, nao ha nivel de severidade. As unicas saidas
em `stdout` sao os avisos de configuracao no boot.

Todo o rastro operacional vai para `data/sofia_events.db`. E os scripts que
leem esse banco (`monitorar_eventos.py`, `status_teste_maxbot.py`,
`janela_teste.py status`) **rodam localmente, contra o arquivo**.

No ar isso significa: para saber se a Sofia respondeu, se deu erro, se filtrou
um telefone, voce precisa abrir um shell no servidor. Os endpoints `/debug/*`
existem, mas a propria regra de seguranca do projeto exige
`DEBUG_ENDPOINTS_ENABLED=false` em endpoint publico — corretamente, porque eles
devolvem PII sem autenticacao.

Este e o maior buraco para o item 4 do seu briefing (operacao).

### B6. `handoff` nao tem saida automatica — trava o cliente

Confirmado no banco atual: a sessao do telefone piloto esta em
`handoff` / `BLOCO_ENCAMINHAMENTO_COMERCIAL` desde 04/08. Ha nove dias.

A regra e correta (a Sofia nao pode falar por cima de um humano), mas nao ha
expiracao, nem por tempo nem por evento. A unica saida e
`py scripts/resetar_sessao.py --session-id <tel> --confirmar`, rodado a mao.

Extrapolando para o piloto: **todo cliente que completar o fluxo fica
permanentemente mudo para a Sofia.** Se ele voltar tres dias depois, nao recebe
nem o menu do Maxbot (voce o ocultou) nem a Sofia. Ele so ve silencio.

E o reset depende de um script rodado por voce, no servidor. Nao ha como a SS
Vale resolver isso sozinha. Isso viola diretamente sua restricao de nao virar
infraestrutura permanente do cliente.

### B7. Sem parada limpa

`run_server` chama `serve_forever()` sem tratar `SIGTERM`. Todo deploy e todo
restart mata o processo no meio do que estiver acontecendo.

O caminho perigoso: a mensagem e marcada como processada **antes** do envio.
O `except` desmarca em caso de excecao — mas um `SIGKILL` nao levanta excecao.
A mensagem fica marcada como processada e nunca foi respondida. Perda
silenciosa, sem retry.

### B8. O modelo de retry foi desenhado para a Meta, nao para o Maxbot

O codigo devolve HTTP 500 em falha de processamento, deliberadamente, para que
a plataforma reenvie. Isso e o contrato documentado da Meta.

**A documentacao do Maxbot nao diz nada sobre retry.** Nao ha mencao a
reenvio, backoff, timeout de webhook ou tratamento de resposta nao-2xx. Se o
Maxbot nao reenviar, o 500 nao recupera nada: apenas descarta a mensagem de
forma mais educada. Pergunta em aberto para o suporte (ver secao c).

### B9. Envio sincrono dentro do webhook, com timeout de 30s

`MaxbotClient.send_message` usa `urlopen(..., timeout=30)` dentro do handler.
O ACK do webhook so sai depois que a API do Maxbot responde.

Se a API estiver lenta, o Maxbot espera ate 30 segundos pelo ACK. Se ele tiver
timeout proprio menor (nao documentado) e reenviar, a dedup ainda nao gravou o
resultado e podemos cair no caminho de duplicidade. Para volume de piloto o
risco e baixo, mas o timeout de 30s e alto demais para um handler de webhook.

### B10. Fuso horario

`channels/maxbot.py` linha 112 usa `datetime.now()` sem timezone para
`msg_date_sql`. Os `CURRENT_TIMESTAMP` do SQLite gravam em UTC.

Servidor em UTC = tres horas de diferenca do horario de Brasilia. Durante uma
janela supervisionada, em que voce compara o relogio do painel do Maxbot com o
`janela_teste.py status`, isso vira confusao na hora errada.

### B11. Segredos sem redundancia, e um segredo exposto no diretorio

`.env` esta corretamente no `.gitignore` e contem token real da conta do
cliente. Mas ele existe **apenas** na sua maquina, sem backup. Se o disco
falhar, o token do cliente se perde (recuperavel via "Gerar Novo Token", com
custo de interrupcao).

Alem disso, `.runtime/WEBHOOK-URL-MAXBOT.txt` contem em texto plano o segredo
do webhook que esta configurado no painel do cliente. `.runtime/` esta no
`.gitignore`, entao nao vaza por commit, mas o segredo circula em arquivo de
projeto. Recomendacao: rotacionar ao migrar para hospedagem.

### B12. A URL publica atual e um tunel temporario

`.runtime/WEBHOOK-URL-MAXBOT.txt` aponta para
`worked-polo-teddy-practical.trycloudflare.com`. Cloudflare Quick Tunnel: o
endereco muda a cada execucao e depende do seu notebook ligado e com rede.

Isso funciona para uma janela de duas horas com voce na frente da maquina. Nao
funciona para um piloto com periodo delimitado.

Ha tambem um passivo: o `BRIEFING-ADAPTADOR-MAXBOT.md` registra uma
configuracao antiga no painel apontando para
`right-alarm-peer-insight.trycloudflare.com`, de origem nao confirmada, em
quatro eventos. Essa URL esta morta hoje. Antes do piloto, e preciso abrir o
painel e confirmar exatamente quais eventos existem e para onde apontam.

### B13. Sem `requirements.txt`, `Dockerfile`, `Procfile` ou pin de runtime

Nao ha nenhum artefato de build. A boa noticia e que, sem dependencias de
terceiros, esses arquivos sao quase triviais de escrever. Nao e um problema,
e um item de checklist.

### Resumo da secao b

| # | Item | Gravidade | Origem |
|---|---|---|---|
| B1 | Sem controle de versao | Bloqueante | Processo |
| B2 | Caminhos relativos ao cwd, falha muda | Bloqueante | Codigo |
| B3 | SQLite em disco efemero | Bloqueante | Arquitetura |
| B4 | `host` 127.0.0.1 e `PORT` ignorada | Alta | Codigo |
| B5 | Sem log; observabilidade so local | Alta | Codigo |
| B6 | `handoff` sem saida automatica | Alta | Regra de negocio |
| B7 | Sem parada limpa (SIGTERM) | Media | Codigo |
| B8 | Retry desenhado para a Meta | Media | Pergunta em aberto |
| B9 | Envio sincrono, timeout 30s | Media | Codigo |
| B10 | Fuso horario | Baixa | Codigo |
| B11 | Segredos sem backup; segredo em arquivo | Media | Processo |
| B12 | URL publica temporaria | Bloqueante | Infra |
| B13 | Sem artefatos de build | Baixa | Processo |

Nada aqui exige refatoracao do fluxo. B2, B4, B7, B9 e B10 sao correcoes
pequenas e pontuais. B1, B3, B12 e B13 sao decisoes de infraestrutura. B5 e B6
sao os dois que mudam o que voce precisa construir, e sao os que definem se
voce vira ou nao suporte permanente do cliente.

---

## c) Integracao com o Maxbot

### Correcao importante de premissa

Voce listou a integracao Maxbot como a peca bloqueante: *"se nao fecha, nada
mais importa"*. **Ela ja fechou.** Este e o achado mais util do diagnostico.

O que ja esta comprovado, por evidencia no repositorio e nos seus registros de
04/08:

| Pergunta | Resposta | Evidencia |
|---|---|---|
| Expoe webhook de entrada? | Sim | 5 eventos documentados; 2 usados |
| Expoe API de envio? | Sim, `send_text` | Adaptador implementado e testado |
| API esta ativa na conta? | Sim, token de 19/05/2026 | Painel do cliente |
| Funcionou de ponta a ponta? | Sim | Conversa real completa em 04/08 |
| Limite por plano? | 10 req/s por token | Doc oficial |

Uma conversa real completa — menu, equipamento, tres perguntas, nome, cidade,
confirmacao — passou pelo numero oficial no dia 04/08. Entrada e saida reais.

O caminho tecnico esta validado. **O bloqueio real do projeto nao e a
integracao. E hospedagem, operacao e handoff.**

### Contratos confirmados na documentacao oficial

Conferi a wiki oficial nesta sessao. O que o adaptador implementa bate com a
documentacao:

- **Entrada:** POST JSON, sem assinatura e sem header de autenticacao. Por isso
  o segredo no caminho e a unica protecao possivel — a decisao do projeto esta
  correta.
- **Dois eventos distintos, com contratos diferentes.** `Mensagem Recebida`
  traz os dados dentro de `contact`. `Mensagem Recebida em Atendimento` traz
  `whatsapp`, `prot_id`, `contact_id` e `chat_id` no nivel raiz, **sem o objeto
  `contact`**. O parser detecta isso corretamente.
- **Saida:** `POST https://app.maxbot.com.br/api/v1.php`, `status` 1-sucesso,
  0-falha, 2-processando. Tratado.
- **Limite:** 10 requisicoes por segundo por token, HTTP 429 acima disso,
  contador reiniciado a cada segundo. Ajustavel mediante contato com o suporte.
  Irrelevante para piloto, **com uma ressalva**: o limite e por token, e o token
  e da conta inteira. Se a SS Vale usar a API para outra coisa, voces dividem a
  mesma cota.
- **So texto puro.** Nao ha botao nem lista. Menus numerados sao a unica opcao,
  e ja e assim que o renderizador funciona.
- **Emojis usam tags proprias** (`[EMOJI1]`). Emoji Unicode direto no texto e
  comportamento nao verificado. O fluxo atual nao usa emoji; manter assim.

### As quatro perguntas realmente em aberto

Nenhuma delas e sobre "o Maxbot permite?". Todas sao sobre "como fazer certo".

**1. Handoff real — a que mais importa**

Hoje a Sofia coleta, monta o resumo, confirma com o cliente e **fica em
silencio**. O resumo nao chega a ninguem. Nao ha abertura nem transferencia de
protocolo.

Os endpoints existem: `open_followup` (abre protocolo),
`put_protocol_annotation` (anota no protocolo, candidato natural para gravar o
resumo do lead), `get_service_sector` e `get_attendant` (para descobrir os IDs).
Nenhum foi chamado ainda.

Perguntas a fazer ao suporte Maxbot, exatamente estas:

1. `open_followup` pode ser usado quando o cliente acabou de iniciar a conversa
   e ja existe protocolo automatico aberto? Ou ele criaria um segundo protocolo?
2. Qual template informar sem disparar mensagem duplicada ao cliente?
3. Quais os IDs de setor de Comercial, Compras e Compras Online?
4. Como impedir que a abertura do protocolo reative o menu automatico?

Sem resposta a isso, o piloto pode validar conversa e silencio, mas **nao pode
atender cliente real que dependa do encaminhamento**. Isso limita o criterio de
sucesso do piloto e precisa ser dito ao cliente antes, nao depois.

**2. Retry do webhook** (relacionado a B8)

O Maxbot reenvia quando o webhook responde nao-2xx? Qual o timeout dele para o
ACK? Ha backoff? Nao consta na documentacao. A resposta determina se o
tratamento de erro atual protege alguma coisa ou e decorativo.

**3. Convivencia menu x Sofia**

Ha um numero so. O procedimento atual e manual e arriscado: esvaziar a saudacao,
ocultar tres itens do menu, ligar a Sofia, e desfazer tudo ao final — sem nunca
deixar os dois ativos. Funciona para uma janela de duas horas com voce olhando.
Nao funciona para um piloto de duas semanas.

As saidas possiveis: numero separado para o piloto, ou segmentacao no painel
que roteie so os contatos do piloto. A segunda depende de o Maxbot conseguir
excluir um segmento do menu — precisa ser confirmado no painel.

Esta e uma decisao da SS Vale, nao sua. E provavelmente e a que define se
existe piloto.

**4. Retencao de dados e LGPD**

`data/sofia_events.db` guarda o texto integral das conversas e os dados do lead.
Hospedar isso significa mover dados pessoais de clientes da SS Vale para um
terceiro contratado **na sua conta**, sob sua responsabilidade, sem politica de
retencao aprovada.

Voce escreveu que nao quer ser infraestrutura permanente e gratuita do cliente.
O mesmo raciocinio vale, com mais forca, para ser a controladora dos dados dele.
Vale resolver isso no contrato antes do deploy, nao depois.

---

## Leitura final

O software esta em melhor estado do que a maioria dos MVPs que chegam a esta
etapa: separacao limpa, 93 testes, guardrails, dedup, allowlist, ACK minimo, e
o caminho Maxbot ja comprovado no ar com conversa real.

O que falta nao e engenharia de aplicacao. E:

- **infraestrutura**: repo, build, disco persistente, URL estavel (B1, B3,
  B12, B13);
- **cinco correcoes pequenas e pontuais** (B2, B4, B7, B9, B10);
- **duas lacunas que definem se voce vira suporte permanente**: observabilidade
  remota (B5) e saida automatica do `handoff` (B6);
- **duas decisoes que sao do cliente, nao suas**: handoff real e convivencia com
  o menu.

A sequencia que respeita suas 8h/semana e resolver a infraestrutura e as cinco
correcoes primeiro — sao baratas e destravam tudo — e tratar B5 e B6 como o
verdadeiro escopo de engenharia do piloto.

**Antes do plano de hospedagem, tres respostas sao necessarias:** a SS Vale
libera um segundo numero? O suporte Maxbot responde sobre `open_followup`? E
quem assume os dados no periodo do piloto?

## Fontes

- [API Maxbot | Maxbot WIKI](https://wiki.maxbot.com.br/pt-br/api-maxbot)
- [Documentacao API MAXBOT v1](https://app.maxbot.com.br/doc-api-v1.php)
- Repositorio `C:\ssvale-chatbot-mvp`: `MVP_STATUS.md`,
  `BRIEFING-ADAPTADOR-MAXBOT.md`, `OPERACAO-PILOTO-MAXBOT.md`,
  `ROTEIRO-JANELA-2.md`, `INVENTARIO-MAXBOT-ATUAL.md`, `src/sofia_chatbot/`.
