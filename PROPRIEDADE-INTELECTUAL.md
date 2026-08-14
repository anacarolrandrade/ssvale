# Propriedade intelectual - Sofia / SS Vale

Documento em duas partes: a **declaracao de intencao** que acompanha este
repositorio, e um **rascunho de clausula** para o contrato entre WeUp e SS Vale.

> **Isto nao e parecer juridico.** E um rascunho de trabalho, escrito por
> quem desenvolve, para servir de ponto de partida a um advogado. A Lei
> 9.609/98 tem um padrao que trabalha contra a prestadora quando o contrato e
> omisso, entao esta e justamente a parte que nao deve ser resolvida no
> improviso.

---

## Parte 1 - Declaracao de intencao

Este projeto contem dois conjuntos de material com origens e destinos
diferentes.

### Motor (titularidade pretendida: WeUp)

Componentes genericos, sem regra de negocio da SS Vale, reaproveitaveis em
qualquer cliente:

| Arquivo | O que e |
|---|---|
| `src/sofia_chatbot/channels/maxbot.py` | Adaptador do Maxbot: parser dos dois contratos de webhook, renderizacao de menu numerado, cliente `send_text`, tratamento de status e 429, allowlist de piloto |
| `src/sofia_chatbot/channels/whatsapp.py` | Adaptador da WhatsApp Business Platform (Meta) |
| `src/sofia_chatbot/api.py` | Esqueleto de webhook, deduplicacao, ACK minimo, limite de corpo, parada limpa |
| `src/sofia_chatbot/session_store.py` | Persistencia de sessao |
| `src/sofia_chatbot/event_log.py` | Log de eventos e deduplicacao por `message_id` |
| `src/sofia_chatbot/flow.py` | **Motor** de maquina de estados (o conteudo das mensagens e da SS Vale) |
| `src/sofia_chatbot/guardrails.py` | **Mecanismo** de limites comerciais (as regras sao da SS Vale) |
| `src/sofia_chatbot/config.py`, `llm/` | Configuracao e camada de modelo |
| `deploy/`, `scripts/`, `tests/` | Artefatos de deploy, ferramental e suite de testes |

### Conteudo do Cliente (titularidade: SS Vale)

Material que descreve o negocio da SS Vale e nao tem valor fora dele:

| Arquivo | O que e |
|---|---|
| `equipamentos.json`, `matriz-equipamentos.md` | Catalogo e regras de produto |
| `regras-negocio.md` | Limites comerciais da SS Vale |
| Textos de conversa em `flow.py` e `guardrails.py` | Redacao das mensagens ao cliente final |
| `INVENTARIO-MAXBOT-ATUAL.md`, `roteiro-maxbot.md`, `SOFIA-NO-MAXBOT.md` | Levantamento do painel e da operacao da SS Vale |
| `PLANO-DOIS-CANAIS.md`, `CHECKLIST-*`, `OPERACAO-*`, `ROTEIRO-*` | Documentacao operacional do projeto deles |
| Dados de conversas, leads e logs | Dados pessoais de clientes da SS Vale |

### Dois arquivos limitrofes

`flow.py` e `guardrails.py` misturam motor e conteudo no mesmo arquivo. Hoje
isso e proposital: separar exigiria fronteira de pacote e versionamento, que
nao se justifica num piloto com um cliente. A separacao vive no contrato, nao
no codigo.

Se a Sofia virar produto, o caminho e extrair o motor para uma biblioteca da
WeUp e deixar o conteudo da SS Vale como configuracao. Ate la, esta tabela e a
fronteira.

---

## Parte 2 - Rascunho de clausula contratual

Redigido para ser lido por um advogado, nao para ser assinado como esta.

### Clausula X - Propriedade intelectual e licenca de uso

**X.1. Definicoes.**

a) **"Motor"**: os componentes de software de natureza generica desenvolvidos
pela CONTRATADA, incluindo adaptadores de canal de mensageria, mecanismos de
persistencia, deduplicacao, roteamento de webhook, maquina de estados e
ferramental de teste e implantacao, que nao incorporam regras de negocio,
catalogo, precos ou textos especificos da CONTRATANTE.

b) **"Conteudo do Cliente"**: o catalogo de produtos, as regras comerciais, os
textos das mensagens dirigidas aos clientes finais, o levantamento da operacao
e demais materiais que descrevem especificamente o negocio da CONTRATANTE.

c) **"Dados"**: os dados pessoais de clientes finais e demais dados
operacionais tratados pela solucao.

**X.2. Titularidade do Motor.** Em estipulacao expressa em contrario ao
disposto no art. 4º da Lei nº 9.609/1998, a titularidade do Motor permanece
integralmente com a CONTRATADA, inclusive quanto a versoes anteriores,
derivadas e a evolucoes posteriores.

**X.3. Licenca a CONTRATANTE.** A CONTRATADA concede a CONTRATANTE licenca
**perpetua, irrevogavel, mundial, nao exclusiva e integralmente paga** para
usar, executar, hospedar, modificar e manter o Motor, na forma de codigo-fonte,
para a operacao propria da CONTRATANTE, incluindo o direito de contratar
terceiros para faze-lo em seu nome.

A licenca **nao** autoriza a CONTRATANTE a comercializar, sublicenciar,
redistribuir ou oferecer o Motor a terceiros como produto ou servico.

**X.4. Titularidade do Conteudo do Cliente.** O Conteudo do Cliente pertence
integralmente a CONTRATANTE. A CONTRATADA nao o reutilizara para outros
clientes.

**X.5. Entrega.** Ao termino do projeto, a CONTRATADA entregara a CONTRATANTE o
codigo-fonte completo em condicoes de execucao autonoma, a documentacao de
operacao e as credenciais sob sua guarda, de modo que a CONTRATANTE possa
operar a solucao **sem dependencia da CONTRATADA**.

**X.6. Sobrevivencia.** A licenca do item X.3 e a entrega do item X.5
sobrevivem ao termino do contrato, por qualquer motivo.

**X.7. Dados.** Os Dados pertencem a CONTRATANTE, que figura como controladora
para os fins da Lei nº 13.709/2018. A CONTRATADA atua como operadora, tratando
os Dados exclusivamente conforme instrucao da CONTRATANTE e pelo prazo do
projeto. Politica de retencao, expurgo e acesso serao definidas pela
CONTRATANTE.

---

## Por que esta divisao, em uma frase

A SS Vale recebe tudo de que precisa para nunca ficar refem da WeUp — codigo,
licenca perpetua, hospedagem na conta deles e documentacao de operacao. A WeUp
mantem o que permite atender o proximo cliente sem reconstruir do zero.

## Ponto de atencao para a negociacao

Se a SS Vale pagou (ou vier a pagar) por desenvolvimento sob encomenda com
expectativa de exclusividade, esta divisao pode ser questionada com razao. Duas
saidas honestas:

1. **Exclusividade temporaria:** a WeUp se compromete a nao licenciar o Motor a
   concorrente direto da SS Vale no mesmo segmento por um prazo definido.
2. **Troca explicita:** a CONTRATANTE adquire a titularidade do Motor mediante
   valor adicional acordado.

O que nao funciona e deixar o contrato omisso: pelo art. 4º da Lei 9.609/98, a
omissao entrega os direitos a CONTRATANTE.
