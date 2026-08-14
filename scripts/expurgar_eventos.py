"""Mostra ou remove registros antigos do log de eventos.

Por seguranca, o modo padrao apenas informa quantos registros seriam removidos.
Use --confirmar somente depois da aprovacao da politica de retencao da SS Vale.
"""

import argparse
from pathlib import Path
import sqlite3


def count_old(connection: sqlite3.Connection, days: int, table: str) -> int:
    row = connection.execute(
        f"SELECT COUNT(*) FROM {table} "
        "WHERE created_at < datetime('now', ?)",
        (f"-{days} days",),
    ).fetchone()
    return int(row[0])


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Simula ou executa o expurgo de eventos e deduplicacoes antigas."
    )
    parser.add_argument("--db", default="data/sofia_events.db")
    parser.add_argument("--dias", type=int, default=90)
    parser.add_argument(
        "--confirmar",
        action="store_true",
        help="Executa a remocao. Sem esta opcao, faz apenas uma simulacao.",
    )
    args = parser.parse_args()

    if args.dias < 1:
        parser.error("--dias deve ser maior que zero")

    db_path = Path(args.db)
    if not db_path.exists():
        raise SystemExit(f"Banco nao encontrado: {db_path}")

    connection = sqlite3.connect(db_path, timeout=5.0)
    try:
        events = count_old(connection, args.dias, "events")
        processed = count_old(connection, args.dias, "processed_messages")
        if args.confirmar:
            threshold = f"-{args.dias} days"
            connection.execute(
                "DELETE FROM events WHERE created_at < datetime('now', ?)",
                (threshold,),
            )
            connection.execute(
                "DELETE FROM processed_messages WHERE created_at < datetime('now', ?)",
                (threshold,),
            )
            connection.commit()
            action = "removidos"
        else:
            action = "encontrados (simulacao; nada foi removido)"
    finally:
        connection.close()

    print(
        f"{events} eventos e {processed} controles de duplicidade {action}. "
        f"Retencao avaliada: {args.dias} dias."
    )


if __name__ == "__main__":
    main()
