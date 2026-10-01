"""
app.ui.components.inputs
=========================

Campos de entrada reutilizáveis do SAFIRA.
"""

from __future__ import annotations

from typing import Optional

import customtkinter as ctk

from app.ui.theme import Colors, Fonts


class LabeledEntry(ctk.CTkFrame):
    """Campo de texto com rótulo acima, no padrão visual do SAFIRA."""

    def __init__(self, master, label: str, placeholder: str = "", **entry_kwargs):
        super().__init__(master, fg_color="transparent")

        self.label = ctk.CTkLabel(
            self, text=label, font=Fonts.small(), text_color=Colors.TEXT_SECONDARY, anchor="w"
        )
        self.label.pack(fill="x", pady=(0, 4))

        defaults = dict(
            placeholder_text=placeholder,
            fg_color=Colors.GRAPHITE_LIGHT,
            border_color=Colors.BORDER,
            text_color=Colors.TEXT_PRIMARY,
            corner_radius=8,
            height=38,
            font=Fonts.body(),
        )
        defaults.update(entry_kwargs)
        self.entry = ctk.CTkEntry(self, **defaults)
        self.entry.pack(fill="x")

    def get(self) -> str:
        return self.entry.get()

    def set(self, value: str) -> None:
        self.entry.delete(0, "end")
        self.entry.insert(0, value)

    def focus(self) -> None:
        self.entry.focus_set()


class PasswordEntry(ctk.CTkFrame):
    """Campo de senha com rótulo e botão de mostrar/ocultar."""

    def __init__(self, master, label: str = "Senha", placeholder: str = "Digite sua senha", **entry_kwargs):
        super().__init__(master, fg_color="transparent")
        self._visible = False

        self.label = ctk.CTkLabel(
            self, text=label, font=Fonts.small(), text_color=Colors.TEXT_SECONDARY, anchor="w"
        )
        self.label.pack(fill="x", pady=(0, 4))

        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x")
        row.grid_columnconfigure(0, weight=1)

        defaults = dict(
            placeholder_text=placeholder,
            fg_color=Colors.GRAPHITE_LIGHT,
            border_color=Colors.BORDER,
            text_color=Colors.TEXT_PRIMARY,
            corner_radius=8,
            height=38,
            font=Fonts.body(),
            show="•",
        )
        defaults.update(entry_kwargs)
        self.entry = ctk.CTkEntry(row, **defaults)
        self.entry.grid(row=0, column=0, sticky="ew")

        self.toggle_btn = ctk.CTkButton(
            row,
            text="Mostrar",
            width=70,
            height=38,
            corner_radius=8,
            fg_color=Colors.GRAPHITE_LIGHTER,
            hover_color=Colors.BORDER,
            text_color=Colors.TEXT_SECONDARY,
            font=Fonts.small(),
            command=self._toggle_visibility,
        )
        self.toggle_btn.grid(row=0, column=1, padx=(8, 0))

    def _toggle_visibility(self) -> None:
        self._visible = not self._visible
        self.entry.configure(show="" if self._visible else "•")
        self.toggle_btn.configure(text="Ocultar" if self._visible else "Mostrar")

    def get(self) -> str:
        return self.entry.get()

    def focus(self) -> None:
        self.entry.focus_set()

    def bind_enter(self, callback) -> None:
        self.entry.bind("<Return>", lambda _event: callback())
