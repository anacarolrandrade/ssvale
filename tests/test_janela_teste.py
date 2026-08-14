"""Testes do apoio operacional as janelas de teste real (scripts/janela_teste.py)."""

import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from sofia_chatbot.config import Settings  # noqa: E402

import janela_teste  # noqa: E402


def criar_banco_de_eventos(caminho: Path, eventos: list[tuple[str, str]]) -> None:
    conexao = sqlite3.connect(caminho)
    try:
        conexao.execute(
            """
            CREATE TABLE events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                session_id TEXT NOT NULL,
                payload TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conexao.executemany(
            "INSERT INTO events (event_type, session_id, payload) VALUES (?, ?, '{}')",
            eventos,
        )
        conexao.commit()
    finally:
        conexao.close()


def criar_banco_de_sessoes(caminho: Path, sessoes: list[tuple[str, dict]]) -> None:
    conexao = sqlite3.connect(caminho)
    try:
        conexao.execute(
            """
            CREATE TABLE sessions (
                session_id TEXT PRIMARY KEY,
                payload TEXT NOT NULL,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conexao.executemany(
            "INSERT INTO sessions (session_id, payload) VALUES (?, ?)",
            [
                (session_id, json.dumps(payload, ensure_ascii=False))
                for session_id, payload in sessoes
            ],
        )
        conexao.commit()
    finally:
        conexao.close()


class MascararTest(unittest.TestCase):
    def test_mostra_somente_os_quatro_ultimos_digitos(self) -> None:
        self.assertEqual(janela_teste.mascarar("5512982619238"), "***9238")

    def test_valor_vazio_nao_vaza_nada(self) -> None:
        self.assertEqual(janela_teste.mascarar(""), "***")


class AvaliarFlagsTest(unittest.TestCase):
    def test_estado_seguro_e_aprovado(self) -> None:
        settings = Settings(
            maxbot_send_messages=False,
            maxbot_pilot_allow_attendance=False,
            maxbot_pilot_mode=True,
            whatsapp_send_messages=False,
            local_api_enabled=False,
            debug_endpoints_enabled=False,
        )
        resultado = janela_teste.avaliar_flags(
            settings, janela_teste.FLAGS_ESPERADAS_PREFLIGHT
        )
        self.assertTrue(all(correto for _, _, correto in resultado))

    def test_envio_real_ligado_reprova_o_preflight(self) -> None:
        settings = Settings(
            maxbot_send_messages=True,
            maxbot_pilot_mode=True,
            local_api_enabled=False,
        )
        resultado = dict(
            (nome, correto)
            for nome, _, correto in janela_teste.avaliar_flags(
                settings, janela_teste.FLAGS_ESPERADAS_PREFLIGHT
            )
        )
        self.assertFalse(resultado["maxbot_send_messages"])

    def test_encerramento_exige_envio_e_excecao_desligados(self) -> None:
        settings = Settings(
            maxbot_send_messages=False, maxbot_pilot_allow_attendance=True
        )
        resultado = dict(
            (nome, correto)
            for nome, _, correto in janela_teste.avaliar_flags(
                settings, janela_teste.FLAGS_ESPERADAS_ENCERRAMENTO
            )
        )
        self.assertTrue(resultado["maxbot_send_messages"])
        self.assertFalse(resultado["maxbot_pilot_allow_attendance"])


class SessoesBloqueadasTest(unittest.TestCase):
    def test_sessao_em_handoff_e_reportada_mascarada(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            caminho = Path(tmpdir) / "sessions.db"
            criar_banco_de_sessoes(
                caminho,
                [
                    ("5512982619238", {"status": "handoff"}),
                    ("5531999990001", {"status": "active"}),
                ],
            )
            bloqueadas = janela_teste.sessoes_bloqueadas(
                Settings(sqlite_path=str(caminho))
            )

        self.assertEqual(len(bloqueadas), 1)
        session_id, status, _ = bloqueadas[0]
        self.assertEqual(session_id, "***9238")
        self.assertEqual(status, "handoff")

    def test_banco_inexistente_nao_quebra(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            caminho = Path(tmpdir) / "ausente.db"
            self.assertEqual(
                janela_teste.sessoes_bloqueadas(Settings(sqlite_path=str(caminho))), []
            )


class ContadoresDesdeBaselineTest(unittest.TestCase):
    def test_eventos_anteriores_ao_baseline_sao_ignorados(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            caminho = Path(tmpdir) / "events.db"
            criar_banco_de_eventos(
                caminho,
                [
                    ("maxbot_error", "5512982619238"),
                    ("maxbot_message", "5512982619238"),
                    ("maxbot_message", "5512982619238"),
                    ("maxbot_duplicate", "5512982619238"),
                ],
            )
            settings = Settings(event_log_path=str(caminho))

            self.assertEqual(janela_teste.ultimo_id_evento(settings), 4)

            # Baseline apos o erro historico: ele nao deve contaminar a janela.
            contagens = dict(janela_teste.contar_eventos(settings, desde_id=1))

        self.assertNotIn("maxbot_error", contagens)
        self.assertEqual(contagens["maxbot_message"], 2)
        self.assertEqual(contagens["maxbot_duplicate"], 1)

    def test_log_inexistente_devolve_zero(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            settings = Settings(event_log_path=str(Path(tmpdir) / "ausente.db"))
            self.assertEqual(janela_teste.ultimo_id_evento(settings), 0)
            self.assertEqual(janela_teste.contar_eventos(settings, desde_id=0), [])


if __name__ == "__main__":
    unittest.main()
