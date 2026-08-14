# Checklist Maxbot - MVP Sofia SS Vale

## Objetivo

Configurar o MVP da Sofia no Maxbot em um bloco separado chamado `0 - MVP_ChatBot`, sem impactar o fluxo atual em producao.

Este checklist deve ser usado para preparar, configurar, testar e liberar o fluxo de pre-venda de forma controlada.

## Regra principal de seguranca

- [ ] Nao editar blocos, gatilhos ou filas do fluxo atual em producao sem validacao previa.
- [ ] Criar todo o MVP dentro do bloco `0 - MVP_ChatBot`.
- [ ] Manter o fluxo atual como caminho principal ate a aprovacao do MVP.
- [ ] Testar o MVP com acesso restrito antes de qualquer redirecionamento real.
- [ ] Registrar quais ajustes foram feitos no Maxbot.

## 1. Preparacao antes de configurar

- [ ] Fazer backup ou registro visual do fluxo atual em producao.
- [ ] Identificar qual bloco inicial esta ativo hoje.
- [ ] Confirmar quais filas, departamentos ou atendentes recebem o atendimento atual.
- [ ] Confirmar quem sera responsavel por testar o MVP.
- [ ] Confirmar se o MVP sera testado por palavra-chave, link interno, contato de teste ou acionamento manual.
- [ ] Definir criterio de aprovacao antes de ligar o MVP ao fluxo principal.

## 2. Criar bloco separado do MVP

- [ ] Criar um novo bloco no Maxbot com o nome exato: `0 - MVP_ChatBot`.
- [ ] Garantir que o bloco nao esteja conectado automaticamente ao fluxo atual.
- [ ] Garantir que nenhum gatilho publico esteja apontando para `0 - MVP_ChatBot` durante a configuracao.
- [ ] Adicionar uma anotacao interna informando que o bloco e de teste/MVP.
- [ ] Conferir se o bloco pode ser acessado manualmente para testes.

## 3. Configurar mensagem de abertura

- [ ] Inserir a mensagem inicial da Sofia.
- [ ] Apresentar a Sofia como assistente virtual da SS Vale.
- [ ] Explicar de forma breve que ela vai direcionar o atendimento.
- [ ] Evitar mencionar que o fluxo e um MVP para o cliente final.

Mensagem sugerida:

> Ola! Eu sou a Sofia, assistente virtual da SS Vale. Vou te ajudar a encontrar o melhor caminho para o seu atendimento. Como posso te ajudar hoje?

## 4. Configurar menu principal

- [ ] Criar as 5 opcoes principais dentro do bloco `0 - MVP_ChatBot`.
- [ ] Usar respostas rapidas ou botoes, se o Maxbot permitir.
- [ ] Manter textos curtos e claros.
- [ ] Criar tratamento para resposta digitada fora das opcoes.

Opcoes do menu:

1. Procuro um equipamento especifico
2. Vou montar ou reformar uma cozinha
3. Suporte / Pos-venda
4. Sou fornecedor ou representante
5. Quero falar com um consultor

## 5. Configurar caminho: Procuro um equipamento especifico

- [ ] Criar submenu com os equipamentos do arquivo `equipamentos.json`.
- [ ] Incluir as opcoes:
  - [ ] Fritadeira
  - [ ] Freezer / Refrigeracao
  - [ ] Forno
  - [ ] Fogao Industrial
  - [ ] Chapa
  - [ ] Outro equipamento
- [ ] Para cada equipamento, configurar as perguntas de qualificacao.
- [ ] Fazer uma pergunta por vez.
- [ ] Salvar respostas em campos, tags ou observacoes do atendimento.
- [ ] Aplicar a tag correspondente ao equipamento.
- [ ] Coletar nome, telefone/WhatsApp, cidade e estado.
- [ ] Encaminhar para humano ao final.

Regra:

- [ ] Todos os equipamentos cadastrados devem exigir atendimento humano obrigatorio.

## 6. Configurar caminho: Vou montar ou reformar uma cozinha

- [ ] Perguntar se o cliente esta montando, reformando ou ampliando.
- [ ] Perguntar tipo de estabelecimento.
- [ ] Perguntar se ja possui projeto, layout ou lista de equipamentos.
- [ ] Perguntar previsao de compra.
- [ ] Coletar nome, telefone/WhatsApp, cidade e estado.
- [ ] Aplicar tag sugerida: `projeto_cozinha`.
- [ ] Encaminhar para consultor comercial.

## 7. Configurar caminho: Suporte / Pos-venda

- [ ] Informar que a Sofia vai registrar e direcionar a solicitacao.
- [ ] Perguntar se o cliente ja comprou com a SS Vale.
- [ ] Perguntar equipamento, pedido ou assunto relacionado.
- [ ] Classificar o motivo:
  - [ ] Garantia
  - [ ] Instalacao
  - [ ] Manutencao
  - [ ] Troca
  - [ ] Outro
- [ ] Coletar nome e telefone/WhatsApp.
- [ ] Aplicar tag sugerida: `pos_venda`.
- [ ] Encaminhar para fila ou responsavel de pos-venda.

Regra:

- [ ] A Sofia nao deve fazer diagnostico tecnico.
- [ ] A Sofia nao deve orientar reparo, instalacao ou manutencao.

## 8. Configurar caminho: Sou fornecedor ou representante

- [ ] Perguntar nome da empresa.
- [ ] Perguntar tipo de contato:
  - [ ] Fornecedor
  - [ ] Representante
  - [ ] Parceria
  - [ ] Outro
- [ ] Coletar nome do contato.
- [ ] Coletar telefone/WhatsApp.
- [ ] Coletar e-mail, se for util para o processo interno.
- [ ] Solicitar breve resumo do motivo do contato.
- [ ] Aplicar tag sugerida: `fornecedor_representante`.
- [ ] Encaminhar para setor responsavel.

## 9. Configurar caminho: Quero falar com um consultor

- [ ] Confirmar que o cliente deseja atendimento humano.
- [ ] Coletar nome.
- [ ] Coletar telefone/WhatsApp.
- [ ] Coletar cidade e estado.
- [ ] Perguntar rapidamente o motivo do contato.
- [ ] Aplicar tag sugerida: `consultor_direto`.
- [ ] Encaminhar para consultor comercial.

## 10. Configurar mensagens de limite

- [ ] Criar resposta padrao para pedido de preco.
- [ ] Criar resposta padrao para pedido de frete.
- [ ] Criar resposta padrao para pedido de pagamento.
- [ ] Criar resposta padrao para pedido de orcamento formal.
- [ ] Criar resposta padrao para suporte tecnico.
- [ ] Criar resposta padrao para mensagem nao entendida.

Regras obrigatorias:

- [ ] Nao negociar preco.
- [ ] Nao calcular frete.
- [ ] Nao processar pagamento.
- [ ] Nao emitir orcamento formal.
- [ ] Nao resolver suporte tecnico.
- [ ] Nao prometer estoque, prazo, desconto ou disponibilidade.

## 11. Configurar tags e campos

- [ ] Criar ou reaproveitar campo para nome.
- [ ] Criar ou reaproveitar campo para telefone/WhatsApp.
- [ ] Criar ou reaproveitar campo para cidade e estado.
- [ ] Criar campo ou observacao para equipamento de interesse.
- [ ] Criar campo ou observacao para prazo de compra.
- [ ] Criar campo ou observacao para tipo de negocio.
- [ ] Criar tags dos equipamentos:
  - [ ] `equipamento_fritadeira`
  - [ ] `equipamento_freezer_refrigeracao`
  - [ ] `equipamento_forno`
  - [ ] `equipamento_fogao_industrial`
  - [ ] `equipamento_chapa`
  - [ ] `equipamento_outro`
- [ ] Criar tags dos caminhos:
  - [ ] `projeto_cozinha`
  - [ ] `pos_venda`
  - [ ] `fornecedor_representante`
  - [ ] `consultor_direto`

## 12. Encaminhamento humano

- [ ] Confirmar qual fila recebe leads comerciais.
- [ ] Confirmar qual fila recebe pos-venda.
- [ ] Confirmar qual fila recebe fornecedores/representantes.
- [ ] Configurar transferencia apenas dentro do bloco `0 - MVP_ChatBot`.
- [ ] Verificar se a transferencia nao altera regras do fluxo atual em producao.
- [ ] Criar mensagem de encerramento antes da transferencia.

Mensagem sugerida:

> Pronto, ja registrei as informacoes. Em breve um consultor da SS Vale continua o atendimento com voce.

## 13. Testes isolados do MVP

- [ ] Testar acesso ao bloco `0 - MVP_ChatBot` sem passar pelo fluxo atual.
- [ ] Testar todas as 5 opcoes do menu principal.
- [ ] Testar todos os equipamentos cadastrados.
- [ ] Testar cliente que digita texto livre.
- [ ] Testar pedido de preco.
- [ ] Testar pedido de frete.
- [ ] Testar pedido de pagamento.
- [ ] Testar pedido de orcamento.
- [ ] Testar suporte tecnico.
- [ ] Testar fornecedor ou representante.
- [ ] Testar falar direto com consultor.
- [ ] Conferir se tags foram aplicadas corretamente.
- [ ] Conferir se dados coletados aparecem para o atendente humano.
- [ ] Conferir se o atendimento atual em producao continua funcionando sem alteracao.

## 14. Validacao com equipe

- [ ] Validar texto das mensagens com a equipe comercial.
- [ ] Validar perguntas de equipamentos com quem atende vendas.
- [ ] Validar encaminhamento de pos-venda.
- [ ] Validar encaminhamento de fornecedores/representantes.
- [ ] Validar se os dados coletados sao suficientes para o consultor.
- [ ] Ajustar mensagens longas antes da liberacao.

## 15. Liberacao controlada

- [ ] Definir como o MVP sera ativado.
- [ ] Evitar substituir o fluxo principal sem teste acompanhado.
- [ ] Se for conectar o MVP ao fluxo atual, fazer isso em horario de baixo movimento.
- [ ] Ter responsavel acompanhando os primeiros atendimentos.
- [ ] Registrar problemas encontrados.
- [ ] Manter possibilidade de voltar rapidamente ao fluxo anterior.

## 16. Acompanhamento apos teste

- [ ] Revisar conversas reais do MVP.
- [ ] Identificar perguntas que geram confusao.
- [ ] Identificar opcoes de equipamento mais usadas.
- [ ] Verificar se leads chegam completos para os consultores.
- [ ] Ajustar tags, perguntas e mensagens.
- [ ] Decidir se o MVP deve continuar separado, evoluir ou ser integrado ao fluxo principal.

## Criterio de pronto

O MVP pode ser considerado pronto para teste controlado quando:

- [ ] O bloco `0 - MVP_ChatBot` existe e esta separado do fluxo atual.
- [ ] Todos os caminhos principais foram configurados.
- [ ] Todos os equipamentos iniciais foram cadastrados.
- [ ] Todas as transferencias humanas foram testadas.
- [ ] O fluxo atual em producao nao foi impactado.
- [ ] A equipe validou mensagens, tags e encaminhamentos.
