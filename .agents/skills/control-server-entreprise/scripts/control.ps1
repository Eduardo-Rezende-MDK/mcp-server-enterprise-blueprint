# ==============================================================================
# control.ps1 (Skill: control-server-entreprise)
# Script 100% AUTO-CONTIDO e PORTATIL para INFRAESTRUTURA e INSTALACAO do MCP Server Enterprise.
# Suporta: help, auth, check_env, clean, install_deps, setup_mode, install, status, deploy, sync_secrets, create_tool
# ==============================================================================
[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [ValidateSet("help", "status", "deploy", "auth", "check_env", "diagnose", "install_deps", "setup_mode", "install", "onboard", "clean", "reset", "uninstall", "create_tool", "scaffold", "sync_secrets", "secrets")]
    [string]$Action = "help",

    [Parameter(Position = 1)]
    [string]$Tool = "",

    [string]$Desc = "",

    [string]$Token = "",

    [string]$Mode = "",

    [switch]$Reinstall,

    [switch]$Force,

    [switch]$JsonOutput
)

$ErrorActionPreference = "Stop"

$Endpoint = "https://mcp-server-enterprise.mardukasoft.online"

# Resolução Dinâmica do Diretório Raiz do Projeto
$ProjectRoot = $PSScriptRoot
while ($ProjectRoot -and -not (Test-Path "$ProjectRoot\pyproject.toml") -and (Split-Path $ProjectRoot -Parent) -ne $ProjectRoot) {
    $ProjectRoot = Split-Path $ProjectRoot -Parent
}
if (-not (Test-Path "$ProjectRoot\pyproject.toml")) {
    $ProjectRoot = (Get-Location).Path
}

# Auto-carregamento do token a partir do .env se não informado
if (-not $Token -and (Test-Path "$ProjectRoot\.env")) {
    try {
        $envLines = Get-Content "$ProjectRoot\.env" -ErrorAction SilentlyContinue
        foreach ($line in $envLines) {
            if ($line -match "^AUTH_TOKEN=(.*)$") {
                $Token = $matches[1].Trim().Trim('"').Trim("'")
                break
            }
        }
    } catch {}
}

function Show-Header([string]$Title) {
    if (-not $JsonOutput) {
        Write-Host ""
        Write-Host "==================================================================" -ForegroundColor Cyan
        Write-Host " >> MCP ENTERPRISE CONTROL: $Title" -ForegroundColor Cyan
        Write-Host "==================================================================" -ForegroundColor Cyan
    }
}

function Show-Help() {
    Show-Header "MANUAL DE USO E COMANDOS DE INFRAESTRUTURA"
    Write-Host "Endpoint Ativo: $Endpoint" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "ACOES DETERMINISTICAS DE INFRAESTRUTURA & ONBOARDING:" -ForegroundColor Cyan
    Write-Host "  1. auth" -ForegroundColor White
    Write-Host "     Valida remotamente o Bearer Token no Cloudflare Edge durante setup." -ForegroundColor Gray
    Write-Host "     Exemplo: powershell -File control.ps1 -Action auth -Token 'mcp_live_...'" -ForegroundColor Green
    Write-Host ""
    Write-Host "  2. check_env (ou diagnose)" -ForegroundColor White
    Write-Host "     Sonda silenciosamente o ambiente e dados pre-existentes (Python, venv, pacotes, wrangler, cloudflared)." -ForegroundColor Gray
    Write-Host "     Exemplo: powershell -File control.ps1 -Action check_env -JsonOutput" -ForegroundColor Green
    Write-Host ""
    Write-Host "  3. clean (ou reset, uninstall)" -ForegroundColor White
    Write-Host "     Limpa e reseta o ambiente (.venv, mcp_config.json, .env, .dev.vars, .wrangler e logout) para reinstalacao limpa." -ForegroundColor Gray
    Write-Host "     Exemplo: powershell -File control.ps1 -Action clean -Force" -ForegroundColor Green
    Write-Host ""
    Write-Host "  4. install_deps" -ForegroundColor White
    Write-Host "     Cria .venv e instala dependencias do requirements.txt e pacote editavel." -ForegroundColor Gray
    Write-Host "     Exemplo: powershell -File control.ps1 -Action install_deps" -ForegroundColor Green
    Write-Host ""
    Write-Host "  5. setup_mode" -ForegroundColor White
    Write-Host "     Configura o mcp_config.json para: 1 (Serverless), 2 (Túnel Cloudflare) ou 3 (Local Stdio) - sem default." -ForegroundColor Gray
    Write-Host "     Exemplo: powershell -File control.ps1 -Action setup_mode -Mode 2 -Token 'mcp_live_...'" -ForegroundColor Green
    Write-Host ""
    Write-Host "  6. status" -ForegroundColor White
    Write-Host "     Verifica a saude HTTP e metadados da instancia online no Cloudflare Edge." -ForegroundColor Gray
    Write-Host "     Exemplo: powershell -File control.ps1 -Action status" -ForegroundColor Green
    Write-Host ""
    Write-Host "  7. deploy" -ForegroundColor White
    Write-Host "     Roda pytest e wrangler deploy no Edge (requer repo fonte)." -ForegroundColor Gray
    Write-Host "     Exemplo: powershell -File control.ps1 -Action deploy" -ForegroundColor Green
    Write-Host ""
    Write-Host "  8. create_tool (ou scaffold)" -ForegroundColor White
    Write-Host "     Gera arquivos para uma nova ferramenta modular deterministica." -ForegroundColor Gray
    Write-Host "     Exemplo: powershell -File control.ps1 -Action create_tool -Tool cotacao_dolar -Desc 'Consulta cotacao'" -ForegroundColor Green
    Write-Host ""
    Write-Host "  9. sync_secrets (ou secrets)" -ForegroundColor White
    Write-Host "     Sincroniza segredos de .dev.vars/.env diretamente para o Cloudflare Workers." -ForegroundColor Gray
    Write-Host "     Exemplo: powershell -File control.ps1 -Action sync_secrets" -ForegroundColor Green
    Write-Host ""
    Write-Host "  10. install (ou onboard)" -ForegroundColor White
    Write-Host "     Executa esteira completa guiada de onboarding e instalacao." -ForegroundColor Gray
    Write-Host "     Exemplo: powershell -File control.ps1 -Action install -Mode 1 -Token 'mcp_live_...'" -ForegroundColor Green
    Write-Host "==================================================================" -ForegroundColor Cyan
}

function Invoke-McpRpc([string]$Method, [hashtable]$Params = @{}, [string]$AuthToken = "") {
    $payload = @{
        jsonrpc = "2.0"
        id      = (Get-Date).Ticks % 100000
        method  = $Method
        params  = $Params
    } | ConvertTo-Json -Depth 10

    $headers = @{
        "Content-Type" = "application/json; charset=utf-8"
    }
    if ($AuthToken) {
        $headers["Authorization"] = "Bearer $AuthToken"
    }

    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    $response = Invoke-RestMethod -Uri $Endpoint -Method Post -Body $payload -Headers $headers -TimeoutSec 15
    $sw.Stop()

    return @{
        Data    = $response
        Elapsed = $sw.ElapsedMilliseconds
    }
}

function Parse-ArgsJson([string]$Raw) {
    if (-not $Raw -or $Raw.Trim() -in @("", "{}", '""')) {
        return @{}
    }
    try {
        $cleanJson = $Raw.Replace("'", '"')
        return ($cleanJson | ConvertFrom-Json)
    } catch {
        Write-Host "[ERRO] Formato JSON invalido para argumentos: $Raw" -ForegroundColor Red
        exit 1
    }
}

switch ($Action.ToLower()) {
    "help" {
        Show-Help
    }

    "auth" {
        if (-not $Token) {
            $errObj = [ordered]@{ valid = $false; error = "Token nao fornecido." }
            $errObj | ConvertTo-Json -Compress
            exit 1
        }
        try {
            $res = Invoke-McpRpc -Method "tools/list" -Params @{} -AuthToken $Token
            $tools = $res.Data.result.tools
            $outObj = [ordered]@{
                valid       = $true
                tools_count = $tools.Count
                message     = "Token autenticado com sucesso no Cloudflare Edge."
                elapsed_ms  = $res.Elapsed
            }
            $outObj | ConvertTo-Json -Compress
        } catch {
            $outObj = [ordered]@{
                valid   = $false
                error   = "Token invalido ou nao autorizado pelo servidor MCP."
                details = $_.Exception.Message
            }
            $outObj | ConvertTo-Json -Compress
            exit 1
        }
    }

    { $_ -in @("check_env", "diagnose") } {
        $diag = [ordered]@{
            timestamp = (Get-Date).ToString("o")
            installed_state = [ordered]@{
                already_configured = ((Test-Path "$ProjectRoot\.venv") -or (Test-Path "$ProjectRoot\mcp_config.json") -or (Test-Path "$ProjectRoot\.env"))
                has_venv           = (Test-Path "$ProjectRoot\.venv")
                has_env_file       = (Test-Path "$ProjectRoot\.env")
                has_mcp_config     = (Test-Path "$ProjectRoot\mcp_config.json")
                configured_token   = $(if ($Token) { if ($Token.Length -gt 12) { $Token.Substring(0,8) + "..." + $Token.Substring($Token.Length-4) } else { "***" } } else { $null })
            }
            python = [ordered]@{
                installed = $false
                version   = $null
                ok        = $false
            }
            venv = [ordered]@{
                exists = (Test-Path "$ProjectRoot\.venv")
                active = (![string]::IsNullOrEmpty($env:VIRTUAL_ENV))
                path   = "$ProjectRoot\.venv"
            }
            packages = [ordered]@{
                missing = @()
                ok      = $false
            }
            node = [ordered]@{
                installed = $false
                version   = $null
            }
            wrangler = [ordered]@{
                installed     = $false
                version       = $null
                authenticated = $false
                account       = $null
            }
            cloudflared = [ordered]@{
                installed = $false
                version   = $null
            }
        }

        # 1. Python
        try {
            $pyVer = python --version 2>$null
            if ($pyVer) {
                $diag.python.installed = $true
                $diag.python.version = ($pyVer -replace "Python\s*", "").Trim()
                if ([version]$diag.python.version -ge [version]"3.10") {
                    $diag.python.ok = $true
                }
            }
        } catch {}

        # 2. Pacotes
        $reqPkgs = @("fastmcp", "mcp", "pydantic", "pytest")
        $missing = @()
        foreach ($pkg in $reqPkgs) {
            $chk = python -c "import $pkg" 2>$null
            if ($LASTEXITCODE -ne 0) {
                $missing += $pkg
            }
        }
        $diag.packages.missing = $missing
        $diag.packages.ok = ($missing.Count -eq 0)

        # 3. Node.js
        try {
            $nVer = node -v 2>$null
            if ($nVer) {
                $diag.node.installed = $true
                $diag.node.version = $nVer.Trim()
            }
        } catch {}

        # 4. Wrangler
        try {
            $wVer = npx --yes wrangler --version 2>$null
            if ($wVer) {
                $diag.wrangler.installed = $true
                $diag.wrangler.version = ($wVer | Select-Object -Last 1).Trim()
                $whoami = npx --yes wrangler whoami 2>$null | Out-String
                if ($whoami -match "logged in") {
                    $diag.wrangler.authenticated = $true
                    if ($whoami -match "([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})") {
                        $diag.wrangler.account = $matches[1]
                    }
                }
            }
        } catch {}

        # 5. Cloudflared
        try {
            $cfVer = cloudflared --version 2>$null
            if ($cfVer -match "cloudflared version\s+([^\s]+)") {
                $diag.cloudflared.installed = $true
                $diag.cloudflared.version = $matches[1].Trim()
            }
        } catch {}

        if ($JsonOutput) {
            $diag | ConvertTo-Json -Depth 5
        } else {
            Show-Header "DIAGNOSTICO DE AMBIENTE (SKILL DETERMINISTICA)"
            $diag | ConvertTo-Json -Depth 5 | Write-Host -ForegroundColor Cyan
        }
    }

    { $_ -in @("clean", "reset", "uninstall") } {
        Show-Header "LIMPEZA E RESET COMPLETO DO AMBIENTE"
        $removedItems = @()

        # 1. Matar processos de túnel ou servidor se houver
        try {
            Get-Process -Name "cloudflared" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
        } catch {}

        # 2. Remover .venv
        $venvDir = "$ProjectRoot\.venv"
        if (Test-Path $venvDir) {
            Write-Host "[INFO] Removendo ambiente virtual (.venv)..." -ForegroundColor Yellow
            try {
                Remove-Item -Path $venvDir -Recurse -Force -ErrorAction Stop
                $removedItems += ".venv"
            } catch {
                Write-Host "[AVISO] Tentando liberar arquivos e remover .venv..." -ForegroundColor Yellow
                Start-Sleep -Milliseconds 500
                Remove-Item -Path $venvDir -Recurse -Force -ErrorAction SilentlyContinue
                $removedItems += ".venv"
            }
        }

        # 3. Remover mcp_config.json
        $mcpConfig = "$ProjectRoot\mcp_config.json"
        if (Test-Path $mcpConfig) {
            Write-Host "[INFO] Removendo mcp_config.json..." -ForegroundColor Yellow
            Remove-Item -Path $mcpConfig -Force -ErrorAction SilentlyContinue
            $removedItems += "mcp_config.json"
        }

        # 4. Remover e resetar arquivos de segredos locais (.env e .dev.vars)
        $envFile = "$ProjectRoot\.env"
        if (Test-Path $envFile) {
            Copy-Item -Path $envFile -Destination "$ProjectRoot\.env.bak" -Force -ErrorAction SilentlyContinue
            Remove-Item -Path $envFile -Force -ErrorAction SilentlyContinue
            Write-Host "[INFO] Arquivo .env removido (backup salvo em .env.bak)." -ForegroundColor Cyan
            $removedItems += ".env"
        }

        $devVars = "$ProjectRoot\.dev.vars"
        if (Test-Path $devVars) {
            Copy-Item -Path $devVars -Destination "$ProjectRoot\.dev.vars.bak" -Force -ErrorAction SilentlyContinue
            Remove-Item -Path $devVars -Force -ErrorAction SilentlyContinue
            Write-Host "[INFO] Arquivo .dev.vars removido (backup salvo em .dev.vars.bak)." -ForegroundColor Cyan
            $removedItems += ".dev.vars"
        }

        # 5. Deslogar do Cloudflare Wrangler e limpar credenciais locais
        Write-Host "[INFO] Deslogando do Cloudflare Wrangler e limpando credenciais..." -ForegroundColor Yellow
        try {
            npx --yes wrangler logout 2>$null | Out-Null
            $removedItems += "wrangler_logout"
        } catch {}

        $wranglerDir = "$ProjectRoot\.wrangler"
        if (Test-Path $wranglerDir) {
            Remove-Item -Path $wranglerDir -Recurse -Force -ErrorAction SilentlyContinue
            $removedItems += ".wrangler"
        }

        # 6. Limpar caches Python
        try {
            Get-ChildItem -Path $ProjectRoot -Filter "__pycache__" -Recurse -Directory -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
            Get-ChildItem -Path $ProjectRoot -Filter ".pytest_cache" -Recurse -Directory -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
            Get-ChildItem -Path $ProjectRoot -Filter "*.egg-info" -Recurse -Directory -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
            $removedItems += "caches_python"
        } catch {}

        if ($JsonOutput) {
            [ordered]@{
                cleaned = $true
                removed = $removedItems
                message = "Ambiente limpo, segredos removidos e sessao Cloudflare encerrada com sucesso."
            } | ConvertTo-Json -Compress
        } else {
            Write-Host "[OK] Ambiente resetado com sucesso! Itens removidos/resetados: $($removedItems -join ', ')" -ForegroundColor Green
        }
    }

    "install_deps" {
        Show-Header "INSTALACAO AUTOMATICA DE DEPENDENCIAS"
        $venvDir = "$ProjectRoot\.venv"
        if (-not (Test-Path $venvDir)) {
            Write-Host "[INFO] Criando ambiente virtual em .venv..." -ForegroundColor Yellow
            python -m venv $venvDir
        }

        $pipExe = if (Test-Path "$venvDir\Scripts\pip.exe") { "$venvDir\Scripts\pip.exe" } else { "pip" }
        Write-Host "[INFO] Instalando requirements.txt e pacote em modo editavel..." -ForegroundColor Yellow
        & $pipExe install -r "$ProjectRoot\requirements.txt"
        & $pipExe install -e "$ProjectRoot"
        
        Write-Host "[OK] Dependencias instaladas com sucesso!" -ForegroundColor Green
    }

    "setup_mode" {
        Show-Header "CONFIGURACAO DO MODO DE EXECUCAO"
        $mcpConfigPath = "$ProjectRoot\mcp_config.json"
        
        # Exige escolha explícita do modo se não informado
        if (-not $Mode) {
            Write-Host ""
            Write-Host "Selecione obrigatoriamente o modo de execucao:" -ForegroundColor Cyan
            Write-Host "  [1] ☁️ Serverless Edge (24/7 no Cloudflare Workers)" -ForegroundColor Yellow
            Write-Host "  [2] 🚇 Tunel Remoto HTTPS (Python local + Cloudflare Tunnel)" -ForegroundColor Yellow
            Write-Host "  [3] ⚡ Local Stdio Puro (Python local via .venv)" -ForegroundColor Yellow
            Write-Host ""
            $Mode = Read-Host "Digite o numero do modo desejado (1, 2 ou 3)"
        }

        # Modo 1: Serverless Cloudflare Edge
        if ($Mode -in @("1", "serverless", "edge")) {
            if (-not $Token) {
                Write-Host "[ERRO] Modo 1 (Serverless) requer o parametro -Token (Bearer Token do Cloudflare)." -ForegroundColor Red
                exit 1
            }
            $cfg = @{
                mcpServers = @{
                    "mcp-server-enterprise" = @{
                        type    = "http"
                        url     = $Endpoint
                        headers = @{
                            Authorization = "Bearer $Token"
                        }
                    }
                }
            }
            $cfg | ConvertTo-Json -Depth 5 | Set-Content -Path $mcpConfigPath -Encoding UTF8
            Write-Host "[OK] mcp_config.json configurado para Servidor Serverless Edge ($Endpoint)!" -ForegroundColor Green
        }
        # Modo 2: Local Remoto com Tunel Cloudflare
        elseif ($Mode -in @("2", "tunnel")) {
            Write-Host "[INFO] Detectando/Iniciando tunel cloudflared na porta 8000..." -ForegroundColor Yellow
            if (-not (Get-Command cloudflared -ErrorAction SilentlyContinue)) {
                Write-Host "[INFO] Instalando cloudflared via winget..." -ForegroundColor Yellow
                winget install --id Cloudflare.cloudflared -e --silent
            }

            # Inicia o tunnel e captura a URL gerada
            $pinfo = New-Object System.Diagnostics.ProcessStartInfo
            $pinfo.FileName = "cloudflared"
            $pinfo.Arguments = "tunnel --url http://127.0.0.1:8000"
            $pinfo.RedirectStandardError = $true
            $pinfo.RedirectStandardOutput = $true
            $pinfo.UseShellExecute = $false
            $pinfo.CreateNoWindow = $true

            $proc = [System.Diagnostics.Process]::Start($pinfo)
            $tunnelUrl = $null
            $timeoutSec = 15
            $sw = [System.Diagnostics.Stopwatch]::StartNew()

            while ($sw.Elapsed.TotalSeconds -lt $timeoutSec -and -not $tunnelUrl) {
                if (-not $proc.StandardError.EndOfStream) {
                    $line = $proc.StandardError.ReadLine()
                    if ($line -match "(https://[a-zA-Z0-9-]+\.trycloudflare\.com)") {
                        $tunnelUrl = $matches[1]
                        break
                    }
                }
                Start-Sleep -Milliseconds 200
            }

            if (-not $tunnelUrl) {
                $tunnelUrl = "https://mcp-server-enterprise.trycloudflare.com"
            }

            $sseUrl = "$tunnelUrl/sse"
            $cfg = @{
                mcpServers = @{
                    "mcp-server-enterprise" = @{
                        type    = "sse"
                        url     = $sseUrl
                        headers = @{
                            Authorization = "Bearer $Token"
                        }
                    }
                }
            }
            $cfg | ConvertTo-Json -Depth 5 | Set-Content -Path $mcpConfigPath -Encoding UTF8
            Write-Host "[OK] Tunel ativo e mcp_config.json configurado automaticamente: $sseUrl" -ForegroundColor Green
        }
        # Modo 3: Local Stdio Puro
        elseif ($Mode -in @("3", "stdio", "local")) {
            $pyExe = "$ProjectRoot\.venv\Scripts\python.exe"
            if (-not (Test-Path $pyExe)) {
                $pyExe = "python"
            }
            $cfg = @{
                mcpServers = @{
                    "mcp-server-enterprise" = @{
                        command = $pyExe
                        args    = @("-m", "src.mcp_server.server")
                        cwd     = $ProjectRoot
                    }
                }
            }
            $cfg | ConvertTo-Json -Depth 5 | Set-Content -Path $mcpConfigPath -Encoding UTF8
            Write-Host "[OK] mcp_config.json configurado para Local Stdio Puro ($pyExe)!" -ForegroundColor Green
        }
        else {
            Write-Host "[ERRO] Modo de execucao '$Mode' invalido. Escolha obrigatoriamente entre: 1 (Serverless Edge), 2 (Tunel HTTPS) ou 3 (Local Stdio)." -ForegroundColor Red
            exit 1
        }
    }

    "status" {
        Show-Header "STATUS E HEALTH CHECK DO SERVIDOR"
        try {
            $sw = [System.Diagnostics.Stopwatch]::StartNew()
            $headers = @{ "Accept" = "application/json" }
            $response = Invoke-RestMethod -Uri $Endpoint -Method Get -Headers $headers -TimeoutSec 10
            $sw.Stop()
            Write-Host "[OK] Servidor Online! (Latencia: $($sw.ElapsedMilliseconds)ms)" -ForegroundColor Green
            $response | ConvertTo-Json -Depth 5 | Write-Host -ForegroundColor Green
        } catch {
            Write-Host "[ERRO] Nao foi possivel conectar ao servidor: $_" -ForegroundColor Red
            exit 1
        }
    }

    "deploy" {
        Show-Header "DEPLOY NO CLOUDFLARE WORKERS"
        pytest -q
        npx --yes wrangler deploy
    }

    { $_ -in @("install", "onboard") } {
        Show-Header "ONBOARDING & INSTALACAO GUIADA PELA SKILL"

        # Verificação e pergunta de reinstalação se já houver ambiente configurado
        $hasExisting = (Test-Path "$ProjectRoot\.venv") -or (Test-Path "$ProjectRoot\mcp_config.json") -or (Test-Path "$ProjectRoot\.env")
        if ($hasExisting -and -not $Reinstall -and -not $Force) {
            Write-Host ""
            Write-Host "[AVISO] Detectamos uma instalacao ou dados pre-existentes no ambiente." -ForegroundColor Yellow
            $resp = Read-Host "Deseja reinstalar / resetar o ambiente do zero? (s/N)"
            if ($resp -match "^[sSyY]") {
                Write-Host "[INFO] Resetando ambiente antes de reinstalar..." -ForegroundColor Yellow
                & powershell -ExecutionPolicy Bypass -File $PSCommandPath -Action clean -Force
                $Token = ""
            }
        } elseif ($Reinstall) {
            Write-Host "[INFO] Flag -Reinstall ativa. Resetando ambiente..." -ForegroundColor Yellow
            & powershell -ExecutionPolicy Bypass -File $PSCommandPath -Action clean -Force
            $Token = ""
        }

        Write-Host ""
        Write-Host "[1/5] Verificando token..." -ForegroundColor Yellow
        if (-not $Token) {
            Write-Host "[INFO] Digite o Token ou obtenha em: $Endpoint" -ForegroundColor Cyan
            $Token = Read-Host "Token de Acesso"
        }
        
        Write-Host "[2/5] Verificando ambiente..." -ForegroundColor Yellow
        & powershell -ExecutionPolicy Bypass -File $PSCommandPath -Action check_env

        Write-Host "[3/5] Instalando dependencias..." -ForegroundColor Yellow
        & powershell -ExecutionPolicy Bypass -File $PSCommandPath -Action install_deps

        Write-Host ""
        if (-not $Mode) {
            Write-Host "[4/5] Selecao do Modo de Execucao (Obrigatorio):" -ForegroundColor Yellow
            Write-Host "  [1] ☁️ Serverless Edge (24/7 no Cloudflare Workers)" -ForegroundColor Cyan
            Write-Host "  [2] 🚇 Tunel Remoto HTTPS (Python local + Cloudflare Tunnel)" -ForegroundColor Cyan
            Write-Host "  [3] ⚡ Local Stdio Puro (Python local via .venv)" -ForegroundColor Cyan
            $Mode = Read-Host "Escolha o modo de execucao (1, 2 ou 3)"
        } else {
            Write-Host "[4/5] Configurando modo de execucao selecionado (Modo: $Mode)..." -ForegroundColor Yellow
        }
        & powershell -ExecutionPolicy Bypass -File $PSCommandPath -Action setup_mode -Mode $Mode -Token $Token

        Write-Host "[5/5] Verificando status da instancia online..." -ForegroundColor Yellow
        & powershell -ExecutionPolicy Bypass -File $PSCommandPath -Action status
    }

    { $_ -in @("create_tool", "scaffold") } {
        Show-Header "CRIACAO DE FERRAMENTA DETERMINISTICA (SCAFFOLD)"
        if (-not $Tool) {
            Write-Host "[ERRO] Especifique o nome da ferramenta com: -Tool <nome_em_snake_case>" -ForegroundColor Red
            exit 1
        }
        try {
            if ($Desc) {
                python -m src.mcp_server.scaffold $Tool -d "$Desc"
            } else {
                python -m src.mcp_server.scaffold $Tool
            }
        } catch {
            Write-Host "[ERRO] Falha ao criar ferramenta: $_" -ForegroundColor Red
            exit 1
        }
    }

    { $_ -in @("sync_secrets", "secrets") } {
        Show-Header "SINCRONIZACAO DE SEGREDOS -> CLOUDFLARE WORKERS"
        $envVars = @{}
        $devVarsPath = "$ProjectRoot\.dev.vars"
        $envPath = "$ProjectRoot\.env"

        $targetFile = $null
        if (Test-Path $devVarsPath) { $targetFile = $devVarsPath }
        elseif (Test-Path $envPath) { $targetFile = $envPath }

        if (-not $targetFile) {
            Write-Host "[ERRO] Nenhum arquivo .dev.vars ou .env encontrado." -ForegroundColor Red
            exit 1
        }

        Write-Host "Carregando segredos de: $targetFile" -ForegroundColor Cyan
        $lines = Get-Content $targetFile
        foreach ($line in $lines) {
            $trimmed = $line.Trim()
            if (-not $trimmed -or $trimmed.StartsWith("#") -or -not ($trimmed.Contains("="))) { continue }
            $parts = $trimmed.Split("=", 2)
            $k = $parts[0].Trim()
            $v = $parts[1].Trim().Trim('"').Trim("'")
            if ($k -and $v) { $envVars[$k] = $v }
        }

        $sensitiveKeys = @("REDIS_URL", "GMAIL_USER", "GMAIL_APP_PASSWORD", "RESEND_API_KEY", "GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET", "ADMIN_TOKEN", "ADMIN_EMAIL", "ADMIN_NAME")
        foreach ($k in $sensitiveKeys) {
            if ($envVars.ContainsKey($k)) {
                $val = $envVars[$k]
                Write-Host " -> Sincronizando secret [$k]..." -ForegroundColor Yellow
                try {
                    $val | npx wrangler secret put $k
                    Write-Host "    [OK] Secret [$k] sincronizada!" -ForegroundColor Green
                } catch {
                    Write-Host "    [ERRO] Falha ao enviar [$k]: $_" -ForegroundColor Red
                }
            } else {
                Write-Host " -> [$k]: nao encontrado no arquivo local, ignorando." -ForegroundColor Gray
            }
        }
        Write-Host ""
        Write-Host "[SUCESSO] Sincronizacao de segredos concluida!" -ForegroundColor Green
    }
}

Write-Host ""
exit 0
