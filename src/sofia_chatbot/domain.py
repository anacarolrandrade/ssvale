from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ConversationStatus(str, Enum):
    ACTIVE = "active"
    HANDOFF = "handoff"


@dataclass
class LeadData:
    nome_cliente: str | None = None
    telefone_whatsapp: str | None = None
    cidade_estado: str | None = None
    motivo_contato: str | None = None
    equipamento_interesse: str | None = None
    tipo_negocio: str | None = None
    previsao_compra: str | None = None
    respostas: dict[str, Any] = field(default_factory=dict)


@dataclass
class ConversationState:
    session_id: str
    current_block: str = "BLOCO_00_BOAS_VINDAS"
    tags: set[str] = field(default_factory=set)
    lead: LeadData = field(default_factory=LeadData)
    status: ConversationStatus = ConversationStatus.ACTIVE
    # Momento em que a conversa entrou em handoff, em UTC ISO-8601.
    # Base para a liberacao automatica: sem isso, a sessao so sai de handoff
    # com um script rodado a mao, e o cliente fica mudo indefinidamente.
    handoff_since: str | None = None


@dataclass(frozen=True)
class BotReply:
    message: str
    options: list[str] = field(default_factory=list)
    next_block: str | None = None
    status: ConversationStatus = ConversationStatus.ACTIVE
    summary: str | None = None
    tags: list[str] = field(default_factory=list)
