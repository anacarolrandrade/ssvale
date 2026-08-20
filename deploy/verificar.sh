#!/usr/bin/env bash
#
# Prova que a instalacao funciona. Rode no servidor depois do provisionar.sh:
#
#   sudo bash /opt/sofia/deploy/verificar.sh sofia-teste.seudominio.com.br
#
# Testa o que realmente importa: servico no ar, HTTPS valido, webhook aceitando
# o segredo certo e recusando o errado, /status protegido, log aparecendo ao
# vivo e parada limpa.

set -uo pipefail

DOMINIO="${1:-}"
[[ -z "$DOMINIO" ]] && {
	echo "Uso: sudo bash verificar.sh <dominio>"
	exit 1
}

SEGREDO=$(grep '^MAXBOT_WEBHOOK_SECRET=' /etc/sofia/sofia.env | cut -d= -f2)
TOKEN=$(grep '^STATUS_TOKEN=' /etc/sofia/sofia.env | cut -d= -f2)
FALHAS=0

checar() {
	local nome="$1" esperado="$2" obtido="$3"
	if [[ "$esperado" == "$obtido" ]]; then
		printf '  [ok ] %-45s %s\n' "$nome" "$obtido"
	else
		printf '  [FALHA] %-43s esperado=%s obtido=%s\n' "$nome" "$esperado" "$obtido"
		FALHAS=$((FALHAS + 1))
	fi
}

codigo() { curl -s -o /dev/null -w '%{http_code}' --max-time 15 "$@"; }

echo "== Servico =="
checar "systemd ativo" "active" "$(systemctl is-active sofia)"
checar "sobe sozinho no boot" "enabled" "$(systemctl is-enabled sofia)"

echo
echo "== Rede e HTTPS =="
checar "escuta em 127.0.0.1:8000" "sim" \
	"$(ss -ltn 2>/dev/null | grep -q '127.0.0.1:8000' && echo sim || echo nao)"
checar "/health local" "200" "$(codigo http://127.0.0.1:8000/health)"
checar "HTTPS com certificado valido" "200" "$(codigo "https://${DOMINIO}/health")"
checar "HTTP redireciona para HTTPS" "308" "$(codigo "http://${DOMINIO}/health")"

echo
echo "== Webhook =="
CORPO='{"contact":{"whatsapp":"5531900000000","name":"Verificacao"},"msg_id":"verificar-'"$(date +%s)"'","msg":"teste","type":"T","origin":"2"}'
checar "segredo correto aceita" "200" \
	"$(codigo -X POST -H 'Content-Type: application/json' -d "$CORPO" "https://${DOMINIO}/webhook/maxbot/${SEGREDO}")"
checar "segredo errado recusa" "404" \
	"$(codigo -X POST -H 'Content-Type: application/json' -d "$CORPO" "https://${DOMINIO}/webhook/maxbot/errado")"
checar "caminho sem segredo recusa" "404" \
	"$(codigo -X POST -H 'Content-Type: application/json' -d "$CORPO" "https://${DOMINIO}/webhook/maxbot/")"

echo
echo "== Endpoints que precisam estar fechados =="
checar "/tester fechado" "404" "$(codigo "https://${DOMINIO}/tester")"
checar "/chat fechado" "404" "$(codigo -X POST -d '{}' "https://${DOMINIO}/chat")"
checar "/debug/session fechado" "404" "$(codigo "https://${DOMINIO}/debug/session?session_id=x")"
checar "/debug/events fechado" "404" "$(codigo "https://${DOMINIO}/debug/events")"

echo
echo "== Status =="
checar "com token responde" "200" \
	"$(codigo -H "X-Status-Token: ${TOKEN}" "https://${DOMINIO}/status")"
checar "sem token recusa" "401" "$(codigo "https://${DOMINIO}/status")"
checar "token errado recusa" "401" \
	"$(codigo -H 'X-Status-Token: chute' "https://${DOMINIO}/status")"

echo
echo "== Envio real =="
ENVIO=$(grep '^MAXBOT_SEND_MESSAGES=' /etc/sofia/sofia.env | cut -d= -f2)
checar "envio ao Maxbot desligado" "false" "$ENVIO"

echo
echo "== Log ao vivo =="
LINHAS=$(journalctl -u sofia --since "5 minutes ago" --no-pager 2>/dev/null | grep -c '\[sofia\]')
if [[ "$LINHAS" -gt 0 ]]; then
	printf '  [ok ] %-45s %s linhas\n' "log aparece sem esperar o processo morrer" "$LINHAS"
	echo "         ultima: $(journalctl -u sofia --no-pager 2>/dev/null | grep '\[sofia\]' | tail -1)"
else
	printf '  [FALHA] %-43s nenhuma linha [sofia]\n' "log ao vivo"
	FALHAS=$((FALHAS + 1))
fi

echo
echo "== Log nao vaza dados pessoais =="
if journalctl -u sofia --no-pager 2>/dev/null | grep -q '5531900000000'; then
	printf '  [FALHA] %-43s telefone completo no log\n' "mascaramento"
	FALHAS=$((FALHAS + 1))
else
	printf '  [ok ] %-45s\n' "telefone aparece mascarado"
fi

echo
echo "== Parada limpa =="
systemctl stop sofia
sleep 2
checar "parou" "inactive" "$(systemctl is-active sofia)"
if journalctl -u sofia -n 5 --no-pager 2>/dev/null | grep -q "requisicoes em voo concluidas"; then
	printf '  [ok ] %-45s\n' "encerrou concluindo o que estava em voo"
else
	printf '  [FALHA] %-43s\n' "mensagem de parada limpa ausente"
	FALHAS=$((FALHAS + 1))
fi
systemctl start sofia
sleep 3
checar "voltou" "active" "$(systemctl is-active sofia)"

echo
if [[ "$FALHAS" -eq 0 ]]; then
	echo "======================================================================"
	echo " TUDO OK. A Sofia esta no ar e as travas de seguranca estao fechadas."
	echo "======================================================================"
	exit 0
fi
echo "======================================================================"
echo " $FALHAS verificacao(oes) falharam. Nao aponte o Maxbot para ca ainda."
echo "======================================================================"
exit 1
