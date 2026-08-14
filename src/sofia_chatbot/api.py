import hmac
import json
import os
import signal
import sys
import threading
import traceback
from copy import deepcopy
from json import JSONDecodeError
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse
from typing import Any

from sofia_chatbot.channels.whatsapp import (
    WhatsAppCloudClient,
    WhatsAppReplyRenderer,
    WhatsAppWebhookParser,
    verify_meta_signature,
)
from sofia_chatbot.channels.maxbot import (
    MaxbotClient,
    MaxbotReplyRenderer,
    MaxbotWebhookParser,
    is_maxbot_pilot_eligible,
    verify_maxbot_webhook_path,
)
from sofia_chatbot.config import Settings
from sofia_chatbot.domain import ConversationStatus
from sofia_chatbot.event_log import create_event_logger
from sofia_chatbot.flow import SofiaFlow
from sofia_chatbot.llm.factory import create_llm_client
from sofia_chatbot.session_store import create_session_store


class SofiaApplication:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.store = create_session_store(settings.session_store, settings.sqlite_path)
        self.event_logger = create_event_logger(settings.event_log_enabled, settings.event_log_path)
        self.flow = SofiaFlow(create_llm_client(settings))
        self.whatsapp_parser = WhatsAppWebhookParser()
        self.whatsapp_renderer = WhatsAppReplyRenderer()
        self.whatsapp_client = WhatsAppCloudClient(settings)
        self.maxbot_parser = MaxbotWebhookParser()
        self.maxbot_renderer = MaxbotReplyRenderer()
        self.maxbot_client = MaxbotClient(settings)

    def chat(self, session_id: str, message: str) -> dict[str, Any]:
        state = self.store.get(session_id)
        reply = self.flow.handle(state, message)
        self.store.save(state)
        response = {
            "session_id": session_id,
            "message": reply.message,
            "options": reply.options,
            "status": reply.status.value,
            "summary": reply.summary,
            "tags": reply.tags,
            "next_block": reply.next_block,
        }
        self.event_logger.log(
            "chat",
            session_id,
            {
                "inbound": message,
                "reply": response,
                "current_block": state.current_block,
                "status": state.status.value,
            },
        )
        return response

    def reset(self, session_id: str) -> dict[str, Any]:
        self.store.reset(session_id)
        return {"session_id": session_id, "status": "reset"}

    def debug_session(self, session_id: str) -> dict[str, Any]:
        state = self.store.get(session_id)
        return {
            "session_id": state.session_id,
            "current_block": state.current_block,
            "status": state.status.value,
            "tags": sorted(state.tags),
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

    def debug_events(self, session_id: str | None = None, limit: int = 20) -> dict[str, Any]:
        return {
            "events": self.event_logger.list_events(session_id=session_id, limit=limit),
        }

    def verify_whatsapp_webhook(self, mode: str, token: str, challenge: str) -> tuple[int, str]:
        expected = self.settings.whatsapp_verify_token
        if (
            mode == "subscribe"
            and token
            and expected
            and hmac.compare_digest(token.encode("utf-8"), expected.encode("utf-8"))
        ):
            return 200, challenge
        return 403, "Forbidden"

    def whatsapp_webhook(self, payload: dict[str, Any]) -> dict[str, Any]:
        inbound_messages = self.whatsapp_parser.parse_messages(payload)
        processed: list[dict[str, Any]] = []
        duplicates: list[dict[str, Any]] = []
        errors: list[dict[str, Any]] = []

        for inbound in inbound_messages:
            is_new = self.event_logger.mark_message_processed("whatsapp", inbound.message_id, inbound.session_id)
            if not is_new:
                duplicate_payload = {
                    "message_id": inbound.message_id,
                    "from": inbound.from_number,
                    "text": inbound.text,
                    "ignored_reason": "duplicate_message",
                }
                self.event_logger.log("whatsapp_duplicate", inbound.session_id, duplicate_payload)
                duplicates.append(duplicate_payload)
                continue

            try:
                state = self.store.get(inbound.session_id)
                if not state.lead.telefone_whatsapp:
                    state.lead.telefone_whatsapp = inbound.from_number
                reply = self.flow.handle(state, inbound.text)
                self.store.save(state)
                outbound_payload = self.whatsapp_renderer.render(inbound.from_number, reply)
                send_result = self.whatsapp_client.send_message(outbound_payload)
            except Exception as exc:
                # Falha depois da marcacao de duplicidade: desfaz a marcacao
                # para que o retry da Meta consiga reprocessar a mensagem.
                self.event_logger.unmark_message_processed("whatsapp", inbound.message_id)
                self.event_logger.log(
                    "whatsapp_error",
                    inbound.session_id,
                    {
                        "message_id": inbound.message_id,
                        "from": inbound.from_number,
                        "error": f"{type(exc).__name__}: {exc}",
                    },
                )
                errors.append({"message_id": inbound.message_id, "error": "processing_failed"})
                continue
            event_payload = {
                "message_id": inbound.message_id,
                "from": inbound.from_number,
                "text": inbound.text,
                "message_type": inbound.message_type,
                "reply": {
                    "message": reply.message,
                    "options": reply.options,
                    "status": reply.status.value,
                    "summary": reply.summary,
                    "tags": reply.tags,
                    "next_block": reply.next_block,
                },
                "outbound": send_result,
                "current_block": state.current_block,
                "status": state.status.value,
            }
            self.event_logger.log("whatsapp_message", inbound.session_id, event_payload)
            processed.append(event_payload)

        return {
            "ok": True,
            "processed": processed,
            "duplicates": duplicates,
            "errors": errors,
            "ignored": len(inbound_messages) == 0,
        }

    def maxbot_webhook(self, payload: dict[str, Any]) -> dict[str, Any]:
        inbound_messages = self.maxbot_parser.parse_messages(payload)
        processed: list[dict[str, Any]] = []
        duplicates: list[dict[str, Any]] = []
        ignored: list[dict[str, Any]] = []
        errors: list[dict[str, Any]] = []

        for inbound in inbound_messages:
            is_new = self.event_logger.mark_message_processed(
                "maxbot", inbound.message_id, inbound.session_id
            )
            if not is_new:
                duplicate_payload = {
                    "message_id": inbound.message_id,
                    "from": inbound.from_number,
                    "ignored_reason": "duplicate_message",
                }
                self.event_logger.log(
                    "maxbot_duplicate", inbound.session_id, duplicate_payload
                )
                duplicates.append(duplicate_payload)
                continue

            attendance_pilot_override = bool(
                inbound.in_attendance
                and self.settings.maxbot_pilot_mode
                and self.settings.maxbot_pilot_allow_attendance
                and inbound.protocol_id
                and is_maxbot_pilot_eligible(self.settings, inbound)
            )

            if inbound.in_attendance and not attendance_pilot_override:
                ignored_payload = {
                    "message_id": inbound.message_id,
                    "from": inbound.from_number,
                    "ignored_reason": "human_attendance",
                    "current_protocol": inbound.current_protocol,
                    "current_attendant": inbound.current_attendant,
                    "protocol_id": inbound.protocol_id,
                    "chat_id": inbound.chat_id,
                }
                self.event_logger.log(
                    "maxbot_human_attendance", inbound.session_id, ignored_payload
                )
                ignored.append(ignored_payload)
                continue

            if not is_maxbot_pilot_eligible(self.settings, inbound):
                ignored_payload = {
                    "message_id": inbound.message_id,
                    "from": inbound.from_number,
                    "ignored_reason": "pilot_not_allowed",
                }
                self.event_logger.log(
                    "maxbot_pilot_filtered", inbound.session_id, ignored_payload
                )
                ignored.append(ignored_payload)
                continue

            try:
                # A copia evita avancar a sessao em memoria se o envio falhar.
                # A sessao so e confirmada depois de o Maxbot aceitar a saida.
                state = deepcopy(self.store.get(inbound.session_id))
                if not state.lead.telefone_whatsapp:
                    state.lead.telefone_whatsapp = inbound.from_number
                if state.status == ConversationStatus.HANDOFF:
                    ignored_payload = {
                        "message_id": inbound.message_id,
                        "from": inbound.from_number,
                        "ignored_reason": "handoff_pending",
                        "current_block": state.current_block,
                    }
                    self.event_logger.log(
                        "maxbot_handoff_pending",
                        inbound.session_id,
                        ignored_payload,
                    )
                    ignored.append(ignored_payload)
                    continue
                resolved_text = self.flow.resolve_numbered_input(state, inbound.text)
                reply = self.flow.handle(state, resolved_text)
                # O protocolo automatico do Maxbot pode existir sem atendente
                # atribuido. Nesse caso, send_chat_msg e recusado; o piloto usa
                # o envio normal ao contato, ainda protegido pela allowlist.
                outbound_payload = self.maxbot_renderer.render(
                    inbound.from_number, reply
                )
                send_result = self.maxbot_client.send_message(outbound_payload)
                self.store.save(state)
            except Exception as exc:
                self.event_logger.unmark_message_processed(
                    "maxbot", inbound.message_id
                )
                self.event_logger.log(
                    "maxbot_error",
                    inbound.session_id,
                    {
                        "message_id": inbound.message_id,
                        "from": inbound.from_number,
                        "error": f"{type(exc).__name__}: {exc}",
                    },
                )
                errors.append(
                    {"message_id": inbound.message_id, "error": "processing_failed"}
                )
                continue

            event_payload = {
                "message_id": inbound.message_id,
                "from": inbound.from_number,
                "text": inbound.text,
                "resolved_text": resolved_text,
                "message_type": inbound.message_type,
                "origin": inbound.origin,
                "ownership": (
                    "human_pending"
                    if state.status == ConversationStatus.HANDOFF
                    else "bot_active"
                ),
                "reply": {
                    "message": reply.message,
                    "options": reply.options,
                    "status": reply.status.value,
                    "summary": reply.summary,
                    "tags": reply.tags,
                    "next_block": reply.next_block,
                },
                "outbound": send_result,
                "current_block": state.current_block,
                "status": state.status.value,
            }
            self.event_logger.log(
                "maxbot_message", inbound.session_id, event_payload
            )
            processed.append(event_payload)

        return {
            "ok": True,
            "processed": processed,
            "duplicates": duplicates,
            "ignored": ignored,
            "errors": errors,
            "unsupported": len(inbound_messages) == 0,
        }


class PayloadTooLarge(Exception):
    pass


def create_handler(app: SofiaApplication) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            parsed = urlparse(self.path)
            if parsed.path in {"/", "/tester"}:
                if not app.settings.local_api_enabled:
                    self.send_error(404)
                    return
                body = (Path(__file__).with_name("tester.html")).read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            if parsed.path == "/health":
                self._json({"ok": True})
                return
            if parsed.path == "/debug/session":
                if not app.settings.debug_endpoints_enabled:
                    self.send_error(404)
                    return
                query = parse_qs(parsed.query)
                session_id = query.get("session_id", query.get("id", [""]))[0]
                if not session_id:
                    self._json({"error": "session_id obrigatorio"}, status=400)
                    return
                self._json(app.debug_session(session_id))
                return
            if parsed.path == "/debug/events":
                if not app.settings.debug_endpoints_enabled:
                    self.send_error(404)
                    return
                query = parse_qs(parsed.query)
                session_id = query.get("session_id", [""])[0] or None
                limit_raw = query.get("limit", ["20"])[0]
                try:
                    limit = int(limit_raw)
                except ValueError:
                    limit = 20
                self._json(app.debug_events(session_id=session_id, limit=limit))
                return
            if parsed.path == "/webhook/whatsapp":
                query = parse_qs(parsed.query)
                status, body = app.verify_whatsapp_webhook(
                    mode=query.get("hub.mode", [""])[0],
                    token=query.get("hub.verify_token", [""])[0],
                    challenge=query.get("hub.challenge", [""])[0],
                )
                self._text(body, status=status)
                return
            self.send_error(404)

        def do_POST(self) -> None:
            try:
                parsed = urlparse(self.path)
                raw_body, payload = self._read_json_with_raw_body()
                session_id = str(payload.get("session_id", "default"))

                if parsed.path == "/reset":
                    if not app.settings.local_api_enabled:
                        self.send_error(404)
                        return
                    self._json(app.reset(session_id))
                    return
                if parsed.path == "/chat":
                    if not app.settings.local_api_enabled:
                        self.send_error(404)
                        return
                    message = str(payload.get("message", ""))
                    if not message.strip():
                        self._json({"error": "message obrigatoria"}, status=400)
                        return
                    self._json(app.chat(session_id, message))
                    return
                if parsed.path == "/webhook/whatsapp":
                    if not verify_meta_signature(
                        app.settings.whatsapp_app_secret,
                        raw_body,
                        self.headers.get("X-Hub-Signature-256"),
                    ):
                        self._json({"ok": False, "error": "invalid_signature"}, status=403)
                        return
                    result = app.whatsapp_webhook(payload)
                    # Resposta minima: nao ecoa texto de resposta, resumo nem
                    # dados de lead para quem chamou o webhook.
                    # Falhas transitorias precisam de status nao-2xx para que
                    # a Meta reenvie a mensagem que foi desmarcada.
                    status = 500 if result["errors"] else 200
                    self._json(
                        {
                            "ok": result["ok"] and not result["errors"],
                            "processed": len(result["processed"]),
                            "duplicates": len(result["duplicates"]),
                            "errors": len(result["errors"]),
                        },
                        status=status,
                    )
                    return
                if verify_maxbot_webhook_path(
                    app.settings.maxbot_webhook_secret, parsed.path
                ):
                    result = app.maxbot_webhook(payload)
                    status = 500 if result["errors"] else 200
                    self._json(
                        {
                            "ok": result["ok"] and not result["errors"],
                            "processed": len(result["processed"]),
                            "duplicates": len(result["duplicates"]),
                            "ignored": len(result["ignored"])
                            + int(result["unsupported"]),
                            "errors": len(result["errors"]),
                        },
                        status=status,
                    )
                    return

                self.send_error(404)
            except Exception as exc:
                if isinstance(exc, PayloadTooLarge):
                    self._json({"error": "payload_muito_grande"}, status=413)
                    return
                if isinstance(exc, JSONDecodeError):
                    self._json({"error": "json invalido"}, status=400)
                    return
                # Nao vaza detalhes internos na resposta HTTP.
                traceback.print_exc()
                self._json({"error": "erro_interno"}, status=500)

        def _read_json(self) -> dict[str, Any]:
            _, payload = self._read_json_with_raw_body()
            return payload

        MAX_BODY_BYTES = 1_000_000
        DRAIN_CAP_BYTES = 16_000_000
        timeout = 30

        def _read_json_with_raw_body(self) -> tuple[bytes, dict[str, Any]]:
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                raise PayloadTooLarge("Content-Length invalido")
            if length < 0 or length > self.MAX_BODY_BYTES:
                # Consome (com limite) o corpo declarado antes de responder,
                # para o cliente nao receber um broken pipe no meio do envio.
                self._drain_body(length)
                self.close_connection = True
                raise PayloadTooLarge("corpo excede o limite")
            raw_body = self.rfile.read(length) if length else b"{}"
            return raw_body, json.loads(raw_body.decode("utf-8"))

        def _drain_body(self, length: int) -> None:
            remaining = min(max(length, 0), self.DRAIN_CAP_BYTES)
            try:
                while remaining > 0:
                    chunk = self.rfile.read(min(65536, remaining))
                    if not chunk:
                        break
                    remaining -= len(chunk)
            except OSError:
                pass

        def _json(self, payload: dict[str, Any], status: int = 200) -> None:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _text(self, payload: str, status: int = 200) -> None:
            body = payload.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format: str, *args: Any) -> None:
            return

    return Handler


def configurar_saida_sem_buffer() -> None:
    """Faz a saida sair linha a linha em vez de ficar presa no buffer.

    Quando o processo roda sob systemd, Docker ou qualquer supervisor, o
    `stdout` e um pipe e o Python passa a usar buffer de bloco: as mensagens so
    aparecem quando o buffer enche ou quando o processo morre. Na pratica, o
    servico parece nao registrar nada enquanto esta no ar, que e exatamente
    quando precisamos ler o log.
    """
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(line_buffering=True)
        except (AttributeError, ValueError):
            # Substituido por um dublê em teste, ou ja fechado. Sem impacto.
            continue


def create_server(app: SofiaApplication, settings: Settings) -> ThreadingHTTPServer:
    server = ThreadingHTTPServer((settings.host, settings.port), create_handler(app))
    # Sem isso as threads sao daemon e morrem junto com o processo. Como a
    # mensagem e marcada como processada ANTES do envio, um deploy no momento
    # errado descartaria a mensagem sem responder e sem registrar erro.
    # Esperando as requisicoes em voo, o encerramento fica previsivel.
    server.daemon_threads = False
    server.block_on_close = True
    return server


def install_shutdown_handlers(server: ThreadingHTTPServer) -> bool:
    """Encerra o servidor ao receber SIGTERM (deploy/restart) ou SIGINT."""

    def parar(signum: int, frame: Any) -> None:
        # `shutdown()` bloqueia ate o `serve_forever()` sair, entao nao pode
        # ser chamado de dentro do proprio handler de sinal.
        threading.Thread(target=server.shutdown, daemon=True).start()

    try:
        signal.signal(signal.SIGTERM, parar)
        signal.signal(signal.SIGINT, parar)
    except ValueError:
        # Sinais so podem ser registrados na thread principal. Em teste ou
        # embutido em outro processo, seguir sem eles e aceitavel.
        return False
    return True


def run_server(settings: Settings) -> None:
    configurar_saida_sem_buffer()
    app = SofiaApplication(settings)
    if settings.env_file:
        print(f"Configuracao carregada de: {settings.env_file}")
    else:
        print(
            "AVISO: nenhum arquivo .env encontrado. A aplicacao esta usando "
            "somente variaveis de ambiente e valores padrao. Sem "
            "MAXBOT_WEBHOOK_SECRET o webhook responde 404 a tudo e a Sofia "
            "fica muda. Use SOFIA_ENV_FILE para apontar o arquivo."
        )
    print(f"Sessoes em: {settings.sqlite_path}")
    if settings.event_log_enabled:
        print(f"Log de eventos em: {settings.event_log_path}")
    if os.environ.get("PORT") and settings.host in {"127.0.0.1", "localhost"}:
        print(
            "AVISO: a variavel PORT esta definida (padrao de plataforma "
            "gerenciada), mas o servidor esta ouvindo apenas em "
            f"{settings.host}. Em container, use SOFIA_HOST=0.0.0.0. "
            "Atras de um proxy reverso na mesma maquina, o padrao esta certo."
        )
    if settings.whatsapp_send_messages and not settings.whatsapp_app_secret:
        print(
            "AVISO: WHATSAPP_SEND_MESSAGES=true sem WHATSAPP_APP_SECRET. "
            "Sem o app secret a assinatura do webhook nao e verificada."
        )
    if settings.debug_endpoints_enabled:
        print("AVISO: endpoints de debug habilitados. Nao expor publicamente.")
    if settings.local_api_enabled and settings.whatsapp_send_messages:
        print(
            "AVISO: /chat e /reset estao habilitados (LOCAL_API_ENABLED=true). "
            "Em endpoint publico, desabilite ou proteja esses endpoints."
        )
    if settings.maxbot_send_messages and not settings.maxbot_webhook_secret:
        print(
            "AVISO: MAXBOT_SEND_MESSAGES=true sem MAXBOT_WEBHOOK_SECRET. "
            "O webhook Maxbot permanecera inacessivel ate configurar o segredo."
        )
    if settings.maxbot_send_messages and not settings.maxbot_api_token:
        print(
            "AVISO: MAXBOT_SEND_MESSAGES=true sem MAXBOT_API_TOKEN. "
            "Os envios falharao ate configurar o token por variavel de ambiente."
        )
    if settings.local_api_enabled and settings.maxbot_send_messages:
        print(
            "AVISO: /chat e /reset estao habilitados (LOCAL_API_ENABLED=true). "
            "Em endpoint publico, desabilite ou proteja esses endpoints."
        )
    if settings.maxbot_send_messages and not settings.maxbot_pilot_mode:
        print(
            "AVISO: MAXBOT_PILOT_MODE=false com envio real. "
            "Todos os contatos fora de atendimento humano ficam elegiveis."
        )
    if (
        settings.maxbot_send_messages
        and settings.maxbot_pilot_mode
        and not settings.maxbot_pilot_segment.strip()
        and not settings.maxbot_pilot_phones
    ):
        print(
            "AVISO: piloto Maxbot sem segmento nem telefones autorizados. "
            "Nenhum contato recebera resposta da Sofia."
        )
    server = create_server(app, settings)
    install_shutdown_handlers(server)
    print(f"Sofia rodando em http://{settings.host}:{settings.port}")
    try:
        server.serve_forever()
    finally:
        server.server_close()
        print("Sofia encerrada com as requisicoes em voo concluidas.")
