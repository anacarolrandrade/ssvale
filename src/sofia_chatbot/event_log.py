import json
from pathlib import Path
import sqlite3
from typing import Any


class EventLogger:
    def log(self, event_type: str, session_id: str, payload: dict[str, Any]) -> None:
        ...

    def mark_message_processed(self, channel: str, message_id: str, session_id: str) -> bool:
        ...

    def unmark_message_processed(self, channel: str, message_id: str) -> None:
        ...

    def list_events(self, session_id: str | None = None, limit: int = 20) -> list[dict[str, Any]]:
        ...

    def contar_por_tipo(self, desde_horas: float = 24.0) -> dict[str, int]:
        ...


class NullEventLogger:
    def log(self, event_type: str, session_id: str, payload: dict[str, Any]) -> None:
        return

    def mark_message_processed(self, channel: str, message_id: str, session_id: str) -> bool:
        return True

    def unmark_message_processed(self, channel: str, message_id: str) -> None:
        return

    def list_events(self, session_id: str | None = None, limit: int = 20) -> list[dict[str, Any]]:
        return []

    def contar_por_tipo(self, desde_horas: float = 24.0) -> dict[str, int]:
        return {}


class SQLiteEventLogger:
    def __init__(self, db_path: str) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def log(self, event_type: str, session_id: str, payload: dict[str, Any]) -> None:
        conn = self._connect()
        try:
            conn.execute(
                """
                INSERT INTO events (event_type, session_id, payload, created_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                """,
                (event_type, session_id, json.dumps(payload, ensure_ascii=False)),
            )
            conn.commit()
        finally:
            conn.close()

    def mark_message_processed(self, channel: str, message_id: str, session_id: str) -> bool:
        conn = self._connect()
        try:
            try:
                conn.execute(
                    """
                    INSERT INTO processed_messages (channel, message_id, session_id, created_at)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                    """,
                    (channel, message_id, session_id),
                )
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                return False
        finally:
            conn.close()

    def unmark_message_processed(self, channel: str, message_id: str) -> None:
        """Remove a marcacao de processada para permitir novo processamento.

        Usado quando o processamento falha depois da marcacao: sem isso, o
        retry da Meta seria descartado como duplicata e a mensagem se perderia.
        """
        conn = self._connect()
        try:
            conn.execute(
                "DELETE FROM processed_messages WHERE channel = ? AND message_id = ?",
                (channel, message_id),
            )
            conn.commit()
        finally:
            conn.close()

    def list_events(self, session_id: str | None = None, limit: int = 20) -> list[dict[str, Any]]:
        safe_limit = max(1, min(limit, 100))
        conn = self._connect()
        try:
            if session_id:
                rows = conn.execute(
                    """
                    SELECT id, event_type, session_id, payload, created_at
                    FROM events
                    WHERE session_id = ?
                    ORDER BY id DESC
                    LIMIT ?
                    """,
                    (session_id, safe_limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT id, event_type, session_id, payload, created_at
                    FROM events
                    ORDER BY id DESC
                    LIMIT ?
                    """,
                    (safe_limit,),
                ).fetchall()
        finally:
            conn.close()

        return [
            {
                "id": row[0],
                "event_type": row[1],
                "session_id": row[2],
                "payload": json.loads(row[3]),
                "created_at": row[4],
            }
            for row in rows
        ]

    def contar_por_tipo(self, desde_horas: float = 24.0) -> dict[str, int]:
        """Contagem de eventos por tipo, para o /status.

        Devolve somente numeros. Nunca texto de conversa, resumo de lead ou
        telefone: o /status existe para responder "esta de pe e respondendo?"
        sem virar uma segunda porta de acesso a dados pessoais.
        """
        janela = max(0.0, float(desde_horas))
        conn = self._connect()
        try:
            rows = conn.execute(
                """
                SELECT event_type, COUNT(*)
                FROM events
                WHERE created_at >= datetime('now', ?)
                GROUP BY event_type
                ORDER BY COUNT(*) DESC
                """,
                (f"-{janela} hours",),
            ).fetchall()
        finally:
            conn.close()
        return {row[0]: row[1] for row in rows}

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=5.0)
        conn.execute("PRAGMA busy_timeout = 5000")
        return conn

    def _init_db(self) -> None:
        conn = self._connect()
        try:
            conn.execute("PRAGMA journal_mode = WAL")
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_events_session_id ON events(session_id)")
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS processed_messages (
                    channel TEXT NOT NULL,
                    message_id TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (channel, message_id)
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_processed_session_id ON processed_messages(session_id)")
            conn.commit()
        finally:
            conn.close()


def create_event_logger(enabled: bool, db_path: str) -> EventLogger:
    if not enabled:
        return NullEventLogger()
    return SQLiteEventLogger(db_path)
