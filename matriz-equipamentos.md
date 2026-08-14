# Matriz de Equipamentos - MVP Sofia SS Vale

Tabela de apoio para configurar manualmente os equipamentos do MVP no Maxbot.

Use as perguntas uma por vez no WhatsApp. As opcoes podem ser configuradas como botoes, respostas rapidas ou lista, conforme o recurso disponivel no Maxbot.

## Matriz

| Equipamento | Tag | Pergunta 1 | Opcoes da Pergunta 1 | Pergunta 2 | Opcoes da Pergunta 2 | Pergunta 3 | Opcoes da Pergunta 3 | Regra de instalacao | Encaminhamento humano obrigatorio? | Observacoes |
|---|---|---|---|---|---|---|---|---|---|---|
| Fritadeira | `equipamento_fritadeira` | O que voce quer preparar? | Batata; Salgados; Frango; Porcoes; Ainda nao sei | O uso sera como? | Pouco uso; Uso medio; Uso alto; Ainda nao sei | Prefere qual modelo? | A gas; Eletrica; Quero ajuda | Nao orientar gas ou eletrica pelo bot. | Sim | Consultor deve validar capacidade, modelo e instalacao. |
| Freezer / Refrigeracao | `equipamento_freezer_refrigeracao` | Qual a necessidade? | Refrigerar; Congelar; Expor produtos; Armazenar; Ainda nao sei | O que vai guardar? | Bebidas; Carnes; Laticinios; Congelados; Outros | Ja sabe o tamanho? | Pequeno; Medio; Grande; Tenho medidas; Nao sei | Nao confirmar temperatura, consumo ou medida final pelo bot. | Sim | Coletar tipo de produto e encaminhar para consultor. |
| Forno | `equipamento_forno` | O que voce vai assar? | Paes; Pizzas; Bolos; Salgados; Assados; Variados | Prefere algum tipo? | A gas; Eletrico; Pizza; Combinado; Quero ajuda | O uso sera como? | Pouco uso; Uso medio; Uso alto; Ainda nao sei | Nao orientar gas, eletrica ou exaustao pelo bot. | Sim | Consultor deve validar tipo de forno e estrutura do local. |
| Fogao Industrial | `equipamento_fogao_industrial` | Quantas bocas precisa? | 2; 4; 6; 8 ou mais; Ainda nao sei | Onde sera usado? | Restaurante; Lanchonete; Cozinha industrial; Buffet; Outro | Ja tem ponto de gas? | Sim; Nao; Em preparacao; Nao sei | Nao orientar instalacao de gas pelo bot. | Sim | Encaminhar sempre para consultor por envolver instalacao e escolha tecnica. |
| Chapa | `equipamento_chapa` | O que voce vai preparar? | Hamburguer; Lanches; Carnes; Porcoes; Variados | Ja sabe o tamanho? | Pequena; Media; Grande; Tenho medidas; Nao sei | Prefere qual modelo? | A gas; Eletrica; Quero ajuda | Nao orientar gas ou eletrica pelo bot. | Sim | Boa triagem para entender uso e tamanho antes do consultor. |
| Outro equipamento | `equipamento_outro` | Qual equipamento voce procura? | Vou digitar; Nao sei o nome; Tenho foto; Quero ajuda | Para que ele sera usado? | Preparar; Refrigerar; Expor; Lavar; Organizar; Outro | Qual seu tipo de negocio? | Restaurante; Lanchonete; Padaria; Mercado; Cozinha industrial; Outro | Nao sugerir modelo pelo bot quando o item nao for identificado. | Sim | Encaminhar rapidamente para humano se o cliente nao souber explicar. |

## Dados para coletar antes do encaminhamento

- Nome
- Telefone ou WhatsApp
- Cidade e estado
- Equipamento de interesse
- Tipo de negocio
- Prazo de compra, se o cliente souber informar

## Mensagem padrao de encaminhamento

> Perfeito. Vou encaminhar suas informacoes para um consultor da SS Vale te orientar com mais precisao.
