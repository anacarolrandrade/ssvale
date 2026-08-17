# Chamado ao suporte Maxbot

Texto pronto para enviar. As perguntas 1 a 4 destravam o handoff real; as 5 e 6
sairam do diagnostico de deploy e afetam a seguranca do piloto.

Envie tudo de uma vez, numerado. Suporte responde melhor pergunta especifica
que mostra leitura previa da documentacao, e pior um "como faco a integracao?".

---

## Texto a enviar

**Assunto:** Integracao via API - duvidas sobre abertura de protocolo, webhook por canal e reenvio

Bom dia.

Somos da conta da **SS Vale**. Temos a API Maxbot ativada (token gerado em
19/05/2026) e ja validamos o webhook `Mensagem Recebida` e o `send_text` em
teste controlado no numero oficial: recebemos a mensagem, processamos em um
sistema externo e respondemos ao contato com sucesso.

Estamos agora preparando um piloto com **um segundo numero dedicado**, em que
um sistema externo faz a triagem inicial (identifica o assunto, coleta alguns
dados) e depois **encaminha o atendimento a uma pessoa do setor correspondente**.

Temos seis duvidas. Consultamos a documentacao em
`https://wiki.maxbot.com.br/pt-br/api-maxbot` e nao encontramos resposta para
elas.

---

### Sobre a abertura e o encaminhamento do protocolo

**1.** Quando o **cliente inicia a conversa** e o Maxbot ja abre um protocolo
automatico, qual o metodo correto para encaminhar esse atendimento a um setor?

O `open_followup` e o caminho adequado nesse cenario, ou ele criaria um
**segundo protocolo** para um contato que ja tem um em aberto? Existe metodo
proprio para transferir/atribuir um protocolo ja existente a um setor?

**2.** Caso o `open_followup` seja o caminho, ele exige informar um template.
Qual template devemos usar para **nao disparar uma mensagem adicional ao
cliente**? Ja teremos conversado com ele; uma mensagem automatica no momento da
transferencia apareceria como duplicada.

**3.** Para direcionar ao setor certo, o `get_service_sector` retorna os
identificadores que devemos usar no encaminhamento? Precisamos direcionar para
**Comercial**, **Compras** e **Compras Online**. Qual campo do retorno deve ser
enviado, e em qual parametro?

**4.** Ao abrir ou encaminhar o protocolo pela API, existe risco de o **menu de
atendimento automatico ser acionado novamente** para esse contato? Se sim, como
evitar? Precisamos que, depois da triagem, o contato va direto para a fila do
setor, sem rever o menu.

---

### Sobre webhook com dois numeros no mesmo cadastro

**5.** Vamos operar **dois canais** (dois numeros de WhatsApp) na mesma conta.

a) A URL de webhook e configuravel **por canal**, ou e unica para a conta
inteira?

b) Se for unica, como identificamos **por qual numero/canal** a mensagem
chegou? No retorno documentado de `Mensagem Recebida` encontramos o campo
`origin` (que indica a plataforma: WhatsApp, Telegram, etc.), mas nenhum campo
que identifique o canal de destino. Existe algum campo para isso que nao esteja
na documentacao?

Isso e importante porque o sistema externo deve responder **somente** aos
contatos do numero do piloto, sem interferir no atendimento normal do numero
principal.

---

### Sobre reenvio do webhook

**6.** Qual o comportamento do Maxbot quando a URL do webhook **nao responde**
ou responde com **status diferente de 2xx** (por exemplo HTTP 500, ou timeout)?

a) A mensagem e **reenviada**? Se sim, quantas tentativas e com qual intervalo?

b) Qual o **tempo maximo** que o Maxbot aguarda a resposta do webhook antes de
considerar falha?

Perguntamos porque hoje nosso sistema responde 500 em falha temporaria,
supondo que isso provocaria um reenvio. Se o Maxbot nao reenvia, precisamos
tratar a falha de outra forma para nao perder mensagem de cliente.

---

Obrigada. Se for mais pratico tratar por telefone ou reuniao, temos
disponibilidade.

Ana Carolina Rodrigues
WeUp - parceira tecnica da SS Vale

---

## Depois que a resposta chegar

| Resposta | O que muda no projeto |
|---|---|
| 1 a 4 respondidas | Fase 4 do `PLANO-PILOTO-PRODUCAO.md` sai do bloqueio; handoff real pode ser implementado |
| `open_followup` nao serve | Vale o plano B: gravar o resumo com `put_protocol_annotation` no protocolo existente, ou enviar por e-mail ao Comercial |
| 5a: webhook por canal | Protecao extra alem da allowlist de telefone; o numero principal deixa de chegar ao sistema |
| 5a: webhook unico por conta | `MAXBOT_PILOT_MODE=true` deixa de ser opcional e vira a unica barreira. Registrar isso como risco aceito do piloto |
| 6a: reenvia | O tratamento atual (HTTP 500 em falha) esta correto e protege de fato |
| 6a: nao reenvia | O 500 e decorativo. Precisamos de fila local ou nova tentativa interna antes de responder o ACK |

## Enquanto a resposta nao chega

Nada aqui bloqueia a Fase 3 (`B5` observabilidade e `B6` expiracao do handoff),
que nao depende do Maxbot e e onde esta o maior risco operacional do piloto.
