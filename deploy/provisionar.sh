#!/usr/bin/env bash
#
# Provisiona a Sofia num Ubuntu limpo. Idempotente: pode rodar de novo sem
# estragar nada.
#
# Uso (dentro do servidor, como root ou com sudo):
#
#   sudo bash provisionar.sh sofia-teste.seudominio.com.br
#
# Na hora de acessar o repositorio privado, o script pede um Personal Access
# Token de forma oculta. O token nao aparece no comando, no historico do shell
# nem na configuracao do Git e e descartado assim que a atualizacao termina.
#
# O que este script faz:
#   1. cria o usuario e os diretorios do servico
#   2. clona o codigo
#   3. gera segredos novos (webhook e status)
#   4. instala e configura o Caddy com HTTPS automatico
#   5. instala o servico systemd
#   6. abre as portas 80 e 443, inclusive no iptables da Oracle
#   7. sobe tudo e valida
#
# Envio real ao Maxbot fica DESLIGADO. Este script nao envia mensagem a
# ninguem.

set -euo pipefail

DOMINIO="${1:-}"
REPO="github.com/anacarolrandrade/ssvale.git"
TOKEN_GITHUB=""
ASKPASS_FILE=""

limpar_credencial_git() {
	unset SOFIA_GITHUB_TOKEN TOKEN_GITHUB
	if [[ -n "${ASKPASS_FILE:-}" && -f "$ASKPASS_FILE" ]]; then
		rm -f -- "$ASKPASS_FILE"
	fi
}
trap limpar_credencial_git EXIT

if [[ -z "$DOMINIO" ]]; then
	echo "ERRO: informe o dominio. Ex: sudo bash provisionar.sh sofia.exemplo.com.br"
	exit 1
fi
if [[ $EUID -ne 0 ]]; then
	echo "ERRO: rode com sudo."
	exit 1
fi

echo "==> 1/7 Pacotes basicos"
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq git curl python3 gnupg iptables-persistent \
	debian-keyring debian-archive-keyring apt-transport-https

PYVER=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "    Python $PYVER"
python3 - <<'EOF'
import sys
if sys.version_info < (3, 11):
    sys.exit("ERRO: a Sofia precisa de Python 3.11 ou superior.")
EOF

echo "==> 2/7 Usuario e diretorios"
id -u sofia &>/dev/null || useradd --system --create-home --home-dir /var/lib/sofia --shell /usr/sbin/nologin sofia
mkdir -p /opt/sofia /var/lib/sofia /etc/sofia
chown -R sofia:sofia /var/lib/sofia

echo "==> 3/7 Codigo"
if [[ ! -r /dev/tty ]]; then
	echo "ERRO: nao foi possivel ler o token com seguranca. Rode em uma sessao SSH interativa."
	exit 1
fi
read -r -s -p "    Token GitHub (entrada oculta): " TOKEN_GITHUB </dev/tty
echo >/dev/tty
if [[ -z "$TOKEN_GITHUB" ]]; then
	echo "ERRO: o token do GitHub e obrigatorio para acessar o repositorio privado."
	exit 1
fi

# O Git pede usuario e senha a este auxiliar temporario. O token fica somente
# em memoria, nunca na URL do clone, na configuracao do remoto ou no historico.
ASKPASS_FILE=$(mktemp /tmp/sofia-git-askpass.XXXXXX)
cat >"$ASKPASS_FILE" <<'EOF'
#!/bin/sh
case "$1" in
	*Username*) printf '%s\n' 'x-access-token' ;;
	*Password*) printf '%s\n' "$SOFIA_GITHUB_TOKEN" ;;
	*) exit 1 ;;
esac
EOF
chmod 700 "$ASKPASS_FILE"
export SOFIA_GITHUB_TOKEN="$TOKEN_GITHUB"

if [[ -d /opt/sofia/.git ]]; then
	echo "    ja existe, atualizando"
	GIT_TERMINAL_PROMPT=0 GIT_ASKPASS="$ASKPASS_FILE" \
		git -C /opt/sofia fetch --quiet origin main
	git -C /opt/sofia reset --hard --quiet origin/main
else
	GIT_TERMINAL_PROMPT=0 GIT_ASKPASS="$ASKPASS_FILE" \
		git clone --quiet "https://${REPO}" /opt/sofia
fi
limpar_credencial_git
trap - EXIT
chown -R root:root /opt/sofia
chmod -R go-w /opt/sofia

echo "==> 4/7 Configuracao e segredos"
if [[ ! -f /etc/sofia/sofia.env ]]; then
	SEGREDO_WEBHOOK=$(head -c 32 /dev/urandom | base64 | tr -d '=+/' | cut -c1-43)
	TOKEN_STATUS=$(head -c 24 /dev/urandom | base64 | tr -d '=+/' | cut -c1-32)
	cat >/etc/sofia/sofia.env <<EOF
# Gerado por provisionar.sh. Segredos novos, nao reaproveitados do ambiente
# local. Configure a URL do webhook no painel do Maxbot com o valor abaixo.

SOFIA_HOST=127.0.0.1
SOFIA_PORT=8000

SESSION_STORE=sqlite
SQLITE_PATH=/var/lib/sofia/sofia_sessions.db
EVENT_LOG_ENABLED=true
EVENT_LOG_PATH=/var/lib/sofia/sofia_events.db

# Fechados: o que esta exposto na internet e somente o webhook e o /status.
LOCAL_API_ENABLED=false
DEBUG_ENDPOINTS_ENABLED=false

MAXBOT_WEBHOOK_SECRET=${SEGREDO_WEBHOOK}
STATUS_TOKEN=${TOKEN_STATUS}

# DESLIGADO. Nenhuma mensagem sai daqui ate alguem trocar isto de proposito.
MAXBOT_SEND_MESSAGES=false
MAXBOT_PILOT_MODE=true
MAXBOT_PILOT_ALLOW_ATTENDANCE=false
MAXBOT_PILOT_PHONES=
MAXBOT_API_TOKEN=
MAXBOT_TIMEOUT_SECONDS=10

HANDOFF_EXPIRA_HORAS=24
WHATSAPP_SEND_MESSAGES=false
LLM_PROVIDER=mock
EOF
	echo "    segredos novos gerados"
else
	echo "    /etc/sofia/sofia.env ja existe, preservado"
fi
chown root:sofia /etc/sofia/sofia.env
chmod 640 /etc/sofia/sofia.env

echo "==> 5/7 Caddy"
if ! command -v caddy &>/dev/null; then
	curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' |
		gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
	curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' |
		tee /etc/apt/sources.list.d/caddy-stable.list >/dev/null
	apt-get update -qq
	apt-get install -y -qq caddy
fi
sed "s/sofia.exemplo.com.br/${DOMINIO}/" /opt/sofia/deploy/Caddyfile >/etc/caddy/Caddyfile
systemctl reload caddy 2>/dev/null || systemctl restart caddy

echo "==> 6/7 Portas"
# A Oracle entrega imagens Ubuntu com iptables restritivo ALEM da Security
# List do console. Esquecer disto e o motivo numero um de "abri a porta no
# painel e mesmo assim nao responde". O pacote iptables-persistent, instalado
# no passo 1, restaura estas regras automaticamente em todo boot.
# Posicao 1 de proposito. O conselho comum e inserir na 6, contando com o
# conjunto padrao da Oracle ter cinco regras antes do REJECT. Se o conjunto
# for diferente, a regra cai DEPOIS do REJECT e nao serve para nada.
iptables -C INPUT -p tcp --dport 80 -j ACCEPT 2>/dev/null || iptables -I INPUT 1 -p tcp --dport 80 -j ACCEPT
iptables -C INPUT -p tcp --dport 443 -j ACCEPT 2>/dev/null || iptables -I INPUT 1 -p tcp --dport 443 -j ACCEPT
netfilter-persistent save >/dev/null
echo "    iptables liberado para 80 e 443 e salvo para os proximos boots"
if command -v ufw &>/dev/null && ufw status | grep -q "Status: active"; then
	ufw allow 80/tcp >/dev/null
	ufw allow 443/tcp >/dev/null
fi

echo "==> 7/7 Servico"
cp /opt/sofia/deploy/sofia.service /etc/systemd/system/sofia.service
systemctl daemon-reload
systemctl enable --quiet sofia
systemctl restart sofia
sleep 3

echo
if systemctl is-active --quiet sofia; then
	echo "OK: servico no ar."
else
	echo "FALHOU. Ultimas linhas do log:"
	journalctl -u sofia -n 20 --no-pager
	exit 1
fi

SEGREDO=$(grep '^MAXBOT_WEBHOOK_SECRET=' /etc/sofia/sofia.env | cut -d= -f2)
TOKEN=$(grep '^STATUS_TOKEN=' /etc/sofia/sofia.env | cut -d= -f2)

echo
echo "======================================================================"
echo " Sofia provisionada"
echo "======================================================================"
echo
echo " URL do webhook (configure no painel do Maxbot):"
echo "   https://${DOMINIO}/webhook/maxbot/${SEGREDO}"
echo
echo " Consultar o status:"
echo "   curl -H \"X-Status-Token: ${TOKEN}\" https://${DOMINIO}/status"
echo
echo " Ver o log ao vivo:      journalctl -u sofia -f"
echo " Desligar a Sofia:       sudo systemctl stop sofia"
echo " Religar:                sudo systemctl start sofia"
echo
echo " Envio real: DESLIGADO. Nenhuma mensagem sai deste servidor."
echo "======================================================================"
