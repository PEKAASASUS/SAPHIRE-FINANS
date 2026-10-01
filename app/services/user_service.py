"""
app.services.user_service
==========================

Camada de serviço (repositório) responsável pelo acesso à tabela
`users`. Nenhuma lógica de UI ou de regras de autenticação vive aqui —
apenas leitura/escrita no banco. Regras de autenticação ficam em
`app.security.auth_service`.
"""

from __future__ import annotations

import sqlite3
from typing import Optional

from app.models.user import User
from app.security.password_manager import PasswordHash


def has_user(connection: sqlite3.Connection) -> bool:
    """Indica se já existe algum usuário cadastrado (senha mestre
    configurada). Usado para decidir entre a tela de 'criar senha
    mestre' e a tela de login."""
    cursor = connection.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]
    return count > 0


def get_primary_user(connection: sqlite3.Connection) -> Optional[User]:
    """Retorna o usuário principal (primeiro cadastrado). Como o SAFIRA
    hoje opera com um único usuário local, isso é suficiente; a
    estrutura permite evoluir para múltiplos perfis sem quebrar esta
    função (bastaria adicionar seleção de perfil antes de chamá-la)."""
    cursor = connection.execute(
        "SELECT * FROM users ORDER BY id ASC LIMIT 1"
    )
    row = cursor.fetchone()
    return User.from_row(row) if row else None


def create_user(
    connection: sqlite3.Connection,
    name: str,
    password_hash: PasswordHash,
) -> User:
    """Cria o usuário local com a senha mestre já derivada em hash."""
    cursor = connection.execute(
        """
        INSERT INTO users (
            name, password_hash, password_salt,
            password_algorithm, password_iterations
        ) VALUES (?, ?, ?, ?, ?)
        """,
        (
            name,
            password_hash.hash_b64,
            password_hash.salt_b64,
            password_hash.algorithm,
            password_hash.iterations,
        ),
    )
    connection.commit()
    user = get_primary_user(connection)
    assert user is not None and user.id == cursor.lastrowid
    return user


def update_password(
    connection: sqlite3.Connection,
    user_id: int,
    password_hash: PasswordHash,
) -> None:
    """Atualiza a senha mestre de um usuário existente (troca de senha)."""
    connection.execute(
        """
        UPDATE users
        SET password_hash = ?,
            password_salt = ?,
            password_algorithm = ?,
            password_iterations = ?,
            updated_at = datetime('now')
        WHERE id = ?
        """,
        (
            password_hash.hash_b64,
            password_hash.salt_b64,
            password_hash.algorithm,
            password_hash.iterations,
            user_id,
        ),
    )
    connection.commit()
