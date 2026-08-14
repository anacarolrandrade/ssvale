# Plano de transicao: Maxbot e WhatsApp Business

## Objetivo

Manter uma unica Sofia, com as mesmas regras comerciais, mensagens e criterios
de qualificacao, enquanto a SS Vale usa o Maxbot e prepara a migracao para a
WhatsApp Business Platform (Cloud API da Meta).

## Versao Maxbot

O canal atual continua sendo configurado pelos artefatos:

- `roteiro-maxbot.md`: blocos, mensagens, variaveis e desvios.
- `fluxo-pratico-maxbot.md`: guia operacional de montagem.
- `checklist-maxbot.md`: verificacao antes da publicacao.
- `testes-mvp.md`: cenarios funcionais de homologacao.

Alteracoes nas regras comerciais devem ser registradas primeiro em
`regras-negocio.md` e depois refletidas tanto no roteiro do Maxbot quanto no
backend da Sofia.

## Versao WhatsApp Business

O backend em `src/sofia_chatbot` concentra o fluxo compartilhado. O adaptador em
`src/sofia_chatbot/channels/whatsapp.py` converte as respostas para texto,
botoes e listas aceitos pela Meta. O webhook esta em
`src/sofia_chatbot/api.py`.

Para teste local, o envio real deve permanecer desligado:

```text
WHATSAPP_SEND_MESSAGES=false
```

Para um teste controlado na Meta, serao necessarios:

- conta WABA e numero de teste ou numero oficial;
- `WHATSAPP_PHONE_NUMBER_ID`;
- `WHATSAPP_ACCESS_TOKEN`;
- `WHATSAPP_APP_SECRET`;
- `WHATSAPP_VERIFY_TOKEN`;
- URL publica HTTPS apontando somente para o webhook;
- `LOCAL_API_ENABLED=false`;
- `DEBUG_ENDPOINTS_ENABLED=false`.

## Fonte unica de verdade

| Assunto | Fonte principal |
|---|---|
| Limites comerciais | `regras-negocio.md` |
| Equipamentos | `equipamentos.json` e `matriz-equipamentos.md` |
| Textos-base | `mensagens.json` |
| Fluxo atual no Maxbot | `roteiro-maxbot.md` |
| Fluxo executavel na Meta | `src/sofia_chatbot/flow.py` |
| Cenarios de aceite | `testes-mvp.md` e `tests/` |

## Etapas de transicao

1. Homologar novamente o fluxo atual no Maxbot.
2. Criar a estrutura empresarial seguindo `CHECKLIST-CONTA-META.md`.
3. Obter as credenciais e o numero de teste da Meta.
4. Publicar o webhook em ambiente controlado, com envio real inicialmente
   desligado.
5. Validar recebimento de texto, botoes, listas, duplicidades e falhas.
6. Ativar o envio apenas no numero de teste, com acompanhamento humano.
7. Executar os mesmos cenarios comerciais nos dois canais e comparar os
   resultados.
8. Definir o destino do handoff humano e o comportamento depois do handoff.
9. Definir politica de retencao e acesso aos logs com dados pessoais.
10. Realizar piloto restrito e monitorado.
11. Migrar o numero oficial e desativar o Maxbot somente depois do aceite.

## Criterio de conclusao

A migracao pode ser considerada pronta quando:

- os cenarios essenciais produzem o mesmo resultado nos dois canais;
- o handoff humano funciona de ponta a ponta;
- credenciais e assinatura do webhook estao configuradas;
- nao existem erros de processamento durante o piloto;
- a politica de dados pessoais esta aprovada;
- existe procedimento documentado de pausa e retorno ao canal anterior.

## Validacao disponivel sem conta Meta

O comando abaixo executa os mesmos cenarios no fluxo direto e nos adaptadores
que interpretam os payloads da Meta e do Maxbot:

```text
py scripts/homologar_canais.py
```

Atualmente sao comparados comercial por equipamento, projeto de cozinha,
pos-venda, fornecedor/representante e compras pelo site. A validacao cobre 31
interacoes equivalentes nos tres caminhos e deve ser executada sempre que uma
regra compartilhada for alterada.
