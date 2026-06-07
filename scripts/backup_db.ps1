# =====================================================================
#  SolePro Finance Assistant — ручная резервная копия базы данных.
#  Копирует finances.db (+ -wal/-shm) в .backup\db с отметкой даты/времени.
#  База лежит в data/ (символьная ссылка на реальное хранилище) - сам
#  каталог data и реальная база при этом НЕ изменяются.
#
#  Запуск (из папки прода):
#     powershell -NoProfile -ExecutionPolicy Bypass -File scripts\backup_db.ps1
#  Оставить только N последних копий:
#     ... scripts\backup_db.ps1 -Keep 30
# =====================================================================
param(
    [string]$ProdPath = (Split-Path -Parent $PSScriptRoot),
    [int]$Keep = 0   # 0 — хранить все; N>0 — оставить только N последних
)

$ErrorActionPreference = "Stop"
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch {}

$dataPath = Join-Path $ProdPath "data"
$dbBackupDir = Join-Path $ProdPath ".backup\db"

$mainDb = Join-Path $dataPath "finances.db"
if (-not (Test-Path -LiteralPath $mainDb)) {
    Write-Warning "finances.db не найдена в '$dataPath' — нечего копировать."
    return
}

New-Item -ItemType Directory -Force -Path $dbBackupDir | Out-Null
$stamp = Get-Date -Format "yyyyMMdd_HHmmss"

$copied = 0
foreach ($ext in @("", "-wal", "-shm")) {
    $src = Join-Path $dataPath ("finances.db" + $ext)
    if (Test-Path -LiteralPath $src) {
        $dst = Join-Path $dbBackupDir ("finances_$stamp.db$ext")
        Copy-Item -LiteralPath $src -Destination $dst -Force
        $copied++
    }
}

$size = [math]::Round((Get-Item -LiteralPath (Join-Path $dbBackupDir "finances_$stamp.db")).Length / 1KB, 1)
Write-Host "Резервная копия создана: $dbBackupDir\finances_$stamp.db ($size KB, файлов: $copied)" -ForegroundColor Green

# Ротация: оставить только последние N основных копий (.db), вместе с их -wal/-shm
if ($Keep -gt 0) {
    $all = Get-ChildItem -LiteralPath $dbBackupDir -Filter "finances_*.db" | Sort-Object LastWriteTime -Descending
    if ($all.Count -gt $Keep) {
        $all | Select-Object -Skip $Keep | ForEach-Object {
            foreach ($ext in @("", "-wal", "-shm")) {
                $old = $_.FullName + $ext
                if (Test-Path -LiteralPath $old) { Remove-Item -LiteralPath $old -Force }
            }
            Write-Host "Удалена старая копия: $($_.Name)"
        }
    }
}

$cnt = (Get-ChildItem -LiteralPath $dbBackupDir -Filter "finances_*.db" -ErrorAction SilentlyContinue).Count
Write-Host "Всего копий в .backup\db: $cnt"
