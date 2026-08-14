# Roteiro Operacional Maxbot - MVP Sofia SS Vale

Este roteiro organiza o fluxo do MVP para configuracao manual no Maxbot.

O MVP deve ficar separado no bloco principal:

`0 - MVP_ChatBot`

Nao incluir IA generativa, calculo de preco, frete, pagamento ou emissao de orcamento.

## Variaveis padrao

- `nome_cliente`
- `telefone_whatsapp`
- `cidade_estado`
- `motivo_contato`
- `equipamento_interesse`
- `tipo_negocio`
- `previsao_compra`
- `ja_comprou_ssvale`
- `assunto_pos_venda`
- `empresa_fornecedor`
- `tipo_contato_fornecedor`
- `resposta_pergunta_1`
- `resposta_pergunta_2`
- `resposta_pergunta_3`

## Regra para resposta fora das opcoes

Em qualquer menu ou pergunta com opcoes, se o cliente digitar algo que nao encaixa nas opcoes configuradas, enviar para:

`BLOCO_RESPOSTA_NAO_ENTENDIDA`

---

## BLOCO_00_BOAS_VINDAS

**Tipo do bloco:** menu

**Mensagem exata:**

Ola! Eu sou a Sofia, assistente virtual da SS Vale. Vou te ajudar a encontrar o melhor caminho para o seu atendimento.

**Opcoes de resposta:**

- Comecar

**Proximo bloco para cada resposta:**

- Comecar -> `BLOCO_01_MENU_INICIAL`
- Resposta fora das opcoes -> `BLOCO_RESPOSTA_NAO_ENTENDIDA`

**Tags aplicadas:**

- `mvp_chatbot`

**Variaveis/campos que devem ser preenchidos:**

- Nenhum

---

## BLOCO_01_MENU_INICIAL

**Tipo do bloco:** menu

**Mensagem exata:**

Como posso te ajudar hoje?

**Opcoes de resposta:**

- Procuro um equipamento especifico
- Vou montar ou reformar uma cozinha
- Suporte / Pos-venda
- Sou fornecedor ou representante
- Quero falar com um consultor

**Proximo bloco para cada resposta:**

- Procuro um equipamento especifico -> `BLOCO_02_EQUIPAMENTO_ESPECIFICO`
- Vou montar ou reformar uma cozinha -> `BLOCO_03_PROJETO_COZINHA`
- Suporte / Pos-venda -> `BLOCO_04_SUPORTE_POS_VENDA`
- Sou fornecedor ou representante -> `BLOCO_05_FORNECEDOR_REPRESENTANTE`
- Quero falar com um consultor -> `BLOCO_06_CONSULTOR_DIRETO`
- Resposta fora das opcoes -> `BLOCO_RESPOSTA_NAO_ENTENDIDA`

**Tags aplicadas:**

- `menu_inicial_mvp`

**Variaveis/campos que devem ser preenchidos:**

- `motivo_contato`

---

## BLOCO_02_EQUIPAMENTO_ESPECIFICO

**Tipo do bloco:** menu

**Mensagem exata:**

Qual equipamento voce procura?

**Opcoes de resposta:**

- Fritadeira
- Freezer / Refrigeracao
- Forno
- Fogao Industrial
- Chapa
- Outro equipamento

**Proximo bloco para cada resposta:**

- Fritadeira -> `BLOCO_EQUIPAMENTO_FRITADEIRA`
- Freezer / Refrigeracao -> `BLOCO_EQUIPAMENTO_FREEZER_REFRIGERACAO`
- Forno -> `BLOCO_EQUIPAMENTO_FORNO`
- Fogao Industrial -> `BLOCO_EQUIPAMENTO_FOGAO_INDUSTRIAL`
- Chapa -> `BLOCO_EQUIPAMENTO_CHAPA`
- Outro equipamento -> `BLOCO_EQUIPAMENTO_OUTRO_EQUIPAMENTO`
- Resposta fora das opcoes -> `BLOCO_RESPOSTA_NAO_ENTENDIDA`

**Tags aplicadas:**

- `equipamento_especifico`

**Variaveis/campos que devem ser preenchidos:**

- `equipamento_interesse`

---

## BLOCO_03_PROJETO_COZINHA

**Tipo do bloco:** pergunta

**Mensagem exata:**

Voce esta montando, reformando ou ampliando uma cozinha?

**Opcoes de resposta:**

- Montando
- Reformando
- Ampliando
- Ainda estou planejando

**Proximo bloco para cada resposta:**

- Montando -> `BLOCO_03A_TIPO_NEGOCIO`
- Reformando -> `BLOCO_03A_TIPO_NEGOCIO`
- Ampliando -> `BLOCO_03A_TIPO_NEGOCIO`
- Ainda estou planejando -> `BLOCO_03A_TIPO_NEGOCIO`
- Resposta fora das opcoes -> `BLOCO_RESPOSTA_NAO_ENTENDIDA`

**Tags aplicadas:**

- `projeto_cozinha`

**Variaveis/campos que devem ser preenchidos:**

- `motivo_contato`: Projeto de cozinha

---

## BLOCO_03A_TIPO_NEGOCIO

**Tipo do bloco:** pergunta

**Mensagem exata:**

Qual e o tipo de negocio?

**Opcoes de resposta:**

- Restaurante
- Lanchonete
- Padaria
- Mercado
- Cozinha industrial
- Outro

**Proximo bloco para cada resposta:**

- Todas as respostas -> `BLOCO_03B_PROJETO_PREVISAO`
- Resposta fora das opcoes -> `BLOCO_RESPOSTA_NAO_ENTENDIDA`

**Tags aplicadas:**

- `projeto_cozinha`

**Variaveis/campos que devem ser preenchidos:**

- `tipo_negocio`

---

## BLOCO_03B_PROJETO_PREVISAO

**Tipo do bloco:** pergunta

**Mensagem exata:**

Quando pretende comprar os equipamentos?

**Opcoes de resposta:**

- Agora
- Em ate 30 dias
- Em 1 a 3 meses
- Ainda estou pesquisando

**Proximo bloco para cada resposta:**

- Todas as respostas -> `BLOCO_COLETA_NOME`
- Resposta fora das opcoes -> `BLOCO_RESPOSTA_NAO_ENTENDIDA`

**Tags aplicadas:**

- `projeto_cozinha`

**Variaveis/campos que devem ser preenchidos:**

- `previsao_compra`

---

## BLOCO_04_SUPORTE_POS_VENDA

**Tipo do bloco:** pergunta

**Mensagem exata:**

Voce ja comprou com a SS Vale?

**Opcoes de resposta:**

- Sim
- Nao
- Nao sei informar

**Proximo bloco para cada resposta:**

- Sim -> `BLOCO_04A_ASSUNTO_POS_VENDA`
- Nao -> `BLOCO_06_CONSULTOR_DIRETO`
- Nao sei informar -> `BLOCO_04A_ASSUNTO_POS_VENDA`
- Resposta fora das opcoes -> `BLOCO_RESPOSTA_NAO_ENTENDIDA`

**Tags aplicadas:**

- `pos_venda`

**Variaveis/campos que devem ser preenchidos:**

- `ja_comprou_ssvale`

---

## BLOCO_04A_ASSUNTO_POS_VENDA

**Tipo do bloco:** pergunta

**Mensagem exata:**

Sobre qual assunto voce precisa de ajuda?

**Opcoes de resposta:**

- Garantia
- Instalacao
- Manutencao
- Troca
- Pedido ja feito
- Outro

**Proximo bloco para cada resposta:**

- Todas as respostas -> `BLOCO_COLETA_NOME`
- Resposta fora das opcoes -> `BLOCO_RESPOSTA_NAO_ENTENDIDA`

**Tags aplicadas:**

- `pos_venda`

**Variaveis/campos que devem ser preenchidos:**

- `assunto_pos_venda`

---

## BLOCO_05_FORNECEDOR_REPRESENTANTE

**Tipo do bloco:** pergunta

**Mensagem exata:**

Voce fala em nome de qual empresa?

**Opcoes de resposta:**

- Resposta livre

**Proximo bloco para cada resposta:**

- Resposta livre -> `BLOCO_05A_TIPO_CONTATO`

**Tags aplicadas:**

- `fornecedor_representante`

**Variaveis/campos que devem ser preenchidos:**

- `empresa_fornecedor`

---

## BLOCO_05A_TIPO_CONTATO

**Tipo do bloco:** pergunta

**Mensagem exata:**

Qual e o tipo de contato?

**Opcoes de resposta:**

- Fornecedor
- Representante
- Parceria
- Outro

**Proximo bloco para cada resposta:**

- Todas as respostas -> `BLOCO_COLETA_NOME`
- Resposta fora das opcoes -> `BLOCO_RESPOSTA_NAO_ENTENDIDA`

**Tags aplicadas:**

- `fornecedor_representante`

**Variaveis/campos que devem ser preenchidos:**

- `tipo_contato_fornecedor`

---

## BLOCO_06_CONSULTOR_DIRETO

**Tipo do bloco:** pergunta

**Mensagem exata:**

Claro. Para chamar um consultor, me diga rapidamente o que voce precisa.

**Opcoes de resposta:**

- Resposta livre

**Proximo bloco para cada resposta:**

- Resposta livre -> `BLOCO_COLETA_NOME`

**Tags aplicadas:**

- `consultor_direto`

**Variaveis/campos que devem ser preenchidos:**

- `motivo_contato`

---

## BLOCO_EQUIPAMENTO_FRITADEIRA

**Tipo do bloco:** pergunta

**Mensagem exata:**

O que voce quer preparar?

**Opcoes de resposta:**

- Batata
- Salgados
- Frango
- Porcoes
- Ainda nao sei

**Proximo bloco para cada resposta:**

- Todas as respostas -> `BLOCO_FRITADEIRA_02`

**Tags aplicadas:**

- `equipamento_fritadeira`

**Variaveis/campos que devem ser preenchidos:**

- `equipamento_interesse`: Fritadeira
- `resposta_pergunta_1`

---

## BLOCO_FRITADEIRA_02

**Tipo do bloco:** pergunta

**Mensagem exata:**

O uso sera como?

**Opcoes de resposta:**

- Pouco uso
- Uso medio
- Uso alto
- Ainda nao sei

**Proximo bloco para cada resposta:**

- Todas as respostas -> `BLOCO_FRITADEIRA_03`

**Tags aplicadas:**

- `equipamento_fritadeira`

**Variaveis/campos que devem ser preenchidos:**

- `resposta_pergunta_2`

---

## BLOCO_FRITADEIRA_03

**Tipo do bloco:** pergunta

**Mensagem exata:**

Prefere qual modelo?

**Opcoes de resposta:**

- A gas
- Eletrica
- Quero ajuda

**Proximo bloco para cada resposta:**

- Todas as respostas -> `BLOCO_COLETA_NOME`

**Tags aplicadas:**

- `equipamento_fritadeira`

**Variaveis/campos que devem ser preenchidos:**

- `resposta_pergunta_3`

**Regra operacional:**

- Atendimento humano obrigatorio ao final deste caminho.

---

## BLOCO_EQUIPAMENTO_FREEZER_REFRIGERACAO

**Tipo do bloco:** pergunta

**Mensagem exata:**

Qual a necessidade?

**Opcoes de resposta:**

- Refrigerar
- Congelar
- Expor produtos
- Armazenar
- Ainda nao sei

**Proximo bloco para cada resposta:**

- Todas as respostas -> `BLOCO_FREEZER_REFRIGERACAO_02`

**Tags aplicadas:**

- `equipamento_freezer_refrigeracao`

**Variaveis/campos que devem ser preenchidos:**

- `equipamento_interesse`: Freezer / Refrigeracao
- `resposta_pergunta_1`

---

## BLOCO_FREEZER_REFRIGERACAO_02

**Tipo do bloco:** pergunta

**Mensagem exata:**

O que vai guardar?

**Opcoes de resposta:**

- Bebidas
- Carnes
- Laticinios
- Congelados
- Outros

**Proximo bloco para cada resposta:**

- Todas as respostas -> `BLOCO_FREEZER_REFRIGERACAO_03`

**Tags aplicadas:**

- `equipamento_freezer_refrigeracao`

**Variaveis/campos que devem ser preenchidos:**

- `resposta_pergunta_2`

---

## BLOCO_FREEZER_REFRIGERACAO_03

**Tipo do bloco:** pergunta

**Mensagem exata:**

Ja sabe o tamanho?

**Opcoes de resposta:**

- Pequeno
- Medio
- Grande
- Tenho medidas
- Nao sei

**Proximo bloco para cada resposta:**

- Todas as respostas -> `BLOCO_COLETA_NOME`

**Tags aplicadas:**

- `equipamento_freezer_refrigeracao`

**Variaveis/campos que devem ser preenchidos:**

- `resposta_pergunta_3`

**Regra operacional:**

- Atendimento humano obrigatorio ao final deste caminho.

---

## BLOCO_EQUIPAMENTO_FORNO

**Tipo do bloco:** pergunta

**Mensagem exata:**

O que voce vai assar?

**Opcoes de resposta:**

- Paes
- Pizzas
- Bolos
- Salgados
- Assados
- Variados

**Proximo bloco para cada resposta:**

- Todas as respostas -> `BLOCO_FORNO_02`

**Tags aplicadas:**

- `equipamento_forno`

**Variaveis/campos que devem ser preenchidos:**

- `equipamento_interesse`: Forno
- `resposta_pergunta_1`

---

## BLOCO_FORNO_02

**Tipo do bloco:** pergunta

**Mensagem exata:**

Prefere algum tipo?

**Opcoes de resposta:**

- A gas
- Eletrico
- Pizza
- Combinado
- Quero ajuda

**Proximo bloco para cada resposta:**

- Todas as respostas -> `BLOCO_FORNO_03`

**Tags aplicadas:**

- `equipamento_forno`

**Variaveis/campos que devem ser preenchidos:**

- `resposta_pergunta_2`

---

## BLOCO_FORNO_03

**Tipo do bloco:** pergunta

**Mensagem exata:**

O uso sera como?

**Opcoes de resposta:**

- Pouco uso
- Uso medio
- Uso alto
- Ainda nao sei

**Proximo bloco para cada resposta:**

- Todas as respostas -> `BLOCO_COLETA_NOME`

**Tags aplicadas:**

- `equipamento_forno`

**Variaveis/campos que devem ser preenchidos:**

- `resposta_pergunta_3`

**Regra operacional:**

- Atendimento humano obrigatorio ao final deste caminho.

---

## BLOCO_EQUIPAMENTO_FOGAO_INDUSTRIAL

**Tipo do bloco:** pergunta

**Mensagem exata:**

Quantas bocas precisa?

**Opcoes de resposta:**

- 2
- 4
- 6
- 8 ou mais
- Ainda nao sei

**Proximo bloco para cada resposta:**

- Todas as respostas -> `BLOCO_FOGAO_INDUSTRIAL_02`

**Tags aplicadas:**

- `equipamento_fogao_industrial`

**Variaveis/campos que devem ser preenchidos:**

- `equipamento_interesse`: Fogao Industrial
- `resposta_pergunta_1`

---

## BLOCO_FOGAO_INDUSTRIAL_02

**Tipo do bloco:** pergunta

**Mensagem exata:**

Onde sera usado?

**Opcoes de resposta:**

- Restaurante
- Lanchonete
- Cozinha industrial
- Buffet
- Outro

**Proximo bloco para cada resposta:**

- Todas as respostas -> `BLOCO_FOGAO_INDUSTRIAL_03`

**Tags aplicadas:**

- `equipamento_fogao_industrial`

**Variaveis/campos que devem ser preenchidos:**

- `tipo_negocio`
- `resposta_pergunta_2`

---

## BLOCO_FOGAO_INDUSTRIAL_03

**Tipo do bloco:** pergunta

**Mensagem exata:**

Ja tem ponto de gas?

**Opcoes de resposta:**

- Sim
- Nao
- Em preparacao
- Nao sei

**Proximo bloco para cada resposta:**

- Todas as respostas -> `BLOCO_COLETA_NOME`

**Tags aplicadas:**

- `equipamento_fogao_industrial`

**Variaveis/campos que devem ser preenchidos:**

- `resposta_pergunta_3`

**Regra operacional:**

- Atendimento humano obrigatorio ao final deste caminho.

---

## BLOCO_EQUIPAMENTO_CHAPA

**Tipo do bloco:** pergunta

**Mensagem exata:**

O que voce vai preparar?

**Opcoes de resposta:**

- Hamburguer
- Lanches
- Carnes
- Porcoes
- Variados

**Proximo bloco para cada resposta:**

- Todas as respostas -> `BLOCO_CHAPA_02`

**Tags aplicadas:**

- `equipamento_chapa`

**Variaveis/campos que devem ser preenchidos:**

- `equipamento_interesse`: Chapa
- `resposta_pergunta_1`

---

## BLOCO_CHAPA_02

**Tipo do bloco:** pergunta

**Mensagem exata:**

Ja sabe o tamanho?

**Opcoes de resposta:**

- Pequena
- Media
- Grande
- Tenho medidas
- Nao sei

**Proximo bloco para cada resposta:**

- Todas as respostas -> `BLOCO_CHAPA_03`

**Tags aplicadas:**

- `equipamento_chapa`

**Variaveis/campos que devem ser preenchidos:**

- `resposta_pergunta_2`

---

## BLOCO_CHAPA_03

**Tipo do bloco:** pergunta

**Mensagem exata:**

Prefere qual modelo?

**Opcoes de resposta:**

- A gas
- Eletrica
- Quero ajuda

**Proximo bloco para cada resposta:**

- Todas as respostas -> `BLOCO_COLETA_NOME`

**Tags aplicadas:**

- `equipamento_chapa`

**Variaveis/campos que devem ser preenchidos:**

- `resposta_pergunta_3`

**Regra operacional:**

- Atendimento humano obrigatorio ao final deste caminho.

---

## BLOCO_EQUIPAMENTO_OUTRO_EQUIPAMENTO

**Tipo do bloco:** pergunta

**Mensagem exata:**

Qual equipamento voce procura?

**Opcoes de resposta:**

- Vou digitar
- Nao sei o nome
- Tenho foto
- Quero ajuda

**Proximo bloco para cada resposta:**

- Vou digitar -> `BLOCO_OUTRO_EQUIPAMENTO_02`
- Nao sei o nome -> `BLOCO_OUTRO_EQUIPAMENTO_02`
- Tenho foto -> `BLOCO_OUTRO_EQUIPAMENTO_02`
- Quero ajuda -> `BLOCO_COLETA_NOME`

**Tags aplicadas:**

- `equipamento_outro`

**Variaveis/campos que devem ser preenchidos:**

- `equipamento_interesse`: Outro equipamento
- `resposta_pergunta_1`

---

## BLOCO_OUTRO_EQUIPAMENTO_02

**Tipo do bloco:** pergunta

**Mensagem exata:**

Para que ele sera usado?

**Opcoes de resposta:**

- Preparar
- Refrigerar
- Expor
- Lavar
- Organizar
- Outro

**Proximo bloco para cada resposta:**

- Todas as respostas -> `BLOCO_OUTRO_EQUIPAMENTO_03`

**Tags aplicadas:**

- `equipamento_outro`

**Variaveis/campos que devem ser preenchidos:**

- `resposta_pergunta_2`

---

## BLOCO_OUTRO_EQUIPAMENTO_03

**Tipo do bloco:** pergunta

**Mensagem exata:**

Qual seu tipo de negocio?

**Opcoes de resposta:**

- Restaurante
- Lanchonete
- Padaria
- Mercado
- Cozinha industrial
- Outro

**Proximo bloco para cada resposta:**

- Todas as respostas -> `BLOCO_COLETA_NOME`

**Tags aplicadas:**

- `equipamento_outro`

**Variaveis/campos que devem ser preenchidos:**

- `tipo_negocio`
- `resposta_pergunta_3`

**Regra operacional:**

- Atendimento humano obrigatorio ao final deste caminho.

---

## BLOCO_COLETA_NOME

**Tipo do bloco:** pergunta

**Mensagem exata:**

Qual e o seu nome?

**Opcoes de resposta:**

- Resposta livre

**Proximo bloco para cada resposta:**

- Resposta livre -> `BLOCO_COLETA_TELEFONE`

**Tags aplicadas:**

- Manter tags ja aplicadas no caminho anterior

**Variaveis/campos que devem ser preenchidos:**

- `nome_cliente`

---

## BLOCO_COLETA_TELEFONE

**Tipo do bloco:** pergunta

**Mensagem exata:**

Qual telefone ou WhatsApp para contato?

**Opcoes de resposta:**

- Resposta livre

**Proximo bloco para cada resposta:**

- Resposta livre -> `BLOCO_COLETA_CIDADE`

**Tags aplicadas:**

- Manter tags ja aplicadas no caminho anterior

**Variaveis/campos que devem ser preenchidos:**

- `telefone_whatsapp`

---

## BLOCO_COLETA_CIDADE

**Tipo do bloco:** pergunta

**Mensagem exata:**

Voce fala de qual cidade e estado?

**Opcoes de resposta:**

- Resposta livre

**Proximo bloco para cada resposta:**

- Resposta livre -> `BLOCO_RESUMO_ATENDIMENTO`

**Tags aplicadas:**

- Manter tags ja aplicadas no caminho anterior

**Variaveis/campos que devem ser preenchidos:**

- `cidade_estado`

---

## BLOCO_RESUMO_ATENDIMENTO

**Tipo do bloco:** resumo

**Mensagem exata:**

Pronto, ja registrei suas informacoes. Vou encaminhar seu atendimento para a equipe da SS Vale.

**Opcoes de resposta:**

- Continuar

**Proximo bloco para cada resposta:**

- Continuar com tag `pos_venda` -> `BLOCO_ENCAMINHAMENTO_POS_VENDA`
- Continuar com tag `fornecedor_representante` -> `BLOCO_ENCAMINHAMENTO_FORNECEDOR`
- Continuar com qualquer tag comercial -> `BLOCO_ENCAMINHAMENTO_COMERCIAL`
- Continuar sem tag identificada -> `BLOCO_ENCAMINHAMENTO_COMERCIAL`

**Tags aplicadas:**

- `lead_mvp_qualificado`

**Variaveis/campos que devem ser preenchidos:**

- Conferir se os campos principais foram preenchidos:
- `nome_cliente`
- `telefone_whatsapp`
- `cidade_estado`
- `motivo_contato`
- `equipamento_interesse`, quando aplicavel
- `tipo_negocio`, quando aplicavel
- `previsao_compra`, quando aplicavel
- `ja_comprou_ssvale`, quando aplicavel
- `assunto_pos_venda`, quando aplicavel
- `empresa_fornecedor`, quando aplicavel
- `tipo_contato_fornecedor`, quando aplicavel

---

## BLOCO_ENCAMINHAMENTO_COMERCIAL

**Tipo do bloco:** encaminhamento

**Mensagem exata:**

Em breve um consultor da SS Vale continua o atendimento com voce.

**Opcoes de resposta:**

- Sem opcoes

**Proximo bloco para cada resposta:**

- Encaminhar para fila comercial definida no Maxbot

**Tags aplicadas:**

- `encaminhar_humano`
- `encaminhar_comercial`

**Variaveis/campos que devem ser preenchidos:**

- Nenhum campo novo

---

## BLOCO_ENCAMINHAMENTO_POS_VENDA

**Tipo do bloco:** encaminhamento

**Mensagem exata:**

Em breve a equipe da SS Vale continua o atendimento com voce.

**Opcoes de resposta:**

- Sem opcoes

**Proximo bloco para cada resposta:**

- Encaminhar para fila de pos-venda definida no Maxbot

**Tags aplicadas:**

- `encaminhar_humano`
- `encaminhar_pos_venda`

**Variaveis/campos que devem ser preenchidos:**

- Nenhum campo novo

---

## BLOCO_ENCAMINHAMENTO_FORNECEDOR

**Tipo do bloco:** encaminhamento

**Mensagem exata:**

Obrigado pelas informacoes. A equipe responsavel da SS Vale vai avaliar seu contato.

**Opcoes de resposta:**

- Sem opcoes

**Proximo bloco para cada resposta:**

- Encaminhar para fila de fornecedores ou responsavel definido no Maxbot

**Tags aplicadas:**

- `encaminhar_humano`
- `encaminhar_fornecedor`

**Variaveis/campos que devem ser preenchidos:**

- Nenhum campo novo

---

## BLOCO_RESPOSTA_NAO_ENTENDIDA

**Tipo do bloco:** menu

**Mensagem exata:**

Nao consegui entender. Pode escolher uma das opcoes abaixo?

**Opcoes de resposta:**

- Voltar ao menu inicial
- Falar com consultor

**Proximo bloco para cada resposta:**

- Voltar ao menu inicial -> `BLOCO_01_MENU_INICIAL`
- Falar com consultor -> `BLOCO_06_CONSULTOR_DIRETO`

**Tags aplicadas:**

- `resposta_nao_entendida`

**Variaveis/campos que devem ser preenchidos:**

- Nenhum campo novo

## Regras de bloqueio

Se o cliente pedir preco, frete, pagamento ou orcamento, responder:

> Eu nao consigo tratar isso por aqui, mas vou encaminhar suas informacoes para um consultor da SS Vale te orientar corretamente.

Depois seguir para:

`BLOCO_COLETA_NOME`

Se o cliente pedir suporte tecnico, responder:

> Eu consigo registrar sua solicitacao e direcionar ao time responsavel, mas nao consigo fazer diagnostico tecnico por aqui.

Depois seguir para:

`BLOCO_04_SUPORTE_POS_VENDA`
