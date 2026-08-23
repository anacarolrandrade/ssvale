import re
import unicodedata


def _strip_accents(text: str) -> str:
    decomposed = unicodedata.normalize("NFD", text)
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch))


def normalize_for_matching(text: str) -> str:
    """Lowercase + remove acentos, para casar padroes sem duplicar variantes."""
    return _strip_accents(text.lower())


# Padroes aplicados sobre texto normalizado (minusculo, sem acento).
# Usar \b evita falsos positivos por substring (ex.: "pagar" em "propagar",
# "pix" em "pixel", "valor" dentro de outras palavras).
_SENSITIVE_PATTERNS = [
    # Preco / valor
    r"\bquanto\s+(que\s+)?(custa|custam|fica|ficam|sai|saem|vale|valem|vem|cobra|cobram|eh?|ta|esta|estao)\b",
    r"\bquanto\s+(que\s+)?vai\s+(ficar|custar|sair)\b",
    r"\bta\s+quanto\b",
    r"\bpor\s+quanto\s+(sai|fica|custa|vende|vendem)\b",
    r"\bq(uan)?to\s+custa\b",
    r"\bcust(a|am|o|os)\b",
    r"\bprec(o|os|inho)\b",
    r"\bvalor(es|zinho)?\b",
    r"\bcotac(ao|oes)\b",
    r"\btabela\s+de\s+preco\b",
    r"\bpromoc(ao|oes)\b",
    r"\bdesconto(s)?\b",
    r"\b(mais\s+)?barat(o|a|os|as|inho|inha)\b",
    r"\bcaro\b",
    # Pagamento
    r"\bpix\b",
    r"\bboleto(s)?\b",
    r"\bcart(ao|oes)\b",
    r"\bparcel(a|as|ar|ado|ada|amento)\b",
    r"\bpagamento(s)?\b",
    r"\bpagar\b",
    r"\bcondic(ao|oes)\b",
    # Frete / retirada
    r"\bfrete(s)?\b",
    r"\bretirada\b",
    r"\bretirar\s+hoje\b",
    # Estoque / disponibilidade / prazo
    r"\bestoque\b",
    r"\bdisponi(vel|veis|bilidade)\b",
    r"\bprazo(s)?\b",
    # Orcamento
    r"\borcamento(s)?\b",
]

_SENSITIVE_REGEX = re.compile("|".join(_SENSITIVE_PATTERNS))
_DELIVERY_REGEX = re.compile(r"\bentrega(m|s)?\b|\bpronta\s+entrega\b")
_DELIVERY_REQUEST_REGEX = re.compile(
    r"\b(pronta\s+entrega|prazo\s+(de|da)\s+entrega|"
    r"(voces?|a\s+ss\s+vale)\s+(faz|fazem|tem|entrega|entregam)|"
    r"(faz|fazem|tem)\s+entrega|"
    r"(quando|onde|como)\s+(voces?\s+)?entrega(m)?|"
    r"entrega(m)?\s+(em|para|no|na|ate|hoje|amanha))\b"
)


def contains_sensitive_commercial_request(text: str, contextual_delivery: bool = False) -> bool:
    normalized = normalize_for_matching(text)
    if _SENSITIVE_REGEX.search(normalized):
        return True
    if contextual_delivery:
        return bool(_DELIVERY_REQUEST_REGEX.search(normalized))
    return bool(_DELIVERY_REGEX.search(normalized))


def commercial_limit_message() -> str:
    return (
        "Vou encaminhar seu pedido a um consultor da SS Vale para confirmar "
        "preço, disponibilidade, prazo e demais condições."
    )


def support_limit_message() -> str:
    return (
        "Eu consigo registrar sua solicitação e direcionar ao time responsável, "
        "mas não consigo fazer diagnóstico técnico por aqui."
    )
