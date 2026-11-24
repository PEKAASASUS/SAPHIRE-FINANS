@echo off
cd /d "%~dp0"
if exist "dist\3.1.0\SAFIRA\SAFIRA.exe" (
    start "" "dist\3.1.0\SAFIRA\SAFIRA.exe"
) else (
    ".venv\Scripts\pythonw.exe" main.py
)
