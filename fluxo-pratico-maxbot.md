# Fluxo Pratico Maxbot - Sofia SS Vale

Passo a passo manual para configurar o chatbot Sofia no Maxbot dentro do bloco:

`0 - MVP_ChatBot`

Este arquivo e para montar o MVP hoje no Maxbot. Nao mexer no fluxo atual em producao sem validacao.

## 1. Bloco inicial da Sofia

### Nome do bloco

`BLOCO_00_BOAS_VINDAS`

### Tipo

Mensagem + botao/menu simples

### Mensagem

Ola! Eu sou a Sofia, assistente virtual da SS Vale. Vou te ajudar a encontrar o melhor caminho para o seu atendimento.

### Opcao

- Comecar

### Proximo passo

- Comecar -> `BLOCO_01_MENU_INICIAL`

### Tag

- `mvp_chatbot`

## 2. Menu principal

### Nome do bloco

`BLOCO_01_MENU_INICIAL`

### Tipo

Menu

### Mensagem

Como posso te ajudar hoje?

### Opcoes

1. Procuro um equipamento especifico
2. Vou montar ou reformar uma cozinha
3. Suporte / Pos-venda
4. Fornecedor / Representante
5. Falar com consultor

### Proximo passo

- Procuro um equipamento especifico -> `BLOCO_02_EQUIPAMENTO_ESPECIFICO`
- Vou montar ou reformar uma cozinha -> `BLOCO_03_PROJETO_COZINHA`
- Suporte / Pos-venda -> `BLOCO_04_SUPORTE_POS_VENDA`
- Fornecedor / Representante -> `BLOCO_05_FORNECEDOR_REPRESENTANTE`
- Falar com consultor -> `BLOCO_06_CONSULTOR_DIRETO`

### Tags

- `menu_inicial_mvp`

## 3. Fluxo "Procuro um equipamento especifico"

### Nome do bloco

`BLOCO_02_EQUIPAMENTO_ESPECIFICO`

### Tipo

Menu

### Mensagem

Qual equipamento voce procura?

### Opcoes

- Fritadeira
- Freezer / Refrigeracao
- Forno
- Fogao Industrial
- Chapa
- Outro equipamento

### Proximo passo

- Fritadeira -> `BLOCO_EQ_FRITADEIRA`
- Freezer / Refrigeracao -> `BLOCO_EQ_FREEZER`
- Forno -> `BLOCO_EQ_FORNO`
- Fogao Industrial -> `BLOCO_EQ_FOGAO`
- Chapa -> `BLOCO_EQ_CHAPA`
- Outro equipamento -> `BLOCO_EQ_OUTRO`

### Tag

- `equipamento_especifico`

---

### Fritadeira

**Nome do bloco:** `BLOCO_EQ_FRITADEIRA`

**Mensagem 1:** O que voce quer preparar?

**Opcoes:**

- Batata
- Salgados
- Frango
- Porcoes
- Ainda nao sei

**Mensagem 2:** O uso sera como?

**Opcoes:**

- Pouco uso
- Uso medio
- Uso alto
- Ainda nao sei

**Mensagem 3:** Prefere qual modelo?

**Opcoes:**

- A gas
- Eletrica
- Quero ajuda

**Depois seguir para:** `BLOCO_COLETA_DADOS`

**Tag:** `equipamento_fritadeira`

---

### Freezer / Refrigeracao

**Nome do bloco:** `BLOCO_EQ_FREEZER`

**Mensagem 1:** Qual a necessidade?

**Opcoes:**

- Refrigerar
- Congelar
- Expor produtos
- Armazenar
- Ainda nao sei

**Mensagem 2:** O que vai guardar?

**Opcoes:**

- Bebidas
- Carnes
- Laticinios
- Congelados
- Outros

**Mensagem 3:** Ja sabe o tamanho?

**Opcoes:**

- Pequeno
- Medio
- Grande
- Tenho medidas
- Nao sei

**Depois seguir para:** `BLOCO_COLETA_DADOS`

**Tag:** `equipamento_freezer_refrigeracao`

---

### Forno

**Nome do bloco:** `BLOCO_EQ_FORNO`

**Mensagem 1:** O que voce vai assar?

**Opcoes:**

- Paes
- Pizzas
- Bolos
- Salgados
- Assados
- Variados

**Mensagem 2:** Prefere algum tipo?

**Opcoes:**

- A gas
- Eletrico
- Pizza
- Combinado
- Quero ajuda

**Mensagem 3:** O uso sera como?

**Opcoes:**

- Pouco uso
- Uso medio
- Uso alto
- Ainda nao sei

**Depois seguir para:** `BLOCO_COLETA_DADOS`

**Tag:** `equipamento_forno`

---

### Fogao Industrial

**Nome do bloco:** `BLOCO_EQ_FOGAO`

**Mensagem 1:** Quantas bocas precisa?

**Opcoes:**

- 2
- 4
- 6
- 8 ou mais
- Ainda nao sei

**Mensagem 2:** Onde sera usado?

**Opcoes:**

- Restaurante
- Lanchonete
- Cozinha industrial
- Buffet
- Outro

**Mensagem 3:** Ja tem ponto de gas?

**Opcoes:**

- Sim
- Nao
- Em preparacao
- Nao sei

**Depois seguir para:** `BLOCO_COLETA_DADOS`

**Tag:** `equipamento_fogao_industrial`

---

### Chapa

**Nome do bloco:** `BLOCO_EQ_CHAPA`

**Mensagem 1:** O que voce vai preparar?

**Opcoes:**

- Hamburguer
- Lanches
- Carnes
- Porcoes
- Variados

**Mensagem 2:** Ja sabe o tamanho?

**Opcoes:**

- Pequena
- Media
- Grande
- Tenho medidas
- Nao sei

**Mensagem 3:** Prefere qual modelo?

**Opcoes:**

- A gas
- Eletrica
- Quero ajuda

**Depois seguir para:** `BLOCO_COLETA_DADOS`

**Tag:** `equipamento_chapa`

---

### Outro equipamento

**Nome do bloco:** `BLOCO_EQ_OUTRO`

**Mensagem 1:** Qual equipamento voce procura?

**Opcoes:**

- Vou digitar
- Nao sei o nome
- Tenho foto
- Quero ajuda

**Mensagem 2:** Para que ele sera usado?

**Opcoes:**

- Preparar
- Refrigerar
- Expor
- Lavar
- Organizar
- Outro

**Mensagem 3:** Qual seu tipo de negocio?

**Opcoes:**

- Restaurante
- Lanchonete
- Padaria
- Mercado
- Cozinha industrial
- Outro

**Depois seguir para:** `BLOCO_COLETA_DADOS`

**Tag:** `equipamento_outro`

## 4. Fluxo "Vou montar ou reformar uma cozinha"

### Nome do bloco

`BLOCO_03_PROJETO_COZINHA`

### Tipo

Perguntas em sequencia

### Mensagem 1

Voce esta montando, reformando ou ampliando uma cozinha?

### Opcoes

- Montando
- Reformando
- Ampliando
- Ainda estou planejando

### Mensagem 2

Qual e o tipo de negocio?

### Opcoes

- Restaurante
- Lanchonete
- Padaria
- Mercado
- Cozinha industrial
- Outro

### Mensagem 3

Quando pretende comprar os equipamentos?

### Opcoes

- Agora
- Em ate 30 dias
- Em 1 a 3 meses
- Ainda estou pesquisando

### Proximo passo

Depois seguir para `BLOCO_COLETA_DADOS`.

### Tag

- `projeto_cozinha`

## 5. Fluxo "Suporte / Pos-venda"

### Nome do bloco

`BLOCO_04_SUPORTE_POS_VENDA`

### Tipo

Perguntas em sequencia

### Mensagem 1

Voce ja comprou com a SS Vale?

### Opcoes

- Sim
- Nao
- Nao sei informar

### Mensagem 2

Sobre qual assunto voce precisa de ajuda?

### Opcoes

- Garantia
- Instalacao
- Manutencao
- Troca
- Pedido ja feito
- Outro

### Mensagem de limite

Eu consigo registrar sua solicitacao e direcionar ao time responsavel, mas nao consigo fazer diagnostico tecnico por aqui.

### Proximo passo

Depois seguir para `BLOCO_COLETA_DADOS`.

### Tags

- `pos_venda`

## 6. Fluxo "Fornecedor / Representante"

### Nome do bloco

`BLOCO_05_FORNECEDOR_REPRESENTANTE`

### Tipo

Perguntas em sequencia

### Mensagem 1

Voce fala em nome de qual empresa?

### Resposta

Resposta livre

### Mensagem 2

Qual e o tipo de contato?

### Opcoes

- Fornecedor
- Representante
- Parceria
- Outro

### Proximo passo

Depois seguir para `BLOCO_COLETA_DADOS`.

### Tag

- `fornecedor_representante`

## 7. Fluxo "Falar com consultor"

### Nome do bloco

`BLOCO_06_CONSULTOR_DIRETO`

### Tipo

Pergunta aberta

### Mensagem

Claro. Para chamar um consultor, me diga rapidamente o que voce precisa.

### Resposta

Resposta livre

### Proximo passo

Depois seguir para `BLOCO_COLETA_DADOS`.

### Tag

- `consultor_direto`

## Coleta de dados obrigatoria

### Nome do bloco

`BLOCO_COLETA_DADOS`

### Tipo

Perguntas em sequencia

### Pergunta 1

Qual e o seu nome?

**Campo:** `nome_cliente`

### Pergunta 2

Qual telefone ou WhatsApp para contato?

**Campo:** `telefone_whatsapp`

### Pergunta 3

Voce fala de qual cidade e estado?

**Campo:** `cidade_estado`

### Proximo passo

Depois seguir para `BLOCO_RESUMO_FINAL`.

## 8. Resumo final para vendedor

### Nome do bloco

`BLOCO_RESUMO_FINAL`

### Tipo

Resumo + encaminhamento humano

### Mensagem para o cliente

Pronto, ja registrei suas informacoes. A equipe da SS Vale vai continuar o atendimento com voce.

### Resumo interno para o atendente

Configurar no Maxbot para o atendente visualizar, quando possivel:

- Nome do cliente
- Telefone ou WhatsApp
- Cidade e estado
- Caminho escolhido no menu
- Equipamento de interesse, se houver
- Respostas das perguntas feitas
- Tag aplicada

### Encaminhamento

- Equipamentos -> fila comercial
- Projeto de cozinha -> fila comercial
- Falar com consultor -> fila comercial
- Suporte / Pos-venda -> fila de pos-venda
- Fornecedor / Representante -> fila responsavel por fornecedores/representantes

## 9. Tags sugeridas

### Tags gerais

- `mvp_chatbot`
- `menu_inicial_mvp`
- `lead_mvp_qualificado`
- `encaminhar_humano`

### Tags por caminho

- `equipamento_especifico`
- `projeto_cozinha`
- `pos_venda`
- `fornecedor_representante`
- `consultor_direto`

### Tags por equipamento

- `equipamento_fritadeira`
- `equipamento_freezer_refrigeracao`
- `equipamento_forno`
- `equipamento_fogao_industrial`
- `equipamento_chapa`
- `equipamento_outro`

### Tags por destino

- `encaminhar_comercial`
- `encaminhar_pos_venda`
- `encaminhar_fornecedor`

## 10. O que NAO deve ser ativado ainda

- Nao ativar IA generativa.
- Nao integrar catalogo automatico.
- Nao calcular preco.
- Nao calcular frete.
- Nao processar pagamento.
- Nao emitir orcamento formal.
- Nao confirmar estoque.
- Nao prometer prazo de entrega.
- Nao prometer desconto.
- Nao fazer diagnostico tecnico.
- Nao substituir o fluxo atual em producao sem teste e aprovacao.
- Nao conectar o bloco `0 - MVP_ChatBot` ao atendimento principal antes de validar todos os caminhos.

## Mensagens de seguranca para usar se necessario

### Pedido de preco, frete, pagamento ou orcamento

Eu nao consigo tratar isso por aqui, mas vou encaminhar suas informacoes para um consultor da SS Vale te orientar corretamente.

### Pedido de suporte tecnico

Eu consigo registrar sua solicitacao e direcionar ao time responsavel, mas nao consigo fazer diagnostico tecnico por aqui.

### Resposta fora das opcoes

Nao consegui entender. Pode escolher uma das opcoes do menu?
