param(
    [string]$ProdPath = (Split-Path -Parent $PSScriptRoot),
    [int]$Keep = 0,
    [string]$Locale = "ru"
)

$ErrorActionPreference = "Stop"
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch {}

. (Join-Path $PSScriptRoot "common.ps1")
$messages = Import-SoleProMessages -ScriptsRoot $PSScriptRoot -Locale $Locale
function Msg([string]$Key, [object[]]$Arguments = @()) {
    return Get-SoleProMessage -Messages $messages -Key $Key -Arguments $Arguments
}

$dataPath = Join-Path $ProdPath "data"
$dbBackupDir = Join-Path $ProdPath ".backup\db"
$mainDatabase = Join-Path $dataPath "finances.db"
if (-not (Test-Path -LiteralPath $mainDatabase)) {
    Write-Warning (Msg "backup_missing" @($dataPath))
    return
}

New-Item -ItemType Directory -Force -Path $dbBackupDir | Out-Null
$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$python = Resolve-SoleProPython -Root $ProdPath
if ($null -eq $python) {
    throw (Msg "error_python")
}

$backupPath = Join-Path $dbBackupDir "finances_$stamp.db"
& $python.Exe @(
    $python.Prefix + @(
        (Join-Path $PSScriptRoot "backup_sqlite.py"),
        $mainDatabase,
        $backupPath
    )
) | Out-Null
if ($LASTEXITCODE -ne 0) {
    throw (Msg "error_command" @($LASTEXITCODE, "SQLite backup"))
}

$size = [math]::Round((Get-Item -LiteralPath $backupPath).Length / 1KB, 1)
Write-Host (Msg "backup_done" @($backupPath, $size)) -ForegroundColor Green

if ($Keep -gt 0) {
    $all = Get-ChildItem -LiteralPath $dbBackupDir -Filter "finances_*.db" |
        Sort-Object LastWriteTime -Descending
    if ($all.Count -gt $Keep) {
        $all | Select-Object -Skip $Keep | ForEach-Object {
            Remove-Item -LiteralPath $_.FullName -Force
            Write-Host (Msg "backup_deleted" @($_.Name))
        }
    }
}

$count = (Get-ChildItem -LiteralPath $dbBackupDir -Filter "finances_*.db" -ErrorAction SilentlyContinue).Count
Write-Host (Msg "backup_count" @($count))
