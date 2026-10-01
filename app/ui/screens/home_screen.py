"""
app.ui.screens.home_screen
=============================

Home minimalista da Etapa 1.

Por definição do briefing, a Home deve permanecer enxuta — funcionalidades
detalhadas (saldo consolidado, gráficos, últimas movimentações etc.)
pertencem à Etapa 2 e serão adicionadas aqui SEM alterar a estrutura de
navegação já criada.
"""

from __future__ import annotations

import customtkinter as ctk

from app.models.user import User
from app.ui.components.cards import Card
from app.ui.theme import Colors, Fonts, Spacing


class HomeScreen(ctk.CTkFrame):
    def __init__(self, master, user: User | None = None):
        super().__init__(master, fg_color=Colors.GRAPHITE_LIGHT, corner_radius=0)

        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=Spacing.XL, pady=Spacing.XL)

        name = user.name if user else "usuário"
        ctk.CTkLabel(
            content,
            text=f"Bem-vindo(a) de volta, {name}.",
            font=Fonts.title(),
            text_color=Colors.TEXT_PRIMARY,
            anchor="w",
        ).pack(fill="x", pady=(0, Spacing.SM))

        ctk.CTkLabel(
            content,
            text="A fundação do SAFIRA está pronta. O painel financeiro completo "
                 "chega na Etapa 2.",
            font=Fonts.body(),
            text_color=Colors.TEXT_SECONDARY,
            anchor="w",
        ).pack(fill="x", pady=(0, Spacing.LG))

        cards_row = ctk.CTkFrame(content, fg_color="transparent")
        cards_row.pack(fill="x")
        cards_row.grid_columnconfigure((0, 1, 2), weight=1, uniform="cards")

        self._empty_card(cards_row, "Saldo consolidado", "Disponível na Etapa 2").grid(
            row=0, column=0, sticky="nsew", padx=(0, Spacing.SM)
        )
        self._empty_card(cards_row, "Movimentações recentes", "Disponível na Etapa 2").grid(
            row=0, column=1, sticky="nsew", padx=Spacing.SM
        )
        self._empty_card(cards_row, "Compromissos próximos", "Disponível na Etapa 2").grid(
            row=0, column=2, sticky="nsew", padx=(Spacing.SM, 0)
        )

    @staticmethod
    def _empty_card(master, title: str, placeholder: str) -> Card:
        card = Card(master, title=title, height=140)
        ctk.CTkLabel(
            card,
            text=placeholder,
            font=Fonts.small(),
            text_color=Colors.TEXT_DISABLED,
        ).pack(padx=Spacing.MD, pady=(0, Spacing.MD), anchor="w")
        return card
