"""Mostra um resumo operacional dos eventos Maxbot sem exibir PII."""

import json
from pathlib import Path
import sqlite3
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sofia_chatbot.config import load_settings


def main() -> None:
    settings = load_settings(ROOT / ".env")
    db_path = Path(settings.event_log_path)
    if not db_path.is_absolute():
        db_path = ROOT / db_path
    if not db_path.is_file():
        print("Nenhum banco de eventos encontrado.")
        return

    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute(
            """
            SELECT event_type, payload, created_at
            FROM events
            WHERE event_type LIKE 'maxbot_%'
            ORDER BY id DESC
            LIMIT 20
            """
        ).fetchall()
    finally:
        conn.close()

    print(f"Eventos Maxbot encontrados: {len(rows)}")
    for event_type, raw_payload, created_at in rows:
        payload = json.loads(raw_payload)
        outbound = payload.get("outbound") or {}
        print(
            " | ".join(
                [
                    created_at,
                    event_type,
                    f"ownership={payload.get('ownership')}",
                    f"block={payload.get('current_block')}",
                    f"outbound_mode={outbound.get('mode')}",
                    f"reason={payload.get('ignored_reason')}",
                ]
            )
        )


if __name__ == "__main__":
    main()
