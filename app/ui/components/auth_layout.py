"""
app.ui.components.auth_layout
==============================

Layout compartilhado pelas telas de autenticação (criação de senha
mestre, login e bloqueio): fundo preto de tela cheia, com um card
centralizado contendo a marca SAFIRA e o formulário específico de cada
tela.

O card se ajusta automaticamente à altura do conteúdo; a largura é
garantida por um "spacer" interno em `form_area`, evitando a
necessidade de travar width/height manualmente (o que é frágil em
Tkinter quando o conteúdo varia entre telas de login/setup/bloqueio).
"""

from __future__ import annotations

import customtkinter as ctk

from app.ui.components.cards import Card
from app.ui.theme import Colors, Fonts, Spacing

CARD_CONTENT_WIDTH = 340


class AuthLayout(ctk.CTkFrame):
    def __init__(self, master, subtitle: str):
        super().__init__(master, fg_color=Colors.BLACK, corner_radius=0)

        # Centraliza o conteúdo vertical e horizontalmente na tela toda.
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        wrapper = ctk.CTkFrame(self, fg_color="transparent")
        wrapper.grid(row=0, column=0)

        ctk.CTkLabel(
            wrapper,
            text="🔷 SAFIRA",
            font=Fonts.brand(),
            text_color=Colors.TEXT_PRIMARY,
        ).pack(pady=(0, Spacing.XS))

        ctk.CTkLabel(
            wrapper,
            text=subtitle,
            font=Fonts.body(),
            text_color=Colors.TEXT_SECONDARY,
        ).pack(pady=(0, Spacing.LG))

        self.card = Card(wrapper)
        self.card.pack()

        # Área interna onde cada tela adiciona seu formulário específico.
        self.form_area = ctk.CTkFrame(self.card, fg_color="transparent", width=CARD_CONTENT_WIDTH)
        self.form_area.pack(fill="both", expand=True, padx=Spacing.LG, pady=Spacing.LG)
