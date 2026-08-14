from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sofia_chatbot.api import SofiaApplication
from sofia_chatbot.config import Settings


def payload(text: str, message_id: str, from_number: str = "5531999990000") -> dict:
    return {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "waba-smoke",
                "changes": [
                    {
                        "field": "messages",
                        "value": {
                            "messaging_product": "whatsapp",
                            "contacts": [
                                {
                                    "profile": {"name": "Cliente Smoke"},
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


def maxbot_payload(
    text: str,
    message_id: str,
    from_number: str = "5531777770000",
    in_attendance: str = "0",
) -> dict:
    return {
        "origin": "2",
        "contact": {
            "id": from_number,
            "name": "Cliente",
            "surname": "Smoke",
            "whatsapp": from_number,
            "segmentation": ["SOFIA_API_PILOTO"],
            "in_attendance": in_attendance,
            "current_protocol": "PROTO-SMOKE" if in_attendance == "1" else "",
            "current_attendant": "Humano" if in_attendance == "1" else "",
        },
        "msg_id": message_id,
        "msg_timestamp": "1720000000",
        "msg_date": "2026-08-04 10:00:00",
        "msg": text,
        "type": "T",
    }


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        app = SofiaApplication(
            Settings(
                session_store="sqlite",
                sqlite_path=str(Path(tmpdir) / "sessions.db"),
                event_log_enabled=True,
                event_log_path=str(Path(tmpdir) / "events.db"),
                whatsapp_send_messages=False,
                debug_endpoints_enabled=True,
            )
        )

        first = app.whatsapp_webhook(payload("Comecar", "wamid.smoke.1"))
        assert_true(first["processed"], "Primeira mensagem deveria ser processada.")
        assert_true("Como posso te ajudar hoje?" in first["processed"][0]["reply"]["message"], "Menu inicial nao apareceu.")

        second = app.whatsapp_webhook(payload("1", "wamid.smoke.2"))
        assert_true(second["processed"][0]["reply"]["next_block"] == "BLOCO_02_EQUIPAMENTO_ESPECIFICO", "Opcao numerica 1 nao abriu equipamentos.")

        third = app.whatsapp_webhook(payload("Fritadeira", "wamid.smoke.3"))
        assert_true("equipamento_fritadeira" in third["processed"][0]["reply"]["tags"], "Fritadeira nao foi marcada.")

        sensitive = app.whatsapp_webhook(payload("quanto custa?", "wamid.smoke.4"))
        assert_true("bloqueio_comercial" in sensitive["processed"][0]["reply"]["tags"], "Pedido sensivel nao foi bloqueado.")

        duplicate_first = app.whatsapp_webhook(payload("Comecar", "wamid.smoke.duplicada", "5531888880000"))
        duplicate_second = app.whatsapp_webhook(payload("Comecar", "wamid.smoke.duplicada", "5531888880000"))
        assert_true(duplicate_first["processed"], "Mensagem duplicada original deveria processar.")
        assert_true(duplicate_second["duplicates"], "Mensagem duplicada deveria ser ignorada.")

        maxbot_first = app.maxbot_webhook(maxbot_payload("Comecar", "maxbot.smoke.1"))
        assert_true(maxbot_first["processed"], "Mensagem Maxbot deveria ser processada.")
        assert_true(
            "1 - Procuro um equipamento" in maxbot_first["processed"][0]["outbound"]["payload"]["msg"],
            "Menu Maxbot deveria ser numerado.",
        )

        human = app.maxbot_webhook(
            maxbot_payload(
                "Mensagem durante atendimento",
                "maxbot.smoke.humano",
                from_number="5531666660000",
                in_attendance="1",
            )
        )
        assert_true(human["ignored"], "Mensagem com atendente humano deveria ser ignorada.")

        events = app.debug_events(limit=20)["events"]
        assert_true(events, "Eventos deveriam ser registrados.")

    print("Smoke test OK: fluxo, Meta, Maxbot, guardrails, duplicidade e logs funcionando.")


if __name__ == "__main__":
    main()
