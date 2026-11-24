# Build on Windows with CPython 3.12. One-folder distribution, no transient data path.
from PyInstaller.utils.hooks import collect_data_files, collect_submodules
a = Analysis(['main.py'], pathex=[], binaries=[],
    datas=collect_data_files('customtkinter') + [('assets/brand', 'assets/brand')],
    hiddenimports=collect_submodules('argon2') + collect_submodules('_argon2_cffi_bindings'),
    hookspath=[], hooksconfig={}, runtime_hooks=[], excludes=[], noarchive=False)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name='SAFIRA', debug=False,
    bootloader_ignore_signals=False, strip=False, upx=False, console=False,
    version='assets/version.txt', icon='assets/brand/favicon-transparente.ico')
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name='SAFIRA')
