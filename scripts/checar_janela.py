"""Comando unico de go/no-go antes de abrir uma janela de teste real.

Roda, em sequencia, tudo que pode ser verificado sem tocar no canal real:

    1. suite de testes automatizados;
    2. smoke test;
    3. homologacao entre os tres canais;
    4. ensaio offline dos cenarios da janela;
    5. preflight de flags, credenciais e sessoes residuais.

No fim imprime um veredito unico. `LIBERADO` significa apenas que a parte
tecnica esta pronta: a decisao de abrir a janela continua sendo humana, com
responsavel pelo painel e acompanhamento das conversas definidos.

Uso:

    py scripts/checar_janela.py

Nada aqui liga envio real, altera sessao ou grava no log de eventos real.
"""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]

ETAPAS: list[tuple[str, list[str]]] = [
    ("Suite de testes", ["-m", "unittest", "discover", "-s", "tests"]),
    ("Smoke test", ["scripts/smoke_test.py"]),
    ("Homologacao dos canais", ["scripts/homologar_canais.py"]),
    ("Ensaio dos cenarios da janela", ["scripts/ensaio_janela_maxbot.py"]),
    ("Preflight da janela", ["scripts/janela_teste.py", "preflight"]),
]


def ultima_linha_util(saida: str) -> str:
    linhas = [linha.strip() for linha in saida.splitlines() if linha.strip()]
    return linhas[-1] if linhas else "(sem saida)"


def pendencias(saida: str) -> list[str]:
    """Linhas que explicam a reprovacao, para nao esconder o motivo real."""
    return [
        linha.strip()
        for linha in saida.splitlines()
        if "[NAO]" in linha or "[FALHA]" in linha
    ]


def executar(argumentos: list[str]) -> tuple[bool, str, list[str]]:
    resultado = subprocess.run(
        [sys.executable, *argumentos],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    saida = (resultado.stdout or "") + (resultado.stderr or "")
    return resultado.returncode == 0, ultima_linha_util(saida), pendencias(saida)


def veredito(resultados: list[tuple[str, bool, str]]) -> tuple[bool, list[str]]:
    """Separa o resultado geral das etapas que reprovaram."""
    reprovadas = [nome for nome, ok, _ in resultados if not ok]
    return not reprovadas, reprovadas


def main() -> None:
    resultados: list[tuple[str, bool, str]] = []

    for nome, argumentos in ETAPAS:
        print(f"-> {nome}...", flush=True)
        ok, resumo, detalhes = executar(argumentos)
        resultados.append((nome, ok, resumo))
        print(f"   [{'ok ' if ok else 'FALHA'}] {resumo}", flush=True)
        if not ok:
            for detalhe in detalhes:
                print(f"      {detalhe}", flush=True)
        print(flush=True)

    liberado, reprovadas = veredito(resultados)

    print("=" * 68)
    for nome, ok, _ in resultados:
        print(f"  [{'ok ' if ok else 'FALHA'}] {nome}")
    print("=" * 68)

    if liberado:
        print("\nVEREDITO: LIBERADO para abrir a janela.")
        print("Antes de ligar o envio real, confirme com os responsaveis:")
        print("  - horario, duracao maxima e quem acompanha as conversas;")
        print("  - backend com permissao de rede para https://app.maxbot.com.br;")
        print("  - marco da janela: py scripts/janela_teste.py baseline --rotulo <nome>;")
        print("  - menu do painel silenciado e confirmado ANTES de MAXBOT_SEND_MESSAGES=true.")
    else:
        print("\nVEREDITO: BLOQUEADO. Resolva antes de abrir a janela:")
        for nome in reprovadas:
            print(f"  - {nome}")
        print("\nRode a etapa reprovada isoladamente para ver o detalhe completo.")

    raise SystemExit(0 if liberado else 1)


if __name__ == "__main__":
    main()
