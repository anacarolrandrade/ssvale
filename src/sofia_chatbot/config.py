from dataclasses import dataclass
import os
from pathlib import Path

# Raiz do projeto, deduzida do proprio arquivo:
# <raiz>/src/sofia_chatbot/config.py -> sobe tres niveis.
#
# Serve para que `.env` e os bancos em `data/` sejam encontrados
# independentemente do diretorio de onde o processo foi iniciado. Sem isso, a
# aplicacao sobe com configuracao vazia quando o servico e iniciado de outro
# diretorio (o caso do systemd), o webhook passa a responder 404 e a Sofia fica
# muda sem registrar nenhum erro.
PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Settings:
    llm_provider: str = "mock"
    llm_base_url: str = ""
    llm_api_key: str = ""
    llm_model: str = ""
    session_store: str = "sqlite"
    sqlite_path: str = "data/sofia_sessions.db"
    event_log_enabled: bool = True
    event_log_path: str = "data/sofia_events.db"
    debug_endpoints_enabled: bool = False
    local_api_enabled: bool = True
    whatsapp_verify_token: str = ""
    whatsapp_access_token: str = ""
    whatsapp_app_secret: str = ""
    whatsapp_phone_number_id: str = ""
    whatsapp_api_version: str = "v20.0"
    whatsapp_send_messages: bool = False
    maxbot_api_token: str = ""
    maxbot_channel_token: str = ""
    maxbot_webhook_secret: str = ""
    maxbot_pilot_mode: bool = True
    maxbot_pilot_segment: str = "SOFIA_API_PILOTO"
    maxbot_pilot_phones: tuple[str, ...] = ()
    maxbot_pilot_allow_attendance: bool = False
    maxbot_send_messages: bool = False
    maxbot_api_url: str = "https://app.maxbot.com.br/api/v1.php"
    # Timeout do envio ao Maxbot. O envio acontece dentro do handler do
    # webhook: um valor alto segura o ACK e pode provocar reenvio.
    maxbot_timeout_seconds: float = 10.0
    host: str = "127.0.0.1"
    port: int = 8000
    # Caminho do arquivo .env efetivamente carregado. Vazio quando nenhum
    # arquivo foi encontrado. Existe para o diagnostico no boot.
    env_file: str = ""


def _as_bool(value: str) -> bool:
    return value.lower().strip() in {"1", "true", "sim", "yes", "on"}


def _read_env_file(path: str | Path) -> dict[str, str]:
    env_path = Path(path)
    if not env_path.is_file():
        return {}

    values: dict[str, str] = {}
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if value[:1] == value[-1:] and value[:1] in {"'", '"'}:
            value = value[1:-1]
        if key:
            values[key] = value
    return values


def resolve_env_path(env_path: str | Path | None = None) -> Path:
    """Decide qual arquivo .env usar, sem depender do diretorio atual.

    Precedencia: argumento explicito, variavel SOFIA_ENV_FILE, `.env` na raiz
    do projeto.
    """
    if env_path is not None:
        return Path(env_path)
    from_environment = os.environ.get("SOFIA_ENV_FILE", "").strip()
    if from_environment:
        return Path(from_environment)
    return PROJECT_ROOT / ".env"


def resolve_data_path(value: str) -> str:
    """Ancora caminhos relativos de banco na raiz do projeto.

    Caminhos absolutos sao respeitados como vierem. Em producao, prefira
    absolutos (por exemplo `/var/lib/sofia/sofia_sessions.db`), fora da arvore
    de codigo, para que um deploy nao encoste nos dados.
    """
    path = Path(value)
    if path.is_absolute():
        return str(path)
    return str(PROJECT_ROOT / path)


def load_settings(env_path: str | Path | None = None) -> Settings:
    resolved_env_path = resolve_env_path(env_path)
    file_values = _read_env_file(resolved_env_path)

    def value(name: str, default: str = "") -> str:
        return os.environ.get(name, file_values.get(name, default))

    return Settings(
        llm_provider=value("LLM_PROVIDER", "mock"),
        llm_base_url=value("LLM_BASE_URL"),
        llm_api_key=value("LLM_API_KEY"),
        llm_model=value("LLM_MODEL"),
        session_store=value("SESSION_STORE", "sqlite"),
        sqlite_path=resolve_data_path(value("SQLITE_PATH", "data/sofia_sessions.db")),
        event_log_enabled=_as_bool(value("EVENT_LOG_ENABLED", "true")),
        event_log_path=resolve_data_path(
            value("EVENT_LOG_PATH", "data/sofia_events.db")
        ),
        debug_endpoints_enabled=_as_bool(value("DEBUG_ENDPOINTS_ENABLED", "false")),
        local_api_enabled=_as_bool(value("LOCAL_API_ENABLED", "true")),
        whatsapp_verify_token=value("WHATSAPP_VERIFY_TOKEN"),
        whatsapp_access_token=value("WHATSAPP_ACCESS_TOKEN"),
        whatsapp_app_secret=value("WHATSAPP_APP_SECRET"),
        whatsapp_phone_number_id=value("WHATSAPP_PHONE_NUMBER_ID"),
        whatsapp_api_version=value("WHATSAPP_API_VERSION", "v20.0"),
        whatsapp_send_messages=_as_bool(value("WHATSAPP_SEND_MESSAGES", "false")),
        maxbot_api_token=value("MAXBOT_API_TOKEN"),
        maxbot_channel_token=value("MAXBOT_CHANNEL_TOKEN"),
        maxbot_webhook_secret=value("MAXBOT_WEBHOOK_SECRET"),
        maxbot_pilot_mode=_as_bool(value("MAXBOT_PILOT_MODE", "true")),
        maxbot_pilot_segment=value("MAXBOT_PILOT_SEGMENT", "SOFIA_API_PILOTO"),
        maxbot_pilot_phones=_as_csv(value("MAXBOT_PILOT_PHONES")),
        maxbot_pilot_allow_attendance=_as_bool(
            value("MAXBOT_PILOT_ALLOW_ATTENDANCE", "false")
        ),
        maxbot_send_messages=_as_bool(value("MAXBOT_SEND_MESSAGES", "false")),
        maxbot_api_url=value("MAXBOT_API_URL", "https://app.maxbot.com.br/api/v1.php"),
        maxbot_timeout_seconds=_as_float(value("MAXBOT_TIMEOUT_SECONDS"), 10.0),
        host=value("SOFIA_HOST", "127.0.0.1"),
        # `PORT` e a convencao das plataformas gerenciadas. `SOFIA_PORT`
        # continua tendo precedencia por ser a variavel propria do projeto.
        port=_resolve_port(value("SOFIA_PORT"), value("PORT")),
        env_file=str(resolved_env_path) if resolved_env_path.is_file() else "",
    )


def _as_csv(value: str) -> tuple[str, ...]:
    return tuple(item.strip() for item in value.split(",") if item.strip())


def _as_float(value: str, default: float) -> float:
    try:
        parsed = float(value.strip())
    except (AttributeError, ValueError):
        return default
    return parsed if parsed > 0 else default


def _resolve_port(sofia_port: str, platform_port: str) -> int:
    for candidate in (sofia_port, platform_port):
        text = (candidate or "").strip()
        if not text:
            continue
        try:
            return int(text)
        except ValueError:
            continue
    return 8000
