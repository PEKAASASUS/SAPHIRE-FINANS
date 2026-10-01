"""
Proteção em repouso dos dados financeiros.

A chave Fernet é derivada da senha mestre (em memória, nunca gravada).
Campos TEXT sensíveis são cifrados na escrita e decifrados na leitura.
Valores monetários permanecem INTEGER (centavos) para cálculo exato;
a confidencialidade do arquivo completo depende da senha mestre e desta
cifra de campos descritivos.

Troca de senha: `reprotect_connection` recifra todos os campos com a
nova chave, sem perda de dados.

Recuperação por arquivo externo NÃO é implementada aqui — o modelo do
arquivo permanece isolado (ver ARCHITECTURE.md). Não há mecanismo de
recuperação de senha.
"""

from __future__ import annotations

import sqlite3
from typing import Iterable

from cryptography.fernet import InvalidToken

from app.models.user import User
from app.security.crypto_utils import (
    b64_to_bytes,
    bytes_to_b64,
    decrypt_data,
    derive_fernet_key_from_password,
    encrypt_data,
)

TOKEN_PREFIX = "SF1:"

ENCRYPTED_COLUMNS: dict[str, tuple[str, ...]] = {
    "accounts": ("name",),
    "categories": ("name",),
    "payment_methods": ("name",),
    "incomes": ("description", "notes"),
    "expenses": ("description", "notes"),
    "transfers": ("description",),
    "cards": ("name",),
    "card_purchases": ("description",),
    "commitments": ("description", "notes"),
    "investments": ("name",),
    "notifications": ("title", "message"),
}


class DataProtectionError(Exception):
    """Falha ao cifrar/decifrar dados financeiros."""


class DataProtector:
    def __init__(self, fernet_key: bytes):
        self._key = fernet_key

    @classmethod
    def from_password(cls, password: str, user: User) -> "DataProtector":
        key = derive_fernet_key_from_password(
            password,
            b64_to_bytes(user.password_salt),
            iterations=user.password_iterations,
        )
        return cls(key)

    def encrypt_text(self, plaintext: str | None) -> str | None:
        if plaintext is None:
            return None
        token = encrypt_data(plaintext.encode("utf-8"), self._key)
        return TOKEN_PREFIX + bytes_to_b64(token)

    def decrypt_text(self, stored: str | None) -> str | None:
        if stored is None:
            return None
        if not stored.startswith(TOKEN_PREFIX):
            return stored
        raw = b64_to_bytes(stored[len(TOKEN_PREFIX) :])
        try:
            return decrypt_data(raw, self._key).decode("utf-8")
        except InvalidToken as exc:
            raise DataProtectionError("Não foi possível decifrar um dado financeiro.") from exc

    def maybe_encrypt(self, value: str | None) -> str | None:
        if value is None:
            return None
        if value.startswith(TOKEN_PREFIX):
            return value
        return self.encrypt_text(value)


def reprotect_connection(
    connection: sqlite3.Connection,
    old_protector: DataProtector,
    new_protector: DataProtector,
    tables: Iterable[str] | None = None,
) -> None:
    """Recifra campos TEXT com a nova senha mestre, em transação."""
    target_tables = list(tables) if tables is not None else list(ENCRYPTED_COLUMNS)
    cursor = connection.cursor()
    try:
        for table in target_tables:
            columns = ENCRYPTED_COLUMNS.get(table)
            if not columns:
                continue
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                (table,),
            )
            if cursor.fetchone() is None:
                continue
            cols_sql = ", ".join(columns)
            cursor.execute(f"SELECT id, {cols_sql} FROM {table}")
            rows = cursor.fetchall()
            for row in rows:
                record_id = row[0]
                updates = []
                values: list = []
                for index, column in enumerate(columns, start=1):
                    plain = old_protector.decrypt_text(row[index])
                    updates.append(f"{column} = ?")
                    values.append(new_protector.encrypt_text(plain) if plain is not None else None)
                values.append(record_id)
                cursor.execute(
                    f"UPDATE {table} SET {', '.join(updates)} WHERE id = ?",
                    values,
                )
        connection.commit()
    except Exception:
        connection.rollback()
        raise
