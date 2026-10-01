"""
app.database.migrations.migration_manager
===========================================

Sistema simples e explícito de migrations para o SAFIRA.

Por que um sistema próprio (e não Alembic ou similar)?
- Manter o app leve e com poucas dependências (requisito de portabilidade).
- As necessidades da Etapa 1 são simples: aplicar scripts SQL/Python
  versionados, em ordem, uma única vez cada.
- A tabela `schema_migrations` registra quais versões já foram
  aplicadas, permitindo evoluir o banco em etapas futuras SEM apagar
  dados existentes do usuário.

Como funciona:
1. Cada migration é um módulo dentro de `app/database/migrations/versions/`
   com um número sequencial no nome (ex.: `m0001_initial_schema.py`).
2. Cada módulo expõe: `VERSION` (int), `NAME` (str) e `up(cursor)`.
3. O MigrationManager aplica, em ordem, todas as migrations cuja
   VERSION ainda não conste na tabela `schema_migrations`.

Para adicionar uma nova migration no futuro (Etapa 2, 3...):
    1. Criar `m0002_nome_da_mudanca.py` em `versions/`.
    2. Definir VERSION = 2, NAME = "descrição curta".
    3. Implementar `up(cursor)` com os comandos SQL necessários.
    4. Registrar o módulo em `MIGRATIONS` (lista abaixo, em ordem).
    Nunca editar uma migration já aplicada em produção — sempre criar uma nova.
"""

from __future__ import annotations

import sqlite3
from types import ModuleType
from typing import List

from app.database.migrations.versions import m0001_initial_schema
from app.database.migrations.versions import m0002_financial_core
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Lista ordenada de migrations conhecidas pelo sistema.
# Adicione novas migrations ao final desta lista, em ordem crescente de versão.
MIGRATIONS: List[ModuleType] = [
    m0001_initial_schema,
    m0002_financial_core,
]

_SCHEMA_TABLE = "schema_migrations"


def _ensure_schema_table(cursor: sqlite3.Cursor) -> None:
    cursor.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {_SCHEMA_TABLE} (
            version     INTEGER PRIMARY KEY,
            name        TEXT NOT NULL,
            applied_at  TEXT NOT NULL DEFAULT (datetime('now'))
        )
        """
    )


def _applied_versions(cursor: sqlite3.Cursor) -> set[int]:
    cursor.execute(f"SELECT version FROM {_SCHEMA_TABLE}")
    return {row[0] for row in cursor.fetchall()}


def run_migrations(connection: sqlite3.Connection) -> list[int]:
    """Aplica todas as migrations pendentes, em ordem, dentro de uma
    transação por migration. Retorna a lista de versões aplicadas nesta
    execução (lista vazia se o banco já estava atualizado).
    """
    cursor = connection.cursor()
    _ensure_schema_table(cursor)
    connection.commit()

    already_applied = _applied_versions(cursor)
    newly_applied: list[int] = []

    for migration in sorted(MIGRATIONS, key=lambda m: m.VERSION):
        if migration.VERSION in already_applied:
            continue

        logger.info(
            "Aplicando migration %04d — %s", migration.VERSION, migration.NAME
        )
        try:
            migration.up(cursor)
            cursor.execute(
                f"INSERT INTO {_SCHEMA_TABLE} (version, name) VALUES (?, ?)",
                (migration.VERSION, migration.NAME),
            )
            connection.commit()
            newly_applied.append(migration.VERSION)
        except Exception:
            connection.rollback()
            logger.exception(
                "Falha ao aplicar migration %04d — banco revertido.",
                migration.VERSION,
            )
            raise

    if newly_applied:
        logger.info("Migrations aplicadas com sucesso: %s", newly_applied)
    else:
        logger.info("Banco de dados já está atualizado (nenhuma migration pendente).")

    return newly_applied


def current_schema_version(connection: sqlite3.Connection) -> int:
    """Retorna a versão mais recente aplicada ao banco (0 se nenhuma)."""
    cursor = connection.cursor()
    _ensure_schema_table(cursor)
    cursor.execute(f"SELECT MAX(version) FROM {_SCHEMA_TABLE}")
    result = cursor.fetchone()[0]
    return int(result) if result is not None else 0
