"""Versioned SQLite store and small explicit repository."""
import sqlite3
from contextlib import contextmanager
from pathlib import Path

SCHEMA = """
CREATE TABLE profile(id INTEGER PRIMARY KEY CHECK(id=1), verifier TEXT NOT NULL,
 failures INTEGER NOT NULL DEFAULT 0, retry_at INTEGER NOT NULL DEFAULT 0);
CREATE TABLE settings(key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE accounts(id INTEGER PRIMARY KEY, name TEXT NOT NULL COLLATE NOCASE UNIQUE,
 kind TEXT NOT NULL CHECK(kind IN ('bank','wallet','reserve','brokerage')),
 initial_cents INTEGER NOT NULL CHECK(typeof(initial_cents)='integer'),
 opened TEXT NOT NULL, active INTEGER NOT NULL DEFAULT 1 CHECK(active IN (0,1)));
CREATE TABLE categories(id INTEGER PRIMARY KEY, name TEXT NOT NULL COLLATE NOCASE,
 kind TEXT NOT NULL CHECK(kind IN ('income','expense')), standard INTEGER NOT NULL DEFAULT 0,
 active INTEGER NOT NULL DEFAULT 1, UNIQUE(name,kind));
CREATE TABLE methods(id INTEGER PRIMARY KEY, name TEXT NOT NULL COLLATE NOCASE UNIQUE,
 standard INTEGER NOT NULL DEFAULT 0, active INTEGER NOT NULL DEFAULT 1);
CREATE TABLE operations(id INTEGER PRIMARY KEY, token TEXT NOT NULL UNIQUE,
 kind TEXT NOT NULL CHECK(kind IN ('income','expense','transfer','invoice_payment','investment')),
 description TEXT NOT NULL, amount_cents INTEGER NOT NULL CHECK(typeof(amount_cents)='integer' AND amount_cents>0),
 occurred TEXT NOT NULL, competence TEXT NOT NULL, confirmed TEXT,
 status TEXT NOT NULL CHECK(status IN ('pending','confirmed','cancelled')),
 category_id INTEGER REFERENCES categories(id) ON DELETE RESTRICT,
 method_id INTEGER REFERENCES methods(id) ON DELETE RESTRICT,
 source TEXT NOT NULL DEFAULT 'manual', created TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE entries(id INTEGER PRIMARY KEY, operation_id INTEGER NOT NULL REFERENCES operations(id) ON DELETE CASCADE,
 account_id INTEGER NOT NULL REFERENCES accounts(id) ON DELETE RESTRICT,
 delta_cents INTEGER NOT NULL CHECK(typeof(delta_cents)='integer' AND delta_cents<>0),
 UNIQUE(operation_id,account_id));
CREATE TABLE positions(id INTEGER PRIMARY KEY, account_id INTEGER NOT NULL REFERENCES accounts(id),
 name TEXT NOT NULL, cost_cents INTEGER NOT NULL CHECK(typeof(cost_cents)='integer' AND cost_cents>=0),
 value_cents INTEGER NOT NULL CHECK(typeof(value_cents)='integer' AND value_cents>=0),
 active INTEGER NOT NULL DEFAULT 1);
CREATE TABLE cards(id INTEGER PRIMARY KEY, name TEXT NOT NULL COLLATE NOCASE UNIQUE,
 kind TEXT NOT NULL CHECK(kind IN ('credit','debit')), account_id INTEGER REFERENCES accounts(id),
 limit_cents INTEGER NOT NULL CHECK(typeof(limit_cents)='integer' AND limit_cents>=0),
 closing_day INTEGER NOT NULL CHECK(closing_day BETWEEN 1 AND 31),
 due_day INTEGER NOT NULL CHECK(due_day BETWEEN 1 AND 31), active INTEGER NOT NULL DEFAULT 1);
CREATE TABLE invoices(id INTEGER PRIMARY KEY, card_id INTEGER NOT NULL REFERENCES cards(id),
 closing TEXT NOT NULL, due TEXT NOT NULL, closed INTEGER NOT NULL DEFAULT 0, UNIQUE(card_id,closing));
CREATE TABLE purchases(id INTEGER PRIMARY KEY, token TEXT NOT NULL UNIQUE, card_id INTEGER NOT NULL REFERENCES cards(id),
 description TEXT NOT NULL, amount_cents INTEGER NOT NULL CHECK(typeof(amount_cents)='integer' AND amount_cents>0),
 occurred TEXT NOT NULL, category_id INTEGER NOT NULL REFERENCES categories(id),
 cancelled INTEGER NOT NULL DEFAULT 0, debit_operation_id INTEGER UNIQUE REFERENCES operations(id));
CREATE TABLE installments(id INTEGER PRIMARY KEY, purchase_id INTEGER NOT NULL REFERENCES purchases(id),
 invoice_id INTEGER NOT NULL REFERENCES invoices(id), number INTEGER NOT NULL,
 amount_cents INTEGER NOT NULL CHECK(typeof(amount_cents)='integer' AND amount_cents>0),
 competence TEXT NOT NULL, UNIQUE(purchase_id,number));
CREATE TABLE invoice_payments(id INTEGER PRIMARY KEY, invoice_id INTEGER NOT NULL REFERENCES invoices(id),
 operation_id INTEGER NOT NULL UNIQUE REFERENCES operations(id));
CREATE TABLE series(id INTEGER PRIMARY KEY, title TEXT NOT NULL, amount_cents INTEGER NOT NULL,
 account_id INTEGER NOT NULL REFERENCES accounts(id), category_id INTEGER NOT NULL REFERENCES categories(id),
 start TEXT NOT NULL, active INTEGER NOT NULL DEFAULT 1);
CREATE TABLE commitments(id INTEGER PRIMARY KEY, series_id INTEGER REFERENCES series(id), occurrence TEXT NOT NULL,
 title TEXT NOT NULL, amount_cents INTEGER NOT NULL CHECK(typeof(amount_cents)='integer' AND amount_cents>0),
 account_id INTEGER NOT NULL REFERENCES accounts(id), category_id INTEGER NOT NULL REFERENCES categories(id),
 due TEXT NOT NULL, original_due TEXT NOT NULL,
 state TEXT NOT NULL DEFAULT 'pending' CHECK(state IN ('pending','paid','ignored','postponed')),
 operation_id INTEGER UNIQUE REFERENCES operations(id), UNIQUE(series_id,occurrence));
CREATE INDEX ix_operations_period ON operations(status,occurred,competence);
CREATE INDEX ix_entries_account ON entries(account_id,operation_id);
CREATE INDEX ix_commitments_due ON commitments(state,due);
CREATE INDEX ix_installments_invoice ON installments(invoice_id);
"""


class Store:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.migrate()

    def connect(self):
        conn = sqlite3.connect(self.path, timeout=15, isolation_level=None)
        conn.row_factory = sqlite3.Row
        conn.execute('PRAGMA foreign_keys=ON')
        conn.execute('PRAGMA busy_timeout=15000')
        return conn

    @contextmanager
    def transaction(self):
        conn = self.connect()
        try:
            conn.execute('BEGIN IMMEDIATE')
            yield conn
            conn.commit()
        except BaseException:
            conn.rollback()
            raise
        finally:
            conn.close()

    def migrate(self):
        with self.transaction() as conn:
            conn.execute('CREATE TABLE IF NOT EXISTS schema_migrations(version INTEGER PRIMARY KEY)')
            version = conn.execute('SELECT coalesce(max(version),0) FROM schema_migrations').fetchone()[0]
            if version > 1:
                raise ValueError('Banco criado por versão mais recente do SAFIRA.')
            if not version:
                for statement in SCHEMA.split(';'):
                    if statement.strip():
                        conn.execute(statement)
                for kind, names in [('income', ['Salário','Freelance','Rendimentos','Reembolso','Outros']),
                                    ('expense', ['Alimentação','Moradia','Transporte','Saúde','Educação','Lazer','Serviços','Impostos','Outros'])]:
                    conn.executemany('INSERT INTO categories(name,kind,standard) VALUES (?,?,1)', [(n,kind) for n in names])
                conn.executemany('INSERT INTO methods(name,standard) VALUES (?,1)', [(n,) for n in ['Pix','Transferência bancária','TED','Dinheiro','Boleto','Débito automático']])
                conn.execute('INSERT INTO schema_migrations VALUES (1)')
        conn = self.connect()
        try:
            conn.execute('PRAGMA journal_mode=WAL')
        finally:
            conn.close()

    def rows(self, sql, params=()):
        conn = self.connect()
        try:
            return [dict(row) for row in conn.execute(sql, params)]
        finally:
            conn.close()

    def one(self, sql, params=()):
        rows = self.rows(sql, params)
        return rows[0] if rows else None

    def get(self, table, identity, conn=None):
        allowed = {'accounts','categories','methods','operations','cards','purchases','invoices','commitments','positions','series'}
        if table not in allowed:
            raise ValueError('Tabela inválida.')
        row = conn.execute(f'SELECT * FROM {table} WHERE id=?', (identity,)).fetchone() if conn else self.one(f'SELECT * FROM {table} WHERE id=?',(identity,))
        if row is None:
            raise ValueError('Registro não encontrado.')
        return dict(row)
