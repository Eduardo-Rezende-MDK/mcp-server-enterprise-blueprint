# ==============================================================================
# 🚀 MCP Server Enterprise - Windows Fast Installer & Onboarding Launcher
# ==============================================================================
[CmdletBinding()]
param (
    [string]$Token,
    [ValidateSet("1","2","3")]
    [string]$Mode,
    [switch]$CheckOnly,
    [switch]$NonInteractive
)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "  🏛️  MCP SERVER ENTERPRISE - WINDOWS QUICK INSTALLER (100% PYTHON)    " -ForegroundColor Cyan -NoNewline
Write-Host ""
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "  Iniciando diagnóstico e onboarding do ambiente..." -ForegroundColor Gray
Write-Host ""

# 1. Localizar Interpretador Python
$pythonCmd = $null

# Checar .venv local primeiro
if (Test-Path ".\.venv\Scripts\python.exe") {
    $pythonCmd = ".\.venv\Scripts\python.exe"
} else {
    # Checar python global
    try {
        $ver = & python --version 2>$null
        if ($ver) {
            $pythonCmd = "python"
        }
    } catch {}
}

# Se ainda não encontrou, tenta 'py' launcher
if (-not $pythonCmd) {
    try {
        $ver = & py -3 --version 2>$null
        if ($ver) {
            $pythonCmd = "py -3"
        }
    } catch {}
}

if (-not $pythonCmd) {
    Write-Host "❌ Python 3.10+ não foi encontrado no sistema ou PATH." -ForegroundColor Red
    Write-Host "Por favor, instale o Python em https://www.python.org/downloads/ ou via winget:" -ForegroundColor Yellow
    Write-Host "  winget install Python.Python.3.12" -ForegroundColor White
    exit 1
}

# 2. Montar argumentos para o install_wizard.py
$wizardArgs = @("scripts/install_wizard.py")

if ($Token) {
    $wizardArgs += @("--token", $Token)
}
if ($Mode) {
    $wizardArgs += @("--mode", $Mode)
}
if ($CheckOnly) {
    $wizardArgs += "--check-only"
}
if ($NonInteractive) {
    $wizardArgs += "--non-interactive"
}

# 3. Executar o wizard
if ($pythonCmd -eq "py -3") {
    & py -3 $wizardArgs
} else {
    & $pythonCmd $wizardArgs
}
