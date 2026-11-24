param(
    [switch]$SkipDependencyInstall
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$exitCode = 1
$releaseRoot = Split-Path -Parent $PSScriptRoot
$previousLocation = Get-Location
$previousCache = $env:PYINSTALLER_CONFIG_DIR
$previousData = $env:SAFIRA_DATA_DIR
$retained = $null
$output = $null
$buildAttempted = $false

try {
    if ($env:OS -ne 'Windows_NT') { throw 'Este build requer Windows e Python 3.12 de 64 bits.' }
    Set-Location -LiteralPath $releaseRoot
    $python = Join-Path $releaseRoot '.venv\Scripts\python.exe'
    if (-not (Test-Path -LiteralPath $python -PathType Leaf)) {
        if (Test-Path -LiteralPath (Join-Path $releaseRoot '.venv')) {
            throw 'A pasta .venv existe, mas nao e uma venv Windows valida. Renomeie-a para preservar seus arquivos e execute novamente.'
        }
        $launcher = Get-Command py.exe -ErrorAction SilentlyContinue
        if (-not $launcher) { throw 'Instale Python 3.12 x64 com o Python Launcher (py.exe) e execute novamente.' }
        Write-Host 'Criando .venv com Python 3.12...'
        & $launcher.Source -3.12 -m venv (Join-Path $releaseRoot '.venv')
        if ($LASTEXITCODE -ne 0) { throw 'Nao foi possivel criar a venv. Verifique a instalacao do Python 3.12.' }
    }

    & $python -c "import sys; raise SystemExit(0 if sys.version_info[:2] == (3, 12) and sys.maxsize > 2**32 else 1)"
    if ($LASTEXITCODE -ne 0) {
        throw 'A .venv precisa usar Python 3.12 x64. Se veio de outro computador, renomeie-a e execute novamente para recria-la.'
    }
    if (-not $SkipDependencyInstall) {
        Write-Host 'Instalando/verificando requirements-dev.txt...'
        & $python -m pip install -r (Join-Path $releaseRoot 'requirements-dev.txt')
        if ($LASTEXITCODE -ne 0) { throw 'Falha nas dependencias. Confira sua conexao e tente novamente.' }
    }
    & $python -m pip check
    if ($LASTEXITCODE -ne 0) { throw 'Dependencias incompativeis. Corrija o ambiente antes do build.' }

    foreach ($asset in @('assets\brand\safira-logo-horizontal-transparente.png', 'assets\brand\safira-icon-transparente-256.png', 'assets\brand\favicon-transparente.ico', 'assets\version.txt', 'SAFIRA.spec')) {
        if (-not (Test-Path -LiteralPath (Join-Path $releaseRoot $asset) -PathType Leaf)) { throw "Arquivo obrigatorio ausente: $asset" }
    }

    $runId = (Get-Date -Format 'yyyyMMdd-HHmmssfff') + '-' + [guid]::NewGuid().ToString('N').Substring(0, 8)
    $qaRoot = Join-Path $releaseRoot ('.test-tmp\build-' + $runId)
    New-Item -ItemType Directory -Force -Path $qaRoot | Out-Null
    # All initialization checks use a disposable profile, never the personal database.
    $env:SAFIRA_DATA_DIR = Join-Path $qaRoot 'profile'
    Write-Host 'Executando testes...'
    $testTemp = Join-Path $qaRoot 'pytest'
    & $python -m pytest -q "--basetemp=$testTemp"
    if ($LASTEXITCODE -ne 0) { throw 'Testes falharam. O build foi interrompido.' }
    & $python main.py --check
    if ($LASTEXITCODE -ne 0) { throw 'Falha na verificacao de inicializacao por fonte.' }

    $buildTarget = [IO.Path]::GetFullPath((Join-Path $releaseRoot 'build\3.1.0'))
    $distTarget = [IO.Path]::GetFullPath((Join-Path $releaseRoot 'dist\3.1.0'))
    foreach ($target in @($buildTarget, $distTarget)) {
        if (-not $target.StartsWith($releaseRoot + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) { throw 'Destino de build invalido.' }
    }
    $env:PYINSTALLER_CONFIG_DIR = Join-Path $buildTarget 'cache'
    $output = Join-Path $distTarget 'SAFIRA'
    if (Test-Path -LiteralPath $output) {
        $retained = Join-Path $distTarget ('SAFIRA-anterior-' + $runId)
        Move-Item -LiteralPath $output -Destination $retained
        Write-Host "Build anterior preservado em: $retained"
    }
    $buildAttempted = $true
    Write-Host 'Gerando executavel com a logo transparente...'
    & $python -m PyInstaller --noconfirm --workpath $buildTarget --distpath $distTarget (Join-Path $releaseRoot 'SAFIRA.spec')
    if ($LASTEXITCODE -ne 0) { throw 'PyInstaller falhou. O build anterior continua na pasta preservada.' }
    $exe = Join-Path $output 'SAFIRA.exe'
    if (-not (Test-Path -LiteralPath $exe -PathType Leaf)) { throw 'Executavel nao foi gerado.' }
    Write-Host 'Verificando o executavel em perfil descartavel...'
    $check = Start-Process -FilePath $exe -ArgumentList '--check' -Wait -PassThru
    if ($check.ExitCode -ne 0) { throw 'O executavel falhou na verificacao --check.' }
    Write-Host ''
    Write-Host "Build concluido: $exe" -ForegroundColor Green
    Write-Host 'Distribua a pasta SAFIRA inteira, incluindo _internal.'
    $exitCode = 0
}
catch {
    Write-Host ''
    Write-Host ('BUILD INTERROMPIDO: ' + $_.Exception.Message) -ForegroundColor Red
    if ($buildAttempted) {
        try {
            if (Test-Path -LiteralPath $output) {
                $failed = Join-Path $distTarget ('SAFIRA-falhou-' + $runId)
                Move-Item -LiteralPath $output -Destination $failed
                Write-Host "Saida incompleta preservada em: $failed"
            }
            if ($retained -and (Test-Path -LiteralPath $retained)) {
                Move-Item -LiteralPath $retained -Destination $output
                Write-Host 'Build anterior recolocado na pasta SAFIRA.'
            }
        }
        catch { Write-Host ('Nao foi possivel reorganizar a saida: ' + $_.Exception.Message) -ForegroundColor Yellow }
    }
}
finally {
    $env:PYINSTALLER_CONFIG_DIR = $previousCache
    $env:SAFIRA_DATA_DIR = $previousData
    Set-Location -LiteralPath $previousLocation.Path
}
exit $exitCode
