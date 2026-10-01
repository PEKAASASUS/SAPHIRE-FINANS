"""
app.core.session
=================

Representa a sessão ativa do usuário dentro do aplicativo em execução.

A Session vive apenas em memória (nunca é persistida em disco). Ela
controla:
- se há um usuário autenticado no momento;
- se o app está bloqueado (lock) sem ter feito logout completo;
- o timestamp da última atividade, usado pelo LockManager para
  decidir quando bloquear automaticamente por inatividade.

Diferença entre "bloquear" e "logout":
- Bloquear: a sessão continua logicamente ativa (o usuário não precisa
  reabrir o app do zero), mas a interface fica oculta atrás da tela de
  bloqueio até a senha ser digitada novamente.
- Logout: encerra a sessão por completo, retornando à tela de login.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from app.models.user import User


@dataclass
class Session:
    user: User | None = None
    is_locked: bool = False
    _last_activity: float = field(default_factory=time.monotonic, repr=False)

    @property
    def is_authenticated(self) -> bool:
        return self.user is not None

    def login(self, user: User) -> None:
        self.user = user
        self.is_locked = False
        self.touch()

    def logout(self) -> None:
        self.user = None
        self.is_locked = False

    def lock(self) -> None:
        if self.is_authenticated:
            self.is_locked = True

    def unlock(self) -> None:
        self.is_locked = False
        self.touch()

    def touch(self) -> None:
        """Registra atividade recente do usuário (reseta o contador de
        inatividade usado para o bloqueio automático)."""
        self._last_activity = time.monotonic()

    def seconds_since_last_activity(self) -> float:
        return time.monotonic() - self._last_activity
