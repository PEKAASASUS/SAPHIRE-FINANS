"""
app.ui.components.buttons
==========================

Botões reutilizáveis do design system do SAFIRA. Nenhuma tela deve
instanciar `ctk.CTkButton` diretamente com cores "cruas" — sempre usar
um destes componentes, garantindo consistência visual.
"""

from __future__ import annotations

from typing import Callable, Optional

import customtkinter as ctk

from app.ui.theme import Colors, Fonts


class PrimaryButton(ctk.CTkButton):
    """Ação principal da tela (ex.: Entrar, Salvar, Confirmar)."""

    def __init__(self, master, text: str, command: Optional[Callable] = None, **kwargs):
        defaults = dict(
            fg_color=Colors.SAFIRA_BLUE,
            hover_color=Colors.SAFIRA_BLUE_HOVER,
            text_color=Colors.TEXT_PRIMARY,
            font=Fonts.body(),
            corner_radius=10,
            height=40,
        )
        defaults.update(kwargs)
        super().__init__(master, text=text, command=command, **defaults)


class SecondaryButton(ctk.CTkButton):
    """Ação secundária (ex.: Cancelar, Voltar)."""

    def __init__(self, master, text: str, command: Optional[Callable] = None, **kwargs):
        defaults = dict(
            fg_color=Colors.GRAPHITE_LIGHTER,
            hover_color=Colors.BORDER,
            text_color=Colors.TEXT_PRIMARY,
            font=Fonts.body(),
            corner_radius=10,
            height=40,
        )
        defaults.update(kwargs)
        super().__init__(master, text=text, command=command, **defaults)


class DangerButton(ctk.CTkButton):
    """Ação destrutiva/crítica (ex.: Excluir, Sair, Encerrar sessão)."""

    def __init__(self, master, text: str, command: Optional[Callable] = None, **kwargs):
        defaults = dict(
            fg_color="transparent",
            hover_color=Colors.DANGER_BG,
            text_color=Colors.DANGER,
            border_color=Colors.DANGER,
            border_width=1,
            font=Fonts.body(),
            corner_radius=10,
            height=36,
        )
        defaults.update(kwargs)
        super().__init__(master, text=text, command=command, **defaults)


class GhostButton(ctk.CTkButton):
    """Ação discreta, sem destaque visual forte (ex.: itens da sidebar)."""

    def __init__(self, master, text: str, command: Optional[Callable] = None, **kwargs):
        defaults = dict(
            fg_color="transparent",
            hover_color=Colors.GRAPHITE_LIGHT,
            text_color=Colors.TEXT_SECONDARY,
            font=Fonts.body(),
            corner_radius=8,
            anchor="w",
            height=40,
        )
        defaults.update(kwargs)
        super().__init__(master, text=text, command=command, **defaults)
