"""
app.ui.screens.placeholder_screen
====================================

Fábrica de telas "placeholder" para os itens da sidebar que ainda não
possuem implementação funcional (todos, exceto Home nesta Etapa 1).

Isso permite que a navegação completa já exista e funcione (o usuário
pode clicar em qualquer item do menu e ver uma resposta visual
coerente com a identidade do SAFIRA), sem antecipar funcionalidades
que pertencem às Etapas 2 e 3.
"""

from __future__ import annotations

import customtkinter as ctk

from app.ui.theme import Colors, Fonts, Spacing


def make_placeholder_screen(title: str, stage_note: str) -> type[ctk.CTkFrame]:
    """Cria uma classe de tela placeholder para o `title` e nota de etapa
    informados. Usada pelo router: `router.register(key, make_placeholder_screen(...))`.
    """

    class _PlaceholderScreen(ctk.CTkFrame):
        def __init__(self, master):
            super().__init__(master, fg_color=Colors.GRAPHITE_LIGHT, corner_radius=0)

            wrapper = ctk.CTkFrame(self, fg_color="transparent")
            wrapper.place(relx=0.5, rely=0.45, anchor="center")

            ctk.CTkLabel(
                wrapper,
                text="🛠️",
                font=ctk.CTkFont(size=40),
            ).pack(pady=(0, Spacing.SM))

            ctk.CTkLabel(
                wrapper,
                text=title,
                font=Fonts.title(),
                text_color=Colors.TEXT_PRIMARY,
            ).pack()

            ctk.CTkLabel(
                wrapper,
                text=f"Em construção — {stage_note}",
                font=Fonts.body(),
                text_color=Colors.TEXT_SECONDARY,
            ).pack(pady=(Spacing.XS, 0))

    return _PlaceholderScreen
