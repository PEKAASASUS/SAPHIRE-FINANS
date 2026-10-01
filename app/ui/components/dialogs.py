"""
app.ui.components.dialogs
==========================

Diálogos modais reutilizáveis: mensagem simples (sucesso/erro/atenção)
e confirmação de ação (ex.: encerrar sessão).
"""

from __future__ import annotations

from typing import Callable, Literal, Optional

import customtkinter as ctk

from app.ui.components.buttons import DangerButton, PrimaryButton, SecondaryButton
from app.ui.theme import Colors, Fonts, Spacing

DialogKind = Literal["success", "error", "warning", "info"]

_ICON_MAP = {
    "success": "✅",
    "error": "⛔",
    "warning": "⚠️",
    "info": "ℹ️",
}


class MessageDialog(ctk.CTkToplevel):
    def __init__(self, master, title: str, message: str, kind: DialogKind = "info"):
        super().__init__(master)
        self.title(title)
        self.geometry("380x180")
        self.resizable(False, False)
        self.configure(fg_color=Colors.GRAPHITE)
        self.grab_set()  # modal

        icon = _ICON_MAP.get(kind, "ℹ️")
        ctk.CTkLabel(
            self, text=f"{icon}  {title}", font=Fonts.subtitle(), text_color=Colors.TEXT_PRIMARY
        ).pack(pady=(Spacing.LG, Spacing.SM), padx=Spacing.LG, anchor="w")

        ctk.CTkLabel(
            self,
            text=message,
            font=Fonts.body(),
            text_color=Colors.TEXT_SECONDARY,
            wraplength=320,
            justify="left",
        ).pack(padx=Spacing.LG, anchor="w")

        PrimaryButton(self, text="OK", command=self.destroy).pack(
            side="bottom", pady=Spacing.LG, padx=Spacing.LG, fill="x"
        )


class ConfirmDialog(ctk.CTkToplevel):
    def __init__(
        self,
        master,
        title: str,
        message: str,
        on_confirm: Callable[[], None],
        confirm_text: str = "Confirmar",
        danger: bool = False,
    ):
        super().__init__(master)
        self.title(title)
        self.geometry("380x200")
        self.resizable(False, False)
        self.configure(fg_color=Colors.GRAPHITE)
        self.grab_set()

        ctk.CTkLabel(
            self, text=title, font=Fonts.subtitle(), text_color=Colors.TEXT_PRIMARY
        ).pack(pady=(Spacing.LG, Spacing.SM), padx=Spacing.LG, anchor="w")

        ctk.CTkLabel(
            self,
            text=message,
            font=Fonts.body(),
            text_color=Colors.TEXT_SECONDARY,
            wraplength=320,
            justify="left",
        ).pack(padx=Spacing.LG, anchor="w")

        button_row = ctk.CTkFrame(self, fg_color="transparent")
        button_row.pack(side="bottom", pady=Spacing.LG, padx=Spacing.LG, fill="x")

        def _confirm_and_close():
            self.destroy()
            on_confirm()

        SecondaryButton(button_row, text="Cancelar", command=self.destroy).pack(
            side="left", expand=True, fill="x", padx=(0, Spacing.SM)
        )
        confirm_button_cls = DangerButton if danger else PrimaryButton
        confirm_button_cls(button_row, text=confirm_text, command=_confirm_and_close).pack(
            side="left", expand=True, fill="x"
        )
