"""
app.utils.logger
=================

Logger local do SAFIRA.

Princípios:
- Nenhum dado é enviado pela rede (sem telemetria, sem serviços externos).
- Os logs ficam em `data/logs/safira.log`, dentro da pasta portátil do
  aplicativo, com rotação de tamanho para não crescer indefinidamente
  em um pendrive com espaço limitado.
- Nunca registrar senhas, hashes, salts ou qualquer segredo em log.
"""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler

from app.config.paths import LOGS_DIR, ensure_runtime_directories

_LOG_FILE_NAME = "safira.log"
_MAX_BYTES = 1 * 1024 * 1024  # 1 MB por arquivo de log
_BACKUP_COUNT = 3

_configured = False


def _configure_root_logger() -> None:
    global _configured
    if _configured:
        return

    ensure_runtime_directories()

    root = logging.getLogger("safira")
    root.setLevel(logging.INFO)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = RotatingFileHandler(
        LOGS_DIR / _LOG_FILE_NAME,
        maxBytes=_MAX_BYTES,
        backupCount=_BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root.addHandler(console_handler)

    _configured = True


def get_logger(name: str) -> logging.Logger:
    """Retorna um logger nomeado (ex.: __name__ do módulo chamador),
    já configurado para gravar em `data/logs/safira.log`."""
    _configure_root_logger()
    return logging.getLogger(f"safira.{name}")
