"""B5 - log operacional e /status remoto.

Sem isso, saber se a Sofia respondeu alguma coisa exigia abrir um shell no
servidor: o processo nao emitia log nenhum e todo o rastro ficava num arquivo
SQLite lido por scripts locais. Os endpoints /debug existem, mas devolvem PII
sem autenticacao e precisam continuar desligados em producao.

A regra que estes testes protegem: observabilidade nao pode virar uma segunda
porta de acesso a dados pessoais.
"""

import io
import json
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from contextlib import redirect_stdout
from http.server import ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sofia_chatbot.api import (
    SofiaApplication,
    create_handler,
    mascarar_telefone,
    registrar,
)
from sofia_chatbot.config import Settings

TELEFONE = "5531911112222"


def payload(text: str, message_id: str, from_number: str = TELEFONE) -> dict:
    return {
        "origin": "2",
        "contact": {
            "id": "1",
            "name": "Fulano",
            "whatsapp": from_number,
            "in_attendance": "0",
        },
        "msg_id": message_id,
        "msg": text,
        "type": "T",
    }


class MascaramentoTest(unittest.TestCase):
    def test_mantem_apenas_os_quatro_ultimos_digitos(self) -> None:
        self.assertEqual(mascarar_telefone("5531911112222"), "***2222")

    def test_numero_curto_some_por_inteiro(self) -> None:
        self.assertEqual(mascarar_telefone("1234"), "***")

    def test_vazio_nao_quebra(self) -> None:
        self.assertEqual(mascarar_telefone(""), "***")

    def test_ignora_formatacao(self) -> None:
        self.assertEqual(mascarar_telefone("+55 (31) 91111-2222"), "***2222")


class FormatoDoLogTest(unittest.TestCase):
    def test_uma_linha_com_prefixo_e_pares_chave_valor(self) -> None:
        saida = io.StringIO()
        with redirect_stdout(saida):
            registrar("respondida", de="***2222", bloco="BLOCO_COLETA_NOME")

        linha = saida.getvalue().strip()
        self.assertEqual(len(linha.splitlines()), 1)
        self.assertTrue(linha.startswith("[sofia] respondida"))
        self.assertIn("de=***2222", linha)
        self.assertIn("bloco=BLOCO_COLETA_NOME", linha)


class LogNaoVazaDadosPessoaisTest(unittest.TestCase):
    def test_conversa_processada_nao_escreve_texto_nem_telefone(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            app = SofiaApplication(
                Settings(
                    session_store="memory",
                    event_log_enabled=True,
                    event_log_path=str(Path(tmpdir) / "e.db"),
                    maxbot_send_messages=False,
                    maxbot_pilot_phones=(TELEFONE,),
                )
            )

            saida = io.StringIO()
            with redirect_stdout(saida):
                app.maxbot_webhook(payload("Comecar", "log.1"))
                app.maxbot_webhook(payload("Procuro um forno industrial", "log.2"))

            registrado = saida.getvalue()

            self.assertIn("[sofia] respondida", registrado)
            self.assertIn("***2222", registrado)
            # O telefone completo nunca pode aparecer.
            self.assertNotIn(TELEFONE, registrado)
            # Nem o texto que o cliente escreveu.
            self.assertNotIn("forno industrial", registrado)

    def test_telefone_fora_do_piloto_tambem_e_mascarado(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            app = SofiaApplication(
                Settings(
                    session_store="memory",
                    event_log_enabled=True,
                    event_log_path=str(Path(tmpdir) / "e.db"),
                    maxbot_pilot_phones=(TELEFONE,),
                )
            )

            saida = io.StringIO()
            with redirect_stdout(saida):
                app.maxbot_webhook(payload("Oi", "log.3", from_number="5511999998888"))

            registrado = saida.getvalue()
            self.assertIn("motivo=fora_do_piloto", registrado)
            self.assertIn("***8888", registrado)
            self.assertNotIn("5511999998888", registrado)


class ContadoresDeStatusTest(unittest.TestCase):
    def _app(self, tmpdir: str, token: str = "token-de-status") -> SofiaApplication:
        return SofiaApplication(
            Settings(
                session_store="memory",
                event_log_enabled=True,
                event_log_path=str(Path(tmpdir) / "e.db"),
                maxbot_send_messages=False,
                maxbot_pilot_phones=(TELEFONE,),
                status_token=token,
            )
        )

    def test_conta_respondidas_e_ignoradas(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            app = self._app(tmpdir)
            saida = io.StringIO()
            with redirect_stdout(saida):
                app.maxbot_webhook(payload("Comecar", "s.1"))
                app.maxbot_webhook(payload("Oi", "s.2", from_number="5511999998888"))
                app.maxbot_webhook(payload("Comecar", "s.1"))

            status = app.status()

            self.assertEqual(status["respondidas"], 1)
            self.assertEqual(status["ignoradas"], 1)
            self.assertEqual(status["duplicadas"], 1)
            self.assertEqual(status["erros"], 0)

    def test_status_nao_devolve_conteudo_de_conversa(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            app = self._app(tmpdir)
            saida = io.StringIO()
            with redirect_stdout(saida):
                app.maxbot_webhook(payload("Quero um forno industrial", "s.3"))

            serializado = json.dumps(app.status(), ensure_ascii=False)

            self.assertNotIn("forno industrial", serializado)
            self.assertNotIn(TELEFONE, serializado)

    def test_expoe_o_estado_das_travas_de_seguranca(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            status = self._app(tmpdir).status()
            self.assertFalse(status["envio_real_ligado"])
            self.assertTrue(status["modo_piloto"])


class RotaDeStatusTest(unittest.TestCase):
    def _servir(self, settings: Settings):
        app = SofiaApplication(settings)
        server = ThreadingHTTPServer(("127.0.0.1", 0), create_handler(app))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        return server, f"http://127.0.0.1:{server.server_address[1]}"

    def _get(self, url: str, token: str | None = None) -> tuple[int, str]:
        request = urllib.request.Request(url)
        if token is not None:
            request.add_header("X-Status-Token", token)
        try:
            with urllib.request.urlopen(request, timeout=5) as response:
                return response.status, response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            return exc.code, exc.read().decode("utf-8")

    def test_token_correto_devolve_contadores(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            server, base = self._servir(
                Settings(
                    session_store="memory",
                    event_log_enabled=True,
                    event_log_path=str(Path(tmpdir) / "e.db"),
                    status_token="token-secreto",
                )
            )
            try:
                codigo, corpo = self._get(f"{base}/status", "token-secreto")
            finally:
                server.shutdown()
                server.server_close()

            self.assertEqual(codigo, 200)
            self.assertIn("respondidas", json.loads(corpo))

    def test_sem_token_responde_401(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            server, base = self._servir(
                Settings(
                    session_store="memory",
                    event_log_enabled=True,
                    event_log_path=str(Path(tmpdir) / "e.db"),
                    status_token="token-secreto",
                )
            )
            try:
                sem_token = self._get(f"{base}/status")
                token_errado = self._get(f"{base}/status", "chute")
            finally:
                server.shutdown()
                server.server_close()

            self.assertEqual(sem_token[0], 401)
            self.assertEqual(token_errado[0], 401)

    def test_sem_token_configurado_a_rota_nem_existe(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            server, base = self._servir(
                Settings(
                    session_store="memory",
                    event_log_enabled=True,
                    event_log_path=str(Path(tmpdir) / "e.db"),
                    status_token="",
                )
            )
            try:
                codigo, _ = self._get(f"{base}/status", "qualquer")
            finally:
                server.shutdown()
                server.server_close()

            self.assertEqual(codigo, 404)

    def test_health_continua_aberto(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            server, base = self._servir(
                Settings(
                    session_store="memory",
                    event_log_enabled=False,
                    status_token="token-secreto",
                )
            )
            try:
                codigo, corpo = self._get(f"{base}/health")
            finally:
                server.shutdown()
                server.server_close()

            self.assertEqual(codigo, 200)
            self.assertTrue(json.loads(corpo)["ok"])


if __name__ == "__main__":
    unittest.main()
