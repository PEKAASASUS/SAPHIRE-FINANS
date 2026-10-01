"""
app.security.auth_service
==========================

Regras de negócio da autenticação do SAFIRA:
- criação da senha mestre (primeiro uso);
- validação de login;
- troca de senha mestre.

Este módulo orquestra `password_manager` (hashing) e `user_service`
(persistência), mas não conhece nada sobre a interface gráfica.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass

from app.config.settings import MIN_MASTER_PASSWORD_LENGTH
from app.models.user import User
from app.security.password_manager import (
    PasswordHash,
    hash_password,
    is_password_strong_enough,
    verify_password,
)
from app.services import user_service
from app.utils.logger import get_logger

logger = get_logger(__name__)


class AuthError(Exception):
    """Erro genérico de autenticação (senha fraca, credenciais inválidas etc.)."""


@dataclass(frozen=True)
class AuthResult:
    success: bool
    user: User | None = None
    error_message: str | None = None


def needs_master_password_setup(connection: sqlite3.Connection) -> bool:
    """True se ainda não existe nenhuma senha mestre configurada."""
    return not user_service.has_user(connection)


def setup_master_password(
    connection: sqlite3.Connection, password: str, confirm_password: str
) -> AuthResult:
    """Cria a senha mestre no primeiro uso do aplicativo."""
    if user_service.has_user(connection):
        return AuthResult(False, error_message="Já existe uma senha mestre configurada.")

    if password != confirm_password:
        return AuthResult(False, error_message="As senhas não coincidem.")

    if not is_password_strong_enough(password, MIN_MASTER_PASSWORD_LENGTH):
        return AuthResult(
            False,
            error_message=(
                f"A senha mestre deve ter pelo menos "
                f"{MIN_MASTER_PASSWORD_LENGTH} caracteres."
            ),
        )

    password_hash = hash_password(password)
    user = user_service.create_user(connection, name="Usuário", password_hash=password_hash)
    logger.info("Senha mestre configurada com sucesso (usuário id=%s).", user.id)
    return AuthResult(True, user=user)


def login(connection: sqlite3.Connection, password: str) -> AuthResult:
    """Valida a senha mestre informada contra o usuário cadastrado."""
    user = user_service.get_primary_user(connection)
    if user is None:
        return AuthResult(False, error_message="Nenhuma senha mestre configurada.")

    stored = PasswordHash(
        algorithm=user.password_algorithm,
        salt_b64=user.password_salt,
        hash_b64=user.password_hash,
        iterations=user.password_iterations,
    )

    if verify_password(password, stored):
        logger.info("Login bem-sucedido (usuário id=%s).", user.id)
        return AuthResult(True, user=user)

    logger.warning("Tentativa de login com senha incorreta (usuário id=%s).", user.id)
    return AuthResult(False, error_message="Senha incorreta.")


def change_master_password(
    connection: sqlite3.Connection,
    user: User,
    current_password: str,
    new_password: str,
    confirm_new_password: str,
) -> AuthResult:
    """Troca a senha mestre, exigindo a senha atual como confirmação."""
    login_check = login(connection, current_password)
    if not login_check.success:
        return AuthResult(False, error_message="Senha atual incorreta.")

    if new_password != confirm_new_password:
        return AuthResult(False, error_message="As novas senhas não coincidem.")

    if not is_password_strong_enough(new_password, MIN_MASTER_PASSWORD_LENGTH):
        return AuthResult(
            False,
            error_message=(
                f"A nova senha deve ter pelo menos "
                f"{MIN_MASTER_PASSWORD_LENGTH} caracteres."
            ),
        )

    password_hash = hash_password(new_password)
    user_service.update_password(connection, user.id, password_hash)
    logger.info("Senha mestre alterada com sucesso (usuário id=%s).", user.id)
    return AuthResult(True, user=user)
