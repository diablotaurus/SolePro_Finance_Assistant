param(
    [string]$ProdPath = (Split-Path -Parent $PSScriptRoot),
    [string]$RepoUrl = "https://github.com/diablotaurus/SolePro_Finance_Assistant.git",
    [string]$Branch = "main",
    [switch]$SkipDeps,
    [switch]$Yes,
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
function Note([string]$Key, [object[]]$Arguments = @()) {
    Write-Host ("    " + (Msg $Key $Arguments)) -ForegroundColor Yellow
}

$robocopy = Join-Path $env:SystemRoot "System32\robocopy.exe"
if (-not (Test-Path -LiteralPath $robocopy)) {
    $command = Get-Command robocopy -ErrorAction SilentlyContinue
    if ($null -eq $command) {
        throw (Msg "error_robocopy")
    }
    $robocopy = $command.Source
}

Write-Host (Msg "update_title") -ForegroundColor Cyan
Write-Host (Msg "update_prod_path" @($ProdPath))

if (-not (Test-Path -LiteralPath (Join-Path $ProdPath "pyproject.toml"))) {
    throw (Msg "error_not_project" @($ProdPath))
}

$dataPath = Join-Path $ProdPath "data"
$dataItem = Get-Item -LiteralPath $dataPath -Force -ErrorAction SilentlyContinue
$isSymlink = $dataItem -and (($dataItem.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0)
if ($isSymlink) {
    Ok "update_data_link" @($dataItem.Target)
    if ($dataItem.Target -and -not (Test-Path -LiteralPath $dataItem.Target)) {
        throw (Msg "error_data_target" @($dataItem.Target))
    }
} else {
    Note "update_data_warning"
    if (-not $Yes) {
        $answer = Read-Host (Msg "update_data_continue")
        if ($answer.Trim().ToLower() -notin @("y", "yes")) {
            throw (Msg "cancelled")
        }
    }
}

try { git --version | Out-Null } catch { throw (Msg "error_git") }
$python = Resolve-SoleProPython -Root $ProdPath
if ($null -eq $python) {
    throw (Msg "error_python")
}
Ok "update_python" @($python.Exe, ($python.Prefix -join " "))

try {
    $escapedProdPath = [regex]::Escape([IO.Path]::GetFullPath($ProdPath))
    $runningProcesses = @(
        Get-CimInstance Win32_Process -ErrorAction Stop |
            Where-Object {
                $_.Name -match '^pythonw?\.exe$' -and
                $_.CommandLine -and
                $_.CommandLine -match $escapedProdPath
            }
    )
} catch {
    throw (Msg "error_process_check" @($_.Exception.Message))
}
if ($runningProcesses.Count -gt 0) {
    $processList = ($runningProcesses | ForEach-Object {
        "{0} (PID {1})" -f $_.Name, $_.ProcessId
    }) -join ", "
    throw (Msg "error_running_processes" @($processList))
}

$pyprojectText = Get-Content -LiteralPath (Join-Path $ProdPath "pyproject.toml") -Raw
$currentVersion = ([regex]::Match($pyprojectText, 'version\s*=\s*"([^"]+)"')).Groups[1].Value
if (-not $currentVersion) { $currentVersion = "unknown" }
Write-Host (Msg "update_version" @($currentVersion))

if (-not $Yes) {
    Write-Host ""
    Note "update_close"
    Note "update_plan"
    Note "update_preserved"
    $answer = Read-Host (Msg "update_confirm")
    if ($answer.Trim().ToLower() -notin @("y", "yes")) {
        throw (Msg "cancelled")
    }
}

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupRoot = Join-Path $ProdPath ".backup"

Step "step_db_backup"
$dbBackupDir = Join-Path $backupRoot "db"
New-Item -ItemType Directory -Force -Path $dbBackupDir | Out-Null
$mainDatabase = Join-Path $dataPath "finances.db"
$databaseBackup = Join-Path $dbBackupDir "finances_${currentVersion}_$stamp.db"
if (Test-Path -LiteralPath $mainDatabase) {
    & $python.Exe @(
        $python.Prefix + @(
            (Join-Path $PSScriptRoot "backup_sqlite.py"),
            $mainDatabase,
            $databaseBackup
        )
    ) | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw (Msg "error_command" @($LASTEXITCODE, "SQLite backup"))
    }
    Ok "db_backup_done" @($databaseBackup)
} else {
    Note "db_backup_missing"
}

$snapshotName = "${currentVersion}_$stamp"
Step "step_snapshot" @($snapshotName)
$snapshotDir = Join-Path $backupRoot $snapshotName
$snapshotArgs = @(
    $ProdPath, $snapshotDir, "/E", "/XJ",
    "/XD", $backupRoot, $dataPath, (Join-Path $ProdPath ".venv"), (Join-Path $ProdPath ".git"),
    "/NFL", "/NDL", "/NJH", "/NJS", "/NP"
)
& $robocopy @snapshotArgs | Out-Null
if ($LASTEXITCODE -ge 8) {
    throw (Msg "error_robocopy_snapshot" @($LASTEXITCODE))
}
Ok "snapshot_done" @($snapshotDir)

Step "step_download" @($Branch)
$tempPath = Join-Path $env:TEMP ("solepro_update_" + $stamp)
if (Test-Path -LiteralPath $tempPath) {
    Remove-Item -LiteralPath $tempPath -Recurse -Force
}
git clone --depth 1 --branch $Branch $RepoUrl $tempPath
if ($LASTEXITCODE -ne 0) {
    throw (Msg "error_git_clone" @($LASTEXITCODE))
}

$newVersion = "unknown"
$tempPyproject = Join-Path $tempPath "pyproject.toml"
if (Test-Path -LiteralPath $tempPyproject) {
    $newVersion = ([regex]::Match(
        (Get-Content -LiteralPath $tempPyproject -Raw),
        'version\s*=\s*"([^"]+)"'
    )).Groups[1].Value
}
Ok "download_done" @($newVersion)

if (-not $SkipDeps) {
    Step "step_dependencies"
    & $python.Exe @(
        $python.Prefix + @(
            "-m", "pip", "install", "-r", (Join-Path $tempPath "requirements.txt")
        )
    )
    if ($LASTEXITCODE -ne 0) {
        throw (Msg "error_command" @($LASTEXITCODE, "pip install"))
    }
    Ok "dependencies_done"
} else {
    Note "dependencies_skipped"
}

Step "step_sync"
$manifestPath = Join-Path $ProdPath ".solepro-files.json"
$newManifestFiles = @(git -C $tempPath ls-files)
if ($LASTEXITCODE -ne 0) {
    throw (Msg "error_command" @($LASTEXITCODE, "git ls-files"))
}
if (Test-Path -LiteralPath $manifestPath) {
    $oldManifestFiles = @(
        Get-Content -LiteralPath $manifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
    )
    $protectedPattern = '^(\.env$|data/|settings/|\.backup/|\.venv/)'
    $prodRoot = [IO.Path]::GetFullPath($ProdPath).TrimEnd('\') + '\'
    foreach ($relativePath in $oldManifestFiles) {
        if ($relativePath -in $newManifestFiles -or $relativePath -match $protectedPattern) {
            continue
        }
        $nativeRelativePath = $relativePath -replace '/', '\'
        $targetPath = [IO.Path]::GetFullPath((Join-Path $ProdPath $nativeRelativePath))
        if ($targetPath.StartsWith($prodRoot, [StringComparison]::OrdinalIgnoreCase) -and
            (Test-Path -LiteralPath $targetPath -PathType Leaf)) {
            Remove-Item -LiteralPath $targetPath -Force
        }
    }
}
$syncArgs = @(
    $tempPath, $ProdPath, "/E", "/XJ",
    "/XD",
        (Join-Path $tempPath ".git"),
        (Join-Path $tempPath "data"),
        (Join-Path $tempPath "settings"),
        (Join-Path $tempPath ".backup"),
        (Join-Path $tempPath ".venv"),
    "/XF", (Join-Path $tempPath ".env"),
    "/NFL", "/NDL", "/NJH", "/NJS", "/NP"
)
& $robocopy @syncArgs | Out-Null
if ($LASTEXITCODE -ge 8) {
    throw (Msg "error_robocopy_sync" @($LASTEXITCODE))
}
Ok "sync_done"

$manifestJson = ConvertTo-Json -InputObject @($newManifestFiles)
[IO.File]::WriteAllText(
    $manifestPath,
    $manifestJson,
    (New-Object Text.UTF8Encoding($false))
)

Step "step_migrations"
Push-Location $ProdPath
try {
    & $python.Exe @($python.Prefix + @("scripts\init_db.py"))
    if ($LASTEXITCODE -ne 0) {
        throw (Msg "error_command" @($LASTEXITCODE, "database migrations"))
    }
} finally {
    Pop-Location
}
Ok "migrations_done"

Step "step_cleanup"
Remove-Item -LiteralPath $tempPath -Recurse -Force -ErrorAction SilentlyContinue
Ok "cleanup_done"

Write-Host ""
Write-Host (Msg "update_complete" @($currentVersion, $newVersion)) -ForegroundColor Cyan
Write-Host (Msg "update_db_backup" @($dbBackupDir)) -ForegroundColor Green
Write-Host (Msg "update_snapshot" @($snapshotDir)) -ForegroundColor Green
Note "update_next"
