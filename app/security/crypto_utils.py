"""
app.security.crypto_utils
==========================

Primitivas criptográficas do SAFIRA.

Regra fundamental deste módulo: NENHUM algoritmo criptográfico é
implementado do zero. Utilizamos exclusivamente a biblioteca
`cryptography` (PyPI), amplamente auditada e mantida, que expõe
implementações corretas de PBKDF2 e criptografia simétrica (Fernet/AES).

Responsabilidades:
- Gerar salts aleatórios criptograficamente seguros.
- Derivar chaves a partir de senhas (PBKDF2-HMAC-SHA256).
- Fornecer utilitários de criptografia simétrica que a Etapa 2/3
  poderão usar para cifrar dados financeiros sensíveis em repouso
  (a infraestrutura já fica pronta desde a fundação, mesmo que ainda
  não seja usada para cifrar tabelas nesta etapa).
"""

from __future__ import annotations

import base64
import os

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.fernet import Fernet

from app.config.settings import PBKDF2_ITERATIONS, PBKDF2_KEY_LENGTH, PBKDF2_SALT_BYTES


def generate_salt(size: int = PBKDF2_SALT_BYTES) -> bytes:
    """Gera um salt aleatório criptograficamente seguro."""
    return os.urandom(size)


def derive_key(
    password: str,
    salt: bytes,
    iterations: int = PBKDF2_ITERATIONS,
    key_length: int = PBKDF2_KEY_LENGTH,
) -> bytes:
    """Deriva uma chave/hash a partir de uma senha usando PBKDF2-HMAC-SHA256.

    Este é o algoritmo utilizado tanto para gerar o hash de verificação
    da senha mestre (password_manager) quanto, futuramente, para
    derivar a chave de criptografia dos dados financeiros.
    """
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=key_length,
        salt=salt,
        iterations=iterations,
    )
    return kdf.derive(password.encode("utf-8"))


def bytes_to_b64(data: bytes) -> str:
    """Codifica bytes em texto (base64) para armazenamento no banco."""
    return base64.b64encode(data).decode("ascii")


def b64_to_bytes(data: str) -> bytes:
    """Decodifica texto (base64) de volta para bytes."""
    return base64.b64decode(data.encode("ascii"))


def derive_fernet_key_from_password(password: str, salt: bytes, iterations: int = PBKDF2_ITERATIONS) -> bytes:
    """Deriva uma chave compatível com `Fernet` (32 bytes, urlsafe-base64)
    a partir da senha mestre. Preparado para uso futuro na criptografia
    dos dados financeiros locais — não utilizado ainda na Etapa 1.
    """
    raw_key = derive_key(password, salt, iterations=iterations, key_length=32)
    return base64.urlsafe_b64encode(raw_key)


def encrypt_data(plaintext: bytes, fernet_key: bytes) -> bytes:
    """Criptografa dados usando AES simétrico via Fernet.

    Infraestrutura pronta para uso nas próximas etapas, quando os
    dados financeiros passarem a ser cifrados em repouso.
    """
    return Fernet(fernet_key).encrypt(plaintext)


def decrypt_data(token: bytes, fernet_key: bytes) -> bytes:
    """Descriptografa dados previamente cifrados com `encrypt_data`."""
    return Fernet(fernet_key).decrypt(token)
