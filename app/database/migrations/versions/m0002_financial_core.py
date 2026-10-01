"""
Migration 0002 — Núcleo financeiro (Etapa 2).

Evolui o esquema da fundação sem apagar dados:
- valores monetários passam a INTEGER (centavos);
- entradas, saídas e transferências em tabelas distintas;
- cartões, parcelas, faturas, pagamentos e estornos;
- compromissos com recorrência;
- investimentos em estrutura mínima;
- notificações da base operacional.
"""

from __future__ import annotations

import sqlite3

VERSION = 2
NAME = "financial_core_schema"


def up(cursor: sqlite3.Cursor) -> None:
    cursor.execute("PRAGMA foreign_keys = OFF")

    _rebuild_categories(cursor)
    _rebuild_accounts(cursor)
    _rebuild_cards(cursor)
    _rebuild_commitments(cursor)
    _rebuild_investments(cursor)
    _rebuild_notifications(cursor)

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS payment_methods (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            name        TEXT NOT NULL,
            flow        TEXT NOT NULL CHECK (flow IN ('entrada', 'saida')),
            is_system   INTEGER NOT NULL DEFAULT 0,
            created_at  TEXT NOT NULL DEFAULT (datetime('now'))
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS incomes (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id             INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            account_id          INTEGER NOT NULL REFERENCES accounts(id),
            category_id         INTEGER NOT NULL REFERENCES categories(id),
            payment_method_id   INTEGER NOT NULL REFERENCES payment_methods(id),
            description         TEXT NOT NULL,
            notes               TEXT,
            amount_cents        INTEGER NOT NULL CHECK (amount_cents > 0),
            happened_on         TEXT NOT NULL,
            created_at          TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at          TEXT NOT NULL DEFAULT (datetime('now'))
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS expenses (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id             INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            account_id          INTEGER NOT NULL REFERENCES accounts(id),
            category_id         INTEGER REFERENCES categories(id),
            payment_method_id   INTEGER REFERENCES payment_methods(id),
            description         TEXT NOT NULL,
            notes               TEXT,
            amount_cents        INTEGER NOT NULL,
            happened_on         TEXT NOT NULL,
            source              TEXT NOT NULL DEFAULT 'manual'
                CHECK (source IN (
                    'manual', 'debit_card', 'invoice_payment',
                    'commitment', 'card_reversal'
                )),
            card_purchase_id    INTEGER REFERENCES card_purchases(id),
            invoice_payment_id  INTEGER,
            commitment_id       INTEGER,
            created_at          TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at          TEXT NOT NULL DEFAULT (datetime('now'))
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS transfers (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id             INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            from_account_id     INTEGER NOT NULL REFERENCES accounts(id),
            to_account_id       INTEGER NOT NULL REFERENCES accounts(id),
            description         TEXT NOT NULL,
            amount_cents        INTEGER NOT NULL CHECK (amount_cents > 0),
            happened_on         TEXT NOT NULL,
            created_at          TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at          TEXT NOT NULL DEFAULT (datetime('now')),
            CHECK (from_account_id <> to_account_id)
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS card_purchases (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id             INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            card_id             INTEGER NOT NULL REFERENCES cards(id),
            category_id         INTEGER REFERENCES categories(id),
            description         TEXT NOT NULL,
            amount_cents        INTEGER NOT NULL CHECK (amount_cents > 0),
            installments_count  INTEGER NOT NULL DEFAULT 1 CHECK (installments_count >= 1),
            purchase_date       TEXT NOT NULL,
            status              TEXT NOT NULL DEFAULT 'ativa'
                CHECK (status IN ('ativa', 'estornada')),
            reversal_of_id      INTEGER REFERENCES card_purchases(id),
            created_at          TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at          TEXT NOT NULL DEFAULT (datetime('now'))
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS invoices (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            card_id         INTEGER NOT NULL REFERENCES cards(id),
            period_year     INTEGER NOT NULL,
            period_month    INTEGER NOT NULL,
            closing_date    TEXT NOT NULL,
            due_date        TEXT NOT NULL,
            status          TEXT NOT NULL DEFAULT 'aberta'
                CHECK (status IN ('aberta', 'fechada', 'pendente', 'paga', 'atrasada', 'cancelada')),
            created_at      TEXT NOT NULL DEFAULT (datetime('now')),
            UNIQUE (card_id, period_year, period_month)
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS card_installments (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            purchase_id     INTEGER NOT NULL REFERENCES card_purchases(id) ON DELETE CASCADE,
            invoice_id      INTEGER REFERENCES invoices(id),
            number          INTEGER NOT NULL,
            total           INTEGER NOT NULL,
            amount_cents    INTEGER NOT NULL,
            status          TEXT NOT NULL DEFAULT 'aberta'
                CHECK (status IN ('aberta', 'cancelada')),
            created_at      TEXT NOT NULL DEFAULT (datetime('now')),
            UNIQUE (purchase_id, number)
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS invoice_payments (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_id      INTEGER NOT NULL REFERENCES invoices(id),
            expense_id      INTEGER NOT NULL REFERENCES expenses(id),
            account_id      INTEGER NOT NULL REFERENCES accounts(id),
            amount_cents    INTEGER NOT NULL,
            paid_on         TEXT NOT NULL,
            created_at      TEXT NOT NULL DEFAULT (datetime('now'))
        )
        """
    )

    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_incomes_user_date ON incomes(user_id, happened_on)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_expenses_user_date ON expenses(user_id, happened_on)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_transfers_user_date ON transfers(user_id, happened_on)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_installments_invoice ON card_installments(invoice_id)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_commitments_series ON commitments(series_id, due_date)"
    )

    cursor.execute("PRAGMA foreign_keys = ON")


def _rename_if_exists(cursor: sqlite3.Cursor, current: str, old_name: str) -> None:
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (current,),
    )
    if cursor.fetchone():
        cursor.execute(f"ALTER TABLE {current} RENAME TO {old_name}")


def _rebuild_categories(cursor: sqlite3.Cursor) -> None:
    cursor.execute("PRAGMA table_info(categories)")
    columns = {row[1] for row in cursor.fetchall()}
    if "user_id" not in columns:
        cursor.execute(
            "ALTER TABLE categories ADD COLUMN user_id INTEGER REFERENCES users(id) ON DELETE CASCADE"
        )
    if "is_system" not in columns:
        cursor.execute(
            "ALTER TABLE categories ADD COLUMN is_system INTEGER NOT NULL DEFAULT 0"
        )


def _rebuild_accounts(cursor: sqlite3.Cursor) -> None:
    _rename_if_exists(cursor, "accounts", "accounts_old")
    cursor.execute(
        """
        CREATE TABLE accounts (
            id                      INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id                 INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            name                    TEXT NOT NULL,
            account_type            TEXT NOT NULL
                CHECK (account_type IN ('banco', 'corretora', 'carteira')),
            initial_balance_cents   INTEGER NOT NULL DEFAULT 0,
            currency                TEXT NOT NULL DEFAULT 'BRL',
            created_at              TEXT NOT NULL DEFAULT (datetime('now'))
        )
        """
    )
    cursor.execute(
        """
        INSERT INTO accounts (id, user_id, name, account_type, initial_balance_cents, currency, created_at)
        SELECT
            id,
            user_id,
            name,
            'banco',
            CAST(ROUND(COALESCE(initial_balance, 0) * 100) AS INTEGER),
            COALESCE(currency, 'BRL'),
            created_at
        FROM accounts_old
        """
    )
    cursor.execute("DROP TABLE accounts_old")


def _rebuild_cards(cursor: sqlite3.Cursor) -> None:
    _rename_if_exists(cursor, "cards", "cards_old")
    cursor.execute(
        """
        CREATE TABLE cards (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id             INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            account_id          INTEGER NOT NULL REFERENCES accounts(id),
            name                TEXT NOT NULL,
            card_type           TEXT NOT NULL CHECK (card_type IN ('credito', 'debito')),
            credit_limit_cents  INTEGER,
            closing_day         INTEGER,
            due_day             INTEGER,
            created_at          TEXT NOT NULL DEFAULT (datetime('now'))
        )
        """
    )
    cursor.execute(
        """
        INSERT INTO cards (
            id, user_id, account_id, name, card_type,
            credit_limit_cents, closing_day, due_day, created_at
        )
        SELECT
            id,
            user_id,
            account_id,
            name,
            COALESCE(card_type, 'credito'),
            CASE WHEN credit_limit IS NULL THEN NULL
                 ELSE CAST(ROUND(credit_limit * 100) AS INTEGER) END,
            closing_day,
            due_day,
            created_at
        FROM cards_old
        WHERE account_id IS NOT NULL
        """
    )
    cursor.execute("DROP TABLE cards_old")


def _rebuild_commitments(cursor: sqlite3.Cursor) -> None:
    _rename_if_exists(cursor, "commitments", "commitments_old")
    cursor.execute(
        """
        CREATE TABLE commitments (
            id                      INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id                 INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            account_id              INTEGER NOT NULL REFERENCES accounts(id),
            category_id             INTEGER REFERENCES categories(id),
            series_id               INTEGER,
            description             TEXT NOT NULL,
            notes                   TEXT,
            expected_amount_cents   INTEGER NOT NULL,
            paid_amount_cents       INTEGER,
            due_date                TEXT NOT NULL,
            recurrence_type         TEXT NOT NULL DEFAULT 'none'
                CHECK (recurrence_type IN ('none', 'weekly', 'monthly', 'yearly', 'custom')),
            recurrence_interval     INTEGER NOT NULL DEFAULT 1,
            recurrence_unit         TEXT CHECK (recurrence_unit IN ('day', 'week', 'month', 'year')),
            status                  TEXT NOT NULL DEFAULT 'pendente'
                CHECK (status IN ('pendente', 'pago', 'atrasado', 'cancelado')),
            paid_expense_id         INTEGER,
            created_at              TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at              TEXT NOT NULL DEFAULT (datetime('now'))
        )
        """
    )
    cursor.execute(
        """
        INSERT INTO commitments (
            id, user_id, account_id, description, expected_amount_cents,
            due_date, status, notes, created_at
        )
        SELECT
            id,
            user_id,
            (SELECT a.id FROM accounts a WHERE a.user_id = commitments_old.user_id LIMIT 1),
            title,
            CAST(ROUND(COALESCE(amount, 0) * 100) AS INTEGER),
            COALESCE(due_date, date('now')),
            CASE status
                WHEN 'concluido' THEN 'pago'
                WHEN 'atrasado' THEN 'atrasado'
                ELSE 'pendente'
            END,
            notes,
            created_at
        FROM commitments_old
        WHERE EXISTS (SELECT 1 FROM accounts a WHERE a.user_id = commitments_old.user_id)
        """
    )
    cursor.execute("DROP TABLE commitments_old")


def _rebuild_investments(cursor: sqlite3.Cursor) -> None:
    _rename_if_exists(cursor, "investments", "investments_old")
    cursor.execute(
        """
        CREATE TABLE investments (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            account_id      INTEGER NOT NULL REFERENCES accounts(id),
            name            TEXT NOT NULL,
            amount_cents    INTEGER NOT NULL DEFAULT 0 CHECK (amount_cents >= 0),
            created_at      TEXT NOT NULL DEFAULT (datetime('now'))
        )
        """
    )
    cursor.execute("DROP TABLE investments_old")


def _rebuild_notifications(cursor: sqlite3.Cursor) -> None:
    _rename_if_exists(cursor, "notifications", "notifications_old")
    cursor.execute(
        """
        CREATE TABLE notifications (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            kind            TEXT NOT NULL,
            title           TEXT NOT NULL,
            message         TEXT,
            related_type    TEXT,
            related_id      INTEGER,
            due_on          TEXT,
            is_read         INTEGER NOT NULL DEFAULT 0,
            created_at      TEXT NOT NULL DEFAULT (datetime('now')),
            UNIQUE (user_id, kind, related_type, related_id)
        )
        """
    )
    cursor.execute("DROP TABLE notifications_old")
