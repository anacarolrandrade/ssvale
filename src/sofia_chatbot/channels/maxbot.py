import json
import hmac
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from sofia_chatbot.config import Settings
from sofia_chatbot.domain import BotReply

# O Maxbot espera data e hora locais. Um servidor em UTC gravaria tres horas a
# mais, o que atrapalha justamente a conferencia com o painel durante uma
# janela supervisionada.
#
# Usamos deslocamento fixo de UTC-3 em vez de `zoneinfo` de proposito: no
# Windows o `zoneinfo` exige o pacote `tzdata`, e este projeto nao tem
# dependencias externas. O Brasil nao adota horario de verao desde 2019 e o
# governo confirmou que tambem nao havera em 2026, entao o deslocamento e
# constante. Se o horario de verao voltar, este ponto precisa ser revisto.
HORARIO_DE_BRASILIA = timezone(timedelta(hours=-3), "America/Sao_Paulo")


def agora_em_brasilia() -> datetime:
    return datetime.now(HORARIO_DE_BRASILIA)


@dataclass(frozen=True)
class MaxbotInboundMessage:
    message_id: str
    from_number: str
    text: str
    message_type: str
    origin: str
    profile_name: str | None = None
    in_attendance: bool = False
    current_protocol: str | None = None
    current_attendant: str | None = None
    contact_id: str | None = None
    protocol_id: str | None = None
    chat_id: str | None = None
    segmentations: tuple[str, ...] = ()

    @property
    def session_id(self) -> str:
        return self.from_number


class MaxbotWebhookParser:
    """Converte o webhook singular do Maxbot para a entrada da Sofia."""

    def parse_messages(self, payload: dict[str, Any]) -> list[MaxbotInboundMessage]:
        if not isinstance(payload, dict):
            return []

        contact = payload.get("contact", {})
        if not isinstance(contact, dict):
            contact = {}

        # O evento "Mensagem Recebida em Atendimento" usa outro contrato:
        # whatsapp, prot_id, contact_id e chat_id ficam no nivel principal.
        attendance_event = bool(
            not contact.get("whatsapp")
            and payload.get("whatsapp")
            and (payload.get("prot_id") or payload.get("chat_id"))
        )

        message_id = str(payload.get("msg_id") or "").strip()
        from_number = str(
            contact.get("whatsapp") or payload.get("whatsapp") or ""
        ).strip()
        message_type = str(payload.get("type") or "").strip().upper()
        text = str(payload.get("msg") or "").strip()

        # O MVP conversa somente por texto. Os demais tipos podem trazer
        # metadados e midia, mas nao devem quebrar nem avancar o fluxo.
        if not message_id or not from_number or not text or message_type not in {"", "T"}:
            return []

        profile_name = " ".join(
            part.strip()
            for part in (str(contact.get("name") or ""), str(contact.get("surname") or ""))
            if part.strip()
        ) or None

        return [
            MaxbotInboundMessage(
                message_id=message_id,
                from_number=from_number,
                text=text,
                message_type=message_type or "T",
                origin=str(payload.get("origin") or ""),
                profile_name=profile_name,
                in_attendance=attendance_event
                or _as_flag(contact.get("in_attendance")),
                current_protocol=_optional_text(
                    contact.get("current_protocol") or payload.get("prot_id")
                ),
                current_attendant=_optional_text(
                    contact.get("current_attendant")
                ),
                contact_id=_optional_text(
                    contact.get("id") or payload.get("contact_id")
                ),
                protocol_id=_optional_text(payload.get("prot_id")),
                chat_id=_optional_text(payload.get("chat_id")),
                segmentations=_parse_segmentations(contact.get("segmentation")),
            )
        ]


class MaxbotReplyRenderer:
    """Renderiza respostas interativas como texto numerado."""

    def render(self, to_number: str, reply: BotReply) -> dict[str, Any]:
        return {
            "cmd": "send_text",
            "ct_whatsapp": to_number,
            "msg": self._render_text(reply),
        }

    def render_attendance(self, protocol_id: str, reply: BotReply) -> dict[str, Any]:
        return {
            "cmd": "send_chat_msg",
            "prot_id": protocol_id,
            "msg": self._render_text(reply),
            "msg_date_sql": agora_em_brasilia().strftime("%Y-%m-%d %H:%M:%S"),
        }

    @staticmethod
    def _render_text(reply: BotReply) -> str:
        text = reply.message.strip()
        options = [option.strip() for option in reply.options if option.strip()]
        if options:
            numbered = "\n".join(
                f"{index} - {option}" for index, option in enumerate(options, start=1)
            )
            text = f"{text}\n\n{numbered}" if text else numbered

        return text


class MaxbotAPIError(RuntimeError):
    pass


class MaxbotRateLimitError(MaxbotAPIError):
    pass


class MaxbotClient:
    def __init__(self, settings: Settings) -> None:
        self.api_token = settings.maxbot_api_token
        self.channel_token = settings.maxbot_channel_token
        self.api_url = settings.maxbot_api_url
        self.send_messages = settings.maxbot_send_messages
        self.timeout_seconds = settings.maxbot_timeout_seconds

    def send_text(self, to_number: str, text: str) -> dict[str, Any]:
        return self.send_message(
            {"cmd": "send_text", "ct_whatsapp": to_number, "msg": text}
        )

    def send_message(self, payload: dict[str, Any]) -> dict[str, Any]:
        command = str(payload.get("cmd", "send_text"))
        if command == "send_chat_msg":
            safe_payload = {
                "cmd": command,
                "prot_id": str(payload.get("prot_id", "")),
                "msg": str(payload.get("msg", "")),
                "msg_date_sql": str(payload.get("msg_date_sql", "")),
            }
        elif command == "send_text":
            safe_payload = {
                "cmd": command,
                "ct_whatsapp": str(payload.get("ct_whatsapp", "")),
                "msg": str(payload.get("msg", "")),
            }
        else:
            raise ValueError("Comando Maxbot nao permitido pelo adaptador.")
        if not self.send_messages:
            return {"sent": False, "mode": "dry_run", "payload": safe_payload}

        if not self.api_token:
            raise ValueError("MAXBOT_API_TOKEN precisa estar configurado.")

        request_payload = {"token": self.api_token, **safe_payload}
        if self.channel_token and command == "send_text":
            request_payload["channel_token"] = self.channel_token

        request = urllib.request.Request(
            self.api_url,
            data=json.dumps(request_payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(
                request, timeout=self.timeout_seconds
            ) as response:
                body = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            if exc.code == 429:
                raise MaxbotRateLimitError("Limite de requisicoes do Maxbot atingido.") from exc
            raise MaxbotAPIError(f"Maxbot respondeu com HTTP {exc.code}.") from exc
        except urllib.error.URLError as exc:
            raise MaxbotAPIError("Falha de comunicacao com o Maxbot.") from exc

        try:
            data = json.loads(body) if body else {}
        except json.JSONDecodeError as exc:
            raise MaxbotAPIError("Maxbot retornou uma resposta invalida.") from exc

        status = _status_number(data.get("status"))
        if status == 0:
            raise MaxbotAPIError("Maxbot recusou o envio da mensagem.")
        if status not in {1, 2}:
            raise MaxbotAPIError("Maxbot retornou um status desconhecido.")

        return {
            "sent": True,
            "status": status,
            "processing": status == 2,
            "message": str(data.get("msg", "")),
        }


def verify_maxbot_webhook_path(webhook_secret: str, path: str) -> bool:
    """Valida o segredo no caminho sem aceitar rota desprotegida."""
    if not webhook_secret:
        return False
    prefix = "/webhook/maxbot/"
    if not path.startswith(prefix):
        return False
    supplied = path[len(prefix) :]
    if not supplied or "/" in supplied:
        return False
    return hmac.compare_digest(
        supplied.encode("utf-8"), webhook_secret.encode("utf-8")
    )


def is_maxbot_pilot_eligible(
    settings: Settings, inbound: MaxbotInboundMessage
) -> bool:
    if not settings.maxbot_pilot_mode:
        return True

    inbound_phone = _digits_only(inbound.from_number)
    allowed_phones = {
        normalized
        for phone in settings.maxbot_pilot_phones
        if (normalized := _digits_only(phone))
    }
    if inbound_phone and inbound_phone in allowed_phones:
        return True

    target_segment = settings.maxbot_pilot_segment.strip().casefold()
    if target_segment and any(
        segment.strip().casefold() == target_segment
        for segment in inbound.segmentations
    ):
        return True
    return False


def _as_flag(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "sim", "yes", "on"}


def _optional_text(value: Any) -> str | None:
    text = str(value or "").strip()
    return text or None


def _status_number(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _parse_segmentations(value: Any) -> tuple[str, ...]:
    if not value:
        return ()
    items = value if isinstance(value, (list, tuple, set)) else [value]
    parsed: list[str] = []
    for item in items:
        if isinstance(item, dict):
            text = str(item.get("title") or item.get("name") or "").strip()
        else:
            text = str(item).strip()
        if text:
            parsed.append(text)
    return tuple(parsed)


def _digits_only(value: str) -> str:
    return "".join(character for character in value if character.isdigit())
