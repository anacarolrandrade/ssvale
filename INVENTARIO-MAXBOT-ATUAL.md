# Inventario do Maxbot atualmente publicado

Levantamento iniciado em 28/07/2026 a partir das telas da conta da SS Vale.
Este documento registra o que foi observado; nao autoriza alteracoes no painel.

## Estrutura visivel

1. Falar com um vendedor
   - Quero um Equipamento
     - MVP_ChatBot (aparecia com icone de olho riscado; estado a confirmar)
   - Quero um Projeto Completo
2. Sou Fornecedor da SS Vale
3. Comprei pelo Site

## Registro: Falar com um vendedor

| Campo | Valor observado |
|---|---|
| Codigo do menu | 1 |
| Titulo | Falar com um vendedor |
| Ordem de exibicao | 1 |
| Exibir | Sim |
| Tipo | Menu |

Conclusao: trata-se de um menu conteiner. Nao ha, nesta tela, setor, atendente,
segmentacao ou mensagem de orientacao associados.

### Exibicao observada

| Dia | Indicacao exibida | Turno 1 | Turno 2 |
|---|---|---|---|
| Segunda | Sim - 24 horas | 08:00-12:00 | 13:00-18:00 |
| Terca | Sim - 24 horas | 08:00-12:00 | 13:00-18:00 |
| Quarta | Sim - 24 horas | 08:00-12:00 | 13:00-18:00 |
| Quinta | Sim - 24 horas | 08:00-12:00 | 13:00-18:00 |
| Sexta | Sim - 24 horas | 08:00-12:00 | 13:00-18:00 |
| Sabado | Sim - 24 horas | 08:00-12:00 | vazio |
| Domingo | Sim - 24 horas | vazio | vazio |

### Ponto a confirmar

A interface mostra simultaneamente `Sim - 24 horas` e turnos preenchidos. Ainda
nao esta claro se os turnos sao ignorados quando a opcao de 24 horas esta ativa
ou se a copia textual da tela misturou o seletor com os campos disponiveis.
Nenhuma alteracao deve ser feita ate confirmar o comportamento com o Maxbot.

## Registro: Quero um Equipamento

| Campo | Valor observado |
|---|---|
| Menu pai | 1 - Falar com um vendedor |
| Codigo do menu | 1 |
| Titulo | Quero um Equipamento |
| Ordem de exibicao | 1 |
| Exibir | Sim |
| Tipo | Encaminhamento |
| Setor | Comercial |
| Atendente | Todos os atendentes |
| Orientacao ao atendente | Ola, gostaria de saber mais sobre um equipamento. |
| Orientacao ao contato | Em breve um vendedor entrara em contato. Qual equipamento deseja? |

### Comportamento atual

Ao escolher esta opcao, o cliente e encaminhado imediatamente ao setor
Comercial. Nao ha qualificacao por tipo de equipamento, uso, modelo, volume,
nome, telefone ou cidade antes do encaminhamento.

### Diferenca para a Sofia

A Sofia proposta identifica o equipamento, faz ate tres perguntas especificas,
coleta os dados basicos e entrega um resumo ao Comercial. Portanto, o fluxo
novo nao deve substituir este encaminhamento antes de uma homologacao
controlada.

### Segmentacoes

A copia textual exibiu todas as opcoes disponiveis, mas nao permitiu identificar
se alguma segmentacao de protocolo ou contato esta efetivamente selecionada.
Esse ponto permanece a confirmar visualmente.

### Horarios

Foi observada a mesma combinacao do menu pai: `Sim - 24 horas` em todos os dias,
com turnos preenchidos de segunda a sabado. O significado efetivo permanece
pendente de confirmacao.

## Registro: MVP_ChatBot

| Campo | Valor observado |
|---|---|
| Menu pai | 1 - Falar com um vendedor |
| Codigo do menu | 0 |
| Titulo | MVP_ChatBot |
| Ordem de exibicao | 2 |
| Exibir | Nao |
| Tipo | Encaminhamento |
| Setor | Comercial |
| Atendente | Kaique Carletti |
| Orientacao ao atendente | Vazia |
| Orientacao ao contato | Perfeito. Qual equipamento voce esta procurando? |

### Interpretacao

O registro nao implementa um chatbot. Ele e uma opcao oculta de encaminhamento
direto ao setor Comercial, atribuida a um atendente especifico. A pergunta ao
cliente ocorre como orientacao do encaminhamento, mas nao ha blocos de
qualificacao associados nesta configuracao.

O codigo `0`, o estado `Exibir: Nao` e a atribuicao nominal indicam um artefato
de teste ou preparacao anterior. A SS Vale confirmou em 28/07/2026 que este
registro nao corresponde ao MVP atual e nao esta em uso. Ele sera tratado como
legado, sem necessidade de investigacao no escopo atual.

### Horarios e segmentacoes

Foi observada a mesma combinacao de 24 horas e turnos dos registros anteriores.
A selecao efetiva de segmentacoes nao pode ser determinada pela copia textual.

## Registro: Sou Fornecedor da SSVale

| Campo | Valor observado |
|---|---|
| Menu pai | Menu principal |
| Codigo do menu | 2 |
| Titulo | Sou Fornecedor da SSVale |
| Ordem de exibicao | 2 |
| Exibir | Sim |
| Tipo | Encaminhamento |
| Setor | Compras |
| Atendente | Todos os atendentes |
| Orientacao ao atendente | COMPRAS |
| Orientacao ao contato | Vazia |

### Comportamento atual

O contato e encaminhado diretamente ao setor de Compras e pode ser assumido por
qualquer atendente do setor. Nao ha coleta previa de empresa, tipo de contato,
produto representado ou objetivo da proposta, nem mensagem de confirmacao ao
contato.

### Diferenca para a Sofia

A Sofia proposta pergunta a empresa e o tipo de contato antes do handoff,
permitindo que Compras receba um resumo minimo. O destino observado confirma que
o handoff deste ramo deve ser `Compras`, e nao `Comercial`.

### Horarios e segmentacoes

Todos os dias aparecem como `Sim - 24 horas` e, neste registro, tambem exibem
os turnos 08:00-12:00 e 13:00-18:00, inclusive sabado e domingo. A regra
efetivamente aplicada ainda precisa ser confirmada. A selecao de segmentacoes
nao pode ser determinada pela copia textual.

## Registro: Comprei pelo Site

| Campo | Valor observado |
|---|---|
| Menu pai | Menu principal |
| Codigo do menu | 4 |
| Titulo | Comprei pelo Site |
| Ordem de exibicao | 4 |
| Exibir | Sim |
| Tipo | Encaminhamento |
| Setor | Compras Online |
| Atendente | Todos os atendentes |
| Orientacao ao atendente | Vazia |
| Orientacao ao contato | Vazia |

### Comportamento atual

O contato e encaminhado diretamente ao setor Compras Online e pode ser assumido
por qualquer atendente. Nao ha coleta de numero do pedido, assunto ou dados
basicos, nem mensagem de confirmacao configurada.

### Regra confirmada para a Sofia

Mensagens explicitas como `comprei pelo site` devem ser destinadas a Compras
Online. Esse caminho e diferente de Compras (fornecedores), Comercial (vendas e
projetos) e do pos-venda generico.

### Horarios e segmentacoes

Foi observada a combinacao de `Sim - 24 horas` com turnos de segunda a sabado;
domingo aparece sem turnos. A selecao efetiva de segmentacoes nao pode ser
determinada pela copia textual.

## Registro: Quero um Projeto Completo

| Campo | Valor observado |
|---|---|
| Menu pai | 1 - Falar com um vendedor |
| Codigo do menu | 2 |
| Titulo | Quero um Projeto Completo |
| Ordem de exibicao | 2 |
| Exibir | Sim |
| Tipo | Encaminhamento |
| Setor | Comercial |
| Atendente | Kaique Carletti |
| Orientacao ao atendente | Vazia |
| Orientacao ao contato | Vazia |

### Comportamento atual

O contato e encaminhado diretamente ao Comercial e atribuido nominalmente ao
atendente Kaique Carletti. Nao ha mensagem de confirmacao, qualificacao do
projeto ou coleta de dados configurada neste registro.

### Risco observado

O caminho depende de uma unica pessoa, enquanto a opcao de equipamento e
distribuida para todos os atendentes. Ferias, ausencia ou mudanca de funcao
podem afetar especificamente os contatos de projeto. A regra de distribuicao
deve ser confirmada pela SS Vale antes de qualquer alteracao.

### Horarios e segmentacoes

Foi observada a mesma combinacao de 24 horas e turnos dos registros anteriores.
A selecao efetiva de segmentacoes nao pode ser determinada pela copia textual.

## Segmentacoes encontradas no formulario de encaminhamento

- COMERCIAL - AGUARDANDO ORCAMENTO
- COMERCIAL - AGUARDANDO RETORNO DO CLIENTE
- COMERCIAL - VENDA FECHADA
- COMERCIAL - VENDA NAO CONVERTIDA
- COMPRAS - FORNECEDOR ADD NA CARTEIRA
- EXPEDICAO - ENTREGA AGENDADA
- EXPEDICAO - ENTREGA REALIZADA

As segmentacoes foram apenas observadas. A associacao efetiva de cada opcao
publicada ainda precisa ser levantada.

## Proximos registros a inspecionar

O mapa principal observado foi concluido.

## Configuracoes complementares

### Setor de Atendimento

A tela consultada foi informada como vazia. Apesar disso, os registros de
encaminhamento confirmam a existencia dos destinos `Comercial`, `Compras` e
`Compras Online`. Responsaveis e horarios efetivos desses setores nao ficaram
visiveis nesse levantamento.

### Interacao Padrao

Texto observado:

> Seja Bem-Vindo ao Canal de Atendimento Digital SSVale.

Essa e a saudacao global atual do canal antes da exibicao do menu.

### Atendimento Personalizado

A tela consultada foi informada como vazia. Nao foram identificadas regras
adicionais de personalizacao nessa area.

## Itens adiados

Por decisao de escopo em 28/07/2026, os itens abaixo ficam para uma etapa
posterior e nao bloqueiam o MVP:

1. confirmar o comportamento efetivo dos horarios (`24 horas` versus turnos);
2. identificar a selecao efetiva de segmentacoes;
3. investigar o webhook antigo e o tunel temporario;
4. limpar ou arquivar configuracoes legadas no painel.

## Levantamento essencial concluido

O escopo essencial do Maxbot esta encerrado: saudacao, menu publicado,
encaminhamentos e setores de destino foram identificados. Nenhuma configuracao
do painel foi alterada durante o levantamento.
