"""Ensaio offline dos cenarios que faltam validar na janela real do Maxbot.

Roda, sem rede e sem envio real, os quatro cenarios pendentes da segunda janela:

    1. guardrail comercial (preco, frete, prazo, desconto, pagamento);
    2. mensagem duplicada;
    3. telefone nao autorizado;
    4. retorno seguro (atendimento humano, handoff pendente e envio desligado).

Tudo acontece em bancos temporarios: o log de eventos real nao e tocado.
O objetivo e chegar na janela com os quatro cenarios ja conhecidos, restando
apenas confirmar o mesmo comportamento no numero oficial.
"""

from __future__ import annotations

from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sofia_chatbot.api import SofiaApplication  # noqa: E402
from sofia_chatbot.config import Settings  # noqa: E402

TELEFONE_PILOTO = "5531999990001"
TELEFONE_ESTRANHO = "5531988880000"


def construir_app(tmpdir: str, telefones: tuple[str, ...] = (TELEFONE_PILOTO,)) -> SofiaApplication:
    return SofiaApplication(
        Settings(
            session_store="sqlite",
            sqlite_path=str(Path(tmpdir) / "sessions.db"),
            event_log_enabled=True,
            event_log_path=str(Path(tmpdir) / "events.db"),
            maxbot_pilot_mode=True,
            maxbot_pilot_phones=telefones,
            maxbot_pilot_allow_attendance=False,
            maxbot_send_messages=False,
            maxbot_webhook_secret="segredo-de-ensaio-com-tamanho-suficiente",
            local_api_enabled=False,
            debug_endpoints_enabled=False,
            whatsapp_send_messages=False,
        )
    )


def payload(texto: str, msg_id: str, telefone: str = TELEFONE_PILOTO, segmento: bool = True) -> dict:
    return {
        "origin": "2",
        "contact": {
            "id": "9001",
            "name": "Ensaio",
            "surname": "Janela",
            "whatsapp": telefone,
            "segmentation": ["SOFIA_API_PILOTO"] if segmento else [],
            "in_attendance": "0",
        },
        "msg_id": msg_id,
        "msg": texto,
        "type": "T",
    }


def payload_em_atendimento(texto: str, msg_id: str, telefone: str = TELEFONE_PILOTO) -> dict:
    return {
        "origin": "2",
        "whatsapp": telefone,
        "prot_id": "3001",
        "contact_id": "9001",
        "chat_id": "5001",
        "msg_id": msg_id,
        "msg": texto,
        "type": "T",
    }


def envio_desligado(resultado: dict) -> bool:
    """Nenhuma saida pode ter sido realmente enviada."""
    for item in resultado.get("processed", []):
        outbound = item.get("outbound") or {}
        if outbound.get("sent") or outbound.get("mode") != "dry_run":
            return False
    return True


def cenario_guardrail_comercial() -> list[tuple[str, bool, str]]:
    checagens = []
    pedidos = [
        ("preco", "Quanto custa uma fritadeira?"),
        ("frete", "Qual o frete para Taubate?"),
        ("prazo", "Qual o prazo de entrega?"),
        ("desconto", "Tem desconto para dois fornos?"),
        ("pagamento", "Posso pagar no pix parcelado?"),
        ("estoque", "Voces tem em estoque hoje?"),
        ("orcamento", "Me manda um orcamento formal"),
    ]
    for indice, (rotulo, texto) in enumerate(pedidos):
        with tempfile.TemporaryDirectory() as tmpdir:
            app = construir_app(tmpdir)
            resultado = app.maxbot_webhook(
                payload(texto, f"ENSAIO-GUARDRAIL-{indice}")
            )
        processados = resultado.get("processed", [])
        if not processados:
            checagens.append((f"guardrail/{rotulo}", False, "mensagem nao foi processada"))
            continue
        reply = processados[0]["reply"]
        bloqueou = "bloqueio_comercial" in reply["tags"] or "pos_venda" in reply["tags"]
        seguiu_para_humano = reply["next_block"] in {
            "BLOCO_COLETA_NOME",
            "BLOCO_04_SUPORTE_POS_VENDA",
        }
        sem_envio = envio_desligado(resultado)
        ok = bloqueou and seguiu_para_humano and sem_envio
        detalhe = f"tags={','.join(reply['tags'])} bloco={reply['next_block']}"
        checagens.append((f"guardrail/{rotulo}", ok, detalhe))
    return checagens


def cenario_duplicidade() -> list[tuple[str, bool, str]]:
    with tempfile.TemporaryDirectory() as tmpdir:
        app = construir_app(tmpdir)
        entrada = payload("Comecar", "ENSAIO-DUPLICADA-1")
        primeira = app.maxbot_webhook(entrada)
        segunda = app.maxbot_webhook(entrada)

    return [
        (
            "duplicidade/primeira responde",
            len(primeira.get("processed", [])) == 1,
            f"processed={len(primeira.get('processed', []))}",
        ),
        (
            "duplicidade/segunda nao responde",
            len(segunda.get("processed", [])) == 0
            and len(segunda.get("duplicates", [])) == 1,
            f"processed={len(segunda.get('processed', []))} "
            f"duplicates={len(segunda.get('duplicates', []))}",
        ),
    ]


def cenario_telefone_nao_autorizado() -> list[tuple[str, bool, str]]:
    with tempfile.TemporaryDirectory() as tmpdir:
        app = construir_app(tmpdir)
        fora = app.maxbot_webhook(
            payload(
                "Comecar",
                "ENSAIO-ESTRANHO-1",
                telefone=TELEFONE_ESTRANHO,
                segmento=False,
            )
        )
        dentro = app.maxbot_webhook(payload("Comecar", "ENSAIO-PILOTO-1"))

    ignorados = fora.get("ignored", [])
    motivo = ignorados[0].get("ignored_reason") if ignorados else "nenhum"
    return [
        (
            "nao autorizado/fica em silencio",
            not fora.get("processed") and motivo == "pilot_not_allowed",
            f"processed={len(fora.get('processed', []))} motivo={motivo}",
        ),
        (
            "nao autorizado/piloto continua respondendo",
            len(dentro.get("processed", [])) == 1,
            f"processed={len(dentro.get('processed', []))}",
        ),
    ]


def cenario_retorno_seguro() -> list[tuple[str, bool, str]]:
    checagens = []

    # Atendimento humano em andamento: a Sofia nao pode responder.
    with tempfile.TemporaryDirectory() as tmpdir:
        app = construir_app(tmpdir)
        humano = app.maxbot_webhook(
            payload_em_atendimento("Obrigado pelo atendimento", "ENSAIO-HUMANO-1")
        )
    ignorados = humano.get("ignored", [])
    motivo = ignorados[0].get("ignored_reason") if ignorados else "nenhum"
    checagens.append(
        (
            "retorno seguro/atendimento humano silencia",
            not humano.get("processed") and motivo == "human_attendance",
            f"processed={len(humano.get('processed', []))} motivo={motivo}",
        )
    )

    # Conversa concluida: depois do handoff a Sofia fica silenciosa.
    with tempfile.TemporaryDirectory() as tmpdir:
        app = construir_app(tmpdir)
        conversa = [
            "Comecar",
            "Falar com consultor",
            "Quero ajuda para comprar equipamentos",
            "Ana",
            "Taubate, SP",
        ]
        ultimo = {}
        for indice, texto in enumerate(conversa):
            ultimo = app.maxbot_webhook(payload(texto, f"ENSAIO-HANDOFF-{indice}"))
        chegou_em_handoff = bool(ultimo.get("processed")) and (
            ultimo["processed"][0]["status"] == "handoff"
        )
        depois = app.maxbot_webhook(payload("Oi, tudo bem?", "ENSAIO-HANDOFF-DEPOIS"))

    motivo_depois = (
        depois.get("ignored", [{}])[0].get("ignored_reason")
        if depois.get("ignored")
        else "nenhum"
    )
    checagens.append(
        (
            "retorno seguro/conversa chega ao handoff",
            chegou_em_handoff,
            f"status={ultimo.get('processed', [{}])[0].get('status', '-')}",
        )
    )
    checagens.append(
        (
            "retorno seguro/silencio apos handoff",
            not depois.get("processed") and motivo_depois == "handoff_pending",
            f"processed={len(depois.get('processed', []))} motivo={motivo_depois}",
        )
    )

    # Envio real desligado: toda saida fica em dry_run.
    with tempfile.TemporaryDirectory() as tmpdir:
        app = construir_app(tmpdir)
        saida = app.maxbot_webhook(payload("Comecar", "ENSAIO-DRYRUN-1"))
    checagens.append(
        (
            "retorno seguro/envio permanece desligado",
            envio_desligado(saida),
            "todas as saidas em dry_run",
        )
    )
    return checagens


def main() -> None:
    grupos = [
        ("1. Guardrail comercial", cenario_guardrail_comercial),
        ("2. Mensagem duplicada", cenario_duplicidade),
        ("3. Telefone nao autorizado", cenario_telefone_nao_autorizado),
        ("4. Retorno seguro", cenario_retorno_seguro),
    ]

    falhas = 0
    for titulo, funcao in grupos:
        print(f"\n== {titulo} ==")
        for nome, ok, detalhe in funcao():
            marca = "ok " if ok else "FALHA"
            print(f"  [{marca}] {nome} — {detalhe}")
            falhas += 0 if ok else 1

    print("\n" + ("Ensaio OK: os quatro cenarios se comportam como esperado."
                  if falhas == 0
                  else f"Ensaio reprovado: {falhas} checagem(ns) com falha."))
    raise SystemExit(0 if falhas == 0 else 1)


if __name__ == "__main__":
    main()
