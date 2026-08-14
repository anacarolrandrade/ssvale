# Operacao do piloto Sofia + Maxbot

Procedimento aprovado em 04/08/2026 para testar a Sofia sem disputar a conversa
com o menu atual ou com um atendente humano.

## Decisao operacional atual

Enquanto a SS Vale nao disponibiliza um segundo numero, o piloto sera feito no
numero atual, durante uma janela curta e controlada. Nessa janela, o menu
automatico precisa ser silenciado antes de habilitar a resposta real da Sofia.
Ao terminar ou diante de qualquer problema, o envio da Sofia deve ser desligado
antes de restaurar o menu.

O teste real de 04/08/2026 confirmou que a chave global `Interacao` nao pode
ser desativada: ela tambem interrompe os webhooks. O procedimento correto no
painel e manter `Ativada - Direcionando Atendimentos`, deixar a mensagem de
boas-vindas vazia e ocultar temporariamente os tres itens publicados do menu
principal.

## Regra de propriedade

| Situacao | Proprietario da conversa | Sofia responde? |
|---|---|---|
| Contato comum | Menu atual do Maxbot | Nao |
| Contato do piloto, sem atendimento | Sofia | Sim |
| Sofia concluiu e pediu handoff | Humano pendente | Nao, depois da confirmacao final |
| Protocolo com atendente humano | Atendente humano | Nao |
| Protocolo automatico do telefone piloto, durante janela | Sofia | Sim, somente com excecao explicita |
| Atendimento encerrado e reset confirmado | Menu ou Sofia, conforme elegibilidade | Sim, em nova sessao |

## Protecoes implementadas

- `MAXBOT_PILOT_MODE=true` por padrao.
- Elegibilidade por segmento (`SOFIA_API_PILOTO`) ou lista de telefones.
- Contratos dos webhooks `Mensagem Recebida` e
  `Mensagem Recebida em Atendimento` tratados separadamente.
- `contact.in_attendance=1`, `prot_id` ou sessao em handoff impedem resposta por
  padrao.
- A excecao `MAXBOT_PILOT_ALLOW_ATTENDANCE=true` exige simultaneamente modo
  piloto, telefone autorizado e `prot_id`. Manter `false` fora da janela.
- ACK HTTP contem somente contagens.
- Envio real permanece desligado por padrao.
- Reset de sessao exige confirmacao explicita.

## Configuracao local

```text
MAXBOT_WEBHOOK_SECRET=<segredo-url-safe>
MAXBOT_API_TOKEN=<somente-variavel-de-ambiente>
MAXBOT_CHANNEL_TOKEN=
MAXBOT_PILOT_MODE=true
MAXBOT_PILOT_SEGMENT=SOFIA_API_PILOTO
MAXBOT_PILOT_PHONES=5531999990001,5531999990002
MAXBOT_PILOT_ALLOW_ATTENDANCE=false
MAXBOT_SEND_MESSAGES=false
LOCAL_API_ENABLED=false
DEBUG_ENDPOINTS_ENABLED=false
```

O contato e elegivel quando o telefone esta na lista **ou** quando o payload
contem o segmento configurado. Nunca grave os tokens neste arquivo ou em outro
arquivo do projeto.

## Ordem do teste

1. Definir data, horario, duracao, responsavel e telefones internos do teste.
2. Confirmar que nao ha atendimento humano em andamento nos telefones usados.
3. Manter o menu atual ativo enquanto toda a preparacao tecnica e feita com
   `MAXBOT_SEND_MESSAGES=false`.
4. Configurar uma URL HTTPS estavel no formato
   `/webhook/maxbot/<MAXBOT_WEBHOOK_SECRET>` para os eventos `Mensagem Recebida`
   e `Mensagem Recebida em Atendimento`.
5. Com envio ainda desligado, confirmar recebimento/ACK nos logs.
6. No inicio da janela, manter a Interacao global ativada, apagar
   temporariamente a mensagem de boas-vindas e ocultar os tres itens publicados
   do menu principal.
7. Somente depois de confirmar o menu inativo, ativar
   `MAXBOT_PILOT_ALLOW_ATTENDANCE=true` e `MAXBOT_SEND_MESSAGES=true`.
8. Testar um telefone interno autorizado e outro nao autorizado.
9. Simular atendimento humano e confirmar `processed=0`, `ignored=1`.
10. Executar os cenarios de aceite e acompanhar `maxbot_error`.
11. No fim da janela, desligar primeiro `MAXBOT_SEND_MESSAGES=false` e
    `MAXBOT_PILOT_ALLOW_ATTENDANCE=false`.
12. Confirmar que a Sofia parou de enviar e somente entao restaurar o menu.

Nunca manter o menu e o envio da Sofia ativos ao mesmo tempo no numero atual.

## Criterios de interrupcao imediata

Interromper o teste e executar o retorno ao menu se ocorrer qualquer um destes
eventos:

- menu e Sofia respondendo na mesma conversa;
- Sofia respondendo durante atendimento humano;
- mensagem duplicada;
- resposta comercial proibida;
- erro `maxbot_error`;
- demora ou indisponibilidade que afete o atendimento normal;
- entrada de cliente real fora do grupo autorizado.

## Retorno seguro ao atendimento atual

1. Definir `MAXBOT_SEND_MESSAGES=false` e
   `MAXBOT_PILOT_ALLOW_ATTENDANCE=false`.
2. Confirmar nos logs que nao existem novos envios da Sofia.
3. Se necessario, remover temporariamente a URL do webhook.
4. Restaurar a mensagem de boas-vindas e os tres itens publicados do menu
   automatico do Maxbot.
5. Fazer uma mensagem de teste e confirmar que somente o menu responde.
6. Registrar horario, resultado e qualquer incidente observado.

## Reset depois do atendimento

Primeiro simule:

```powershell
py scripts/resetar_sessao.py --session-id 5531999990001
```

Depois de confirmar que o protocolo humano terminou:

```powershell
py scripts/resetar_sessao.py --session-id 5531999990001 --confirmar
```

O reset e individual. Nao existe reset automatico durante o piloto.

## Bloqueio atual do handoff real

O backend ja gera o resumo e muda a propriedade para `human_pending`, mas ainda
nao abre nem transfere protocolo automaticamente. A documentacao do Maxbot
oferece `open_followup`, que exige template, setor e contato, e
`put_protocol_annotation`, que exige um `prot_id` existente.

Antes de implementar essa chamada, confirmar com o suporte Maxbot:

1. Se `open_followup` deve ser usado quando o cliente acabou de iniciar a
   conversa e a janela de atendimento esta aberta.
2. Qual template deve ser informado sem gerar uma mensagem duplicada.
3. Quais IDs usar para Comercial, Compras e Compras Online.
4. Como evitar que o menu seja acionado ao abrir o protocolo.

Ate essas respostas, o piloto pode validar entrada, conversa e silencio, mas
nao deve atender clientes reais que dependam do handoff de ponta a ponta.

## Validacao local obrigatoria

```powershell
py -m unittest discover -s tests
py scripts/smoke_test.py
py scripts/homologar_canais.py
```

Resultado validado apos a primeira janela: 75 testes, smoke test aprovado e
homologacao de 5 cenarios/26 interacoes nos tres canais.
