# Subir a Sofia num servidor - passo a passo

Para o **uso de validacao**: provar que o deploy funciona, sem dado real e sem
enviar mensagem a ninguem. O piloto com clientes reais roda depois, no VPS pago
da conta da SS Vale.

Voce vai colar comandos. Nao precisa entender de infraestrutura: das oito
etapas, cinco sao clique de tela e duas sao um comando cada.

Tempo: cerca de 40 minutos, sendo 20 esperando a Oracle criar a maquina.

---

## O que voce precisa antes

1. Cartao de credito (a Oracle usa so para verificar identidade; a camada
   Always Free nao cobra).
2. Um dominio ou subdominio que voce controle.
3. Um Personal Access Token **fine-grained** do GitHub, restrito ao repositorio
   `ssvale`, com permissao `Contents: Read-only`. Ele sera digitado de forma
   oculta e pode ser revogado assim que a instalacao terminar.

---

## 1. Criar a conta Oracle Cloud

`https://www.oracle.com/br/cloud/free/`

**Na hora de escolher a regiao, marque `Brazil East (Sao Paulo)`.**

Isto nao pode ser trocado depois. A regiao de origem define onde as instancias
Always Free podem existir, e Sao Paulo e o motivo de termos escolhido a Oracle:
os dados ficam no Brasil.

---

## 2. Criar a maquina

No console: **Compute / Instances / Create Instance**.

| Campo | Escolha |
|---|---|
| Name | `sofia-validacao` |
| Image | Canonical Ubuntu 24.04 |
| Shape | **VM.Standard.E2.1.Micro** (x86, 1 GB) |
| SSH keys | Generate a key pair for me — **baixe a chave privada** |

Sobre o shape: a Oracle oferece uma ARM Ampere de ate 4 nucleos e 24 GB, bem
mais generosa. Nao use. E justamente a que devolve `out of host capacity` nas
regioes concorridas. A Sofia e Python de biblioteca padrao com SQLite — 1 GB
sobra, e a micro x86 sempre tem vaga.

Guarde o **IP publico** que aparece ao final.

---

## 3. Abrir as portas no console

**Networking / Virtual Cloud Networks / sua VCN / Security Lists / Default**.

Add Ingress Rules, duas vezes:

| Source CIDR | Protocol | Destination Port |
|---|---|---|
| `0.0.0.0/0` | TCP | `80` |
| `0.0.0.0/0` | TCP | `443` |

Isto libera a porta na **nuvem**. A imagem Ubuntu da Oracle tambem vem com
`iptables` fechado por dentro — o script do passo 6 cuida dessa segunda
camada. Esquecer disso e a causa numero um de "abri a porta e mesmo assim nao
responde".

---

## 4. Apontar o dominio

No painel do seu provedor de dominio, crie um registro:

| Tipo | Nome | Valor |
|---|---|---|
| A | `sofia-teste` | o IP publico da instancia |

Espere alguns minutos e confirme (no seu Windows mesmo):

```powershell
nslookup sofia-teste.seudominio.com.br
```

Precisa devolver o IP da instancia. **Nao siga antes disso**: o Caddy pede
certificado ao Let's Encrypt, que so emite se o dominio ja apontar para ca.

---

## 5. Conectar no servidor

No PowerShell, envie primeiro o script que ja esta no seu projeto. Isso evita
colocar o token do GitHub em um comando `curl`:

```powershell
icacls ssh-key.key /inheritance:r /grant:r "$($env:USERNAME):(R)"
scp -i ssh-key.key C:\ssvale-chatbot-mvp\deploy\provisionar.sh ubuntu@SEU_IP_PUBLICO:/tmp/provisionar.sh
ssh -i ssh-key.key ubuntu@SEU_IP_PUBLICO
```

O `icacls` ajusta a permissao do arquivo; sem isso o SSH recusa a chave por
estar "muito aberta". Aceite a impressao digital na primeira conexao.

A partir daqui voce esta dentro do servidor.

---

## 6. Provisionar - o unico comando que importa

```bash
sudo bash /tmp/provisionar.sh sofia-teste.seudominio.com.br
```

Cerca de tres minutos. O script cria usuario e diretorios, clona o codigo,
**gera segredos novos** (nao reaproveita os da sua maquina), instala o Caddy
com HTTPS automatico, abre e persiste o `iptables`, instala o servico e sobe.
Quando pedir o token do GitHub, cole-o e pressione Enter. Nada aparece na tela:
isso e proposital. O token nao entra no historico nem fica gravado no remoto do
Git. Revogue o token no GitHub depois que a verificacao terminar.

Ao final ele imprime a URL do webhook e o token de status. **Copie os dois.**

---

## 7. Verificar

```bash
sudo bash /opt/sofia/deploy/verificar.sh sofia-teste.seudominio.com.br
```

Confere 20 pontos: servico ativo, HTTPS valido, webhook aceitando o segredo
certo e recusando o errado, `/tester`, `/chat` e `/debug/*` fechados, `/status`
exigindo token, envio real desligado, log aparecendo ao vivo, telefone
mascarado no log e parada limpa.

Criterio: **TUDO OK**. Qualquer falha, nao aponte o Maxbot para ca.

---

## 8. Teste real com o Maxbot (opcional, e o mais valioso)

Ate aqui voce provou a infraestrutura. Este passo prova a integracao.

No painel do Maxbot, aponte o evento **Mensagem Recebida** para a URL que o
script imprimiu. Mande uma mensagem de um telefone qualquer e observe:

```bash
journalctl -u sofia -f
```

Deve aparecer `[sofia] ignorada motivo=fora_do_piloto de=***XXXX`. Isso prova
o caminho inteiro — Maxbot alcanca seu servidor, o segredo confere, o payload
e entendido, a allowlist funciona — **sem responder nada a ninguem**, porque o
envio esta desligado e nenhum telefone esta autorizado.

Ao terminar, remova a URL do painel.

---

## Comandos do dia a dia

```bash
journalctl -u sofia -f                 # log ao vivo
sudo systemctl stop sofia              # desligar
sudo systemctl start sofia             # religar
sudo systemctl restart sofia           # reiniciar
curl -H "X-Status-Token: TOKEN" https://SEU_DOMINIO/status   # contadores

sudo bash /opt/sofia/deploy/provisionar.sh SEU_DOMINIO   # atualizar com token oculto
```

---

## Quando der errado

**`out of host capacity` ao criar a instancia** — capacidade momentanea.
Tente outro Availability Domain no mesmo formulario, ou espere algumas horas.
Acontece mais com a ARM; por isso a recomendacao da x86.

**O dominio nao responde depois do script** — quase sempre e o passo 3. Teste
de dentro do servidor: `curl -I http://127.0.0.1:8000/health`. Se responder
localmente mas nao de fora, e porta bloqueada, nao aplicacao.

**Caddy nao consegue certificado** — o DNS ainda nao propagou, ou a porta 80
esta fechada (o Let's Encrypt precisa dela). Veja: `journalctl -u caddy -n 30`.

**Servico nao sobe** — `journalctl -u sofia -n 30`. Se disser que nenhum `.env`
foi encontrado, confira `/etc/sofia/sofia.env`.

---

## Lembretes

Este servidor e de **validacao**. Nao coloque telefone real em
`MAXBOT_PILOT_PHONES`, nao ligue `MAXBOT_SEND_MESSAGES` e nao aponte o numero
de producao para ca.

O piloto com clientes reais roda no VPS pago da conta da SS Vale, pelos motivos
do `PLANO-PILOTO-PRODUCAO.md`: dados pessoais deles, na conta deles, com
contrato que sustente. Camada gratuita nao tem SLA e e recuperada por
inatividade.

Ao terminar a validacao, desligue a instancia: **Compute / Instances /
Terminate**.
