import sys
import tempfile
from pathlib import Path
import unittest
import hmac
import hashlib
import json

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sofia_chatbot.api import SofiaApplication
from sofia_chatbot.channels.whatsapp import WhatsAppReplyRenderer, WhatsAppWebhookParser, verify_meta_signature
from sofia_chatbot.config import Settings
from sofia_chatbot.domain import BotReply
from sofia_chatbot.event_log import SQLiteEventLogger


def whatsapp_text_payload(text: str, from_number: str = "5531999990000", message_id: str = "wamid.test") -> dict:
    return {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "waba-id",
                "changes": [
                    {
                        "field": "messages",
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {
                                "display_phone_number": "553133330000",
                                "phone_number_id": "phone-number-id",
                            },
                            "contacts": [
                                {
                                    "profile": {"name": "Cliente Teste"},
                                    "wa_id": from_number,
                                }
                            ],
                            "messages": [
                                {
                                    "from": from_number,
                                    "id": message_id,
                                    "timestamp": "1720000000",
                                    "text": {"body": text},
                                    "type": "text",
                                }
                            ],
                        },
                    }
                ],
            }
        ],
    }


class WhatsAppWebhookParserTest(unittest.TestCase):
    def test_parses_text_message(self) -> None:
        messages = WhatsAppWebhookParser().parse_messages(whatsapp_text_payload("Comecar"))

        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].session_id, "5531999990000")
        self.assertEqual(messages[0].text, "Comecar")
        self.assertEqual(messages[0].profile_name, "Cliente Teste")

    def test_ignores_status_webhook(self) -> None:
        payload = {
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "statuses": [
                                    {"id": "wamid.status", "status": "delivered"},
                                ]
                            }
                        }
                    ]
                }
            ]
        }

        messages = WhatsAppWebhookParser().parse_messages(payload)

        self.assertEqual(messages, [])


class WhatsAppReplyRendererTest(unittest.TestCase):
    def test_renders_text_payload_without_options(self) -> None:
        payload = WhatsAppReplyRenderer().render("5531999990000", BotReply("Ola"))

        self.assertEqual(payload["type"], "text")
        self.assertEqual(payload["text"]["body"], "Ola")

    def test_renders_button_payload_for_up_to_three_options(self) -> None:
        payload = WhatsAppReplyRenderer().render(
            "5531999990000",
            BotReply("Escolha", ["Sim", "Nao", "Talvez"]),
        )

        self.assertEqual(payload["type"], "interactive")
        self.assertEqual(payload["interactive"]["type"], "button")
        self.assertEqual(len(payload["interactive"]["action"]["buttons"]), 3)

    def test_renders_list_payload_for_more_than_three_options(self) -> None:
        payload = WhatsAppReplyRenderer().render(
            "5531999990000",
            BotReply("Escolha", ["1", "2", "3", "4"]),
        )

        self.assertEqual(payload["type"], "interactive")
        self.assertEqual(payload["interactive"]["type"], "list")
        self.assertEqual(len(payload["interactive"]["action"]["sections"][0]["rows"]), 4)


class WhatsAppApplicationWebhookTest(unittest.TestCase):
    def test_verifies_webhook_with_expected_token(self) -> None:
        settings = Settings(
            session_store="memory",
            whatsapp_verify_token="token-teste",
        )
        app = SofiaApplication(settings)

        status, body = app.verify_whatsapp_webhook("subscribe", "token-teste", "desafio")

        self.assertEqual(status, 200)
        self.assertEqual(body, "desafio")

    def test_rejects_webhook_with_wrong_token(self) -> None:
        app = SofiaApplication(Settings(session_store="memory", whatsapp_verify_token="token-teste"))

        status, _ = app.verify_whatsapp_webhook("subscribe", "errado", "desafio")

        self.assertEqual(status, 403)

    def test_processes_whatsapp_message_in_dry_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            app = SofiaApplication(
                Settings(
                    session_store="sqlite",
                    sqlite_path=str(Path(tmpdir) / "sessions.db"),
                    event_log_path=str(Path(tmpdir) / "events.db"),
                    whatsapp_send_messages=False,
                )
            )

            response = app.whatsapp_webhook(whatsapp_text_payload("Comecar", message_id="wamid.dry_run"))

            self.assertTrue(response["ok"])
            self.assertFalse(response["ignored"])
            self.assertEqual(response["processed"][0]["outbound"]["mode"], "dry_run")
            self.assertIn("Como posso te ajudar hoje?", response["processed"][0]["reply"]["message"])

    def test_keeps_whatsapp_session_by_phone_number(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            app = SofiaApplication(
                Settings(
                    session_store="memory",
                    event_log_enabled=True,
                    event_log_path=str(Path(tmpdir) / "events.db"),
                )
            )

            app.whatsapp_webhook(whatsapp_text_payload("Comecar", message_id="wamid.session.1"))
            response = app.whatsapp_webhook(whatsapp_text_payload("1", message_id="wamid.session.2"))

            processed = response["processed"][0]
            self.assertEqual(processed["reply"]["next_block"], "BLOCO_02_EQUIPAMENTO_ESPECIFICO")
            self.assertIn("Fritadeira", processed["reply"]["options"])

    def test_whatsapp_uses_sender_phone_and_skips_phone_question(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            app = SofiaApplication(
                Settings(
                    session_store="memory",
                    event_log_enabled=True,
                    event_log_path=str(Path(tmpdir) / "events.db"),
                )
            )
            state = app.store.get("5531999990000")
            state.current_block = "BLOCO_COLETA_NOME"
            app.store.save(state)

            response = app.whatsapp_webhook(
                whatsapp_text_payload("Cliente Teste", message_id="wamid.autofill")
            )

            processed = response["processed"][0]
            saved = app.store.get("5531999990000")
            self.assertEqual(
                processed["reply"]["next_block"], "BLOCO_COLETA_CIDADE"
            )
            self.assertIn("cidade e estado", processed["reply"]["message"])
            self.assertEqual(saved.lead.telefone_whatsapp, "5531999990000")

    def test_ignores_duplicate_whatsapp_message(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            app = SofiaApplication(
                Settings(
                    session_store="memory",
                    event_log_enabled=True,
                    event_log_path=str(Path(tmpdir) / "events.db"),
                )
            )
            payload = whatsapp_text_payload("Comecar", message_id="wamid.duplicate")

            first = app.whatsapp_webhook(payload)
            second = app.whatsapp_webhook(payload)

            self.assertEqual(len(first["processed"]), 1)
            self.assertEqual(second["processed"], [])
            self.assertEqual(second["duplicates"][0]["ignored_reason"], "duplicate_message")

    def test_logs_whatsapp_event_to_sqlite(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            event_path = str(Path(tmpdir) / "events.db")
            app = SofiaApplication(
                Settings(
                    session_store="memory",
                    event_log_enabled=True,
                    event_log_path=event_path,
                )
            )

            app.whatsapp_webhook(whatsapp_text_payload("Comecar"))

            import sqlite3

            conn = sqlite3.connect(event_path)
            try:
                count = conn.execute("SELECT COUNT(*) FROM events WHERE event_type = 'whatsapp_message'").fetchone()[0]
            finally:
                conn.close()

            self.assertEqual(count, 1)

    def test_debug_session_and_events_are_available_from_application(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            app = SofiaApplication(
                Settings(
                    session_store="sqlite",
                    sqlite_path=str(Path(tmpdir) / "sessions.db"),
                    event_log_enabled=True,
                    event_log_path=str(Path(tmpdir) / "events.db"),
                    debug_endpoints_enabled=True,
                )
            )

            app.chat("debug-1", "Comecar")

            session = app.debug_session("debug-1")
            events = app.debug_events(session_id="debug-1", limit=5)

            self.assertEqual(session["current_block"], "BLOCO_01_MENU_INICIAL")
            self.assertTrue(events["events"])



class WhatsAppWebhookFailureRecoveryTest(unittest.TestCase):
    def test_failed_processing_is_retryable(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            app = SofiaApplication(
                Settings(
                    session_store="memory",
                    event_log_enabled=True,
                    event_log_path=str(Path(tmpdir) / "events.db"),
                )
            )
            payload = whatsapp_text_payload("Comecar", message_id="wamid.retry")

            original_handle = app.flow.handle

            def boom(*args, **kwargs):
                raise RuntimeError("falha transitoria")

            app.flow.handle = boom
            first = app.whatsapp_webhook(payload)
            self.assertEqual(first["processed"], [])
            self.assertEqual(first["errors"][0]["error"], "processing_failed")

            # Retry da Meta com o mesmo message_id deve reprocessar, nao cair como duplicata.
            app.flow.handle = original_handle
            second = app.whatsapp_webhook(payload)
            self.assertEqual(len(second["processed"]), 1)
            self.assertEqual(second["duplicates"], [])
            self.assertIn("Como posso te ajudar hoje?", second["processed"][0]["reply"]["message"])


class HttpServerTest(unittest.TestCase):
    """Testes de nivel HTTP no handler real, com servidor efemero."""

    def _start_server(self, settings: Settings):
        from http.server import ThreadingHTTPServer
        import threading

        from sofia_chatbot.api import create_handler

        app = SofiaApplication(settings)
        server = ThreadingHTTPServer(("127.0.0.1", 0), create_handler(app))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base_url = f"http://127.0.0.1:{server.server_address[1]}"
        return app, server, base_url

    def _post(self, url: str, body: bytes, headers: dict | None = None):
        import urllib.error
        import urllib.request

        request = urllib.request.Request(
            url,
            data=body,
            headers={"Content-Type": "application/json", **(headers or {})},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                return response.status, json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode("utf-8", errors="replace")
            try:
                return exc.code, json.loads(raw)
            except json.JSONDecodeError:
                return exc.code, {"raw": raw}

    def test_webhook_http_response_is_minimal_ack(self) -> None:
        settings = Settings(session_store="memory", event_log_enabled=False)
        app, server, base_url = self._start_server(settings)
        try:
            payload = whatsapp_text_payload("Comecar", message_id="wamid.http.ack")
            status, body = self._post(f"{base_url}/webhook/whatsapp", json.dumps(payload).encode("utf-8"))

            self.assertEqual(status, 200)
            self.assertEqual(body, {"ok": True, "processed": 1, "duplicates": 0, "errors": 0})
            # Nada do conteudo da conversa deve vazar na resposta HTTP.
            self.assertNotIn("reply", body)
            self.assertNotIn("summary", json.dumps(body))
        finally:
            server.shutdown()
            server.server_close()

    def test_webhook_http_failure_returns_500_and_allows_retry(self) -> None:
        settings = Settings(session_store="memory", event_log_enabled=False)
        app, server, base_url = self._start_server(settings)
        original_handle = app.flow.handle

        def boom(*args, **kwargs):
            raise RuntimeError("falha transitoria")

        try:
            payload = whatsapp_text_payload("Comecar", message_id="wamid.http.retry")
            raw_payload = json.dumps(payload).encode("utf-8")
            app.flow.handle = boom

            first_status, first_body = self._post(
                f"{base_url}/webhook/whatsapp", raw_payload
            )
            self.assertEqual(first_status, 500)
            self.assertEqual(
                first_body,
                {"ok": False, "processed": 0, "duplicates": 0, "errors": 1},
            )
            self.assertNotIn("falha transitoria", json.dumps(first_body))

            app.flow.handle = original_handle
            second_status, second_body = self._post(
                f"{base_url}/webhook/whatsapp", raw_payload
            )
            self.assertEqual(second_status, 200)
            self.assertEqual(
                second_body,
                {"ok": True, "processed": 1, "duplicates": 0, "errors": 0},
            )
        finally:
            app.flow.handle = original_handle
            server.shutdown()
            server.server_close()

    def test_local_api_can_be_disabled(self) -> None:
        settings = Settings(session_store="memory", event_log_enabled=False, local_api_enabled=False)
        app, server, base_url = self._start_server(settings)
        try:
            status, _ = self._post(f"{base_url}/chat", json.dumps({"session_id": "x", "message": "oi"}).encode("utf-8"))
            self.assertEqual(status, 404)

            status, _ = self._post(f"{base_url}/reset", json.dumps({"session_id": "x"}).encode("utf-8"))
            self.assertEqual(status, 404)
        finally:
            server.shutdown()
            server.server_close()

    def test_oversized_body_is_rejected(self) -> None:
        settings = Settings(session_store="memory", event_log_enabled=False)
        app, server, base_url = self._start_server(settings)
        try:
            big = b'{"session_id": "x", "message": "' + b"a" * 1_100_000 + b'"}'
            status, body = self._post(f"{base_url}/chat", big)

            self.assertEqual(status, 413)
            self.assertEqual(body.get("error"), "payload_muito_grande")
        finally:
            server.shutdown()
            server.server_close()

    def test_internal_error_is_not_leaked(self) -> None:
        settings = Settings(session_store="memory", event_log_enabled=False)
        app, server, base_url = self._start_server(settings)
        try:
            def boom(*args, **kwargs):
                raise RuntimeError("segredo interno: /caminho/sensivel")

            app.chat = boom
            status, body = self._post(f"{base_url}/chat", json.dumps({"session_id": "x", "message": "oi"}).encode("utf-8"))

            self.assertEqual(status, 500)
            self.assertEqual(body.get("error"), "erro_interno")
            self.assertNotIn("segredo interno", json.dumps(body))
        finally:
            server.shutdown()
            server.server_close()


class EventLoggerTest(unittest.TestCase):
    def test_mark_message_processed_returns_false_for_duplicate(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = SQLiteEventLogger(str(Path(tmpdir) / "events.db"))

            self.assertTrue(logger.mark_message_processed("whatsapp", "wamid.1", "5531"))
            self.assertFalse(logger.mark_message_processed("whatsapp", "wamid.1", "5531"))

    def test_unmark_allows_reprocessing(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = SQLiteEventLogger(str(Path(tmpdir) / "events.db"))

            self.assertTrue(logger.mark_message_processed("whatsapp", "wamid.2", "5531"))
            logger.unmark_message_processed("whatsapp", "wamid.2")
            self.assertTrue(logger.mark_message_processed("whatsapp", "wamid.2", "5531"))


class MetaSignatureTest(unittest.TestCase):
    def test_accepts_valid_signature_when_secret_is_configured(self) -> None:
        body = json.dumps({"ok": True}).encode("utf-8")
        digest = hmac.new(b"secret", body, hashlib.sha256).hexdigest()

        self.assertTrue(verify_meta_signature("secret", body, f"sha256={digest}"))

    def test_rejects_invalid_signature_when_secret_is_configured(self) -> None:
        body = json.dumps({"ok": True}).encode("utf-8")

        self.assertFalse(verify_meta_signature("secret", body, "sha256=errada"))

    def test_accepts_without_secret_for_local_development(self) -> None:
        self.assertTrue(verify_meta_signature("", b"{}", None))


if __name__ == "__main__":
    unittest.main()
