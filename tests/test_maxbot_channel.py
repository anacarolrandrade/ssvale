import json
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sofia_chatbot.api import SofiaApplication, create_handler
from sofia_chatbot.channels.maxbot import (
    MaxbotClient,
    MaxbotRateLimitError,
    MaxbotReplyRenderer,
    MaxbotWebhookParser,
    verify_maxbot_webhook_path,
)
from sofia_chatbot.config import Settings
from sofia_chatbot.domain import BotReply, ConversationStatus
from sofia_chatbot.flow import agora_utc


def maxbot_text_payload(
    text: str,
    message_id: str = "3EB04714F09C9DE532E2",
    from_number: str = "5531911112222",
    in_attendance: str = "0",
    segmentations: list[str] | None = None,
) -> dict:
    return {
        "origin": "2",
        "contact": {
            "id": "1",
            "name": "Fulano",
            "surname": "Mariano",
            "whatsapp": from_number,
            "segmentation": (
                ["SOFIA_API_PILOTO"]
                if segmentations is None
                else segmentations
            ),
            "in_attendance": in_attendance,
            "current_protocol": "PROTO-1" if in_attendance == "1" else "",
            "current_attendant": "Atendente" if in_attendance == "1" else "",
        },
        "msg_id": message_id,
        "msg_timestamp": "1643129533",
        "msg_date": "2022-01-25 13:52:15",
        "msg": text,
        "type": "T",
        "quoted_msg_id": "",
    }


class MaxbotWebhookParserTest(unittest.TestCase):
    def test_parses_text_and_attendance_context(self) -> None:
        messages = MaxbotWebhookParser().parse_messages(
            maxbot_text_payload("Ola", in_attendance="1")
        )

        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].session_id, "5531911112222")
        self.assertEqual(messages[0].text, "Ola")
        self.assertEqual(messages[0].profile_name, "Fulano Mariano")
        self.assertTrue(messages[0].in_attendance)
        self.assertEqual(messages[0].current_protocol, "PROTO-1")
        self.assertEqual(messages[0].segmentations, ("SOFIA_API_PILOTO",))

    def test_parses_official_message_in_attendance_contract(self) -> None:
        payload = {
            "origin": "2",
            "whatsapp": "553111112222",
            "prot_id": "2398",
            "contact_id": "845",
            "chat_id": "19273",
            "msg_id": "3EB04714F09C9DE532E2",
            "msg_timestamp": "1643129533",
            "msg_date": "2022-01-25 13:52:15",
            "msg": "Mensagem para o atendente",
            "type": "T",
        }

        messages = MaxbotWebhookParser().parse_messages(payload)

        self.assertEqual(len(messages), 1)
        self.assertTrue(messages[0].in_attendance)
        self.assertEqual(messages[0].session_id, "553111112222")
        self.assertEqual(messages[0].protocol_id, "2398")
        self.assertEqual(messages[0].contact_id, "845")
        self.assertEqual(messages[0].chat_id, "19273")

    def test_ignores_unsupported_media_without_breaking(self) -> None:
        payload = maxbot_text_payload("")
        payload.update({"type": "I", "img_url": "https://example.invalid/a.jpg"})

        self.assertEqual(MaxbotWebhookParser().parse_messages(payload), [])

    def test_all_example_payloads_are_valid_and_parse_safely(self) -> None:
        examples_dir = Path(__file__).resolve().parents[1] / "examples" / "maxbot"
        parsed_counts = {}
        for path in sorted(examples_dir.glob("*.json")):
            payload = json.loads(path.read_text(encoding="utf-8"))
            parsed_counts[path.name] = len(MaxbotWebhookParser().parse_messages(payload))

        self.assertEqual(len(parsed_counts), 7)
        self.assertEqual(parsed_counts["imagem-ignorada.json"], 0)
        self.assertTrue(all(count == 1 for name, count in parsed_counts.items() if name != "imagem-ignorada.json"))


class MaxbotReplyRendererTest(unittest.TestCase):
    def test_renders_options_as_numbered_plain_text(self) -> None:
        payload = MaxbotReplyRenderer().render(
            "5531911112222", BotReply("Escolha", ["Primeira", "Segunda"])
        )

        self.assertEqual(payload["cmd"], "send_text")
        self.assertEqual(payload["ct_whatsapp"], "5531911112222")
        self.assertEqual(payload["msg"], "Escolha\n\n1 - Primeira\n2 - Segunda")

    def test_renders_attendance_reply_for_existing_protocol(self) -> None:
        payload = MaxbotReplyRenderer().render_attendance(
            "2398", BotReply("Escolha", ["Primeira", "Segunda"])
        )

        self.assertEqual(payload["cmd"], "send_chat_msg")
        self.assertEqual(payload["prot_id"], "2398")
        self.assertEqual(payload["msg"], "Escolha\n\n1 - Primeira\n2 - Segunda")
        self.assertTrue(payload["msg_date_sql"])


class MaxbotClientTest(unittest.TestCase):
    def test_dry_run_never_includes_api_tokens(self) -> None:
        client = MaxbotClient(
            Settings(
                maxbot_api_token="segredo-api",
                maxbot_channel_token="segredo-canal",
                maxbot_send_messages=False,
            )
        )

        result = client.send_text("5531911112222", "Ola")

        self.assertEqual(result["mode"], "dry_run")
        self.assertNotIn("token", json.dumps(result).lower())

    def test_live_request_accepts_processing_status_without_exposing_token(self) -> None:
        class FakeResponse:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self):
                return b'{"status": 2, "msg": "Processing"}'

        client = MaxbotClient(
            Settings(
                maxbot_api_token="segredo-api",
                maxbot_channel_token="segredo-canal",
                maxbot_send_messages=True,
            )
        )

        with patch(
            "sofia_chatbot.channels.maxbot.urllib.request.urlopen",
            return_value=FakeResponse(),
        ) as urlopen:
            result = client.send_text("5531911112222", "Ola")

        sent_body = json.loads(urlopen.call_args.args[0].data.decode("utf-8"))
        self.assertEqual(sent_body["token"], "segredo-api")
        self.assertEqual(sent_body["channel_token"], "segredo-canal")
        self.assertTrue(result["sent"])
        self.assertTrue(result["processing"])
        self.assertNotIn("segredo", json.dumps(result))

    def test_attendance_request_uses_protocol_command(self) -> None:
        class FakeResponse:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self):
                return b'{"status": 1, "msg": "Success"}'

        client = MaxbotClient(
            Settings(
                maxbot_api_token="segredo-api",
                maxbot_channel_token="segredo-canal",
                maxbot_send_messages=True,
            )
        )

        with patch(
            "sofia_chatbot.channels.maxbot.urllib.request.urlopen",
            return_value=FakeResponse(),
        ) as urlopen:
            result = client.send_message(
                {
                    "cmd": "send_chat_msg",
                    "prot_id": "2398",
                    "msg": "Ola",
                    "msg_date_sql": "2026-08-04 20:00:00",
                }
            )

        sent_body = json.loads(urlopen.call_args.args[0].data.decode("utf-8"))
        self.assertEqual(sent_body["cmd"], "send_chat_msg")
        self.assertEqual(sent_body["prot_id"], "2398")
        self.assertNotIn("channel_token", sent_body)
        self.assertTrue(result["sent"])

    def test_http_429_has_specific_failure(self) -> None:
        client = MaxbotClient(
            Settings(maxbot_api_token="segredo", maxbot_send_messages=True)
        )
        failure = urllib.error.HTTPError(
            "https://app.maxbot.com.br/api/v1.php", 429, "Too Many", {}, None
        )

        with patch(
            "sofia_chatbot.channels.maxbot.urllib.request.urlopen",
            side_effect=failure,
        ):
            with self.assertRaises(MaxbotRateLimitError):
                client.send_text("5531911112222", "Ola")


class MaxbotWebhookPathTest(unittest.TestCase):
    def test_requires_exact_configured_secret(self) -> None:
        self.assertTrue(
            verify_maxbot_webhook_path("segredo-123", "/webhook/maxbot/segredo-123")
        )
        self.assertFalse(
            verify_maxbot_webhook_path("segredo-123", "/webhook/maxbot/errado")
        )
        self.assertFalse(verify_maxbot_webhook_path("", "/webhook/maxbot/"))


class MaxbotApplicationWebhookTest(unittest.TestCase):
    def _app(self, tmpdir: str) -> SofiaApplication:
        return SofiaApplication(
            Settings(
                session_store="memory",
                event_log_enabled=True,
                event_log_path=str(Path(tmpdir) / "events.db"),
                maxbot_send_messages=False,
            )
        )

    def test_processes_numbered_choices_across_the_flow(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            app = self._app(tmpdir)

            first = app.maxbot_webhook(maxbot_text_payload("Comecar", "max.1"))
            second = app.maxbot_webhook(maxbot_text_payload("1", "max.2"))
            third = app.maxbot_webhook(maxbot_text_payload("2", "max.3"))
            fourth = app.maxbot_webhook(maxbot_text_payload("2", "max.4"))

            self.assertIn("1 - Procuro um equipamento", first["processed"][0]["outbound"]["payload"]["msg"])
            self.assertEqual(second["processed"][0]["reply"]["next_block"], "BLOCO_02_EQUIPAMENTO_ESPECIFICO")
            self.assertEqual(third["processed"][0]["resolved_text"], "Freezer / Refrigeração")
            self.assertEqual(fourth["processed"][0]["resolved_text"], "Congelar")

    def test_deduplicates_by_maxbot_message_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            app = self._app(tmpdir)
            payload = maxbot_text_payload("Comecar", "max.duplicate")

            first = app.maxbot_webhook(payload)
            second = app.maxbot_webhook(payload)

            self.assertEqual(len(first["processed"]), 1)
            self.assertEqual(second["processed"], [])
            self.assertEqual(second["duplicates"][0]["ignored_reason"], "duplicate_message")

    def test_never_responds_during_human_attendance(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            app = self._app(tmpdir)

            with patch.object(
                app.maxbot_client,
                "send_message",
                side_effect=AssertionError("nao deveria enviar"),
            ):
                result = app.maxbot_webhook(
                    maxbot_text_payload("Ola", "max.human", in_attendance="1")
                )

            self.assertEqual(result["processed"], [])
            self.assertEqual(result["ignored"][0]["ignored_reason"], "human_attendance")
            self.assertEqual(app.store.get("5531911112222").current_block, "BLOCO_00_BOAS_VINDAS")

    def test_controlled_pilot_can_reply_inside_automatic_protocol(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            app = SofiaApplication(
                Settings(
                    session_store="memory",
                    event_log_enabled=True,
                    event_log_path=str(Path(tmpdir) / "events.db"),
                    maxbot_pilot_phones=("5531911112222",),
                    maxbot_pilot_allow_attendance=True,
                    maxbot_send_messages=False,
                )
            )
            payload = {
                "origin": "2",
                "whatsapp": "5531911112222",
                "prot_id": "2398",
                "contact_id": "845",
                "chat_id": "19273",
                "msg_id": "max.pilot.attendance",
                "msg": "Comecar",
                "type": "T",
            }

            result = app.maxbot_webhook(payload)

            self.assertEqual(len(result["processed"]), 1)
            outbound = result["processed"][0]["outbound"]["payload"]
            self.assertEqual(outbound["cmd"], "send_text")
            self.assertEqual(outbound["ct_whatsapp"], "5531911112222")

    def test_attendance_override_never_bypasses_pilot_allowlist(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            app = SofiaApplication(
                Settings(
                    session_store="memory",
                    event_log_enabled=True,
                    event_log_path=str(Path(tmpdir) / "events.db"),
                    maxbot_pilot_phones=("5531999999999",),
                    maxbot_pilot_allow_attendance=True,
                )
            )
            payload = {
                "origin": "2",
                "whatsapp": "5531911112222",
                "prot_id": "2398",
                "contact_id": "845",
                "chat_id": "19273",
                "msg_id": "max.blocked.attendance",
                "msg": "Comecar",
                "type": "T",
            }

            with patch.object(
                app.maxbot_client,
                "send_message",
                side_effect=AssertionError("nao deveria enviar"),
            ):
                result = app.maxbot_webhook(payload)

            self.assertEqual(result["processed"], [])
            self.assertEqual(
                result["ignored"][0]["ignored_reason"], "human_attendance"
            )

    def test_pilot_filters_contacts_without_phone_or_segment_permission(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            app = self._app(tmpdir)

            with patch.object(
                app.maxbot_client,
                "send_message",
                side_effect=AssertionError("nao deveria enviar"),
            ):
                result = app.maxbot_webhook(
                    maxbot_text_payload(
                        "Comecar", "max.filtered", segmentations=[]
                    )
                )

            self.assertEqual(result["processed"], [])
            self.assertEqual(
                result["ignored"][0]["ignored_reason"], "pilot_not_allowed"
            )

    def test_pilot_phone_allowlist_accepts_contact_without_segment(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            app = SofiaApplication(
                Settings(
                    session_store="memory",
                    event_log_enabled=True,
                    event_log_path=str(Path(tmpdir) / "events.db"),
                    maxbot_pilot_phones=("+55 (31) 91111-2222",),
                )
            )

            result = app.maxbot_webhook(
                maxbot_text_payload(
                    "Comecar", "max.allowed-phone", segmentations=[]
                )
            )

            self.assertEqual(len(result["processed"]), 1)

    def test_maxbot_uses_sender_phone_and_skips_phone_question(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            app = self._app(tmpdir)
            state = app.store.get("5531911112222")
            state.current_block = "BLOCO_COLETA_NOME"
            app.store.save(state)

            result = app.maxbot_webhook(
                maxbot_text_payload("Cliente Teste", "max.autofill-phone")
            )

            processed = result["processed"][0]
            saved = app.store.get("5531911112222")
            self.assertEqual(
                processed["reply"]["next_block"], "BLOCO_COLETA_CIDADE"
            )
            self.assertIn("cidade e estado", processed["reply"]["message"])
            self.assertEqual(saved.lead.telefone_whatsapp, "5531911112222")

    def test_handoff_pending_stays_silent_until_manual_reset(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            app = self._app(tmpdir)
            state = app.store.get("5531911112222")
            state.status = ConversationStatus.HANDOFF
            state.current_block = "BLOCO_ENCAMINHAMENTO_COMERCIAL"
            # Handoff recem-criado. O marco precisa ser explicito: uma sessao
            # em handoff sem `handoff_since` e tratada como legada e liberada
            # pela expiracao automatica (ver tests/test_handoff_expiracao.py).
            state.handoff_since = agora_utc().isoformat(timespec="seconds")
            app.store.save(state)

            with patch.object(
                app.maxbot_client,
                "send_message",
                side_effect=AssertionError("nao deveria enviar"),
            ):
                result = app.maxbot_webhook(
                    maxbot_text_payload("Ainda estou aguardando", "max.pending")
                )

            self.assertEqual(result["processed"], [])
            self.assertEqual(
                result["ignored"][0]["ignored_reason"], "handoff_pending"
            )

    def test_failed_send_is_retryable_without_advancing_session(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            app = self._app(tmpdir)
            payload = maxbot_text_payload("Comecar", "max.retry")
            original_send = app.maxbot_client.send_message

            app.maxbot_client.send_message = lambda *_: (_ for _ in ()).throw(
                RuntimeError("falha transitoria")
            )
            first = app.maxbot_webhook(payload)
            self.assertEqual(first["errors"][0]["error"], "processing_failed")
            self.assertEqual(app.store.get("5531911112222").current_block, "BLOCO_00_BOAS_VINDAS")

            app.maxbot_client.send_message = original_send
            second = app.maxbot_webhook(payload)

            self.assertEqual(second["duplicates"], [])
            self.assertIn("Olá! Eu sou a Sofia", second["processed"][0]["reply"]["message"])


class MaxbotHttpServerTest(unittest.TestCase):
    def _post(self, url: str, payload: dict) -> tuple[int, dict]:
        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
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

    def test_http_ack_is_minimal_and_wrong_secret_is_hidden(self) -> None:
        app = SofiaApplication(
            Settings(
                session_store="memory",
                event_log_enabled=False,
                maxbot_webhook_secret="segredo-webhook",
            )
        )
        server = ThreadingHTTPServer(("127.0.0.1", 0), create_handler(app))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base_url = f"http://127.0.0.1:{server.server_address[1]}"
        try:
            status, body = self._post(
                f"{base_url}/webhook/maxbot/segredo-webhook",
                maxbot_text_payload("Comecar", "max.http"),
            )
            wrong_status, _ = self._post(
                f"{base_url}/webhook/maxbot/errado",
                maxbot_text_payload("Comecar", "max.http.wrong"),
            )
            filtered_status, filtered_body = self._post(
                f"{base_url}/webhook/maxbot/segredo-webhook",
                maxbot_text_payload(
                    "Comecar", "max.http.filtered", segmentations=[]
                ),
            )
            attendance_status, attendance_body = self._post(
                f"{base_url}/webhook/maxbot/segredo-webhook",
                {
                    "origin": "2",
                    "whatsapp": "553111112222",
                    "prot_id": "2398",
                    "contact_id": "845",
                    "chat_id": "19273",
                    "msg_id": "max.http.attendance",
                    "msg": "Mensagem para o atendente",
                    "type": "T",
                },
            )

            self.assertEqual(status, 200)
            self.assertEqual(
                body,
                {"ok": True, "processed": 1, "duplicates": 0, "ignored": 0, "errors": 0},
            )
            self.assertNotIn("reply", body)
            self.assertNotIn("summary", json.dumps(body))
            self.assertEqual(wrong_status, 404)
            self.assertEqual(filtered_status, 200)
            self.assertEqual(filtered_body["processed"], 0)
            self.assertEqual(filtered_body["ignored"], 1)
            self.assertEqual(attendance_status, 200)
            self.assertEqual(attendance_body["processed"], 0)
            self.assertEqual(attendance_body["ignored"], 1)
        finally:
            server.shutdown()
            server.server_close()


if __name__ == "__main__":
    unittest.main()
