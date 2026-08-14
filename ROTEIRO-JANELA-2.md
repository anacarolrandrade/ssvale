# Roteiro da segunda janela de teste - Maxbot

Preparado em 11/08/2026. Complementa `OPERACAO-PILOTO-MAXBOT.md` (procedimento)
e `CHECKLIST-JANELA-TESTE-MAXBOT.md` (registro a preencher no dia).

A primeira janela, em 04/08/2026, validou entrada real, filtro por telefone,
menu numerado, coleta e encerramento em handoff. Faltou testar no ar: guardrail
comercial, duplicidade, telefone nao autorizado e o retorno seguro ao menu.
Esta janela existe para fechar esses quatro pontos com contadores limpos.

## O que mudou desde a primeira janela

- Os quatro cenarios pendentes ja passam offline
  (`py scripts/ensaio_janela_maxbot.py`, 16 checagens).
- As mensagens de limite comercial e de suporte foram acentuadas; havia texto
  sem acento indo ao cliente exatamente no cenario de guardrail.
- A suite deixou de gravar no log de eventos real, que continha PII do piloto.
- Existe apoio operacional em `py scripts/janela_teste.py`.
- Suite: 93 testes. Smoke test e homologacao aprovados.

## Contadores limpos sem apagar dados

Nada e expurgado: a politica de retencao da SS Vale ainda nao foi aprovada e o
log contem PII. Em vez disso, a janela grava um marco e todos os contadores
passam a valer a partir dele.

```powershell
py scripts/janela_teste.py baseline --rotulo janela-2
py scripts/janela_teste.py status
```

Os dois erros `maxbot_error` de 04/08 (falta de permissao de rede) ficam para
tras do marco e nao contaminam o veredito desta janela.

## Antes do dia

1. Confirmar data, horario, duracao maxima e os tres responsaveis
   (painel, acompanhamento das conversas, tecnico).
2. Rodar o go/no-go, que executa tudo de uma vez e da um veredito unico:

   ```powershell
   py scripts/checar_janela.py
   ```

   Ele roda suite, smoke test, homologacao, ensaio dos cenarios e preflight.
   `LIBERADO` significa apenas que a parte tecnica esta pronta; a decisao de
   abrir a janela continua humana. Se reprovar, o motivo aparece na propria
   saida e as etapas podem ser rodadas isoladamente:

   ```powershell
   py -m unittest discover -s tests
   py scripts/smoke_test.py
   py scripts/homologar_canais.py
   py scripts/ensaio_janela_maxbot.py
   py scripts/janela_teste.py preflight
   ```

3. Resolver o que o go/no-go apontar.

   **Pendencia conhecida:** a sessao do telefone piloto ficou em `handoff` desde
   04/08. Se ela nao for reiniciada, a Sofia ficara silenciosa justamente com o
   telefone do teste. Depois de confirmar que nao ha atendimento humano aberto:

   ```powershell
   py scripts/resetar_sessao.py --session-id <telefone-piloto>
   py scripts/resetar_sessao.py --session-id <telefone-piloto> --confirmar
   ```

4. Subir o backend com permissao de rede externa para `https://app.maxbot.com.br`.
   Sem isso, o envio real falha com `URLError/PermissionError`, como em 04/08.
5. Publicar a URL HTTPS e apontar os dois eventos do painel
   (`Mensagem Recebida` e `Mensagem Recebida em Atendimento`) para
   `/webhook/maxbot/<segredo>`.
6. Com `MAXBOT_SEND_MESSAGES=false`, mandar uma mensagem de teste e confirmar
   ACK nos logs, sem nenhuma resposta da Sofia.

## Ordem da janela

Nunca deixar o menu e o envio da Sofia ativos ao mesmo tempo.

1. Liberar a sessao do telefone piloto, que ficou em `handoff` desde 04/08.
   Antes, confirmar no painel que **nao ha atendimento humano aberto** com esse
   numero; caso contrario a Sofia voltaria a falar por cima de um atendente.

   ```powershell
   cd C:\ssvale-chatbot-mvp
   py scripts/resetar_sessao.py --session-id <telefone-piloto>
   py scripts/resetar_sessao.py --session-id <telefone-piloto> --confirmar
   py scripts/checar_janela.py
   ```

   Seguir adiante somente com o veredito `LIBERADO`.
2. `py scripts/janela_teste.py baseline --rotulo janela-2`.
3. Manter `Interacao: Ativada - Direcionando Atendimentos`. Desativar essa
   chave derruba os webhooks.
4. Esvaziar a mensagem de boas-vindas e ocultar os tres itens publicados do
   menu principal.
5. Confirmar, com uma mensagem real, que o menu nao responde mais.
6. Somente entao ligar `MAXBOT_PILOT_ALLOW_ATTENDANCE=true` e
   `MAXBOT_SEND_MESSAGES=true`.
7. Executar os cenarios abaixo, na ordem.
8. `py scripts/janela_teste.py status` ao final de cada bloco.

## Cenarios e criterio de aprovacao

| # | Cenario | O que enviar | Aprovado quando |
|---|---|---|---|
| 1 | Retomada basica | "Oi" do telefone piloto | Saudacao e menu numerado da Sofia, com acentos |
| 2 | Guardrail preco | "Quanto custa uma fritadeira?" | Resposta de limite acentuada, sem valor, seguindo para coleta de nome |
| 3 | Guardrail frete | "Qual o frete para Taubate?" | Mesmo comportamento, sem estimar frete |
| 4 | Guardrail prazo | "Qual o prazo de entrega?" | Mesmo comportamento, sem prometer prazo |
| 5 | Guardrail desconto | "Tem desconto?" | Mesmo comportamento, sem negociar |
| 6 | Guardrail pagamento | "Posso pagar no pix parcelado?" | Mesmo comportamento, sem tratar pagamento |
| 7 | Duplicidade | Reenviar a mesma mensagem rapidamente | Apenas uma resposta; `maxbot_duplicate` no status |
| 8 | Telefone nao autorizado | "Oi" de um numero fora da lista | Nenhuma resposta da Sofia; `maxbot_pilot_filtered` |
| 9 | Atendimento humano | Atendente assume o protocolo e o cliente escreve | Sofia silenciosa; `maxbot_human_attendance` |
| 10 | Handoff | Concluir uma conversa ate a confirmacao final e escrever de novo | Sofia silenciosa apos o resumo; `maxbot_handoff_pending` |

Em todos: `maxbot_error` precisa permanecer em zero no `status`.

Cenarios 2 a 6 e 7 a 10 ja passaram offline; a janela existe para confirmar o
mesmo comportamento com payload e envio reais.

## Interromper imediatamente se

- menu e Sofia responderem na mesma conversa;
- a Sofia responder durante atendimento humano;
- houver resposta duplicada;
- sair qualquer preco, frete, prazo, desconto ou orcamento;
- aparecer `maxbot_error`;
- um cliente real entrar na conversa;
- houver demora que atrapalhe o atendimento normal.

Interrupcao: `MAXBOT_SEND_MESSAGES=false` primeiro, confirmar que a Sofia parou,
restaurar o menu, registrar o incidente e nao retomar sem nova revisao.

## Encerramento

1. `MAXBOT_SEND_MESSAGES=false` e `MAXBOT_PILOT_ALLOW_ATTENDANCE=false`.
2. Confirmar que a Sofia nao envia mais nada.
3. Restaurar a mensagem de boas-vindas e os tres itens do menu principal.
4. Mensagem de teste: somente o menu pode responder.
5. Conferir e arquivar o resultado:

   ```powershell
   py scripts/janela_teste.py status
   py scripts/janela_teste.py encerrar
   ```

6. Reiniciar as sessoes de teste que ficaram em `handoff`, uma a uma, com
   `--confirmar`.
7. Preencher o registro da janela em `CHECKLIST-JANELA-TESTE-MAXBOT.md` e
   atualizar `MVP_STATUS.md`.

## O que esta janela ainda nao resolve

O handoff real continua pendente: a Sofia gera o resumo e fica silenciosa em
`human_pending`, mas nao abre nem transfere protocolo. Isso depende de confirmar
com o suporte Maxbot o uso de `open_followup` em conversa iniciada pelo cliente,
o template a informar e os IDs de Comercial, Compras e Compras Online.

Enquanto isso nao estiver resolvido, o piloto nao deve atender clientes reais
que dependam do encaminhamento de ponta a ponta.
