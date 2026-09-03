param(
    [string]$ProjectRoot = (Split-Path -Parent $PSScriptRoot),
    [switch]$Dev,
    [switch]$SkipDatabase,
    [string]$Locale = "ru"
)

$ErrorActionPreference = "Stop"
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch {}

. (Join-Path $PSScriptRoot "common.ps1")
$messages = Import-SoleProMessages -ScriptsRoot $PSScriptRoot -Locale $Locale
function Msg([string]$Key, [object[]]$Arguments = @()) {
    return Get-SoleProMessage -Messages $messages -Key $Key -Arguments $Arguments
}
function Step([string]$Key, [object[]]$Arguments = @()) {
    Write-Host ("==> " + (Msg $Key $Arguments)) -ForegroundColor Cyan
}
function Ok([string]$Key, [object[]]$Arguments = @()) {
    Write-Host ("    " + (Msg $Key $Arguments)) -ForegroundColor Green
}
function Run-Python($Python, [string[]]$Arguments, [string]$Description) {
    & $Python.Exe @($Python.Prefix + $Arguments)
    if ($LASTEXITCODE -ne 0) {
        throw (Msg "error_command" @($LASTEXITCODE, $Description))
    }
}

Write-Host (Msg "setup_title") -ForegroundColor Cyan
Write-Host (Msg "setup_root" @($ProjectRoot))

foreach ($required in @("pyproject.toml", "requirements.txt", ".env.example")) {
    $path = Join-Path $ProjectRoot $required
    if (-not (Test-Path -LiteralPath $path)) {
        throw (Msg "error_missing_file" @($path))
    }
}

$venvPythonPath = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $venvPythonPath)) {
    $systemPython = Resolve-SoleProPython -Root $ProjectRoot -SystemOnly
    if ($null -eq $systemPython) {
        throw (Msg "error_python")
    }
    Ok "setup_python" @($systemPython.Exe, ($systemPython.Prefix -join " "))
    Step "setup_venv_create"
    Run-Python $systemPython @("-m", "venv", (Join-Path $ProjectRoot ".venv")) "venv"
} else {
    Ok "setup_venv_exists"
}

$venvPython = Resolve-SoleProPython -Root $ProjectRoot
if ($null -eq $venvPython -or $venvPython.Exe -ne $venvPythonPath) {
    throw (Msg "error_python")
}

Push-Location $ProjectRoot
try {
    Step "setup_pip"
    Run-Python $venvPython @("-m", "pip", "install", "--upgrade", "pip") "pip upgrade"

    Step "setup_dependencies"
    Run-Python $venvPython @("-m", "pip", "install", "-r", "requirements.txt") "requirements"

    Step "setup_project"
    Run-Python $venvPython @("-m", "pip", "install", "--no-deps", "-e", $ProjectRoot) "project"

    if ($Dev) {
        Step "setup_dev_dependencies"
        Run-Python $venvPython @("-m", "pip", "install", "-r", "requirements-dev.txt") "dev requirements"
    }

    $envPath = Join-Path $ProjectRoot ".env"
    if (-not (Test-Path -LiteralPath $envPath)) {
        Copy-Item -LiteralPath (Join-Path $ProjectRoot ".env.example") -Destination $envPath
        Ok "setup_env_created"
    } else {
        Ok "setup_env_preserved"
    }

    Step "setup_directories"
    foreach ($directory in @("data", "logs", "backups", "exports")) {
        New-Item -ItemType Directory -Force -Path (Join-Path $ProjectRoot $directory) | Out-Null
    }

    if (-not $SkipDatabase) {
        Step "setup_database"
        Run-Python $venvPython @("scripts\init_db.py") "database initialization"
    } else {
        Write-Host ("    " + (Msg "setup_database_skipped")) -ForegroundColor Yellow
    }
} finally {
    Pop-Location
}

Write-Host ""
Write-Host (Msg "setup_complete") -ForegroundColor Cyan
Write-Host (Msg "setup_next") -ForegroundColor Green
