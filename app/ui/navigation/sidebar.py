"""
app.ui.navigation.sidebar
==========================

Barra lateral principal do SAFIRA.

Contém TODOS os itens de navegação previstos para o produto completo
(Home, Movimentações, Contas, Cartões, Planejamento, Compromissos,
Mapa do Dinheiro, Metas/Cofres, Investimentos, Relatórios,
Notificações, Configurações), mesmo que a maioria ainda aponte para
telas placeholder nesta Etapa 1. Isso evita que a estrutura de
navegação precise ser refeita nas próximas etapas — apenas as telas
"por trás" de cada item serão implementadas.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import customtkinter as ctk

from app.ui.theme import Colors, Fonts, Spacing


@dataclass(frozen=True)
class NavItem:
    key: str
    icon: str
    label: str


NAV_ITEMS: list[NavItem] = [
    NavItem("home", "🏠", "Home"),
    NavItem("movimentacoes", "💰", "Movimentações"),
    NavItem("contas", "🏦", "Contas"),
    NavItem("cartoes", "💳", "Cartões"),
    NavItem("planejamento", "📅", "Planejamento"),
    NavItem("compromissos", "🔔", "Compromissos"),
    NavItem("mapa_do_dinheiro", "🗺️", "Mapa do Dinheiro"),
    NavItem("metas", "🎯", "Metas / Cofres"),
    NavItem("investimentos", "📈", "Investimentos"),
    NavItem("relatorios", "📊", "Relatórios"),
    NavItem("notificacoes", "🔔", "Notificações"),
    NavItem("configuracoes", "⚙️", "Configurações"),
]


class Sidebar(ctk.CTkFrame):
    def __init__(self, master, on_select: Callable[[str], None]):
        super().__init__(
            master,
            fg_color=Colors.BLACK,
            width=Spacing.SIDEBAR_WIDTH,
            corner_radius=0,
        )
        self.grid_propagate(False)
        self._on_select = on_select
        self._buttons: dict[str, ctk.CTkButton] = {}
        self._active_key: str | None = None

        self._build_brand()
        self._build_nav_items()

    def _build_brand(self) -> None:
        brand_frame = ctk.CTkFrame(self, fg_color="transparent", height=72)
        brand_frame.pack(fill="x", pady=(Spacing.LG, Spacing.MD), padx=Spacing.MD)

        ctk.CTkLabel(
            brand_frame,
            text="🔷 SAFIRA",
            font=Fonts.brand(),
            text_color=Colors.TEXT_PRIMARY,
        ).pack(anchor="w")

        ctk.CTkLabel(
            brand_frame,
            text="Controle Financeiro",
            font=Fonts.small(),
            text_color=Colors.TEXT_SECONDARY,
        ).pack(anchor="w")

    def _build_nav_items(self) -> None:
        nav_container = ctk.CTkScrollableFrame(
            self, fg_color="transparent", scrollbar_button_color=Colors.GRAPHITE_LIGHTER
        )
        nav_container.pack(fill="both", expand=True, padx=Spacing.SM)

        for item in NAV_ITEMS:
            button = ctk.CTkButton(
                nav_container,
                text=f"  {item.icon}   {item.label}",
                anchor="w",
                fg_color="transparent",
                hover_color=Colors.GRAPHITE_LIGHT,
                text_color=Colors.TEXT_SECONDARY,
                font=Fonts.body(),
                corner_radius=8,
                height=42,
                command=lambda k=item.key: self._handle_select(k),
            )
            button.pack(fill="x", pady=2)
            self._buttons[item.key] = button

    def _handle_select(self, key: str) -> None:
        self.set_active(key)
        self._on_select(key)

    def set_active(self, key: str) -> None:
        if self._active_key and self._active_key in self._buttons:
            self._buttons[self._active_key].configure(
                fg_color="transparent", text_color=Colors.TEXT_SECONDARY
            )

        if key in self._buttons:
            self._buttons[key].configure(
                fg_color=Colors.SAFIRA_BLUE_DIM, text_color=Colors.TEXT_PRIMARY
            )
            self._active_key = key
