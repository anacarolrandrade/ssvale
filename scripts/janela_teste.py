"""Apoio operacional as janelas curtas de teste real do Maxbot.

O objetivo e ter "contadores limpos" sem apagar dados: em vez de expurgar o log
de eventos (que contem PII e depende da politica de retencao da SS Vale), a
janela grava um marco (baseline) e todos os contadores passam a ser contados a
partir dele.

Subcomandos:

    preflight   Confere flags de seguranca, segredo/token e sessoes residuais.
    baseline    Marca o inicio da janela (ultimo id de evento conhecido).
    status      Mostra os contadores e o veredito desde o baseline.
    encerrar    Confere o estado seguro depois da janela.

Nenhum subcomando altera sessoes ou envia mensagens. O reset de sessao continua
sendo feito por `scripts/resetar_sessao.py --confirmar`.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sofia_chatbot.config import Settings, load_settings  # noqa: E402

BASELINE_PATH = ROOT / ".runtime" / "janela-teste.json"

# Flags que precisam estar nesses valores antes de qualquer janela.
FLAGS_ESPERADAS_PREFLIGHT = {
    "maxbot_send_messages": False,
    "maxbot_pilot_allow_attendance": False,
    "maxbot_pilot_mode": True,
    "whatsapp_send_messages": False,
    "local_api_enabled": False,
    "debug_endpoints_enabled": False,
}

# Estado seguro obrigatorio ao encerrar a janela.
FLAGS_ESPERADAS_ENCERRAMENTO = {
    "maxbot_send_messages": False,
    "maxbot_pilot_allow_attendance": False,
}

EVENTOS_CRITICOS = ("maxbot_error",)
EVENTOS_DE_ATENCAO = ("maxbot_duplicate", "maxbot_human_attendance")


def mascarar(valor: str) -> str:
    """Reduz um telefone/session_id aos quatro ultimos digitos."""
    texto = str(valor or "")
    digitos = "".join(caractere for caractere in texto if caractere.isdigit())
    sufixo = digitos[-4:] if digitos else texto[-4:]
    return f"***{sufixo}" if sufixo else "***"


def avaliar_flags(settings: Settings, esperadas: dict[str, bool]) -> list[tuple[str, bool, bool]]:
    """Retorna (nome, valor_atual, esta_correto) para cada flag esperada."""
    resultado = []
    for nome, esperado in esperadas.items():
        atual = bool(getattr(settings, nome))
        resultado.append((nome, atual, atual == esperado))
    return resultado


def caminho_absoluto(valor: str) -> Path:
    caminho = Path(valor)
    return caminho if caminho.is_absolute() else ROOT / caminho


def carregar_settings() -> Settings:
    return load_settings(ROOT / ".env")


def _conectar_somente_leitura(caminho: Path) -> sqlite3.Connection | None:
    if not caminho.is_file():
        return None
    return sqlite3.connect(f"file:{caminho}?mode=ro", uri=True, timeout=5.0)


def sessoes_bloqueadas(settings: Settings) -> list[tuple[str, str, str]]:
    """Sessoes que impediriam a Sofia de responder no inicio da janela."""
    conexao = _conectar_somente_leitura(caminho_absoluto(settings.sqlite_path))
    if conexao is None:
        return []
    try:
        linhas = conexao.execute(
            "SELECT session_id, payload, updated_at FROM sessions"
        ).fetchall()
    except sqlite3.OperationalError:
        return []
    finally:
        conexao.close()

    bloqueadas = []
    for session_id, payload_bruto, atualizado_em in linhas:
        try:
            payload = json.loads(payload_bruto)
        except (TypeError, json.JSONDecodeError):
            payload = {}
        status = str(payload.get("status") or "")
        if status and status != "active":
            bloqueadas.append((mascarar(session_id), status, str(atualizado_em)))
    return bloqueadas


def contar_eventos(settings: Settings, desde_id: int) -> list[tuple[str, int]]:
    conexao = _conectar_somente_leitura(caminho_absoluto(settings.event_log_path))
    if conexao is None:
        return []
    try:
        return [
            (str(tipo), int(total))
            for tipo, total in conexao.execute(
                """
                SELECT event_type, COUNT(*)
                FROM events
                WHERE id > ?
                GROUP BY event_type
                ORDER BY COUNT(*) DESC
                """,
                (desde_id,),
            ).fetchall()
        ]
    except sqlite3.OperationalError:
        return []
    finally:
        conexao.close()


def ultimo_id_evento(settings: Settings) -> int:
    conexao = _conectar_somente_leitura(caminho_absoluto(settings.event_log_path))
    if conexao is None:
        return 0
    try:
        linha = conexao.execute("SELECT COALESCE(MAX(id), 0) FROM events").fetchone()
        return int(linha[0])
    except sqlite3.OperationalError:
        return 0
    finally:
        conexao.close()


def ler_baseline() -> dict | None:
    if not BASELINE_PATH.is_file():
        return None
    try:
        return json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def imprimir_flags(settings: Settings, esperadas: dict[str, bool]) -> bool:
    tudo_certo = True
    for nome, atual, correto in avaliar_flags(settings, esperadas):
        marca = "ok " if correto else "NAO"
        esperado = esperadas[nome]
        print(f"  [{marca}] {nome}={str(atual).lower()} (esperado {str(esperado).lower()})")
        tudo_certo = tudo_certo and correto
    return tudo_certo


def comando_preflight(settings: Settings) -> int:
    print("== Flags de seguranca ==")
    flags_ok = imprimir_flags(settings, FLAGS_ESPERADAS_PREFLIGHT)

    print("\n== Credenciais (sem exibir valores) ==")
    segredo = settings.maxbot_webhook_secret
    segredo_ok = len(segredo) >= 32
    print(f"  [{'ok ' if segredo_ok else 'NAO'}] MAXBOT_WEBHOOK_SECRET: {len(segredo)} caracteres (minimo 32)")
    token_ok = bool(settings.maxbot_api_token)
    print(f"  [{'ok ' if token_ok else 'NAO'}] MAXBOT_API_TOKEN: {'configurado' if token_ok else 'ausente'}")
    telefones = settings.maxbot_pilot_phones
    telefones_ok = bool(telefones)
    mascarados = ", ".join(mascarar(telefone) for telefone in telefones) or "nenhum"
    print(f"  [{'ok ' if telefones_ok else 'NAO'}] MAXBOT_PILOT_PHONES: {mascarados}")
    print(f"  [ok ] MAXBOT_PILOT_SEGMENT: {settings.maxbot_pilot_segment or 'nao configurado'}")

    print("\n== Sessoes residuais ==")
    bloqueadas = sessoes_bloqueadas(settings)
    if bloqueadas:
        for session_id, status, atualizado_em in bloqueadas:
            print(f"  [NAO] {session_id} em status {status!r} desde {atualizado_em}")
        print("  Resolva com: py scripts/resetar_sessao.py --session-id <telefone> --confirmar")
    else:
        print("  [ok ] Nenhuma sessao presa em handoff ou atendimento.")

    print("\n== Historico do log de eventos ==")
    ultimo = ultimo_id_evento(settings)
    print(f"  Ultimo id de evento: {ultimo}")
    print("  O baseline preserva esse historico; nada sera apagado.")

    aprovado = flags_ok and segredo_ok and token_ok and telefones_ok and not bloqueadas
    print("\nPreflight: " + ("APROVADO" if aprovado else "PENDENCIAS ACIMA"))
    return 0 if aprovado else 1


def comando_baseline(settings: Settings, rotulo: str) -> int:
    ultimo = ultimo_id_evento(settings)
    registro = {
        "rotulo": rotulo,
        "ultimo_id_evento": ultimo,
        "marcado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    BASELINE_PATH.parent.mkdir(parents=True, exist_ok=True)
    BASELINE_PATH.write_text(
        json.dumps(registro, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Baseline gravado em {BASELINE_PATH.relative_to(ROOT)}")
    print(f"  rotulo: {rotulo}")
    print(f"  ultimo id de evento: {ultimo}")
    print("Os contadores de `status` passam a considerar somente eventos novos.")
    return 0


def comando_status(settings: Settings) -> int:
    baseline = ler_baseline()
    if baseline is None:
        print("Nenhum baseline encontrado. Execute: py scripts/janela_teste.py baseline")
        return 1

    desde_id = int(baseline.get("ultimo_id_evento", 0))
    print(f"Baseline: {baseline.get('rotulo')} (id {desde_id}, {baseline.get('marcado_em')})")

    contagens = contar_eventos(settings, desde_id)
    if not contagens:
        print("Nenhum evento novo desde o baseline.")
    else:
        print("\n== Eventos desde o baseline ==")
        for tipo, total in contagens:
            print(f"  {tipo:26} {total}")

    mapa = dict(contagens)
    criticos = sum(mapa.get(tipo, 0) for tipo in EVENTOS_CRITICOS)
    atencao = {tipo: mapa.get(tipo, 0) for tipo in EVENTOS_DE_ATENCAO if mapa.get(tipo)}

    print("\n== Veredito ==")
    print(f"  maxbot_error desde o baseline: {criticos}")
    for tipo, total in atencao.items():
        print(f"  {tipo}: {total} (esperado apenas nos cenarios que testam isso)")
    print("  " + ("SEM ERROS" if criticos == 0 else "INTERROMPER A JANELA"))
    return 0 if criticos == 0 else 1


def comando_encerrar(settings: Settings) -> int:
    print("== Estado seguro pos-janela ==")
    flags_ok = imprimir_flags(settings, FLAGS_ESPERADAS_ENCERRAMENTO)

    print("\n== Sessoes que ficaram bloqueadas ==")
    bloqueadas = sessoes_bloqueadas(settings)
    if bloqueadas:
        for session_id, status, atualizado_em in bloqueadas:
            print(f"  {session_id} em status {status!r} desde {atualizado_em}")
        print("  Reset individual e manual, apos confirmar o fim do atendimento humano.")
    else:
        print("  Nenhuma.")

    print("\nLembretes manuais (nao verificaveis por aqui):")
    print("  - restaurar a mensagem de boas-vindas e os tres itens do menu principal;")
    print("  - confirmar com uma mensagem de teste que somente o menu responde;")
    print("  - registrar horario, resultado e incidentes no checklist da janela.")

    print("\nEncerramento: " + ("ESTADO SEGURO" if flags_ok else "CORRIGIR AS FLAGS ACIMA"))
    return 0 if flags_ok else 1


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    subparsers = parser.add_subparsers(dest="comando", required=True)
    subparsers.add_parser("preflight", help="Confere flags, credenciais e sessoes residuais")
    parser_baseline = subparsers.add_parser("baseline", help="Marca o inicio da janela")
    parser_baseline.add_argument(
        "--rotulo",
        default=f"janela-{datetime.now().strftime('%Y-%m-%d')}",
        help="Identificacao da janela",
    )
    subparsers.add_parser("status", help="Contadores desde o baseline")
    subparsers.add_parser("encerrar", help="Confere o estado seguro pos-janela")

    args = parser.parse_args()
    settings = carregar_settings()

    if args.comando == "preflight":
        codigo = comando_preflight(settings)
    elif args.comando == "baseline":
        codigo = comando_baseline(settings, args.rotulo)
    elif args.comando == "status":
        codigo = comando_status(settings)
    else:
        codigo = comando_encerrar(settings)
    raise SystemExit(codigo)


if __name__ == "__main__":
    main()
