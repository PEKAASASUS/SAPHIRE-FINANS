"""
SAFIRA — Controle Financeiro Pessoal
======================================

Ponto de entrada do aplicativo (Etapa 1 — Fundação).

Execução:
    python main.py

Este arquivo permanece intencionalmente enxuto: toda a lógica de
inicialização vive em `app.core.app_controller.AppController`, e toda a
interface em `app.ui.main_window.MainWindow`. `main.py` apenas conecta
as duas pontas e trata falhas fatais de inicialização.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Garante que o pacote `app` seja importável independentemente de qual
# seja o diretório de trabalho atual no momento da execução — essencial
# para que o SAFIRA funcione corretamente quando executado a partir de
# um pendrive em qualquer computador.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.core.app_controller import AppController  # noqa: E402
from app.ui.main_window import MainWindow  # noqa: E402
from app.utils.logger import get_logger  # noqa: E402

logger = get_logger("main")


def main() -> None:
    try:
        controller = AppController()
        window = MainWindow(controller)
        window.mainloop()
    except Exception:
        logger.exception("Erro fatal ao iniciar o SAFIRA.")
        raise


if __name__ == "__main__":
    main()
