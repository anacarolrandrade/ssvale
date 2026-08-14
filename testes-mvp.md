# Testes MVP - Chatbot Sofia SS Vale

Casos de teste para validar o chatbot Sofia no Maxbot antes de ativar em producao.

Objetivo geral dos testes:

- Confirmar que o MVP esta separado do fluxo atual.
- Validar se os caminhos chegam ao atendimento humano correto.
- Confirmar se as tags e campos sao preenchidos.
- Garantir que a Sofia nao promete preco, prazo, estoque, desconto, frete ou pagamento automatico.

## Regra obrigatoria para todos os testes

Em nenhum cenario a Sofia deve:

- Informar preco.
- Prometer desconto.
- Confirmar estoque.
- Informar prazo de entrega.
- Calcular frete.
- Processar pagamento.
- Emitir orcamento formal.
- Fazer diagnostico tecnico.

Quando o cliente pedir algo desse tipo, a Sofia deve coletar os dados e encaminhar para atendimento humano.

---

## 1. Cliente procurando fritadeira

**Objetivo do teste**

Validar o caminho de equipamento especifico para fritadeira e o encaminhamento comercial obrigatorio.

**Mensagens simuladas do cliente**

- Comecar
- Procuro um equipamento especifico
- Fritadeira
- Batata
- Uso alto
- Quero ajuda
- Maria Silva
- 31 99999-0000
- Belo Horizonte, MG

**Caminho esperado no fluxo**

`BLOCO_00_BOAS_VINDAS` -> `BLOCO_01_MENU_INICIAL` -> `BLOCO_02_EQUIPAMENTO_ESPECIFICO` -> `BLOCO_EQUIPAMENTO_FRITADEIRA` -> `BLOCO_FRITADEIRA_02` -> `BLOCO_FRITADEIRA_03` -> `BLOCO_COLETA_NOME` -> `BLOCO_COLETA_TELEFONE` -> `BLOCO_COLETA_CIDADE` -> `BLOCO_RESUMO_ATENDIMENTO` -> `BLOCO_ENCAMINHAMENTO_COMERCIAL`

**Tags esperadas**

- `mvp_chatbot`
- `menu_inicial_mvp`
- `equipamento_especifico`
- `equipamento_fritadeira`
- `lead_mvp_qualificado`
- `encaminhar_humano`
- `encaminhar_comercial`

**Resumo esperado para o vendedor**

Cliente Maria Silva procura uma fritadeira. Pretende preparar batata, informou uso alto e pediu ajuda para escolher o modelo. Contato: 31 99999-0000. Cidade: Belo Horizonte, MG.

**Resultado esperado**

Lead encaminhado para fila comercial. Sofia nao informa preco, frete, prazo, estoque, desconto ou pagamento.

---

## 2. Cliente procurando freezer/refrigeracao

**Objetivo do teste**

Validar a triagem de refrigeracao sem confirmar temperatura, consumo, medida final ou disponibilidade.

**Mensagens simuladas do cliente**

- Comecar
- Procuro um equipamento especifico
- Freezer / Refrigeracao
- Congelar
- Carnes
- Grande
- Joao Pereira
- 11 98888-1111
- Sao Paulo, SP

**Caminho esperado no fluxo**

`BLOCO_00_BOAS_VINDAS` -> `BLOCO_01_MENU_INICIAL` -> `BLOCO_02_EQUIPAMENTO_ESPECIFICO` -> `BLOCO_EQUIPAMENTO_FREEZER_REFRIGERACAO` -> `BLOCO_FREEZER_REFRIGERACAO_02` -> `BLOCO_FREEZER_REFRIGERACAO_03` -> `BLOCO_COLETA_NOME` -> `BLOCO_COLETA_TELEFONE` -> `BLOCO_COLETA_CIDADE` -> `BLOCO_RESUMO_ATENDIMENTO` -> `BLOCO_ENCAMINHAMENTO_COMERCIAL`

**Tags esperadas**

- `mvp_chatbot`
- `menu_inicial_mvp`
- `equipamento_especifico`
- `equipamento_freezer_refrigeracao`
- `lead_mvp_qualificado`
- `encaminhar_humano`
- `encaminhar_comercial`

**Resumo esperado para o vendedor**

Cliente Joao Pereira procura freezer/refrigeracao para congelar carnes. Indicou tamanho grande. Contato: 11 98888-1111. Cidade: Sao Paulo, SP.

**Resultado esperado**

Lead encaminhado para fila comercial. Sofia nao confirma temperatura ideal, estoque, medida final, frete, prazo ou preco.

---

## 3. Cliente procurando forno

**Objetivo do teste**

Validar o caminho de forno e evitar orientacao tecnica sobre gas, energia ou exaustao.

**Mensagens simuladas do cliente**

- Comecar
- Procuro um equipamento especifico
- Forno
- Pizzas
- Pizza
- Uso medio
- Carla Mendes
- 21 97777-2222
- Niteroi, RJ

**Caminho esperado no fluxo**

`BLOCO_00_BOAS_VINDAS` -> `BLOCO_01_MENU_INICIAL` -> `BLOCO_02_EQUIPAMENTO_ESPECIFICO` -> `BLOCO_EQUIPAMENTO_FORNO` -> `BLOCO_FORNO_02` -> `BLOCO_FORNO_03` -> `BLOCO_COLETA_NOME` -> `BLOCO_COLETA_TELEFONE` -> `BLOCO_COLETA_CIDADE` -> `BLOCO_RESUMO_ATENDIMENTO` -> `BLOCO_ENCAMINHAMENTO_COMERCIAL`

**Tags esperadas**

- `mvp_chatbot`
- `menu_inicial_mvp`
- `equipamento_especifico`
- `equipamento_forno`
- `lead_mvp_qualificado`
- `encaminhar_humano`
- `encaminhar_comercial`

**Resumo esperado para o vendedor**

Cliente Carla Mendes procura forno para pizzas. Preferencia informada: forno de pizza. Uso medio. Contato: 21 97777-2222. Cidade: Niteroi, RJ.

**Resultado esperado**

Lead encaminhado para fila comercial. Sofia nao orienta instalacao, nao informa preco e nao promete disponibilidade.

---

## 4. Cliente procurando fogao industrial

**Objetivo do teste**

Validar triagem de fogao industrial com humano obrigatorio e sem orientacao tecnica de gas.

**Mensagens simuladas do cliente**

- Comecar
- Procuro um equipamento especifico
- Fogao Industrial
- 6
- Restaurante
- Nao sei
- Pedro Rocha
- 19 96666-3333
- Campinas, SP

**Caminho esperado no fluxo**

`BLOCO_00_BOAS_VINDAS` -> `BLOCO_01_MENU_INICIAL` -> `BLOCO_02_EQUIPAMENTO_ESPECIFICO` -> `BLOCO_EQUIPAMENTO_FOGAO_INDUSTRIAL` -> `BLOCO_FOGAO_INDUSTRIAL_02` -> `BLOCO_FOGAO_INDUSTRIAL_03` -> `BLOCO_COLETA_NOME` -> `BLOCO_COLETA_TELEFONE` -> `BLOCO_COLETA_CIDADE` -> `BLOCO_RESUMO_ATENDIMENTO` -> `BLOCO_ENCAMINHAMENTO_COMERCIAL`

**Tags esperadas**

- `mvp_chatbot`
- `menu_inicial_mvp`
- `equipamento_especifico`
- `equipamento_fogao_industrial`
- `lead_mvp_qualificado`
- `encaminhar_humano`
- `encaminhar_comercial`

**Resumo esperado para o vendedor**

Cliente Pedro Rocha procura fogao industrial de 6 bocas para restaurante. Nao sabe informar se ja tem ponto de gas. Contato: 19 96666-3333. Cidade: Campinas, SP.

**Resultado esperado**

Lead encaminhado para fila comercial. Sofia nao orienta instalacao de gas e nao promete prazo, preco, frete ou estoque.

---

## 5. Cliente procurando chapa

**Objetivo do teste**

Validar caminho de chapa e coleta das informacoes basicas antes do consultor.

**Mensagens simuladas do cliente**

- Comecar
- Procuro um equipamento especifico
- Chapa
- Hamburguer
- Grande
- A gas
- Ana Costa
- 41 95555-4444
- Curitiba, PR

**Caminho esperado no fluxo**

`BLOCO_00_BOAS_VINDAS` -> `BLOCO_01_MENU_INICIAL` -> `BLOCO_02_EQUIPAMENTO_ESPECIFICO` -> `BLOCO_EQUIPAMENTO_CHAPA` -> `BLOCO_CHAPA_02` -> `BLOCO_CHAPA_03` -> `BLOCO_COLETA_NOME` -> `BLOCO_COLETA_TELEFONE` -> `BLOCO_COLETA_CIDADE` -> `BLOCO_RESUMO_ATENDIMENTO` -> `BLOCO_ENCAMINHAMENTO_COMERCIAL`

**Tags esperadas**

- `mvp_chatbot`
- `menu_inicial_mvp`
- `equipamento_especifico`
- `equipamento_chapa`
- `lead_mvp_qualificado`
- `encaminhar_humano`
- `encaminhar_comercial`

**Resumo esperado para o vendedor**

Cliente Ana Costa procura chapa para hamburguer. Informou tamanho grande e preferencia por modelo a gas. Contato: 41 95555-4444. Cidade: Curitiba, PR.

**Resultado esperado**

Lead encaminhado para fila comercial. Sofia nao valida instalacao, preco, frete, prazo, desconto ou estoque.

---

## 6. Cliente procurando outro equipamento

**Objetivo do teste**

Validar caminho de equipamento nao listado e encaminhamento rapido para humano.

**Mensagens simuladas do cliente**

- Comecar
- Procuro um equipamento especifico
- Outro equipamento
- Nao sei o nome
- Preparar
- Padaria
- Lucas Almeida
- 27 94444-5555
- Vitoria, ES

**Caminho esperado no fluxo**

`BLOCO_00_BOAS_VINDAS` -> `BLOCO_01_MENU_INICIAL` -> `BLOCO_02_EQUIPAMENTO_ESPECIFICO` -> `BLOCO_EQUIPAMENTO_OUTRO_EQUIPAMENTO` -> `BLOCO_OUTRO_EQUIPAMENTO_02` -> `BLOCO_OUTRO_EQUIPAMENTO_03` -> `BLOCO_COLETA_NOME` -> `BLOCO_COLETA_TELEFONE` -> `BLOCO_COLETA_CIDADE` -> `BLOCO_RESUMO_ATENDIMENTO` -> `BLOCO_ENCAMINHAMENTO_COMERCIAL`

**Tags esperadas**

- `mvp_chatbot`
- `menu_inicial_mvp`
- `equipamento_especifico`
- `equipamento_outro`
- `lead_mvp_qualificado`
- `encaminhar_humano`
- `encaminhar_comercial`

**Resumo esperado para o vendedor**

Cliente Lucas Almeida procura outro equipamento, mas nao sabe o nome. Informou que sera usado para preparo em padaria. Contato: 27 94444-5555. Cidade: Vitoria, ES.

**Resultado esperado**

Lead encaminhado para fila comercial. Sofia nao sugere modelo especifico e nao promete preco, estoque, frete ou prazo.

---

## 7. Cliente querendo montar/reformar cozinha

**Objetivo do teste**

Validar caminho de projeto de cozinha e qualificacao inicial para atendimento comercial.

**Mensagens simuladas do cliente**

- Comecar
- Vou montar ou reformar uma cozinha
- Reformando
- Restaurante
- Em ate 30 dias
- Fernanda Lima
- 62 93333-6666
- Goiania, GO

**Caminho esperado no fluxo**

`BLOCO_00_BOAS_VINDAS` -> `BLOCO_01_MENU_INICIAL` -> `BLOCO_03_PROJETO_COZINHA` -> `BLOCO_03A_TIPO_NEGOCIO` -> `BLOCO_03B_PROJETO_PREVISAO` -> `BLOCO_COLETA_NOME` -> `BLOCO_COLETA_TELEFONE` -> `BLOCO_COLETA_CIDADE` -> `BLOCO_RESUMO_ATENDIMENTO` -> `BLOCO_ENCAMINHAMENTO_COMERCIAL`

**Tags esperadas**

- `mvp_chatbot`
- `menu_inicial_mvp`
- `projeto_cozinha`
- `lead_mvp_qualificado`
- `encaminhar_humano`
- `encaminhar_comercial`

**Resumo esperado para o vendedor**

Cliente Fernanda Lima quer reformar uma cozinha de restaurante. Previsao de compra: em ate 30 dias. Contato: 62 93333-6666. Cidade: Goiania, GO.

**Resultado esperado**

Lead encaminhado para fila comercial. Sofia nao promete projeto, visita, prazo, preco, desconto, frete ou estoque.

---

## 8. Cliente pedindo suporte/pos-venda

**Objetivo do teste**

Validar separacao de suporte/pos-venda e impedir diagnostico tecnico pelo bot.

**Mensagens simuladas do cliente**

- Comecar
- Suporte / Pos-venda
- Sim
- Manutencao
- Roberto Nunes
- 31 92222-7777
- Contagem, MG

**Caminho esperado no fluxo**

`BLOCO_00_BOAS_VINDAS` -> `BLOCO_01_MENU_INICIAL` -> `BLOCO_04_SUPORTE_POS_VENDA` -> `BLOCO_04A_ASSUNTO_POS_VENDA` -> `BLOCO_COLETA_NOME` -> `BLOCO_COLETA_TELEFONE` -> `BLOCO_COLETA_CIDADE` -> `BLOCO_RESUMO_ATENDIMENTO` -> `BLOCO_ENCAMINHAMENTO_POS_VENDA`

**Tags esperadas**

- `mvp_chatbot`
- `menu_inicial_mvp`
- `pos_venda`
- `lead_mvp_qualificado`
- `encaminhar_humano`
- `encaminhar_pos_venda`

**Resumo esperado para o vendedor/atendente**

Cliente Roberto Nunes informa que ja comprou com a SS Vale e precisa de ajuda com manutencao. Contato: 31 92222-7777. Cidade: Contagem, MG.

**Resultado esperado**

Atendimento encaminhado para pos-venda. Sofia nao faz diagnostico tecnico, nao orienta reparo e nao promete garantia, prazo ou visita.

---

## 9. Fornecedor/representante

**Objetivo do teste**

Validar separacao de fornecedor ou representante para a fila correta.

**Mensagens simuladas do cliente**

- Comecar
- Sou fornecedor ou representante
- Equipamentos Alfa Ltda
- Fornecedor
- Rafael Souza
- 51 91111-8888
- Porto Alegre, RS

**Caminho esperado no fluxo**

`BLOCO_00_BOAS_VINDAS` -> `BLOCO_01_MENU_INICIAL` -> `BLOCO_05_FORNECEDOR_REPRESENTANTE` -> `BLOCO_05A_TIPO_CONTATO` -> `BLOCO_COLETA_NOME` -> `BLOCO_COLETA_TELEFONE` -> `BLOCO_COLETA_CIDADE` -> `BLOCO_RESUMO_ATENDIMENTO` -> `BLOCO_ENCAMINHAMENTO_FORNECEDOR`

**Tags esperadas**

- `mvp_chatbot`
- `menu_inicial_mvp`
- `fornecedor_representante`
- `lead_mvp_qualificado`
- `encaminhar_humano`
- `encaminhar_fornecedor`

**Resumo esperado para o vendedor/atendente**

Contato Rafael Souza fala em nome da empresa Equipamentos Alfa Ltda. Tipo de contato: fornecedor. Telefone: 51 91111-8888. Cidade: Porto Alegre, RS.

**Resultado esperado**

Contato encaminhado para fila de fornecedores ou responsavel definido. Sofia nao trata negociacao comercial de fornecedor pelo bot.

---

## 10. Cliente querendo falar com consultor

**Objetivo do teste**

Validar caminho direto para consultor com coleta minima de dados.

**Mensagens simuladas do cliente**

- Comecar
- Quero falar com um consultor
- Quero ajuda para escolher equipamentos para minha lanchonete
- Juliana Martins
- 71 90000-9999
- Salvador, BA

**Caminho esperado no fluxo**

`BLOCO_00_BOAS_VINDAS` -> `BLOCO_01_MENU_INICIAL` -> `BLOCO_06_CONSULTOR_DIRETO` -> `BLOCO_COLETA_NOME` -> `BLOCO_COLETA_TELEFONE` -> `BLOCO_COLETA_CIDADE` -> `BLOCO_RESUMO_ATENDIMENTO` -> `BLOCO_ENCAMINHAMENTO_COMERCIAL`

**Tags esperadas**

- `mvp_chatbot`
- `menu_inicial_mvp`
- `consultor_direto`
- `lead_mvp_qualificado`
- `encaminhar_humano`
- `encaminhar_comercial`

**Resumo esperado para o vendedor**

Cliente Juliana Martins quer falar com consultor para escolher equipamentos para lanchonete. Contato: 71 90000-9999. Cidade: Salvador, BA.

**Resultado esperado**

Lead encaminhado para fila comercial. Sofia nao pergunta preco, nao promete retorno em prazo especifico e nao oferece desconto.

---

## 11. Cliente abandonando atendimento

**Objetivo do teste**

Validar se o fluxo nao trava quando o cliente para de responder antes de concluir a coleta de dados.

**Mensagens simuladas do cliente**

- Comecar
- Procuro um equipamento especifico
- Fritadeira
- Salgados
- Uso medio
- Cliente para de responder

**Caminho esperado no fluxo**

`BLOCO_00_BOAS_VINDAS` -> `BLOCO_01_MENU_INICIAL` -> `BLOCO_02_EQUIPAMENTO_ESPECIFICO` -> `BLOCO_EQUIPAMENTO_FRITADEIRA` -> `BLOCO_FRITADEIRA_02` -> aguardando resposta em `BLOCO_FRITADEIRA_03`

**Tags esperadas**

- `mvp_chatbot`
- `menu_inicial_mvp`
- `equipamento_especifico`
- `equipamento_fritadeira`

**Resumo esperado para o vendedor**

Atendimento incompleto. Cliente demonstrou interesse em fritadeira para salgados e informou uso medio, mas abandonou antes de informar modelo, nome, telefone e cidade.

**Resultado esperado**

O bot deve ficar aguardando resposta ou encerrar conforme regra de inatividade do Maxbot. Nao deve encaminhar como lead qualificado sem telefone. Nao deve prometer contato sem dados.

---

## 12. Cliente com urgencia

**Objetivo do teste**

Validar tratamento de urgencia sem promessa de prazo, estoque ou entrega.

**Mensagens simuladas do cliente**

- Comecar
- Procuro um equipamento especifico
- Freezer / Refrigeracao
- Congelar
- Congelados
- Grande
- Preciso urgente, entrega hoje?
- Beatriz Santos
- 85 98888-3333
- Fortaleza, CE

**Caminho esperado no fluxo**

`BLOCO_00_BOAS_VINDAS` -> `BLOCO_01_MENU_INICIAL` -> `BLOCO_02_EQUIPAMENTO_ESPECIFICO` -> `BLOCO_EQUIPAMENTO_FREEZER_REFRIGERACAO` -> `BLOCO_FREEZER_REFRIGERACAO_02` -> `BLOCO_FREEZER_REFRIGERACAO_03` -> regra de bloqueio para prazo/entrega -> `BLOCO_COLETA_NOME` -> `BLOCO_COLETA_TELEFONE` -> `BLOCO_COLETA_CIDADE` -> `BLOCO_RESUMO_ATENDIMENTO` -> `BLOCO_ENCAMINHAMENTO_COMERCIAL`

**Tags esperadas**

- `mvp_chatbot`
- `menu_inicial_mvp`
- `equipamento_especifico`
- `equipamento_freezer_refrigeracao`
- `lead_mvp_qualificado`
- `encaminhar_humano`
- `encaminhar_comercial`

**Resumo esperado para o vendedor**

Cliente Beatriz Santos procura freezer/refrigeracao para congelados, tamanho grande. Informou urgencia e perguntou sobre entrega hoje. Contato: 85 98888-3333. Cidade: Fortaleza, CE.

**Resultado esperado**

Lead encaminhado para fila comercial com observacao de urgencia. Sofia nao promete entrega hoje, nao confirma estoque, nao calcula frete e nao informa prazo.

---

## 13. Cliente digitando resposta fora das opcoes

**Objetivo do teste**

Validar o bloco de resposta nao entendida e garantir que o cliente nao fique sem saida quando digitar algo fora das opcoes.

**Mensagens simuladas do cliente**

- Comecar
- Quero ver tudo
- Voltar ao menu inicial
- Quero falar com um consultor
- Preciso de ajuda para comprar equipamentos
- Marcos Oliveira
- 48 97777-1010
- Florianopolis, SC

**Caminho esperado no fluxo**

`BLOCO_00_BOAS_VINDAS` -> `BLOCO_01_MENU_INICIAL` -> resposta fora das opcoes -> `BLOCO_RESPOSTA_NAO_ENTENDIDA` -> `BLOCO_01_MENU_INICIAL` -> `BLOCO_06_CONSULTOR_DIRETO` -> `BLOCO_COLETA_NOME` -> `BLOCO_COLETA_TELEFONE` -> `BLOCO_COLETA_CIDADE` -> `BLOCO_RESUMO_ATENDIMENTO` -> `BLOCO_ENCAMINHAMENTO_COMERCIAL`

**Tags esperadas**

- `mvp_chatbot`
- `menu_inicial_mvp`
- `resposta_nao_entendida`
- `consultor_direto`
- `lead_mvp_qualificado`
- `encaminhar_humano`
- `encaminhar_comercial`

**Resumo esperado para o vendedor**

Cliente Marcos Oliveira digitou uma resposta fora das opcoes, voltou ao menu e pediu atendimento com consultor. Motivo informado: ajuda para comprar equipamentos. Contato: 48 97777-1010. Cidade: Florianopolis, SC.

**Resultado esperado**

Cliente recuperado pelo fluxo sem travar. Sofia nao inventa resposta, nao promete condicao comercial e encaminha para atendimento humano.

---

## 14. Cliente pedindo preco, frete ou pagamento

**Objetivo do teste**

Validar a regra de bloqueio para pedidos de preco, frete, pagamento ou orcamento.

**Mensagens simuladas do cliente**

- Comecar
- Procuro um equipamento especifico
- Chapa
- Hamburguer
- Media
- Eletrica
- Qual o preco? Tem frete gratis? Posso pagar por aqui?
- Patricia Gomes
- 16 96666-2020
- Ribeirao Preto, SP

**Caminho esperado no fluxo**

`BLOCO_00_BOAS_VINDAS` -> `BLOCO_01_MENU_INICIAL` -> `BLOCO_02_EQUIPAMENTO_ESPECIFICO` -> `BLOCO_EQUIPAMENTO_CHAPA` -> `BLOCO_CHAPA_02` -> `BLOCO_CHAPA_03` -> regra de bloqueio para preco/frete/pagamento/orcamento -> `BLOCO_COLETA_NOME` -> `BLOCO_COLETA_TELEFONE` -> `BLOCO_COLETA_CIDADE` -> `BLOCO_RESUMO_ATENDIMENTO` -> `BLOCO_ENCAMINHAMENTO_COMERCIAL`

**Tags esperadas**

- `mvp_chatbot`
- `menu_inicial_mvp`
- `equipamento_especifico`
- `equipamento_chapa`
- `lead_mvp_qualificado`
- `encaminhar_humano`
- `encaminhar_comercial`

**Resumo esperado para o vendedor**

Cliente Patricia Gomes procura chapa para hamburguer, tamanho medio, preferencia eletrica. Perguntou sobre preco, frete gratis e pagamento pelo WhatsApp. Contato: 16 96666-2020. Cidade: Ribeirao Preto, SP.

**Resultado esperado**

Lead encaminhado para fila comercial. Sofia nao informa preco, nao oferece frete gratis, nao processa pagamento e nao emite orcamento.
