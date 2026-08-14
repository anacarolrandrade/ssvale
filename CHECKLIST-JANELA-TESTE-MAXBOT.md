# Checklist da janela curta de teste - numero atual

Preencher antes de qualquer ativacao real.

## Identificacao

- Data: ____________________
- Inicio previsto: ____________________
- Fim previsto: ____________________
- Duracao maxima: ____________________
- Responsavel pelo painel Maxbot: ____________________
- Responsavel por acompanhar as conversas: ____________________
- Responsavel tecnico: ____________________
- Telefones internos autorizados: ____________________

## Antes da janela

- [ ] Suite, smoke test e homologacao aprovados.
- [ ] URL HTTPS estavel validada.
- [ ] Segredo do webhook configurado sem registro em documento ou captura.
- [ ] Token configurado somente como variavel de ambiente.
- [ ] `MAXBOT_PILOT_MODE=true`.
- [ ] Telefones internos ou segmento do piloto configurados.
- [ ] `LOCAL_API_ENABLED=false`.
- [ ] `DEBUG_ENDPOINTS_ENABLED=false`.
- [ ] `MAXBOT_SEND_MESSAGES=false`.
- [ ] Webhook recebe payload e devolve ACK com envio desligado.
- [ ] Procedimento de retorno ao menu revisado pelos responsaveis.

## Inicio da janela

- [ ] Responsaveis presentes e canal interno de comunicacao aberto.
- [ ] Nenhum teste iniciado por cliente real.
- [ ] Menu automatico desativado no painel.
- [ ] Confirmado que o menu nao responde mais.
- [ ] `MAXBOT_SEND_MESSAGES=true` ativado somente depois da confirmacao acima.

## Cenarios obrigatorios

- [ ] Telefone autorizado recebe a saudacao e o menu numerado da Sofia.
- [ ] Telefone nao autorizado nao recebe resposta da Sofia.
- [ ] Escolhas numeradas avancam corretamente.
- [ ] Pedido de preco/frete/prazo e bloqueado.
- [ ] Mensagem duplicada nao produz segunda resposta.
- [ ] Atendimento humano ativo deixa a Sofia silenciosa.
- [ ] Handoff pendente deixa a Sofia silenciosa depois da confirmacao final.
- [ ] `maxbot_error` permanece em zero.

## Encerramento normal

- [ ] `MAXBOT_SEND_MESSAGES=false` aplicado primeiro.
- [ ] Confirmado que a Sofia nao envia novas mensagens.
- [ ] Menu automatico restaurado depois da confirmacao.
- [ ] Mensagem final de teste recebe somente a resposta do menu.
- [ ] Horario final e resultado registrados.

## Interrupcao imediata

Se houver resposta dupla, resposta durante atendimento humano, duplicidade,
erro ou entrada de cliente real:

- [ ] Aplicar `MAXBOT_SEND_MESSAGES=false` imediatamente.
- [ ] Confirmar fim dos envios da Sofia.
- [ ] Restaurar o menu automatico.
- [ ] Registrar o incidente e nao retomar sem nova revisao.

## Resultado

- Resultado: [ ] Aprovado  [ ] Reprovado  [ ] Interrompido
- Incidentes: ____________________________________________________________
- Observacoes: ___________________________________________________________
- Proxima decisao: ______________________________________________________

## Registro da primeira janela - 04/08/2026

- Resultado: **parcialmente aprovado; repetir no fim de semana antes de
  homologar para clientes reais**.
- Entrada real, webhook, lista de telefones piloto, escolhas numeradas,
  respostas livres, coleta de nome/cidade e encerramento em handoff foram
  validados no numero oficial.
- O telefone nao autorizado permaneceu silencioso e foi filtrado pelo piloto.
- O Maxbot precisa ficar com `Interacao: Ativada - Direcionando Atendimentos`;
  desativar essa chave tambem interrompe os webhooks.
- Para silenciar o fluxo nativo, a mensagem de boas-vindas ficou vazia e os
  tres itens publicados do menu principal foram ocultados.
- O Maxbot abre um protocolo automatico. Durante a janela, somente o telefone
  explicitamente autorizado pode usar a excecao
  `MAXBOT_PILOT_ALLOW_ATTENDANCE=true`; a chave fica `false` fora do teste.
- O primeiro processo local foi iniciado sem permissao de rede externa e gerou
  `maxbot_error`. O backend de envio real precisa ser iniciado com acesso a
  `https://app.maxbot.com.br`.
- O comando `send_chat_msg` foi recusado para protocolo sem atendente. O piloto
  usa `send_text` para responder ao contato autorizado.
- Melhorias identificadas e implementadas depois da janela: textos com acentos
  e telefone obtido automaticamente do remetente, sem perguntar novamente no
  WhatsApp ou Maxbot.
- Estado seguro ao encerrar: `MAXBOT_SEND_MESSAGES=false` e
  `MAXBOT_PILOT_ALLOW_ATTENDANCE=false`.
- Validacao posterior: 75 testes, smoke test e homologacao de 5 cenarios/26
  interacoes aprovados.
