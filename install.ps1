# ==============================================================================
# 🚀 MCP Server Enterprise - Windows Quick Launcher (Delega para a Skill)
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
$SkillScript = Join-Path $PSScriptRoot ".agents\skills\control-server-entreprise\scripts\control.ps1"

if ($CheckOnly) {
    & powershell -ExecutionPolicy Bypass -File $SkillScript -Action check_env
} elseif ($Token -and $Mode) {
    & powershell -ExecutionPolicy Bypass -File $SkillScript -Action setup_mode -Mode $Mode -Token $Token
} else {
    & python (Join-Path $PSScriptRoot "scripts\install_wizard.py")
}
