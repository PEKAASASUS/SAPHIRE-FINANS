"""
app.security.lock_manager
==========================

Verifica periodicamente se a sessão ativa excedeu o tempo de
inatividade configurado e, em caso positivo, aciona o bloqueio do
aplicativo (sem encerrar a sessão — ver `app.core.session`).

Este módulo não depende da biblioteca gráfica: a camada de UI é quem
agenda a checagem periódica (via `after()` do Tkinter/CustomTkinter) e
reage à mudança de estado chamando `session.lock()`.
"""

from __future__ import annotations

from app.core.session import Session


class LockManager:
    def __init__(self, session: Session, timeout_seconds: int):
        self.session = session
        self.timeout_seconds = timeout_seconds

    def set_timeout(self, timeout_seconds: int) -> None:
        self.timeout_seconds = timeout_seconds

    def should_lock(self) -> bool:
        """Indica se a sessão autenticada e não bloqueada excedeu o
        tempo de inatividade permitido."""
        if not self.session.is_authenticated or self.session.is_locked:
            return False
        return self.session.seconds_since_last_activity() >= self.timeout_seconds

    def check_and_apply(self) -> bool:
        """Verifica e aplica o bloqueio, se necessário.

        Retorna True se o app acabou de ser bloqueado nesta checagem.
        """
        if self.should_lock():
            self.session.lock()
            return True
        return False
