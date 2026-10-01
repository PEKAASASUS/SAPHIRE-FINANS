"""
app.security.password_manager
==============================

Responsável exclusivamente por transformar uma senha em texto puro em
um hash seguro para armazenamento, e por verificar tentativas de login
contra esse hash — nunca a senha em si é armazenada.

Algoritmo: PBKDF2-HMAC-SHA256 (via `cryptography`), com salt aleatório
por usuário e número de iterações configurável (app.config.settings).
Este é um algoritmo padrão da indústria, recomendado pelo NIST/OWASP
para derivação de chaves a partir de senhas.
"""

from __future__ import annotations

import hmac
from dataclasses import dataclass

from app.config.settings import PBKDF2_ITERATIONS
from app.security.crypto_utils import (
    b64_to_bytes,
    bytes_to_b64,
    derive_key,
    generate_salt,
)


@dataclass(frozen=True)
class PasswordHash:
    """Representa o resultado do hashing de uma senha, pronto para ser
    persistido no banco de dados (todos os campos são texto/base64)."""

    algorithm: str
    salt_b64: str
    hash_b64: str
    iterations: int


def hash_password(password: str, iterations: int = PBKDF2_ITERATIONS) -> PasswordHash:
    """Gera um novo salt e hash para a senha informada.

    Usado tanto na criação da senha mestre quanto na troca de senha.
    """
    salt = generate_salt()
    derived = derive_key(password, salt, iterations=iterations)
    return PasswordHash(
        algorithm="pbkdf2_sha256",
        salt_b64=bytes_to_b64(salt),
        hash_b64=bytes_to_b64(derived),
        iterations=iterations,
    )


def verify_password(password: str, stored: PasswordHash) -> bool:
    """Verifica se `password` corresponde ao hash armazenado.

    Utiliza comparação em tempo constante (`hmac.compare_digest`) para
    mitigar ataques de timing.
    """
    if stored.algorithm != "pbkdf2_sha256":
        raise ValueError(f"Algoritmo de senha não suportado: {stored.algorithm}")

    salt = b64_to_bytes(stored.salt_b64)
    expected = b64_to_bytes(stored.hash_b64)
    candidate = derive_key(password, salt, iterations=stored.iterations)

    return hmac.compare_digest(candidate, expected)


def is_password_strong_enough(password: str, minimum_length: int) -> bool:
    """Validação mínima de força da senha mestre.

    Nesta etapa, mantemos a regra simples (tamanho mínimo). Regras mais
    elaboradas podem ser adicionadas em etapas futuras sem alterar a
    arquitetura de hashing.
    """
    return len(password) >= minimum_length
