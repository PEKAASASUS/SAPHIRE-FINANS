"""
app.ui.components.header
=========================

Cabeçalho superior exibido dentro da área de conteúdo (ao lado da
sidebar), com o título da página atual e os controles de sessão
(bloquear / encerrar sessão).
"""

from __future__ import annotations

from typing import Callable

import customtkinter as ctk

from app.ui.components.buttons import GhostButton
from app.ui.theme import Colors, Fonts, Spacing


class Header(ctk.CTkFrame):
    def __init__(
        self,
        master,
        on_lock: Callable[[], None],
        on_logout: Callable[[], None],
        **kwargs,
    ):
        defaults = dict(fg_color=Colors.BLACK, height=64, corner_radius=0)
        defaults.update(kwargs)
        super().__init__(master, **defaults)
        self.grid_propagate(False)
        self.grid_columnconfigure(0, weight=1)

        self.title_label = ctk.CTkLabel(
            self,
            text="",
            font=Fonts.title(),
            text_color=Colors.TEXT_PRIMARY,
            anchor="w",
        )
        self.title_label.grid(row=0, column=0, sticky="w", padx=Spacing.LG)

        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.grid(row=0, column=1, sticky="e", padx=Spacing.LG)

        self.lock_button = GhostButton(actions, text="🔒 Bloquear", command=on_lock, width=110)
        self.lock_button.pack(side="left", padx=(0, Spacing.SM))

        self.logout_button = GhostButton(actions, text="↪ Sair", command=on_logout, width=90)
        self.logout_button.pack(side="left")

    def set_title(self, title: str) -> None:
        self.title_label.configure(text=title)
