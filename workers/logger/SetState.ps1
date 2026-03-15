# workers/logger/SetState.ps1
#
# Standardized Debug State Toggler for OPEN-AIR.
# Scans for variables ending in _DEBUG and flips or sets their boolean state.
#
# Author: Anthony Peter Kuzub
# Blog: www.Like.audio (Contributor to this project)
#
# Professional services for customizing and tailoring this software to your
# specific application can be negotiated. There is no charge to use, modify,
# or fork this software.
#
# Build Log: https://like.audio/category/software/spectrum-scanner/
# Source Code: https://github.com/APKaudio/
# Feature Requests can be emailed to i @ like . audio
#
# Version 20260314.013000.REV01

<#
.SYNOPSIS
    Primary Purpose:
    Recursively scans the project directory for Python modules containing 
    standardized debug flags (ending in _DEBUG) and modifies their boolean 
    assignment.

    Hard Constraints:
    - Environment: Requires PowerShell 5.1 or Core (pwsh).
    - Permissions: Requires write access to all target .py files.
    - Scope: Operates on files relative to the parent of the script's directory.
#>

param (
    # SetTo: Explicitly force flags to 'True' or 'False'. 
    # If omitted, the script toggles the current state of each flag found.
    [Parameter(Mandatory=$false)]
    [ValidateSet("True", "False")]
    [string]$SetTo 
)

# Establish the project search root. 
# We move up from workers/logger to the repository root for full coverage.
$targetDir = Get-Item -Path ".." 
Write-Host "💓🫀🔄 [WATCHDOG] Scanning for _DEBUG heartbeat flags in $targetDir..." -ForegroundColor Cyan

# Recursively locate all Python source files.
$files = Get-ChildItem -Path $targetDir -Filter "*.py" -Recurse

foreach ($file in $files) {
    # Read file content as a single raw string to facilitate multi-line regex.
    $content = Get-Content -Path $file.FullName -Raw
    $updated = $false

    # Search Pattern: Matches uppercase variable names suffixed with _DEBUG
    # that are assigned a boolean literal at the start of a line.
    $pattern = '(?m)^([A-Z0-9_]+_DEBUG)\s*=\s*(True|False)'
    
    $matches = [regex]::Matches($content, $pattern)
    
    foreach ($match in $matches) {
        $varName = $match.Groups[1].Value
        $currentValue = $match.Groups[2].Value
        
        $newValue = ""
        if ($SetTo) {
            # Use explicit override if provided by caller.
            $newValue = $SetTo
        } else {
            # Toggle logic: Flip True to False and vice-versa.
            $newValue = if ($currentValue -eq "True") { "False" } else { "True" }
        }

        # Avoid redundant I/O if the value is already at the target state.
        if ($currentValue -ne $newValue) {
            $content = $content -replace "$varName\s*=\s*$currentValue", "$varName = $newValue"
            Write-Host "⚡ Flip: $($file.Name) -> $varName set to $newValue" -ForegroundColor Yellow
            $updated = $true
        }
    }

    # Atomic-like write back to the filesystem.
    if ($updated) {
        $content | Set-Content -Path $file.FullName
    }
}

Write-Host "✅🆗✅ [SUCCESS] Global state transition complete." -ForegroundColor Green
