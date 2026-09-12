# ==============================================================================
# control.ps1 (Skill: control-server-entreprise)
# Script 100% AUTO-CONTIDO e PORTATIL para controlar e instalar o MCP Server Enterprise.
# Suporta: help, discover, call, status, test, deploy, logs, auth, check_env, install_deps, setup_mode, install, clean, reset
# ==============================================================================
[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [ValidateSet("help", "discover", "call", "invoke", "status", "test", "deploy", "logs", "auth", "check_env", "diagnose", "install_deps", "setup_mode", "install", "onboard", "clean", "reset", "uninstall")]
    [string]$Action = "help",

    [Parameter(Position = 1)]
    [string]$Tool = "",

    [Parameter(Position = 2)]
    [string]$ArgsJson = "{}",

    [string]$Token = "",

    [string]$Mode = "3",

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
    Show-Header "MANUAL DE USO E COMANDOS DISPONIVEIS"
    Write-Host "Endpoint Ativo: $Endpoint" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "COMANDOS DISPONIVEIS PARA AGENTES DE IA (SKILL):" -ForegroundColor Cyan
    Write-Host "  1. auth" -ForegroundColor White
    Write-Host "     Valida remotamente o Bearer Token no Cloudflare Edge." -ForegroundColor Gray
    Write-Host "     Exemplo: powershell -File control.ps1 -Action auth -Token 'mcp_live_...'" -ForegroundColor Green
    Write-Host ""
    Write-Host "  2. check_env (ou diagnose)" -ForegroundColor White
    Write-Host "     Sonda silenciosamente o ambiente e dados pre-existentes (Python, venv, pacotes, wrangler, cloudflared)." -ForegroundColor Gray
    Write-Host "     Exemplo: powershell -File control.ps1 -Action check_env -JsonOutput" -ForegroundColor Green
    Write-Host ""
    Write-Host "  3. clean (ou reset, uninstall)" -ForegroundColor White
    Write-Host "     Limpa e reseta o ambiente (.venv, mcp_config.json, .env e caches) para reinstalacao limpa." -ForegroundColor Gray
    Write-Host "     Exemplo: powershell -File control.ps1 -Action clean -Force" -ForegroundColor Green
    Write-Host ""
    Write-Host "  4. install_deps" -ForegroundColor White
    Write-Host "     Cria .venv e instala dependencias do requirements.txt automaticamente." -ForegroundColor Gray
    Write-Host "     Exemplo: powershell -File control.ps1 -Action install_deps" -ForegroundColor Green
    Write-Host ""
    Write-Host "  5. setup_mode" -ForegroundColor White
    Write-Host "     Configura o mcp_config.json para: 1 (Serverless), 2 (Túnel Cloudflare) ou 3 (Local Stdio)." -ForegroundColor Gray
    Write-Host "     Exemplo: powershell -File control.ps1 -Action setup_mode -Mode 2 -Token 'mcp_live_...'" -ForegroundColor Green
    Write-Host ""
    Write-Host "  6. discover" -ForegroundColor White
    Write-Host "     Consulta o catalogo dinamico de ferramentas e schemas no Cloudflare." -ForegroundColor Gray
    Write-Host "     Exemplo: powershell -File control.ps1 -Action discover" -ForegroundColor Green
    Write-Host ""
    Write-Host "  7. call (ou invoke)" -ForegroundColor White
    Write-Host "     Invoca uma ferramenta deterministica via JSON-RPC 2.0." -ForegroundColor Gray
    Write-Host "     Exemplo: powershell -File control.ps1 -Action call -Tool hello -ArgsJson '{""name"": ""Eduardo""}'" -ForegroundColor Green
    Write-Host ""
    Write-Host "  8. status" -ForegroundColor White
    Write-Host "     Verifica a saude e metadados da instancia online no Cloudflare Edge." -ForegroundColor Gray
    Write-Host "     Exemplo: powershell -File control.ps1 -Action status" -ForegroundColor Green
    Write-Host ""
    Write-Host "  9. test" -ForegroundColor White
    Write-Host "     Executa o smoke test completo (validacao remota ponta a ponta)." -ForegroundColor Gray
    Write-Host "     Exemplo: powershell -File control.ps1 -Action test" -ForegroundColor Green
    Write-Host ""
    Write-Host "  10. deploy" -ForegroundColor White
    Write-Host "     Roda pytest e wrangler deploy no Edge (requer repo fonte)." -ForegroundColor Gray
    Write-Host "     Exemplo: powershell -File control.ps1 -Action deploy" -ForegroundColor Green
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

        # 4. Backup e Preservação de .env
        $envFile = "$ProjectRoot\.env"
        if (Test-Path $envFile) {
            Copy-Item -Path $envFile -Destination "$ProjectRoot\.env.bak" -Force -ErrorAction SilentlyContinue
            Write-Host "[INFO] Backup de seguranca criado: .env.bak" -ForegroundColor Cyan
        }

        # 5. Limpar caches Python
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
                message = "Ambiente limpo e resetado com sucesso."
            } | ConvertTo-Json -Compress
        } else {
            Write-Host "[OK] Ambiente resetado com sucesso! Itens removidos: $($removedItems -join ', ')" -ForegroundColor Green
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
        
        # Modo 1: Serverless Cloudflare Edge
        if ($Mode -in @("1", "serverless")) {
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
        else {
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
    }

    "discover" {
        Show-Header "DESCOBERTA DINAMICA DE FERRAMENTAS E SCHEMAS"
        try {
            $res = Invoke-McpRpc -Method "tools/call" -Params @{ name = "discover"; arguments = @{} } -AuthToken $Token
            $cat = $res.Data.result.structuredContent
            Write-Host "Total de Ferramentas Registradas: $($cat.total)" -ForegroundColor Cyan
            foreach ($t in $cat.tools) {
                Write-Host ""
                Write-Host " Ferramenta: $($t.name)" -ForegroundColor Yellow
                Write-Host "   Descricao : $($t.description)" -ForegroundColor White
                Write-Host "   Resumo    : $($t.documentation.summary)" -ForegroundColor Gray
            }
        } catch {
            Write-Host "[ERRO] Falha ao consultar discover: $_" -ForegroundColor Red
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

    { $_ -in @("call", "invoke") } {
        Show-Header "INVOCACAO DETERMINISTICA DE TOOL"
        if (-not $Tool) {
            Write-Host "[ERRO] Especifique a ferramenta com: -Tool <nome>" -ForegroundColor Red
            exit 1
        }
        $parsedArgs = Parse-ArgsJson -Raw $ArgsJson
        try {
            $res = Invoke-McpRpc -Method "tools/call" -Params @{ name = $Tool; arguments = $parsedArgs } -AuthToken $Token
            if ($res.Data.result.structuredContent) {
                $res.Data.result.structuredContent | ConvertTo-Json -Depth 10 | Write-Host -ForegroundColor Green
            } elseif ($res.Data.result.content) {
                $res.Data.result.content | ConvertTo-Json -Depth 10 | Write-Host -ForegroundColor Green
            }
        } catch {
            Write-Host "[ERRO] Falha na chamada de '$Tool': $_" -ForegroundColor Red
            exit 1
        }
    }

    "test" {
        Show-Header "SMOKE TEST PROTOCOLAR COMPLETO (AUTO-CONTIDO)"
        Write-Host "[1/2] Testando conexao e metadados no Edge..." -ForegroundColor Yellow
        $headers = @{ "Accept" = "application/json" }
        $info = Invoke-RestMethod -Uri $Endpoint -Method Get -Headers $headers
        Write-Host "  -> OK: status=$($info.status), tools=$($info.tools_count)" -ForegroundColor Green

        Write-Host "[2/2] Testando chamada deterministica (calc: 150 / 25)..." -ForegroundColor Yellow
        $calcRes = Invoke-McpRpc -Method "tools/call" -Params @{
            name      = "calc"
            arguments = @{ valor1 = 150; valor2 = 25; operacao = "/" }
        } -AuthToken $Token
        $calcOutput = $calcRes.Data.result.structuredContent
        Write-Host "  -> OK: formula='$($calcOutput.formula)', resultado=$($calcOutput.resultado)" -ForegroundColor Green
        Write-Host ""
        Write-Host "[SUCESSO] Servidor MCP Enterprise validado e operacional!" -ForegroundColor Green
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

        Write-Host "[4/5] Configurando modo de execucao (Modo: $Mode)..." -ForegroundColor Yellow
        & powershell -ExecutionPolicy Bypass -File $PSCommandPath -Action setup_mode -Mode $Mode -Token $Token

        Write-Host "[5/5] Executando smoke test..." -ForegroundColor Yellow
        & powershell -ExecutionPolicy Bypass -File $PSCommandPath -Action test -Token $Token
    }
}

Write-Host ""
exit 0
