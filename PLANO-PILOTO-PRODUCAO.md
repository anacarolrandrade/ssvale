# Plano do piloto em producao - Sofia / SS Vale

Etapa 2 de tres: **diagnostico -> plano -> implementacao**.
Depende de `DIAGNOSTICO-DEPLOY.md`, que identifica os itens B1 a B13 citados aqui.

Escrito em 13/08/2026. Nenhum codigo foi escrito ainda.

---

## Decisoes ja tomadas

| Decisao | Escolha | Consequencia |
|---|---|---|
| Segundo numero | Liberado pela SS Vale | Acaba a janela manual; piloto pode durar semanas |
| Infraestrutura | Conta da SS Vale | Voce configura, eles pagam e sao donos dos dados |
| Handoff | Ponta a ponta | **Depende do suporte Maxbot.** Chamado no dia 1 |

A escolha do handoff ponta a ponta e a unica que introduz dependencia externa
com prazo desconhecido. Todo o plano abaixo foi organizado para que ela nao
pare mais nada: o chamado sai primeiro, e as fases 1 a 3 avancam em paralelo.

---

## Recomendacao de hospedagem

**VPS pequeno em regiao brasileira, com Caddy e systemd.**

Concretamente: uma maquina de 1-2 vCPU e 2 GB, contratada em nome da SS Vale,
em provedor com datacenter no Brasil (Magalu Cloud, Locaweb, Hostinger BR, ou
AWS/GCP/Azure Sao Paulo). Custo tipico de R$ 30 a R$ 80 por mes.

### Por que esta, e nao uma PaaS

Considerei Render e Railway, que sao mais simples de comecar. Quatro motivos
inclinaram para o VPS **neste caso especifico**:

1. **O SQLite passa a ser um nao-problema.** O B3 (disco efemero) e o bloqueio
   mais chato do diagnostico. Em PaaS ele exige configurar volume, aceitar
   instancia unica e conviver com detach/attach a cada deploy. Em VPS, disco
   persistente e o comportamento padrao. O problema deixa de existir em vez de
   ser gerenciado.
2. **Os dados ficam no Brasil.** Sao dados de clientes da SS Vale, sob a conta
   deles. Render nao tem regiao no Brasil — Sao Paulo ainda e pedido aberto de
   funcionalidade. Hospedar fora e legal, mas exige incorporar as
   clausulas-padrao contratuais da ANPD (Resolucao CD/ANPD nº 19/2024, com
   prazo de adequacao ja encerrado em 23/08/2025). Manter no Brasil elimina a
   conversa inteira. Nao sou advogada e voce tambem nao — evitar o tema custa
   menos que resolve-lo.
3. **A entrega ao final e trivial.** Terminado o piloto, transferir um servidor
   para a TI da SS Vale e entregar credenciais. E o caminho mais curto para
   voce nao virar infraestrutura permanente deles, que era sua restricao.
4. **Voce tem 10 anos de .NET e PostgreSQL.** Um systemd e um Caddyfile nao sao
   territorio novo para voce. O que seria novo sao os conceitos proprios de
   cada PaaS — volume, workspace fee, cold start, health check que derruba o
   servico. Menos pecas, no seu caso, significa menos plataforma, nao menos
   servidor.

O custo real do VPS e voce manter o sistema operacional atualizado. Para um
piloto delimitado, isso e cerca de uma hora de setup e um `apt upgrade`
ocasional. TLS e automatico com o Caddy.

**Alternativa**, se a TI da SS Vale nao aceitar administrar um servidor: Render,
disco persistente a US$ 0,25/GB/mes, com as clausulas-padrao da ANPD
incorporadas ao contrato. Funciona; so troca trabalho de sysadmin por trabalho
juridico.

### Pecas finais

```
Maxbot  --HTTPS-->  Caddy (TLS automatico)  -->  Sofia (systemd)  -->  SQLite
                                                       |
                                                  journald (logs)
                    monitor externo de uptime  -->  /health
```

Quatro pecas, uma maquina, uma conta. Sem banco gerenciado, sem fila, sem
container orquestrado, sem CDN.

---

## Fase 0 — Destravar o que depende de terceiros

**Quando:** dia 1. **Seu tempo:** ~1h. **Calendario:** dias ou semanas.

Nada aqui e trabalho tecnico. E tudo coisa que so anda se for pedida cedo.

1. **Abrir o chamado no suporte Maxbot** com as seis perguntas consolidadas.
   Texto pronto em `CHAMADO-SUPORTE-MAXBOT.md`. Duas dessas perguntas sao
   novas e vieram do diagnostico, nao estavam no material anterior.
2. **Pedir a SS Vale:** contratacao do VPS em nome deles, e confirmacao de que
   o segundo numero ja esta ativo como canal no Maxbot.
3. **Rodar `get_channel`** para obter o token de cada canal. Isso resolve o
   problema de a Sofia responder pelo numero errado, e e uma chamada de leitura
   — nao envia nada a ninguem.
4. **Conferir no painel** se o webhook pode ser configurado por canal ou se e
   por conta. Isso muda o desenho da protecao contra trafego real.

---

## Fase 1 — Fundacao

**Quando:** semana 1. **Estimativa:** ~3h. Resolve B1, B11, B12, B13.

1. `git init`, primeiro commit, remoto privado. Conferir que `.env`, `data/` e
   `.runtime/` ficam de fora — o `.gitignore` atual ja esta correto.
   Excluir tambem `revisao-recebida-fable-5/` (53 MB de copia historica) e o
   `.zip` da raiz.
2. **Rotacionar os dois segredos.** O `MAXBOT_WEBHOOK_SECRET` circulou em texto
   plano em `.runtime/WEBHOOK-URL-MAXBOT.txt`, e o token da API so existe na
   sua maquina, sem backup. Gerar novos e guardar no cofre da SS Vale.
3. Criar `requirements.txt` (vazio, com comentario explicando que e stdlib
   puro), fixar a versao do Python e escrever o `systemd unit` e o `Caddyfile`.
4. Provisionar o VPS, apontar um subdominio, subir com
   `MAXBOT_SEND_MESSAGES=false`.
5. Validar: `/health` responde, o webhook responde ACK, e **nenhuma mensagem
   sai**. Este e o mesmo teste de fumaca que voce ja fez em 04/08, agora fora
   da sua maquina.

**Criterio de saida:** o Maxbot posta em uma URL estavel, recebe ACK, e a Sofia
nao responde nada a ninguem.

---

## Fase 2 — As cinco correcoes pontuais

**Quando:** semana 2. **Estimativa:** ~3h. Resolve B2, B4, B7, B9, B10.

Sao pequenas e independentes entre si. Cada uma com teste de regressao, como
manda o `CLAUDE.md`.

| Item | Correcao | Teste de regressao |
|---|---|---|
| B2 | Ancorar `.env` e `data/` em caminho absoluto vindo de variavel, nao do cwd | Subir a app de outro diretorio e provar que o segredo carrega |
| B4 | `host` padrao `0.0.0.0`; aceitar `PORT` alem de `SOFIA_PORT` | Config le `PORT` quando presente |
| B7 | Tratar `SIGTERM`: parar de aceitar, terminar o que esta em voo, sair | Envio de sinal encerra sem perder mensagem marcada |
| B9 | Baixar o timeout do `send_text` de 30s para ~10s | Timeout levanta erro tratado e desmarca a mensagem |
| B10 | Usar horario de Brasilia explicito em `msg_date_sql` e nos eventos | Evento gravado bate com o fuso esperado |

**B2 e o mais importante dos cinco.** Ele e a diferenca entre "nao funcionou e
eu descobri em 30 segundos" e "nao funcionou e eu perdi uma tarde".

**Criterio de saida:** os 93 testes continuam passando, mais os novos. Smoke
test, homologacao e ensaio aprovados.

---

## Fase 3 — Operacao: as duas lacunas que importam

**Quando:** semana 3. **Estimativa:** ~4h. Resolve B5 e B6.

Esta e a fase que decide se voce vira suporte permanente do cliente. As fases
1 e 2 sao encanamento; esta e o escopo real de engenharia do piloto.

### B5 — Enxergar o que esta acontecendo

Hoje o processo nao emite log nenhum e toda observabilidade depende de scripts
locais lendo o arquivo `.db`.

1. Log estruturado em `stdout`, capturado pelo `journald`. Uma linha por
   mensagem: horario, evento, sessao mascarada, bloco, resultado. **Sem texto
   de conversa e sem dados de lead** — o log operacional nao pode virar um
   segundo deposito de PII.
2. Um endpoint `/status` autenticado por token, devolvendo os mesmos contadores
   do `janela_teste.py status`: processadas, duplicadas, ignoradas, erros.
   Contagens, nunca conteudo. E o que substitui o "abrir shell no servidor".
3. Monitor externo de uptime batendo em `/health`, com alerta por e-mail ou
   WhatsApp para voce. Gratuito e leva 10 minutos.

### B6 — Tirar o cliente do `handoff` sem voce

Hoje quem completa o fluxo fica mudo para sempre, e so um script rodado por
voce libera. Com um numero dedicado e um piloto de semanas, isso deixa de ser
detalhe e vira o defeito mais visivel.

Proposta: expiracao automatica por tempo. Passado o prazo sem atividade, a
sessao volta ao estado inicial sozinha e o cliente que escrever de novo e
atendido normalmente.

**Isto precisa de uma decisao da SS Vale, nao sua:** qual prazo? Minha
sugesticao e 24 horas, por ser mais longo que um dia comercial e curto o
bastante para o cliente que volta no dia seguinte nao encontrar silencio. Mas
quem conhece o ritmo do Comercial deles e eles.

Importante: a expiracao vale para o `handoff` da Sofia. Ela **nao** pode
sobrepor o silencio durante atendimento humano ativo, que continua sendo
decidido pelo `in_attendance` do proprio Maxbot a cada mensagem.

**Criterio de saida:** voce consegue responder "a Sofia esta de pe e respondeu
quantas mensagens hoje?" sem abrir um terminal, e nenhum cliente fica preso.

---

## Fase 4 — Handoff real

**Quando:** semana 4, ou quando o suporte Maxbot responder. **Estimativa:** ~4h
depois da resposta.

Depende inteiramente da Fase 0. O desenho provavel, a confirmar:

1. Ao concluir a coleta, gravar o resumo do lead com
   `put_protocol_annotation` no `prot_id` que o proprio webhook de atendimento
   ja entrega.
2. Encaminhar ao setor correto (Comercial, Compras ou Compras Online) conforme
   o ramo do fluxo, usando os IDs obtidos via `get_service_sector`.
3. So entao marcar a sessao como `handoff`.

**Se o suporte demorar ou responder que nao da:** existe um plano B que nao
depende deles. O protocolo automatico do Maxbot ja abre sozinho, e a conversa
inteira ja fica visivel no painel para o atendente. O resumo pode ir por
anotacao no protocolo ou, no limite, por e-mail ao Comercial. Nao e elegante,
mas entrega o valor — o vendedor recebe um lead qualificado em vez de um "oi".

Vale conversar com a SS Vale sobre esse plano B **antes** de o chamado voltar,
para que a resposta do Maxbot deixe de ser bloqueante para o piloto inteiro.

---

## Fase 5 — Entregar a operacao

**Quando:** semana 5. **Estimativa:** ~2h.

O item 4 do seu briefing: o que a SS Vale precisa saber fazer sem te chamar.

1. **Runbook de uma pagina**, em linguagem de negocio, com: como desligar a
   Sofia (uma variavel, um restart), como saber se ela esta no ar, o que fazer
   se um cliente reclamar, e quando ligar para voce.
2. **Botao de panico.** Desligar a Sofia precisa ser uma acao de uma linha que
   qualquer pessoa da SS Vale execute, sem esperar por voce. Isso e requisito
   de seguranca, nao de conveniencia.
3. **Criterio de sucesso e data de fim**, acordados por escrito.
4. **Plano de desligamento:** o que acontece com o servidor, os dados e o
   numero quando o piloto terminar.

---

## Criterio de sucesso do piloto — a definir com a SS Vale

Voce escreveu que o piloto precisa de criterio de sucesso definido. Ele ainda
nao existe. Sugestao de forma, para eles preencherem os numeros:

- **Escopo:** um numero, o fluxo atual, sem novas funcionalidades.
- **Periodo:** 4 semanas corridas, com data de inicio e fim.
- **Volume esperado:** N conversas.
- **Aprovado se:** X% das conversas chegam ao resumo completo; zero respostas
  comerciais proibidas; zero mensagens duplicadas; zero respostas por cima de
  atendente humano; `maxbot_error` em zero.
- **Reprovado se:** qualquer criterio de interrupcao imediata do
  `ROTEIRO-JANELA-2.md` ocorrer duas vezes.

Sem isso escrito, "o piloto deu certo?" vira discussao de opiniao no fim, e
essa e uma conversa que voce nao quer ter com um cliente.

---

## Resumo de esforco

| Fase | Entrega | Horas | Semana |
|---|---|---|---|
| 0 | Chamado Maxbot, VPS pedido, tokens de canal | 1h | 1 |
| 1 | Repo, segredos rotacionados, VPS no ar, ACK | 3h | 1 |
| 2 | Cinco correcoes com regressao | 3h | 2 |
| 3 | Log, `/status`, monitor, expiracao de handoff | 4h | 3 |
| 4 | Handoff real | 4h | 4 |
| 5 | Runbook, botao de panico, criterios | 2h | 5 |

**Total: ~17h de trabalho tecnico, distribuidas em 5 semanas de calendario.**
Cabe com folga em 8h/semana. A folga e proposital: o calendario e ditado pelo
suporte Maxbot e pela SS Vale, nao pelo seu tempo de teclado.

---

## O que continua fora do escopo

Deliberadamente, para o piloto nao inchar:

- Migracao para a WhatsApp Business Platform da Meta. O adaptador existe e os
  testes passam, mas ativa-lo agora dobra a superficie de risco sem necessidade.
- Qualquer uso de LLM. O fluxo deterministico e uma vantagem aqui: sem custo por
  mensagem, sem latencia, sem alucinacao a auditar.
- Politica definitiva de retencao e expurgo. O `expurgar_eventos.py` existe em
  modo simulacao; a aprovacao da politica e da SS Vale e nao bloqueia o piloto,
  desde que o periodo seja curto e delimitado.
- Alto volume. SQLite atende o piloto com folga. Trocar de banco antes de haver
  volume real e otimizacao prematura.

---

## Proximo passo imediato

Enviar `CHAMADO-SUPORTE-MAXBOT.md` ao suporte e pedir o VPS a SS Vale. As duas
coisas levam menos de uma hora e sao as unicas que dependem do calendario dos
outros.

## Fontes

- [Regulamento de Transferencia Internacional de Dados - ANPD](https://www.gov.br/anpd/pt-br/assuntos/assuntos-internacionais/transferencia-internacional-de-dados)
- [LGPD Art. 35 - Clausulas contratuais padrao](https://lgpd-brasil.info/capitulo_05/artigo_35)
- [Render - pedido de regiao Brasil (Sao Paulo)](https://feedback.render.com/features/p/brazil-sau-paulo-region)
- [Railway - Volumes](https://docs.railway.com/volumes/reference)
- [API Maxbot | Maxbot WIKI](https://wiki.maxbot.com.br/pt-br/api-maxbot)
