from pathlib import Path
import sys
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sofia_chatbot.api import SofiaApplication
from sofia_chatbot.config import Settings


def build_payload(text: str, from_number: str, message_id: str) -> dict:
    return {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "waba-simulada",
                "changes": [
                    {
                        "field": "messages",
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {
                                "display_phone_number": "553133330000",
                                "phone_number_id": "phone-number-id-simulado",
                            },
                            "contacts": [
                                {
                                    "profile": {"name": "Cliente Simulado"},
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


def main() -> None:
    app = SofiaApplication(
        Settings(
            session_store="memory",
            event_log_enabled=False,
            whatsapp_send_messages=False,
        )
    )
    from_number = "5531999990000"

    print("Simulador WhatsApp da Sofia")
    print("Digite mensagens como cliente. Use Ctrl+C para sair.")
    print()

    while True:
        text = input("Cliente > ").strip()
        if not text:
            continue

        payload = build_payload(text, from_number, f"wamid.simulado.{uuid.uuid4()}")
        response = app.whatsapp_webhook(payload)

        if not response["processed"]:
            print("Sofia > Nenhuma mensagem processada.")
            continue

        processed = response["processed"][0]
        reply = processed["reply"]
        print(f"Sofia > {reply['message']}")
        if reply["options"]:
            print("Opcoes:")
            for index, option in enumerate(reply["options"], start=1):
                print(f"  {index}. {option}")
        if reply["status"] == "handoff":
            print()
            print("Resumo para atendimento:")
            print(reply["summary"])
        print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nSimulador encerrado.")
