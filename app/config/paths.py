"""
app.config.paths
=================

Resolução centralizada de caminhos do SAFIRA.

Este módulo é a ÚNICA fonte de verdade sobre "onde as coisas moram" no
disco. Nenhum outro módulo deve montar caminhos manualmente com base em
`os.getcwd()`, `~` (home do usuário) ou diretórios fixos do sistema
operacional (`AppData`, `~/.config`, etc). Isso é o que garante a
portabilidade exigida pelo projeto: o SAFIRA deve poder rodar a partir
de um pendrive, em qualquer computador, sem gravar nada fora da sua
própria pasta.

Regra de ouro:
    BASE_DIR = pasta onde o SAFIRA está instalado (pendrive ou disco).

Quando o app estiver empacotado com PyInstaller (modo "frozen"), o
`sys.executable` aponta para o .exe portátil, e é a partir dele que
calculamos a BASE_DIR. Quando rodando via `python main.py`, usamos a
pasta que contém o próprio projeto (dois níveis acima deste arquivo).
"""

from __future__ import annotations

import sys
from pathlib import Path


def _detect_base_dir() -> Path:
    """Detecta a pasta raiz portátil do SAFIRA.

    - Executável empacotado (PyInstaller/cx_Freeze): usa a pasta do .exe.
    - Execução via código-fonte: usa a raiz do projeto (onde está main.py).
    """
    if getattr(sys, "frozen", False):
        # Aplicativo empacotado (ex.: SAFIRA.exe rodando do pendrive)
        return Path(sys.executable).resolve().parent

    # app/config/paths.py -> sobe 2 níveis até a raiz do projeto
    return Path(__file__).resolve().parent.parent.parent


# Pasta raiz portátil (tudo deve viver dentro dela)
BASE_DIR: Path = _detect_base_dir()

# Subpastas padronizadas do projeto
APP_DIR: Path = BASE_DIR / "app"
ASSETS_DIR: Path = BASE_DIR / "assets"
ICONS_DIR: Path = ASSETS_DIR / "icons"
DATA_DIR: Path = BASE_DIR / "data"
CONFIG_DIR: Path = BASE_DIR / "config"
LOGS_DIR: Path = DATA_DIR / "logs"

# Arquivos específicos
DATABASE_FILE: Path = DATA_DIR / "safira.db"
APP_CONFIG_FILE: Path = CONFIG_DIR / "app_config.json"


def ensure_runtime_directories() -> None:
    """Garante que as pastas de dados/config/logs existem.

    Deve ser chamada uma única vez, no início do `main.py`, antes de
    qualquer acesso a banco de dados, configuração ou log. Não cria
    nada fora de BASE_DIR.
    """
    for directory in (DATA_DIR, CONFIG_DIR, LOGS_DIR, ICONS_DIR):
        directory.mkdir(parents=True, exist_ok=True)


def is_portable_safe() -> bool:
    """Verificação de sanidade: confirma que os caminhos calculados
    estão dentro de BASE_DIR (nunca em pastas do usuário/sistema).

    Usado nos testes e na checklist de validação da Etapa 1.
    """
    paths_to_check = (DATA_DIR, CONFIG_DIR, LOGS_DIR, DATABASE_FILE.parent)
    return all(str(p.resolve()).startswith(str(BASE_DIR.resolve())) for p in paths_to_check)
