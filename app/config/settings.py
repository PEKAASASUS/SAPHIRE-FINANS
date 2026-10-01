"""
app.config.settings
====================

Constantes globais do SAFIRA: identidade do app, parâmetros de
segurança e valores padrão de configuração.

Nenhum segredo (senha, chave, hash) é armazenado aqui — apenas
parâmetros e metadados públicos do aplicativo.
"""

from __future__ import annotations

import json

from app.config.paths import APP_CONFIG_FILE

# ---------------------------------------------------------------------------
# Identidade do aplicativo
# ---------------------------------------------------------------------------
APP_NAME: str = "SAFIRA"
APP_FULL_NAME: str = "SAFIRA — Controle Financeiro Pessoal"
APP_VERSION: str = "0.1.0"          # versão da Etapa 1 (fundação)
APP_STAGE: str = "Etapa 1 — Fundação"

# ---------------------------------------------------------------------------
# Janela principal
# ---------------------------------------------------------------------------
WINDOW_DEFAULT_WIDTH: int = 1280
WINDOW_DEFAULT_HEIGHT: int = 760
WINDOW_MIN_WIDTH: int = 1024
WINDOW_MIN_HEIGHT: int = 640

# ---------------------------------------------------------------------------
# Segurança
# ---------------------------------------------------------------------------
# Iterações do PBKDF2-HMAC-SHA256 usadas na derivação da senha mestre.
# 200_000 é um valor seguro e recomendado (OWASP, 2023+) para hardware comum,
# equilibrando segurança e tempo de resposta em um app desktop.
PBKDF2_ITERATIONS: int = 200_000
PBKDF2_SALT_BYTES: int = 16
PBKDF2_KEY_LENGTH: int = 32  # 256 bits

# Tempo (em segundos) de inatividade até o bloqueio automático do app.
# Pode ser sobrescrito pelo arquivo de configuração local (não secreto).
DEFAULT_AUTO_LOCK_SECONDS: int = 5 * 60  # 5 minutos

# Tamanho mínimo exigido para a senha mestre.
MIN_MASTER_PASSWORD_LENGTH: int = 8

# ---------------------------------------------------------------------------
# Configuração local não sensível (config/app_config.json)
# ---------------------------------------------------------------------------
_DEFAULT_CONFIG: dict = {
    "auto_lock_seconds": DEFAULT_AUTO_LOCK_SECONDS,
    "appearance_mode": "dark",   # "dark" | "light"
}


def load_app_config() -> dict:
    """Carrega config/app_config.json (não sensível), com fallback seguro
    para os valores padrão caso o arquivo não exista ou esteja corrompido.

    Este arquivo NUNCA deve conter senhas, hashes, salts ou chaves.
    """
    if not APP_CONFIG_FILE.exists():
        return dict(_DEFAULT_CONFIG)

    try:
        with open(APP_CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        merged = dict(_DEFAULT_CONFIG)
        merged.update({k: v for k, v in data.items() if k in _DEFAULT_CONFIG})
        return merged
    except (json.JSONDecodeError, OSError):
        return dict(_DEFAULT_CONFIG)


def save_app_config(config: dict) -> None:
    """Persiste a configuração local não sensível."""
    safe_config = {k: config.get(k, v) for k, v in _DEFAULT_CONFIG.items()}
    with open(APP_CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(safe_config, f, indent=2, ensure_ascii=False)
