"""
app.core.app_controller
========================

Ponto único de orquestração da inicialização do SAFIRA (fora da UI):

1. Garante que as pastas portáteis existem.
2. Abre a conexão com o banco de dados local.
3. Aplica migrations pendentes.
4. Cria a Session e o LockManager em memória.

A camada de UI (`app.ui.main_window`) consome este controller e nunca
acessa diretamente o banco de dados ou os módulos de segurança —
mantendo a separação de responsabilidades exigida pela arquitetura.
"""

from __future__ import annotations

from app.config.paths import ensure_runtime_directories
from app.config.settings import load_app_config
from app.core.session import Session
from app.database.connection import get_connection
from app.database.migrations.migration_manager import run_migrations
from app.security.lock_manager import LockManager
from app.utils.logger import get_logger

logger = get_logger(__name__)


class AppController:
    def __init__(self) -> None:
        ensure_runtime_directories()
        self.config: dict = load_app_config()

        logger.info("Inicializando SAFIRA...")
        self.connection = get_connection()
        run_migrations(self.connection)

        self.session = Session()
        self.lock_manager = LockManager(
            session=self.session,
            timeout_seconds=self.config.get("auto_lock_seconds", 300),
        )
        logger.info("Inicialização concluída.")

    def shutdown(self) -> None:
        """Encerramento controlado do aplicativo."""
        logger.info("Encerrando o SAFIRA.")
        self.session.logout()
