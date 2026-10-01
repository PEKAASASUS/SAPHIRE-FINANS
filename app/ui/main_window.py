"""
app.ui.main_window
====================

Janela principal do SAFIRA. Responsável por:

- alternar entre o fluxo de autenticação (criar senha mestre / login /
  bloqueio) e a "casca" principal do app (sidebar + cabeçalho + rota
  ativa);
- registrar todas as telas de navegação no Router;
- monitorar atividade do usuário e acionar o bloqueio automático via
  LockManager.

Este é o único módulo que "conhece" tanto a UI quanto o AppController —
todas as outras telas recebem apenas o que precisam (controller,
callbacks), mantendo baixo acoplamento.
"""

from __future__ import annotations

import customtkinter as ctk

from app.config.settings import (
    APP_FULL_NAME,
    WINDOW_DEFAULT_HEIGHT,
    WINDOW_DEFAULT_WIDTH,
    WINDOW_MIN_HEIGHT,
    WINDOW_MIN_WIDTH,
)
from app.core.app_controller import AppController
from app.database.connection import close_connection
from app.security import auth_service
from app.ui.components.dialogs import ConfirmDialog
from app.ui.components.header import Header
from app.ui.navigation.router import Router
from app.ui.navigation.sidebar import NAV_ITEMS, Sidebar
from app.ui.screens.home_screen import HomeScreen
from app.ui.screens.lock_screen import LockScreen
from app.ui.screens.login_screen import LoginScreen
from app.ui.screens.placeholder_screen import make_placeholder_screen
from app.ui.screens.setup_master_password_screen import SetupMasterPasswordScreen
from app.ui.theme import Colors, apply_global_appearance
from app.utils.logger import get_logger

logger = get_logger(__name__)

_LOCK_CHECK_INTERVAL_MS = 1000
_ACTIVITY_EVENTS = ("<Motion>", "<KeyPress>", "<Button>")


class MainWindow(ctk.CTk):
    def __init__(self, controller: AppController):
        apply_global_appearance()
        super().__init__()

        self.controller = controller

        self.title(APP_FULL_NAME)
        self.geometry(f"{WINDOW_DEFAULT_WIDTH}x{WINDOW_DEFAULT_HEIGHT}")
        self.minsize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
        self.configure(fg_color=Colors.BLACK)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        # Container único: hospeda ou o fluxo de autenticação (tela cheia)
        # ou a casca principal (sidebar + header + conteúdo roteado).
        self.container = ctk.CTkFrame(self, fg_color=Colors.BLACK, corner_radius=0)
        self.container.pack(fill="both", expand=True)

        self._sidebar: Sidebar | None = None
        self._header: Header | None = None
        self._router: Router | None = None

        self._bind_activity_events()
        self._schedule_lock_check()
        self._route_initial_view()

    # ------------------------------------------------------------------
    # Fluxo de autenticação
    # ------------------------------------------------------------------
    def _route_initial_view(self) -> None:
        if auth_service.needs_master_password_setup(self.controller.connection):
            self._show_setup()
        else:
            self._show_login()

    def _show_setup(self) -> None:
        self._clear_container()
        screen = SetupMasterPasswordScreen(self.container, self.controller, on_success=self._enter_app)
        screen.pack(fill="both", expand=True)

    def _show_login(self) -> None:
        self._clear_container()
        screen = LoginScreen(self.container, self.controller, on_success=self._enter_app)
        screen.pack(fill="both", expand=True)

    def _show_lock(self) -> None:
        self._clear_container()
        screen = LockScreen(
            self.container,
            self.controller,
            on_unlock=self._enter_app,
            on_logout=self._show_login,
        )
        screen.pack(fill="both", expand=True)

    def _enter_app(self, *_args) -> None:
        """Chamado após login, criação de senha mestre ou desbloqueio.
        Aceita args extras (ex.: o `User` retornado pelo login) sem
        depender deles, pois a sessão já reflete o estado atual."""
        self._build_app_shell()

    # ------------------------------------------------------------------
    # Casca principal (sidebar + header + rota ativa)
    # ------------------------------------------------------------------
    def _build_app_shell(self) -> None:
        self._clear_container()

        shell = ctk.CTkFrame(self.container, fg_color=Colors.GRAPHITE_LIGHT, corner_radius=0)
        shell.pack(fill="both", expand=True)
        shell.grid_rowconfigure(0, weight=1)
        shell.grid_columnconfigure(1, weight=1)

        self._sidebar = Sidebar(shell, on_select=self._navigate)
        self._sidebar.grid(row=0, column=0, sticky="ns")

        right_side = ctk.CTkFrame(shell, fg_color=Colors.GRAPHITE_LIGHT, corner_radius=0)
        right_side.grid(row=0, column=1, sticky="nsew")
        right_side.grid_rowconfigure(1, weight=1)
        right_side.grid_columnconfigure(0, weight=1)

        self._header = Header(right_side, on_lock=self._manual_lock, on_logout=self._manual_logout)
        self._header.grid(row=0, column=0, sticky="ew")

        content_area = ctk.CTkFrame(right_side, fg_color=Colors.GRAPHITE_LIGHT, corner_radius=0)
        content_area.grid(row=1, column=0, sticky="nsew")

        self._router = Router(content_area)
        self._router.on_navigate(self._on_route_changed)
        self._register_screens()

        self._navigate("home")

    def _register_screens(self) -> None:
        assert self._router is not None
        user = self.controller.session.user

        self._router.register("home", lambda master: HomeScreen(master, user=user))

        for item in NAV_ITEMS:
            if item.key == "home":
                continue
            self._router.register(
                item.key, make_placeholder_screen(item.label, "disponível nas próximas etapas")
            )

    def _navigate(self, key: str) -> None:
        assert self._router is not None and self._sidebar is not None
        self._router.show(key)
        self._sidebar.set_active(key)

    def _on_route_changed(self, key: str) -> None:
        if self._header is None:
            return
        label = next((item.label for item in NAV_ITEMS if item.key == key), key.title())
        self._header.set_title(label)

    # ------------------------------------------------------------------
    # Sessão: bloqueio manual/automático e logout
    # ------------------------------------------------------------------
    def _manual_lock(self) -> None:
        self.controller.session.lock()
        self._show_lock()

    def _manual_logout(self) -> None:
        def _confirmed_logout() -> None:
            self.controller.session.logout()
            self._show_login()

        ConfirmDialog(
            self,
            title="Encerrar sessão",
            message="Deseja realmente encerrar a sessão atual do SAFIRA?",
            on_confirm=_confirmed_logout,
            confirm_text="Encerrar sessão",
            danger=True,
        )

    def _bind_activity_events(self) -> None:
        for sequence in _ACTIVITY_EVENTS:
            self.bind_all(sequence, self._on_user_activity, add="+")

    def _on_user_activity(self, _event=None) -> None:
        self.controller.session.touch()

    def _schedule_lock_check(self) -> None:
        self.after(_LOCK_CHECK_INTERVAL_MS, self._check_lock)

    def _check_lock(self) -> None:
        if self.controller.lock_manager.check_and_apply():
            logger.info("Aplicativo bloqueado automaticamente por inatividade.")
            self._show_lock()
        self._schedule_lock_check()

    # ------------------------------------------------------------------
    # Utilitários
    # ------------------------------------------------------------------
    def _clear_container(self) -> None:
        for widget in self.container.winfo_children():
            widget.destroy()

    def _on_close(self) -> None:
        self.controller.shutdown()
        close_connection()
        self.destroy()
