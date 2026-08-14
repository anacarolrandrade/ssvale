import argparse
import json
from pathlib import Path
import sqlite3
import time


IMPORTANT_EVENTS = {
    "whatsapp_error": "!!! ERRO !!!",
    "whatsapp_duplicate": "*** DUPLICATA ***",
}


def mask_session(session_id: str) -> str:
    digits = "".join(character for character in session_id if character.isdigit())
    suffix = digits[-4:] if digits else session_id[-4:]
    return f"***{suffix}" if suffix else "***"


def compact_text(value: object, limit: int = 60) -> str:
    text = " ".join(str(value or "").split())
    return text if len(text) <= limit else text[: limit - 1] + "…"


def event_details(payload: dict) -> tuple[str, str, str]:
    block = str(payload.get("current_block") or payload.get("next_block") or "-")
    reply = payload.get("reply") if isinstance(payload.get("reply"), dict) else {}
    tags = payload.get("tags") or reply.get("tags") or []
    tags_text = ",".join(str(tag) for tag in tags) if tags else "-"
    inbound_text = payload.get("text") or payload.get("inbound_text") or ""
    return block, tags_text, compact_text(inbound_text)


def read_new_events(db_path: Path, last_id: int) -> list[tuple]:
    if not db_path.exists():
        return []
    connection = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True, timeout=2.0)
    try:
        return connection.execute(
            """
            SELECT id, created_at, event_type, session_id, payload
            FROM events
            WHERE id > ?
            ORDER BY id ASC
            """,
            (last_id,),
        ).fetchall()
    except sqlite3.OperationalError:
        return []
    finally:
        connection.close()


def monitor(db_path: Path, interval: float, from_start: bool) -> None:
    last_id = 0
    if db_path.exists() and not from_start:
        connection = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        try:
            row = connection.execute("SELECT COALESCE(MAX(id), 0) FROM events").fetchone()
            last_id = int(row[0])
        except sqlite3.OperationalError:
            pass
        finally:
            connection.close()

    print(f"Monitorando {db_path} a cada {interval:g}s. Ctrl+C para encerrar.")
    try:
        while True:
            for event_id, created_at, event_type, session_id, raw_payload in read_new_events(db_path, last_id):
                last_id = max(last_id, int(event_id))
                try:
                    payload = json.loads(raw_payload)
                except (TypeError, json.JSONDecodeError):
                    payload = {}
                block, tags, inbound_text = event_details(payload)
                marker = IMPORTANT_EVENTS.get(event_type, "")
                print(
                    f"{marker} {created_at} | {event_type} | {mask_session(str(session_id))} "
                    f"| bloco={block} | tags={tags} | texto={inbound_text}",
                    flush=True,
                )
            time.sleep(interval)
    except KeyboardInterrupt:
        print("Monitor encerrado.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Monitora eventos da Sofia sem expor o telefone completo.")
    parser.add_argument("--db", default="data/sofia_events.db", help="Caminho do banco de eventos")
    parser.add_argument("--interval", type=float, default=2.0, help="Intervalo de polling em segundos")
    parser.add_argument("--from-start", action="store_true", help="Exibe tambem eventos ja existentes")
    args = parser.parse_args()
    monitor(Path(args.db), max(args.interval, 0.2), args.from_start)


if __name__ == "__main__":
    main()
