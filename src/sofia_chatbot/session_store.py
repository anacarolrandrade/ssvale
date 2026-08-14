import json
from pathlib import Path
import sqlite3
from typing import Protocol

from sofia_chatbot.domain import ConversationState, ConversationStatus, LeadData


class SessionStore(Protocol):
    def get(self, session_id: str) -> ConversationState:
        ...

    def save(self, state: ConversationState) -> None:
        ...

    def reset(self, session_id: str) -> ConversationState:
        ...


class InMemorySessionStore:
    def __init__(self) -> None:
        self._sessions: dict[str, ConversationState] = {}

    def get(self, session_id: str) -> ConversationState:
        if session_id not in self._sessions:
            self._sessions[session_id] = ConversationState(session_id=session_id)
        return self._sessions[session_id]

    def save(self, state: ConversationState) -> None:
        self._sessions[state.session_id] = state

    def reset(self, session_id: str) -> ConversationState:
        self._sessions[session_id] = ConversationState(session_id=session_id)
        return self._sessions[session_id]


class SQLiteSessionStore:
    def __init__(self, db_path: str) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def get(self, session_id: str) -> ConversationState:
        conn = self._connect()
        try:
            row = conn.execute(
                "SELECT payload FROM sessions WHERE session_id = ?",
                (session_id,),
            ).fetchone()
        finally:
            conn.close()

        if not row:
            state = ConversationState(session_id=session_id)
            self.save(state)
            return state

        return _state_from_dict(json.loads(row[0]))

    def save(self, state: ConversationState) -> None:
        payload = json.dumps(_state_to_dict(state), ensure_ascii=False)
        conn = self._connect()
        try:
            conn.execute(
                """
                INSERT INTO sessions (session_id, payload, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(session_id) DO UPDATE SET
                    payload = excluded.payload,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (state.session_id, payload),
            )
            conn.commit()
        finally:
            conn.close()

    def reset(self, session_id: str) -> ConversationState:
        state = ConversationState(session_id=session_id)
        self.save(state)
        return state

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
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    payload TEXT NOT NULL,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.commit()
        finally:
            conn.close()


def create_session_store(kind: str, sqlite_path: str) -> SessionStore:
    normalized = kind.lower().strip()
    if normalized == "memory":
        return InMemorySessionStore()
    if normalized == "sqlite":
        return SQLiteSessionStore(sqlite_path)
    raise ValueError(f"Armazenamento de sessao nao suportado: {kind}")


def _state_to_dict(state: ConversationState) -> dict:
    return {
        "session_id": state.session_id,
        "current_block": state.current_block,
        "tags": sorted(state.tags),
        "status": state.status.value,
        "lead": {
            "nome_cliente": state.lead.nome_cliente,
            "telefone_whatsapp": state.lead.telefone_whatsapp,
            "cidade_estado": state.lead.cidade_estado,
            "motivo_contato": state.lead.motivo_contato,
            "equipamento_interesse": state.lead.equipamento_interesse,
            "tipo_negocio": state.lead.tipo_negocio,
            "previsao_compra": state.lead.previsao_compra,
            "respostas": state.lead.respostas,
        },
    }


def _state_from_dict(data: dict) -> ConversationState:
    lead_data = data.get("lead", {})
    return ConversationState(
        session_id=data["session_id"],
        current_block=data.get("current_block", "BLOCO_00_BOAS_VINDAS"),
        tags=set(data.get("tags", [])),
        status=ConversationStatus(data.get("status", ConversationStatus.ACTIVE.value)),
        lead=LeadData(
            nome_cliente=lead_data.get("nome_cliente"),
            telefone_whatsapp=lead_data.get("telefone_whatsapp"),
            cidade_estado=lead_data.get("cidade_estado"),
            motivo_contato=lead_data.get("motivo_contato"),
            equipamento_interesse=lead_data.get("equipamento_interesse"),
            tipo_negocio=lead_data.get("tipo_negocio"),
            previsao_compra=lead_data.get("previsao_compra"),
            respostas=lead_data.get("respostas", {}),
        ),
    )
