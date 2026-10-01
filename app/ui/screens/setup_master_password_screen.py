"""
app.ui.screens.setup_master_password_screen
=============================================

Exibida apenas no primeiro uso do SAFIRA (quando ainda não existe
nenhuma senha mestre cadastrada no banco). Cria o usuário local com a
senha informada, já em hash seguro (ver app.security.auth_service).
"""

from __future__ import annotations

from typing import Callable

import customtkinter as ctk

from app.config.settings import MIN_MASTER_PASSWORD_LENGTH
from app.core.app_controller import AppController
from app.models.user import User
from app.security import auth_service
from app.ui.components.auth_layout import AuthLayout
from app.ui.components.buttons import PrimaryButton
from app.ui.components.dialogs import MessageDialog
from app.ui.components.inputs import PasswordEntry
from app.ui.components.status_badge import StatusBadge
from app.ui.theme import Colors, Fonts, Spacing


class SetupMasterPasswordScreen(AuthLayout):
    def __init__(self, master, controller: AppController, on_success: Callable[[User], None]):
        super().__init__(
            master,
            subtitle="Bem-vindo! Crie sua senha mestre para começar.",
        )
        self.controller = controller
        self.on_success = on_success
        self._error_badge: StatusBadge | None = None

        _hint = self._make_hint()
        _hint.pack(fill="x", pady=(0, Spacing.MD))

        self.password_field = PasswordEntry(self.form_area, label="Nova senha mestre")
        self.password_field.pack(fill="x", pady=(0, Spacing.MD))

        self.confirm_field = PasswordEntry(self.form_area, label="Confirmar senha mestre")
        self.confirm_field.pack(fill="x", pady=(0, Spacing.MD))
        self.confirm_field.bind_enter(self._submit)

        self.submit_button = PrimaryButton(self.form_area, text="Criar senha mestre", command=self._submit)
        self.submit_button.pack(fill="x", pady=(Spacing.SM, 0))

        self.password_field.focus()

    def _make_hint(self):
        return ctk.CTkLabel(
            self.form_area,
            text=(
                f"A senha mestre protege o acesso ao SAFIRA. Use pelo menos "
                f"{MIN_MASTER_PASSWORD_LENGTH} caracteres e guarde-a em local seguro — "
                f"ela não pode ser recuperada."
            ),
            font=Fonts.small(),
            text_color=Colors.TEXT_SECONDARY,
            wraplength=340,
            justify="left",
        )

    def _submit(self) -> None:
        password = self.password_field.get()
        confirm = self.confirm_field.get()

        result = auth_service.setup_master_password(
            self.controller.connection, password, confirm
        )

        if not result.success:
            MessageDialog(
                self, title="Não foi possível continuar", message=result.error_message or "Erro desconhecido.", kind="error"
            )
            return

        assert result.user is not None
        self.controller.session.login(result.user)
        self.on_success(result.user)
