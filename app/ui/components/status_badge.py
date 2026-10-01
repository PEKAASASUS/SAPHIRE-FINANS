"""
app.ui.components.status_badge
===============================

Indicador visual compacto para estados de sucesso, erro e atenção —
usado em mensagens de validação, listas e cabeçalhos de status.
"""

from __future__ import annotations

from typing import Literal

import customtkinter as ctk

from app.ui.theme import Colors, Fonts

StatusKind = Literal["success", "error", "warning"]

_STYLE_MAP = {
    "success": (Colors.SUCCESS, Colors.SUCCESS_BG),
    "error": (Colors.DANGER, Colors.DANGER_BG),
    "warning": (Colors.WARNING, Colors.WARNING_BG),
}


class StatusBadge(ctk.CTkLabel):
    def __init__(self, master, text: str, kind: StatusKind = "success", **kwargs):
        text_color, bg_color = _STYLE_MAP[kind]
        defaults = dict(
            text=f"  {text}  ",
            text_color=text_color,
            fg_color=bg_color,
            font=Fonts.small(),
            corner_radius=8,
        )
        defaults.update(kwargs)
        super().__init__(master, **defaults)

    def update_status(self, text: str, kind: StatusKind) -> None:
        text_color, bg_color = _STYLE_MAP[kind]
        self.configure(text=f"  {text}  ", text_color=text_color, fg_color=bg_color)
