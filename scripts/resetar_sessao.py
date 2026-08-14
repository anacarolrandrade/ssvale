"""Reinicia uma unica sessao da Sofia mediante confirmacao explicita."""

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sofia_chatbot.config import load_settings
from sofia_chatbot.event_log import create_event_logger
from sofia_chatbot.session_store import create_session_store


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Reinicia uma sessao individual da Sofia."
    )
    parser.add_argument("--session-id", required=True, help="Telefone/session_id exato")
    parser.add_argument(
        "--confirmar",
        action="store_true",
        help="Confirma a alteracao. Sem esta opcao, apenas simula.",
    )
    args = parser.parse_args()
    session_id = args.session_id.strip()
    if not session_id:
        parser.error("--session-id nao pode ser vazio")

    if not args.confirmar:
        print(
            f"Simulacao: a sessao {session_id!r} seria reiniciada. "
            "Execute novamente com --confirmar para aplicar."
        )
        return

    settings = load_settings(ROOT / ".env")
    sqlite_path = Path(settings.sqlite_path)
    if not sqlite_path.is_absolute():
        sqlite_path = ROOT / sqlite_path
    event_log_path = Path(settings.event_log_path)
    if not event_log_path.is_absolute():
        event_log_path = ROOT / event_log_path

    store = create_session_store(settings.session_store, str(sqlite_path))
    store.reset(session_id)
    event_logger = create_event_logger(
        settings.event_log_enabled, str(event_log_path)
    )
    event_logger.log(
        "manual_session_reset",
        session_id,
        {"reason": "operator_confirmed"},
    )
    print(f"Sessao {session_id!r} reiniciada com sucesso.")


if __name__ == "__main__":
    main()
