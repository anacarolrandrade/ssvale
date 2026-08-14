# Inicializar o repositorio - comandos para rodar no Windows

O `.gitignore` ja esta revisado e validado. Falta so executar o `git init`,
que precisa ser feito por voce: o ambiente onde eu trabalho consegue criar
arquivos na pasta, mas nao apagar, e o `git` precisa remover arquivos
temporarios a cada operacao.

## 1. Limpar a tentativa anterior

Eu deixei uma pasta `.git` incompleta na raiz. Apague antes de comecar:

```powershell
cd C:\ssvale-chatbot-mvp
Remove-Item -Recurse -Force .git
```

## 2. Criar o repositorio e o primeiro commit

```powershell
cd C:\ssvale-chatbot-mvp
git init -b main
git add -A
```

**Antes de commitar, confira o que vai entrar.** Este comando precisa nao
imprimir nada:

```powershell
git diff --cached --name-only | Select-String -Pattern "^\.env$|^data/|^\.runtime/|fable-5|\.zip$"
```

Se imprimir alguma linha, pare: tem segredo ou dado com PII prestes a ser
versionado. Se nao imprimir nada, siga:

```powershell
git commit -m "Estado do MVP da Sofia com correcoes de prontidao para deploy"
```

Esperado: **76 arquivos**, repositorio de cerca de 860 KB.

## 3. Criar o remoto privado - na conta da WeUp

**Decisao tomada:** o repositorio fica na conta da **WeUp**, privado, com a SS
Vale adicionada como colaboradora de **leitura**. A hospedagem vai para a conta
da SS Vale; a titularidade do codigo generico, nao. Justificativa e a clausula
de contrato em `PROPRIEDADE-INTELECTUAL.md`.

No GitHub, criar um repositorio **privado**, vazio (sem README, sem
`.gitignore`, sem licenca), na conta ou organizacao da WeUp:

```powershell
git remote add origin https://github.com/<conta-weup>/ssvale-sofia.git
git push -u origin main
```

Depois, em Settings / Collaborators, adicionar o contato tecnico da SS Vale com
permissao **Read**. Nao conceda Write durante o piloto: quem faz deploy e voce,
e o registro de quem alterou o que precisa ficar limpo.

### Ordem importa

Antes do primeiro push, inclua o `PROPRIEDADE-INTELECTUAL.md` no commit. Ele
nao substitui o contrato — nada num repositorio substitui — mas deixa a
intencao declarada e datada no historico, em vez de aparecer retroativamente se
o assunto surgir depois.

O passo que realmente protege continua sendo o contrato. Enquanto ele nao for
assinado com a clausula, o padrao legal brasileiro (Lei 9.609/98, art. 4º)
atribui os direitos a SS Vale.

## O que NAO vai para o repositorio, e por que

| Excluido | Motivo |
|---|---|
| `.env` | Token real da API do Maxbot e segredo do webhook |
| `data/` | Bancos SQLite com conversas e dados pessoais do piloto |
| `.runtime/` | PIDs e a URL do tunel, que contem o segredo do webhook |
| `revisao-recebida-fable-5/` | Copia historica, 53 MB, duplica o codigo da raiz |
| `entrega-fable-5/` | Copia historica |
| `ssvale-chatbot-mvp-revisao-claude.zip` | Copia historica |
| `__pycache__/` | Artefato de execucao |

As copias historicas continuam no disco para consulta, como diz o `CLAUDE.md`.
Elas so nao entram no controle de versao.

## Lembrete de seguranca

O `.env` atual tem o token real da conta do cliente e existe **so na sua
maquina**, sem backup. Antes do deploy, o plano prevê rotacionar esse token e o
segredo do webhook (que ja circulou em texto plano em
`.runtime/WEBHOOK-URL-MAXBOT.txt`) e guardar os novos no cofre da SS Vale.
