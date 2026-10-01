"""
app.ui.screens.lock_screen
============================

Exibida quando o aplicativo é bloqueado — manualmente pelo usuário ou
automaticamente por inatividade (ver app.security.lock_manager).

Diferente do logout: a sessão continua ativa (o usuário autenticado
não muda), apenas a interface fica oculta até a senha ser confirmada
novamente. Também é oferecida a opção de encerrar a sessão a partir
daqui, para quem preferir sair completamente.
"""

from __future__ import annotations

from typing import Callable

from app.core.app_controller import AppController
from app.security import auth_service
from app.ui.components.auth_layout import AuthLayout
from app.ui.components.buttons import GhostButton, PrimaryButton
from app.ui.components.dialogs import MessageDialog
from app.ui.components.inputs import PasswordEntry
from app.ui.theme import Colors, Fonts, Spacing


class LockScreen(AuthLayout):
    def __init__(
        self,
        master,
        controller: AppController,
        on_unlock: Callable[[], None],
        on_logout: Callable[[], None],
    ):
        user = controller.session.user
        user_name = user.name if user else "Usuário"

        super().__init__(master, subtitle=f"🔒 Aplicativo bloqueado — {user_name}")
        self.controller = controller
        self.on_unlock = on_unlock
        self.on_logout = on_logout

        self.password_field = PasswordEntry(self.form_area, label="Senha mestre")
        self.password_field.pack(fill="x", pady=(0, Spacing.MD))
        self.password_field.bind_enter(self._submit)

        self.submit_button = PrimaryButton(self.form_area, text="Desbloquear", command=self._submit)
        self.submit_button.pack(fill="x", pady=(0, Spacing.SM))

        GhostButton(self.form_area, text="Encerrar sessão", command=self._logout, anchor="center").pack(fill="x")

        self.password_field.focus()

    def _submit(self) -> None:
        password = self.password_field.get()
        result = auth_service.login(self.controller.connection, password)

        if not result.success:
            MessageDialog(
                self, title="Senha incorreta", message="Não foi possível desbloquear o SAFIRA.", kind="error"
            )
            return

        self.controller.session.unlock()
        self.on_unlock()

    def _logout(self) -> None:
        self.controller.session.logout()
        self.on_logout()
