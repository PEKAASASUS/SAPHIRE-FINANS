"""
Migration 0001 — Esquema inicial (fundação).

Cria a estrutura mínima de tabelas necessárias para a Etapa 1
(autenticação e sessão) e prepara — sem implementar a lógica completa —
as tabelas que as Etapas 2 e 3 irão utilizar e evoluir.

Nenhum dado financeiro é manipulado nesta etapa: as tabelas de domínio
financeiro (contas, cartões, movimentações, categorias, compromissos,
metas, investimentos, notificações) existem apenas como infraestrutura,
com as colunas essenciais para não exigir recriação da tabela nas
próximas etapas (apenas ALTER/novas migrations incrementais).
"""

from __future__ import annotations

import sqlite3

VERSION = 1
NAME = "initial_schema"


def up(cursor: sqlite3.Cursor) -> None:
    # -----------------------------------------------------------------
    # users — usuário local do SAFIRA (o app é pessoal; normalmente 1
    # único usuário, mas a estrutura permite múltiplos perfis futuros).
    # -----------------------------------------------------------------
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            name                TEXT NOT NULL DEFAULT 'Usuário',
            password_hash       TEXT NOT NULL,
            password_salt       TEXT NOT NULL,
            password_algorithm  TEXT NOT NULL DEFAULT 'pbkdf2_sha256',
            password_iterations INTEGER NOT NULL,
            created_at          TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at          TEXT NOT NULL DEFAULT (datetime('now'))
        )
        """
    )

    # -----------------------------------------------------------------
    # app_settings — pares chave/valor para preferências internas do
    # app que precisem ser versionadas junto ao banco (diferente do
    # config/app_config.json, que é config local não sensível de
    # inicialização rápida, lido antes mesmo do banco existir).
    # -----------------------------------------------------------------
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS app_settings (
            key         TEXT PRIMARY KEY,
            value       TEXT,
            updated_at  TEXT NOT NULL DEFAULT (datetime('now'))
        )
        """
    )

    # -----------------------------------------------------------------
    # categories — categorias de movimentações (Etapa 2)
    # -----------------------------------------------------------------
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS categories (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT NOT NULL,
            type        TEXT NOT NULL CHECK (type IN ('entrada', 'saida')),
            color       TEXT,
            icon        TEXT,
            created_at  TEXT NOT NULL DEFAULT (datetime('now'))
        )
        """
    )

    # -----------------------------------------------------------------
    # accounts — contas bancárias (Etapa 2)
    # -----------------------------------------------------------------
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS accounts (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            name            TEXT NOT NULL,
            bank_name       TEXT,
            initial_balance REAL NOT NULL DEFAULT 0,
            currency        TEXT NOT NULL DEFAULT 'BRL',
            is_archived     INTEGER NOT NULL DEFAULT 0,
            created_at      TEXT NOT NULL DEFAULT (datetime('now'))
        )
        """
    )

    # -----------------------------------------------------------------
    # cards — cartões (Etapa 2)
    # -----------------------------------------------------------------
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS cards (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            account_id      INTEGER REFERENCES accounts(id) ON DELETE SET NULL,
            name            TEXT NOT NULL,
            card_type       TEXT NOT NULL DEFAULT 'credito' CHECK (card_type IN ('credito', 'debito')),
            credit_limit    REAL,
            closing_day     INTEGER,
            due_day         INTEGER,
            is_archived     INTEGER NOT NULL DEFAULT 0,
            created_at      TEXT NOT NULL DEFAULT (datetime('now'))
        )
        """
    )

    # -----------------------------------------------------------------
    # transactions — movimentações (Etapa 2)
    # -----------------------------------------------------------------
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS transactions (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            account_id      INTEGER REFERENCES accounts(id) ON DELETE SET NULL,
            card_id         INTEGER REFERENCES cards(id) ON DELETE SET NULL,
            category_id     INTEGER REFERENCES categories(id) ON DELETE SET NULL,
            description     TEXT NOT NULL,
            amount          REAL NOT NULL,
            type            TEXT NOT NULL CHECK (type IN ('entrada', 'saida')),
            transaction_date TEXT NOT NULL,
            is_paid         INTEGER NOT NULL DEFAULT 1,
            notes           TEXT,
            created_at      TEXT NOT NULL DEFAULT (datetime('now'))
        )
        """
    )

    # -----------------------------------------------------------------
    # commitments — compromissos/contas a pagar-receber (Etapa 2)
    # -----------------------------------------------------------------
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS commitments (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            title           TEXT NOT NULL,
            amount          REAL,
            due_date        TEXT,
            status          TEXT NOT NULL DEFAULT 'pendente' CHECK (status IN ('pendente', 'concluido', 'atrasado')),
            notes           TEXT,
            created_at      TEXT NOT NULL DEFAULT (datetime('now'))
        )
        """
    )

    # -----------------------------------------------------------------
    # goals — metas / cofres (Etapa 3)
    # -----------------------------------------------------------------
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS goals (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            name            TEXT NOT NULL,
            target_amount   REAL NOT NULL DEFAULT 0,
            current_amount  REAL NOT NULL DEFAULT 0,
            target_date     TEXT,
            created_at      TEXT NOT NULL DEFAULT (datetime('now'))
        )
        """
    )

    # -----------------------------------------------------------------
    # investments — investimentos (Etapa 3)
    # -----------------------------------------------------------------
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS investments (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            name            TEXT NOT NULL,
            investment_type TEXT,
            invested_amount REAL NOT NULL DEFAULT 0,
            current_amount  REAL NOT NULL DEFAULT 0,
            created_at      TEXT NOT NULL DEFAULT (datetime('now'))
        )
        """
    )

    # -----------------------------------------------------------------
    # notifications — notificações (Etapa 3)
    # -----------------------------------------------------------------
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS notifications (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            title           TEXT NOT NULL,
            message         TEXT,
            is_read         INTEGER NOT NULL DEFAULT 0,
            created_at      TEXT NOT NULL DEFAULT (datetime('now'))
        )
        """
    )

    # Índices essenciais para consultas futuras mais comuns.
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_transactions_user_date "
        "ON transactions(user_id, transaction_date)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_commitments_user_due "
        "ON commitments(user_id, due_date)"
    )
