"""Prepara configuracao local temporaria sem revelar credenciais."""

import argparse
from pathlib import Path
import secrets
import sys

ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT / ".env"


def digits_only(value: str) -> str:
    return "".join(character for character in value if character.isdigit())


def init_environment(authorized_phone: str) -> None:
    if ENV_PATH.exists():
        raise SystemExit(
            ".env ja existe; preparacao interrompida para nao sobrescrever configuracao."
        )

    phone = digits_only(authorized_phone)
    if len(phone) == 11:
        phone = "55" + phone
    if len(phone) not in {12, 13}:
        raise SystemExit("Telefone autorizado invalido.")

    webhook_secret = secrets.token_urlsafe(32)
    content = f"""LLM_PROVIDER=mock
SESSION_STORE=sqlite
SQLITE_PATH=data/sofia_sessions.db
EVENT_LOG_ENABLED=true
EVENT_LOG_PATH=data/sofia_events.db
DEBUG_ENDPOINTS_ENABLED=false
LOCAL_API_ENABLED=false
WHATSAPP_SEND_MESSAGES=false
SOFIA_HOST=127.0.0.1
SOFIA_PORT=8000

MAXBOT_API_TOKEN=
MAXBOT_CHANNEL_TOKEN=
MAXBOT_WEBHOOK_SECRET={webhook_secret}
MAXBOT_PILOT_MODE=true
MAXBOT_PILOT_SEGMENT=SOFIA_API_PILOTO
MAXBOT_PILOT_PHONES={phone}
MAXBOT_PILOT_ALLOW_ATTENDANCE=false
MAXBOT_SEND_MESSAGES=false
MAXBOT_API_URL=https://app.maxbot.com.br/api/v1.php
"""
    ENV_PATH.write_text(content, encoding="utf-8")
    print("Ambiente local criado com envio real desligado.")
    print("Insira o token diretamente em .env; nao envie o token pelo chat.")


def write_webhook_url(base_url: str, output_path: str) -> None:
    if not ENV_PATH.is_file():
        raise SystemExit(".env nao encontrado. Execute primeiro o comando init.")

    values = {}
    for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip()
    secret = values.get("MAXBOT_WEBHOOK_SECRET", "")
    if not secret:
        raise SystemExit("MAXBOT_WEBHOOK_SECRET nao configurado.")

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    full_url = f"{base_url.rstrip('/')}/webhook/maxbot/{secret}"
    output.write_text(full_url + "\n", encoding="utf-8")
    print(f"URL temporaria gravada em {output}")


def main() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init")
    init_parser.add_argument("--authorized-phone", required=True)

    url_parser = subparsers.add_parser("webhook-url")
    url_parser.add_argument("--base-url", required=True)
    url_parser.add_argument("--output", required=True)

    args = parser.parse_args()
    if args.command == "init":
        init_environment(args.authorized_phone)
    elif args.command == "webhook-url":
        write_webhook_url(args.base_url, args.output)


if __name__ == "__main__":
    main()
