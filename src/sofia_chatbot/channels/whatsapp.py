import json
import hashlib
import hmac
import re
import urllib.request
from dataclasses import dataclass
from typing import Any

from sofia_chatbot.config import Settings
from sofia_chatbot.domain import BotReply


@dataclass(frozen=True)
class WhatsAppInboundMessage:
    message_id: str
    from_number: str
    text: str
    message_type: str
    profile_name: str | None = None

    @property
    def session_id(self) -> str:
        return self.from_number


class WhatsAppWebhookParser:
    def parse_messages(self, payload: dict[str, Any]) -> list[WhatsAppInboundMessage]:
        messages: list[WhatsAppInboundMessage] = []

        for entry in payload.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})
                contacts_by_id = self._contacts_by_id(value)

                for message in value.get("messages", []):
                    parsed = self._parse_message(message, contacts_by_id)
                    if parsed:
                        messages.append(parsed)

        return messages

    @staticmethod
    def _contacts_by_id(value: dict[str, Any]) -> dict[str, str]:
        contacts: dict[str, str] = {}
        for contact in value.get("contacts", []):
            wa_id = contact.get("wa_id")
            name = contact.get("profile", {}).get("name")
            if wa_id and name:
                contacts[wa_id] = name
        return contacts

    def _parse_message(self, message: dict[str, Any], contacts_by_id: dict[str, str]) -> WhatsAppInboundMessage | None:
        from_number = str(message.get("from", ""))
        message_id = str(message.get("id", ""))
        message_type = str(message.get("type", ""))
        text = self._extract_text(message, message_type)

        if not from_number or not message_id or not text:
            return None

        return WhatsAppInboundMessage(
            message_id=message_id,
            from_number=from_number,
            text=text,
            message_type=message_type,
            profile_name=contacts_by_id.get(from_number),
        )

    @staticmethod
    def _extract_text(message: dict[str, Any], message_type: str) -> str | None:
        if message_type == "text":
            return message.get("text", {}).get("body")
        if message_type == "button":
            button = message.get("button", {})
            return button.get("text") or button.get("payload")
        if message_type == "interactive":
            interactive = message.get("interactive", {})
            if interactive.get("type") == "button_reply":
                reply = interactive.get("button_reply", {})
                return reply.get("title") or reply.get("id")
            if interactive.get("type") == "list_reply":
                reply = interactive.get("list_reply", {})
                return reply.get("title") or reply.get("id")
        return None


class WhatsAppReplyRenderer:
    def render(self, to_number: str, reply: BotReply) -> dict[str, Any]:
        options = [option for option in reply.options if option.strip()]
        if not options:
            return self._text_message(to_number, reply.message)
        if len(options) <= 3:
            return self._button_message(to_number, reply.message, options)
        return self._list_message(to_number, reply.message, options)

    @staticmethod
    def _base(to_number: str, message_type: str) -> dict[str, Any]:
        return {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to_number,
            "type": message_type,
        }

    def _text_message(self, to_number: str, text: str) -> dict[str, Any]:
        payload = self._base(to_number, "text")
        payload["text"] = {"preview_url": False, "body": text}
        return payload

    def _button_message(self, to_number: str, text: str, options: list[str]) -> dict[str, Any]:
        payload = self._base(to_number, "interactive")
        payload["interactive"] = {
            "type": "button",
            "body": {"text": text},
            "action": {
                "buttons": [
                    {
                        "type": "reply",
                        "reply": {
                            "id": _option_id(option, index),
                            "title": _trim(option, 20),
                        },
                    }
                    for index, option in enumerate(options, start=1)
                ]
            },
        }
        return payload

    def _list_message(self, to_number: str, text: str, options: list[str]) -> dict[str, Any]:
        payload = self._base(to_number, "interactive")
        payload["interactive"] = {
            "type": "list",
            "body": {"text": text},
            "action": {
                "button": "Escolher",
                "sections": [
                    {
                        "title": "Opcoes",
                        "rows": [
                            {
                                "id": _option_id(option, index),
                                "title": _trim(option, 24),
                            }
                            for index, option in enumerate(options[:10], start=1)
                        ],
                    }
                ],
            },
        }
        return payload


class WhatsAppCloudClient:
    def __init__(self, settings: Settings) -> None:
        self.access_token = settings.whatsapp_access_token
        self.phone_number_id = settings.whatsapp_phone_number_id
        self.api_version = settings.whatsapp_api_version
        self.send_messages = settings.whatsapp_send_messages

    def send_message(self, payload: dict[str, Any]) -> dict[str, Any]:
        if not self.send_messages:
            return {"sent": False, "mode": "dry_run", "payload": payload}

        if not self.access_token or not self.phone_number_id:
            raise ValueError("WHATSAPP_ACCESS_TOKEN e WHATSAPP_PHONE_NUMBER_ID precisam estar configurados.")

        url = f"https://graph.facebook.com/{self.api_version}/{self.phone_number_id}/messages"
        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        with urllib.request.urlopen(request, timeout=30) as response:
            body = response.read().decode("utf-8")
            data = json.loads(body) if body else {}
            data["sent"] = True
            return data


def verify_meta_signature(app_secret: str, raw_body: bytes, signature_header: str | None) -> bool:
    if not app_secret:
        return True
    if not signature_header:
        return False

    try:
        algorithm, received_signature = signature_header.split("=", 1)
    except ValueError:
        return False

    if algorithm != "sha256" or not received_signature:
        return False

    expected = hmac.new(app_secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, received_signature)


def _option_id(option: str, index: int) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9_]+", "_", option.lower()).strip("_")
    if not normalized:
        return f"opt_{index}"
    return f"opt_{index}_{normalized[:40]}"


def _trim(text: str, limit: int) -> str:
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"
