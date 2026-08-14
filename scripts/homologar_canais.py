"""Compara o fluxo direto com os adaptadores da Meta e do Maxbot."""

from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sofia_chatbot.api import SofiaApplication
from sofia_chatbot.config import Settings


SCENARIOS = {
    "equipamento": [
        "quero uma fritadeira",
        "Batata",
        "Uso alto",
        "A gas",
        "Ana",
        "Sao Paulo, SP",
    ],
    "projeto": [
        "Vou montar uma cozinha",
        "Montando",
        "Restaurante",
        "Em 1 a 3 meses",
        "Bruno",
        "Rio de Janeiro, RJ",
    ],
    "pos_venda": [
        "preciso de suporte pos venda",
        "Sim",
        "Manutencao",
        "Carla",
        "Belo Horizonte, MG",
    ],
    "fornecedor": [
        "sou fornecedor",
        "Empresa Exemplo",
        "Fornecedor",
        "Diego",
        "Curitiba, PR",
    ],
    "compras_online": [
        "comprei pelo site",
        "Pedido ja feito",
        "Elisa",
        "Porto Alegre, RS",
    ],
}


def whatsapp_payload(text: str, message_id: str, phone: str) -> dict:
    return {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "waba-homologacao",
                "changes": [
                    {
                        "field": "messages",
                        "value": {
                            "messaging_product": "whatsapp",
                            "contacts": [{"profile": {"name": "Teste"}, "wa_id": phone}],
                            "messages": [
                                {
                                    "from": phone,
                                    "id": message_id,
                                    "timestamp": "0",
                                    "type": "text",
                                    "text": {"body": text},
                                }
                            ],
                        },
                    }
                ],
            }
        ],
    }


def maxbot_payload(text: str, message_id: str, phone: str) -> dict:
    return {
        "origin": "2",
        "contact": {
            "id": phone,
            "name": "Teste",
            "surname": "Homologacao",
            "whatsapp": phone,
            "segmentation": ["SOFIA_API_PILOTO"],
            "in_attendance": "0",
            "current_protocol": "",
            "current_attendant": "",
        },
        "msg_id": message_id,
        "msg_timestamp": "0",
        "msg_date": "1970-01-01 00:00:00",
        "msg": text,
        "type": "T",
    }


def comparable(reply: dict) -> tuple:
    return (
        reply.get("next_block"),
        reply.get("status"),
        tuple(reply.get("options") or []),
        tuple(reply.get("tags") or []),
    )


def run() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        direct = SofiaApplication(
            Settings(
                sqlite_path=str(base / "direct-sessions.db"),
                event_log_path=str(base / "direct-events.db"),
            )
        )
        meta = SofiaApplication(
            Settings(
                sqlite_path=str(base / "meta-sessions.db"),
                event_log_path=str(base / "meta-events.db"),
            )
        )
        maxbot = SofiaApplication(
            Settings(
                sqlite_path=str(base / "maxbot-sessions.db"),
                event_log_path=str(base / "maxbot-events.db"),
            )
        )

        checked = 0
        for scenario_index, (name, messages) in enumerate(SCENARIOS.items(), start=1):
            direct_session = f"direto-{name}"
            phone = f"553199990{scenario_index:04d}"
            # Normaliza o canal direto com o mesmo telefone que Meta e Maxbot
            # fornecem automaticamente no webhook. O fluxo local sem telefone
            # continua coberto separadamente pelos testes unitarios.
            direct_state = direct.store.get(direct_session)
            direct_state.lead.telefone_whatsapp = phone
            direct.store.save(direct_state)
            for message_index, message in enumerate(messages, start=1):
                direct_reply = direct.chat(direct_session, message)
                result = meta.whatsapp_webhook(
                    whatsapp_payload(message, f"{name}-{message_index}", phone)
                )
                meta_reply = result["processed"][0]["reply"]
                maxbot_result = maxbot.maxbot_webhook(
                    maxbot_payload(message, f"maxbot-{name}-{message_index}", phone)
                )
                maxbot_reply = maxbot_result["processed"][0]["reply"]
                expected = comparable(direct_reply)
                if expected != comparable(meta_reply):
                    raise AssertionError(
                        f"Divergencia Meta em {name}, mensagem {message_index}: "
                        f"{expected!r} != {comparable(meta_reply)!r}"
                    )
                if expected != comparable(maxbot_reply):
                    raise AssertionError(
                        f"Divergencia Maxbot em {name}, mensagem {message_index}: "
                        f"{expected!r} != {comparable(maxbot_reply)!r}"
                    )
                checked += 1

        print(
            f"Homologacao OK: {len(SCENARIOS)} cenarios e "
            f"{checked} interacoes equivalentes nos tres canais."
        )


if __name__ == "__main__":
    run()
