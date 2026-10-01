"""
app.ui.theme
============

Identidade visual centralizada do SAFIRA.

Todo componente da interface deve importar cores e fontes daqui — nunca
usar valores de cor "soltos" espalhados pelo código. Isso garante que a
identidade visual (item 7 do briefing) permaneça consistente e fácil de
ajustar em um único lugar.

Paleta: preto, grafite e azul Safira, com verde/vermelho/amarelo
reservados exclusivamente para significado semântico (positivo,
negativo, atenção) — nunca decorativos.
"""

from __future__ import annotations

import customtkinter as ctk


class Colors:
    # Base — preto e grafite (fundo, elevação de superfícies)
    BLACK = "#0B0D10"
    GRAPHITE = "#15181D"
    GRAPHITE_LIGHT = "#1E2229"
    GRAPHITE_LIGHTER = "#2A2F38"
    BORDER = "#2E333C"

    # Azul Safira — cor principal da marca e de ações primárias
    SAFIRA_BLUE = "#2F6FED"
    SAFIRA_BLUE_HOVER = "#3D7DFF"
    SAFIRA_BLUE_DIM = "#1B3A73"
    SAFIRA_GLOW = "#2F6FED33"  # uso sutil (bordas/realces), nunca neon

    # Texto
    TEXT_PRIMARY = "#F2F4F7"
    TEXT_SECONDARY = "#9AA3AF"
    TEXT_DISABLED = "#5C636F"

    # Semântico — significado, não decoração
    SUCCESS = "#2ECC71"    # entradas / valores positivos
    DANGER = "#E5484D"     # saídas / valores negativos
    WARNING = "#E8B339"    # atenção / pendências

    # Superfícies de estado (fundo suave para banners/badges)
    SUCCESS_BG = "#1B3A2A"
    DANGER_BG = "#3A1E20"
    WARNING_BG = "#3A331A"


class Fonts:
    FAMILY = "Segoe UI"  # fallback confiável no Windows; customtkinter
                          # usa a fonte padrão do SO caso não exista.

    @staticmethod
    def title() -> ctk.CTkFont:
        return ctk.CTkFont(family=Fonts.FAMILY, size=22, weight="bold")

    @staticmethod
    def subtitle() -> ctk.CTkFont:
        return ctk.CTkFont(family=Fonts.FAMILY, size=15, weight="bold")

    @staticmethod
    def body() -> ctk.CTkFont:
        return ctk.CTkFont(family=Fonts.FAMILY, size=13)

    @staticmethod
    def small() -> ctk.CTkFont:
        return ctk.CTkFont(family=Fonts.FAMILY, size=11)

    @staticmethod
    def brand() -> ctk.CTkFont:
        return ctk.CTkFont(family=Fonts.FAMILY, size=20, weight="bold")


class Spacing:
    XS = 4
    SM = 8
    MD = 16
    LG = 24
    XL = 32

    SIDEBAR_WIDTH = 240


def apply_global_appearance() -> None:
    """Configura o modo de aparência global do CustomTkinter.

    Chamado uma única vez, no início da aplicação (main_window), antes
    de qualquer widget ser criado.
    """
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")  # base neutra; cores reais vêm de Colors
