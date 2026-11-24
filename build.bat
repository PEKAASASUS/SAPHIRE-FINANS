@echo off
setlocal
pushd "%~dp0" || exit /b 1
where powershell.exe >nul 2>&1
if errorlevel 1 (
    echo ERRO: Windows PowerShell nao encontrado.
    set "buildResult=1"
    goto :done
)
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\build.ps1" %*
set "buildResult=%errorlevel%"
:done
popd
if not defined SAFIRA_BUILD_NO_PAUSE pause
exit /b %buildResult%
