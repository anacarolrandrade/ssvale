# Sofia no Maxbot - configuracao criada em 04/08/2026

Registro do que foi configurado no painel do Maxbot da SS Vale para lancar uma
versao reduzida da Sofia no canal atual, antes da migracao para a Meta.

Tudo foi criado com `Exibir: Nao`. Nenhum registro em producao foi editado.
O atendimento que roda hoje continua exatamente como estava.

## Por que a versao e reduzida

O `roteiro-maxbot.md` descreve 37 blocos com variaveis, perguntas de resposta
livre, ramificacao condicional e resumo montado a partir das respostas. A
inspecao do painel em 04/08/2026 mostrou que o Maxbot nao oferece esses
recursos.

O painel possui exatamente quatro tipos de registro:

| Tipo | O que faz |
|---|---|
| Menu | Contêiner. Agrupa opcoes filhas. Nao tem campo de mensagem. |
| Encaminhamento | Manda para um setor. Tem `Orientacao ao Contato` e `Orientacao ao Atendente`. |
| Informativo | Mostra texto, imagem ou arquivo. |
| Integracao | Gera link, opcionalmente pede informacao, consulta URL e devolve JSON. |

Campos disponiveis em Encaminhamento: Codigo do Menu, Titulo, Ordem de
Exibicao, Exibir, Tipo, Setor, Atendente, Segmentacao Protocolo, Segmentacao
Contato, Orientacao ao Atendente, Orientacao ao Contato e horarios por dia.

### O que o roteiro pede e o painel nao faz

- Guardar resposta do cliente em variavel (`nome_cliente`, `telefone_whatsapp`,
  `cidade_estado`, `tipo_negocio`, `previsao_compra` e demais).
- Pergunta de resposta livre.
- Ramificacao condicional por resposta.
- Bloco de fallback para resposta fora das opcoes.
- Resumo interno montado a partir do que o cliente respondeu.

Conclusao: no Maxbot, a qualificacao so pode vir do caminho que o cliente
percorre no menu. Cada folha carrega um texto fixo em `Orientacao ao Atendente`
descrevendo esse caminho.

### Limite combinatorio

Cada nivel de pergunta multiplica o numero de registros. Uma pergunta por
equipamento seria viavel (cerca de 35 registros). As tres perguntas por
equipamento previstas no roteiro passariam de uma centena de registros
estaticos, inviavel de manter. Por isso foi escolhido o escopo enxuto.

## O que foi criado

Todos os registros abaixo estao com `Exibir: Nao`.

### Sob `1 - Falar com um vendedor`

`3 - Quero um Equipamento` - Tipo: Menu, Ordem 3

Filhos, todos Tipo Encaminhamento, Setor `Comercial`, Atendente
`-- Para Todos os Atendentes --`:

| Codigo | Titulo | Orientacao ao Atendente |
|---|---|---|
| 1 | Fritadeira | Sofia MVP - Cliente procura: Fritadeira. |
| 2 | Freezer / Refrigeracao | Sofia MVP - Cliente procura: Freezer / Refrigeracao. |
| 3 | Forno | Sofia MVP - Cliente procura: Forno. |
| 4 | Fogao Industrial | Sofia MVP - Cliente procura: Fogao Industrial. |
| 5 | Chapa | Sofia MVP - Cliente procura: Chapa. |
| 6 | Outro equipamento | Sofia MVP - Cliente procura: outro equipamento (nao listado no menu). Confirmar qual equipamento com o cliente. |

Orientacao ao Contato dos seis: *Perfeito. Em breve um consultor da SS Vale
continua o atendimento com voce.*

### No menu principal

Tipo Encaminhamento, Setor `Comercial`, Atendente
`-- Para Todos os Atendentes --`:

`5 - Suporte / Pos-venda`

- Orientacao ao Contato: *Eu consigo registrar sua solicitacao e direcionar ao
  time responsavel, mas nao consigo fazer diagnostico tecnico por aqui. Em
  breve a equipe da SS Vale continua o atendimento com voce.*
- Orientacao ao Atendente: *Sofia MVP - Suporte / Pos-venda. Assunto pode ser
  garantia, instalacao, manutencao, troca ou pedido ja realizado. Confirmar com
  o cliente.*

`6 - Falar com um consultor`

- Orientacao ao Contato: *Claro. Em breve um consultor da SS Vale continua o
  atendimento com voce.*
- Orientacao ao Atendente: *Sofia MVP - Cliente pediu para falar diretamente
  com um consultor. Confirmar o que ele precisa.*

Total: 9 registros novos, todos ocultos.

## Ganho real em relacao ao fluxo atual

Hoje o Comercial recebe apenas `Quero um Equipamento`, sem nenhuma informacao
adicional. Com a arvore nova, recebe qual equipamento o cliente procura.

Alem disso, `Suporte / Pos-venda` e `Falar com um consultor` passam a existir.
Hoje esses contatos caem no Comercial sem distincao.

## Limitacoes conhecidas desta versao

1. Nao ha coleta de nome, telefone ou cidade. O telefone ja vem do WhatsApp;
   nome e cidade dependem do cadastro de contato do Maxbot.
2. O tipo Menu nao tem campo de mensagem, entao a pergunta
   "Qual equipamento voce procura?" nao pode ser configurada. O Maxbot lista as
   opcoes sob o titulo do menu.
3. Nao ha tratamento de resposta fora das opcoes.
4. Nao ha resumo consolidado; a qualificacao e o texto fixo da folha escolhida.
5. Nao ha as tres perguntas por equipamento previstas no roteiro.

## Setores existentes no painel

`Comercial` `Compras` `Compras Online` `Expedicao` `Financeiro` `Projetos`

O `INVENTARIO-MAXBOT-ATUAL.md` registrava apenas tres, porque so esses estavam
em uso nos encaminhamentos. Nao existe setor de pos-venda ou assistencia
tecnica. Por decisao da SS Vale em 04/08/2026, `Suporte / Pos-venda` e
`Falar com um consultor` foram direcionados ao `Comercial`.

## Como ativar quando for aprovado

Nao ha nada a redigitar. A ativacao e so trocar `Exibir` de `Nao` para `Sim`.

1. Testar antes. Como os registros estao ocultos, o teste exige uma janela
   curta com eles visiveis, de preferencia em horario de baixo movimento.
2. Ativar `3 - Quero um Equipamento` e os seis filhos.
3. Desativar `1 - Quero um Equipamento`, que e o encaminhamento direto atual.
   Os dois tem o mesmo titulo; o novo e do tipo Menu e tem codigo 3.
4. Ativar `5 - Suporte / Pos-venda` e `6 - Falar com um consultor`.
5. Acompanhar as primeiras conversas com uma pessoa responsavel.

Para voltar atras, basta inverter: ocultar os novos e reexibir
`1 - Quero um Equipamento`.

## Pontos que dependem de decisao da SS Vale

1. Setor definitivo para pos-venda. O ideal seria um setor proprio, nao o
   Comercial.
2. `2 - Quero um Projeto Completo` vai hoje para o `Comercial`, atribuido
   nominalmente a um unico atendente, enquanto existe um setor `Projetos` sem
   uso. Pode ser um descasamento. Nao foi alterado por ser registro de
   producao.
3. Se a qualificacao por equipamento se mostrar util, avaliar uma pergunta
   adicional por equipamento (cerca de 35 registros no total).
4. O registro legado `0 - MVP_ChatBot` continua oculto e sem uso.

## Relacao com a fase Meta

Esta configuracao nao substitui o backend em `src/sofia_chatbot`. Ela e uma
versao reduzida para o canal atual. O fluxo completo, com coleta de dados,
guardrails e resumo, continua dependendo da migracao para a WhatsApp Business
Platform, conforme `PLANO-DOIS-CANAIS.md`.

Se algum dia o Maxbot for usado com o tipo `Integracao` execucao 4 ou 5, que
consulta uma URL externa e devolve JSON, seria possivel ligar o Maxbot ao
backend da Sofia. Isso exigiria a mesma URL publica HTTPS que a fase Meta ja
espera, e nao foi explorado neste momento.
