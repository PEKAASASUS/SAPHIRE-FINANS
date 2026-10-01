"""
app.database.connection
========================

Gerenciamento centralizado da conexão SQLite do SAFIRA.

Decisões arquiteturais:
- SQLite foi escolhido por ser um banco local, leve, sem servidor,
  incluído na biblioteca padrão do Python (sem dependências extras) e
  perfeitamente adequado para uso portátil em pendrive.
- Uma única conexão é reaproveitada durante a vida do processo
  (padrão singleton simples), evitando overhead de abrir/fechar
  conexões a cada operação.
- `PRAGMA foreign_keys = ON` é ativado em toda conexão, pois o SQLite
  não garante integridade referencial por padrão.
- O arquivo do banco fica em `data/safira.db`, dentro da pasta
  portátil do aplicativo (ver app.config.paths).
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from typing import Iterator, Optional

from app.config.paths import DATABASE_FILE, ensure_runtime_directories
from app.utils.logger import get_logger

logger = get_logger(__name__)

_connection: Optional[sqlite3.Connection] = None


def get_connection() -> sqlite3.Connection:
    """Retorna a conexão SQLite única do processo, criando-a se necessário."""
    global _connection

    if _connection is None:
        ensure_runtime_directories()
        logger.info("Abrindo conexão com o banco de dados em %s", DATABASE_FILE)
        _connection = sqlite3.connect(
            str(DATABASE_FILE),
            check_same_thread=False,  # a UI roda em thread única, mas mantemos flexível
        )
        _connection.row_factory = sqlite3.Row
        _connection.execute("PRAGMA foreign_keys = ON;")

    return _connection


def close_connection() -> None:
    """Fecha a conexão ativa, se existir. Usado no encerramento do app
    e em testes automatizados."""
    global _connection
    if _connection is not None:
        _connection.close()
        _connection = None
        logger.info("Conexão com o banco de dados encerrada.")


@contextmanager
def transaction() -> Iterator[sqlite3.Cursor]:
    """Context manager para operações transacionais seguras.

    Faz commit automático ao final do bloco `with`, e rollback caso
    qualquer exceção seja levantada.

    Exemplo:
        with transaction() as cursor:
            cursor.execute("INSERT INTO users (...) VALUES (...)")
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        yield cursor
        conn.commit()
    except Exception:
        conn.rollback()
        logger.exception("Transação revertida (rollback) devido a um erro.")
        raise
    finally:
        cursor.close()
