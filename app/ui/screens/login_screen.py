"""
app.ui.screens.login_screen
=============================

Exibida quando já existe uma senha mestre cadastrada. Solicita a
senha e autentica via `app.security.auth_service.login`.
"""

from __future__ import annotations

from typing import Callable

from app.core.app_controller import AppController
from app.models.user import User
from app.security import auth_service
from app.ui.components.auth_layout import AuthLayout
from app.ui.components.buttons import PrimaryButton
from app.ui.components.dialogs import MessageDialog
from app.ui.components.inputs import PasswordEntry
from app.ui.theme import Spacing


class LoginScreen(AuthLayout):
    def __init__(self, master, controller: AppController, on_success: Callable[[User], None]):
        super().__init__(master, subtitle="Digite sua senha mestre para entrar.")
        self.controller = controller
        self.on_success = on_success

        self.password_field = PasswordEntry(self.form_area, label="Senha mestre")
        self.password_field.pack(fill="x", pady=(0, Spacing.MD))
        self.password_field.bind_enter(self._submit)

        self.submit_button = PrimaryButton(self.form_area, text="Entrar", command=self._submit)
        self.submit_button.pack(fill="x")

        self.password_field.focus()

    def _submit(self) -> None:
        password = self.password_field.get()
        result = auth_service.login(self.controller.connection, password)

        if not result.success:
            MessageDialog(
                self, title="Não foi possível entrar", message=result.error_message or "Erro desconhecido.", kind="error"
            )
            return

        assert result.user is not None
        self.controller.session.login(result.user)
        self.on_success(result.user)
