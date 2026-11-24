$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath (Split-Path -Parent $PSScriptRoot)
New-Item -ItemType Directory -Force -Path '.test-tmp' | Out-Null
$testRun = '.test-tmp/run-' + (Get-Date -Format 'yyyyMMddHHmmssfff')
& '.\.venv\Scripts\python.exe' -m pytest --basetemp=$testRun @args
exit $LASTEXITCODE
