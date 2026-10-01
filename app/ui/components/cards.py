"""
app.ui.components.cards
========================

Container tipo "card" reutilizável — usado para agrupar conteúdo com
leve elevação visual (fundo grafite, cantos arredondados), seguindo a
identidade premium/sóbria do SAFIRA.
"""

from __future__ import annotations

import customtkinter as ctk

from app.ui.theme import Colors, Fonts, Spacing


class Card(ctk.CTkFrame):
    def __init__(self, master, title: str | None = None, **kwargs):
        defaults = dict(
            fg_color=Colors.GRAPHITE,
            corner_radius=14,
            border_width=1,
            border_color=Colors.BORDER,
        )
        defaults.update(kwargs)
        super().__init__(master, **defaults)

        self._body = self
        if title:
            self.title_label = ctk.CTkLabel(
                self,
                text=title,
                font=Fonts.subtitle(),
                text_color=Colors.TEXT_PRIMARY,
                anchor="w",
            )
            self.title_label.pack(fill="x", padx=Spacing.MD, pady=(Spacing.MD, Spacing.SM))

    @property
    def body(self) -> "Card":
        """Alias semântico para adicionar widgets filhos ao card."""
        return self
