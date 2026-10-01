"""
app.ui.navigation.router
=========================

Roteador simples baseado em troca de frames (screens) dentro de um
container fixo. Não é um roteador de URLs — é apenas um registro de
"nome da página -> fábrica de widget", com troca da tela visível.

Isso permite que a Etapa 2/3 adicionem novas telas (Movimentações,
Contas, Cartões, etc.) apenas registrando-as aqui, sem qualquer
alteração na estrutura de navegação principal (MainWindow/Sidebar).
"""

from __future__ import annotations

from typing import Callable, Dict

import customtkinter as ctk


ScreenFactory = Callable[[ctk.CTkBaseClass], ctk.CTkBaseClass]


class Router:
    def __init__(self, content_container: ctk.CTkBaseClass):
        self._container = content_container
        self._factories: Dict[str, ScreenFactory] = {}
        self._current_screen: ctk.CTkBaseClass | None = None
        self._current_name: str | None = None
        self._on_navigate_callbacks: list[Callable[[str], None]] = []

    def register(self, name: str, factory: ScreenFactory) -> None:
        """Registra uma tela pelo nome (ex.: 'home', 'movimentacoes')."""
        self._factories[name] = factory

    def on_navigate(self, callback: Callable[[str], None]) -> None:
        """Registra um callback chamado sempre que a navegação ocorre,
        recebendo o nome da tela ativada (usado pelo header/sidebar)."""
        self._on_navigate_callbacks.append(callback)

    def has_screen(self, name: str) -> bool:
        return name in self._factories

    def show(self, name: str) -> None:
        if name not in self._factories:
            raise KeyError(f"Tela não registrada no router: '{name}'")

        if self._current_screen is not None:
            self._current_screen.destroy()

        factory = self._factories[name]
        screen = factory(self._container)
        screen.pack(fill="both", expand=True)

        self._current_screen = screen
        self._current_name = name

        for callback in self._on_navigate_callbacks:
            callback(name)

    @property
    def current_name(self) -> str | None:
        return self._current_name
