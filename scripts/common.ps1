# Shared helpers for SolePro maintenance scripts.

function Import-SoleProMessages {
    param(
        [Parameter(Mandatory = $true)][string]$ScriptsRoot,
        [string]$Locale = "ru"
    )

    $path = Join-Path $ScriptsRoot ("locales\messages.{0}.json" -f $Locale)
    if (-not (Test-Path -LiteralPath $path)) {
        throw "Messages catalog not found: $path"
    }

    return Get-Content -LiteralPath $path -Raw -Encoding UTF8 | ConvertFrom-Json
}

function Get-SoleProMessage {
    param(
        [Parameter(Mandatory = $true)]$Messages,
        [Parameter(Mandatory = $true)][string]$Key,
        [object[]]$Arguments = @()
    )

    $property = $Messages.PSObject.Properties[$Key]
    if ($null -eq $property) {
        return $Key
    }

    $text = [string]$property.Value
    if ($Arguments.Count -eq 0) {
        return $text
    }
    return $text -f $Arguments
}

function Test-SoleProPython {
    param(
        [Parameter(Mandatory = $true)][string]$Executable,
        [string[]]$Prefix = @()
    )

    try {
        $output = & $Executable @($Prefix + @("--version")) 2>&1
    } catch {
        return $null
    }

    $match = [regex]::Match("$output", 'Python (\d+)\.(\d+)')
    if (-not $match.Success) {
        return $null
    }

    $major = [int]$match.Groups[1].Value
    $minor = [int]$match.Groups[2].Value
    if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 13)) {
        return $null
    }

    return @{
        Exe = $Executable
        Prefix = $Prefix
        Version = "$major.$minor"
    }
}

function Resolve-SoleProPython {
    param(
        [Parameter(Mandatory = $true)][string]$Root,
        [switch]$SystemOnly
    )

    if (-not $SystemOnly) {
        $venvPython = Join-Path $Root ".venv\Scripts\python.exe"
        if (Test-Path -LiteralPath $venvPython) {
            $resolved = Test-SoleProPython -Executable $venvPython
            if ($null -ne $resolved) {
                return $resolved
            }
        }
    }

    $candidates = @(
        @{ Exe = "py"; Prefix = @("-3.13") },
        @{ Exe = "py"; Prefix = @("-3") },
        @{ Exe = "python"; Prefix = @() },
        @{ Exe = "python3"; Prefix = @() }
    )
    foreach ($candidate in $candidates) {
        if (-not (Get-Command $candidate.Exe -ErrorAction SilentlyContinue)) {
            continue
        }
        $resolved = Test-SoleProPython `
            -Executable $candidate.Exe `
            -Prefix $candidate.Prefix
        if ($null -ne $resolved) {
            return $resolved
        }
    }

    return $null
}
