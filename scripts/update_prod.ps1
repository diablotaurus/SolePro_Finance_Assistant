# =====================================================================
#  SolePro Finance Assistant — обновление ПРОД-версии с GitHub.
#
#  Делает резервную копию реальной базы и снимок текущей версии,
#  забирает последний код из GitHub и обновляет зависимости.
#  Боевые .env, settings/ и data (символьная ссылка на реальную БД)
#  НЕ затрагиваются.
#
#  Запуск (из папки прода):
#     scripts\update_prod.bat
#  или:
#     powershell -NoProfile -ExecutionPolicy Bypass -File scripts\update_prod.ps1
#
#  ВАЖНО: перед запуском ЗАКРОЙТЕ приложение SolePro (десктоп и бот).
#  Скрипт ничего не удаляет из данных; перед обновлением база копируется
#  в .backup\db, а вся прежняя версия — в .backup\<версия>_<дата>.
# =====================================================================
param(
    [string]$ProdPath = (Split-Path -Parent $PSScriptRoot),
    [string]$RepoUrl  = "https://github.com/diablotaurus/SolePro_Finance_Assistant.git",
    [string]$Branch   = "main",
    [switch]$SkipDeps,
    [switch]$Yes
)

$ErrorActionPreference = "Stop"

function Write-Step($m) { Write-Host "==> $m" -ForegroundColor Cyan }
function Write-Ok($m)   { Write-Host "    $m" -ForegroundColor Green }
function Write-Note($m) { Write-Host "    $m" -ForegroundColor Yellow }

Write-Host "=== SolePro Finance Assistant — обновление прод-версии ===" -ForegroundColor Cyan
Write-Host "Прод-папка: $ProdPath"

# --- Проверки окружения ---
if (-not (Test-Path -LiteralPath (Join-Path $ProdPath "pyproject.toml"))) {
    throw "Не похоже на SolePro: не найден pyproject.toml в '$ProdPath'."
}

$dataPath = Join-Path $ProdPath "data"
$dataItem = Get-Item -LiteralPath $dataPath -Force -ErrorAction SilentlyContinue
$isSymlink = $dataItem -and (($dataItem.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0)
if ($isSymlink) {
    Write-Ok "data -> $($dataItem.Target)"
    if ($dataItem.Target -and -not (Test-Path -LiteralPath $dataItem.Target)) {
        throw "Цель символьной ссылки data не найдена: $($dataItem.Target). Проверьте, смонтирован ли диск."
    }
} else {
    Write-Note "ВНИМАНИЕ: 'data' не является символьной ссылкой — возможно, это НЕ прод-папка."
    if (-not $Yes) {
        $ans = Read-Host "Продолжить всё равно? (введите 'yes' для продолжения)"
        if ($ans -ne "yes") { throw "Отменено пользователем." }
    }
}

try { git --version | Out-Null } catch { throw "git не найден в PATH." }
try { py -3.13 --version | Out-Null } catch { throw "py -3.13 (Python 3.13) не найден." }

# --- Текущая версия прода ---
$pyprojText = Get-Content -LiteralPath (Join-Path $ProdPath "pyproject.toml") -Raw
$curVer = ([regex]::Match($pyprojText, 'version\s*=\s*"([^"]+)"')).Groups[1].Value
if (-not $curVer) { $curVer = "unknown" }
Write-Host "Текущая версия прода: $curVer"

# --- Подтверждение ---
if (-not $Yes) {
    Write-Host ""
    Write-Note "ЗАКРОЙТЕ приложение SolePro (десктоп и бот) перед продолжением!"
    Write-Note "Будет: бэкап БД + снимок текущей версии, затем обновление кода из GitHub."
    Write-Note "Боевые .env, settings/, data (символьная ссылка) НЕ затрагиваются."
    $ans = Read-Host "Продолжить обновление? (yes/no)"
    if ($ans -ne "yes") { throw "Отменено пользователем." }
}

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupRoot = Join-Path $ProdPath ".backup"

# --- 1) Резервная копия базы ---
Write-Step "Резервная копия базы данных"
$dbBackupDir = Join-Path $backupRoot "db"
New-Item -ItemType Directory -Force -Path $dbBackupDir | Out-Null
$dbCopied = 0
foreach ($ext in @("", "-wal", "-shm")) {
    $src = Join-Path $dataPath ("finances.db" + $ext)
    if (Test-Path -LiteralPath $src) {
        $dst = Join-Path $dbBackupDir ("finances_${curVer}_$stamp.db$ext")
        Copy-Item -LiteralPath $src -Destination $dst -Force
        $dbCopied++
    }
}
if ($dbCopied -gt 0) { Write-Ok "База скопирована в $dbBackupDir ($dbCopied файл(ов))" }
else { Write-Note "finances.db не найдена — резервная копия БД пропущена." }

# --- 2) Снимок текущей версии (код + конфиг) ---
Write-Step "Снимок текущей версии в .backup\${curVer}_$stamp"
$snapDir = Join-Path $backupRoot "${curVer}_$stamp"
$snapArgs = @(
    $ProdPath, $snapDir, "/E", "/XJ",
    "/XD", $backupRoot, $dataPath, (Join-Path $ProdPath ".venv"), (Join-Path $ProdPath ".git"),
    "/NFL", "/NDL", "/NJH", "/NJS", "/NP"
)
& robocopy @snapArgs | Out-Null
if ($LASTEXITCODE -ge 8) { throw "Ошибка robocopy при создании снимка (код $LASTEXITCODE)." }
Write-Ok "Снимок создан: $snapDir"

# --- 3) Загрузка новой версии из GitHub во временную папку ---
Write-Step "Получение версии из GitHub (ветка $Branch)"
$tmp = Join-Path $env:TEMP ("solepro_update_" + $stamp)
if (Test-Path -LiteralPath $tmp) { Remove-Item -LiteralPath $tmp -Recurse -Force }
git clone --depth 1 --branch $Branch $RepoUrl $tmp
if ($LASTEXITCODE -ne 0) { throw "git clone завершился с ошибкой (код $LASTEXITCODE)." }

$newVer = "unknown"
$tmpPyproj = Join-Path $tmp "pyproject.toml"
if (Test-Path -LiteralPath $tmpPyproj) {
    $newVer = ([regex]::Match((Get-Content -LiteralPath $tmpPyproj -Raw), 'version\s*=\s*"([^"]+)"')).Groups[1].Value
}
Write-Ok "Загружена версия: $newVer"

# --- 4) Синхронизация кода в прод (с исключениями) ---
Write-Step "Обновление кода (сохраняя .env, settings/, data, .backup)"
$syncArgs = @(
    $tmp, $ProdPath, "/E", "/XJ",
    "/XD",
        (Join-Path $tmp ".git"),
        (Join-Path $tmp "data"),
        (Join-Path $tmp "settings"),
        (Join-Path $tmp ".backup"),
        (Join-Path $tmp ".venv"),
    "/XF", (Join-Path $tmp ".env"),
    "/NFL", "/NDL", "/NJH", "/NJS", "/NP"
)
& robocopy @syncArgs | Out-Null
if ($LASTEXITCODE -ge 8) { throw "Ошибка robocopy при обновлении кода (код $LASTEXITCODE)." }
Write-Ok "Код обновлён."

# --- 5) Зависимости ---
if (-not $SkipDeps) {
    Write-Step "Обновление зависимостей (py -3.13 -m pip)"
    Push-Location $ProdPath
    try {
        py -3.13 -m pip install -r requirements.txt
        if ($LASTEXITCODE -ne 0) { throw "pip install завершился с ошибкой (код $LASTEXITCODE)." }
    } finally { Pop-Location }
    Write-Ok "Зависимости обновлены."
} else {
    Write-Note "Зависимости пропущены (-SkipDeps)."
}

# --- 6) Очистка временной папки ---
Write-Step "Очистка временных файлов"
Remove-Item -LiteralPath $tmp -Recurse -Force -ErrorAction SilentlyContinue
Write-Ok "Готово."

Write-Host ""
Write-Host "=== Обновление завершено: $curVer -> $newVer ===" -ForegroundColor Cyan
Write-Host "Резервная копия БД: $dbBackupDir" -ForegroundColor Green
Write-Host "Снимок версии:      $snapDir" -ForegroundColor Green
Write-Note "Запустите RunDesktopApp.pyw — миграции БД применятся автоматически при старте."
