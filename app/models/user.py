"""
app.models.user
================

Modelo de dados do usuário local do SAFIRA.

Nesta etapa, o SAFIRA opera com um único usuário (senha mestre local),
mas a tabela e o modelo já suportam múltiplos registros caso isso seja
necessário no futuro (ex.: perfis separados no mesmo pendrive).
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass


@dataclass(frozen=True)
class User:
    id: int
    name: str
    password_hash: str
    password_salt: str
    password_algorithm: str
    password_iterations: int
    created_at: str
    updated_at: str

    @staticmethod
    def from_row(row: sqlite3.Row) -> "User":
        return User(
            id=row["id"],
            name=row["name"],
            password_hash=row["password_hash"],
            password_salt=row["password_salt"],
            password_algorithm=row["password_algorithm"],
            password_iterations=row["password_iterations"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
