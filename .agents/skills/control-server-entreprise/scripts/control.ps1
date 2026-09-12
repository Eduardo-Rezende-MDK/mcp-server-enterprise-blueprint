# ==============================================================================
# control.ps1 (Skill: control-server-entreprise)
# Script 100% AUTO-CONTIDO e PORTATIL para controlar o MCP Server Enterprise.
# Suporta: help, discover, call, status, test, deploy, logs
# ==============================================================================
[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [ValidateSet("help", "discover", "call", "invoke", "status", "test", "deploy", "logs")]
    [string]$Action = "help",

    [Parameter(Position = 1)]
    [string]$Tool = "",

    [Parameter(Position = 2)]
    [string]$ArgsJson = "{}"
)

$ErrorActionPreference = "Stop"

$Endpoint = "https://mcp-server-enterprise.mardukasoft.online"

function Show-Header([string]$Title) {
    Write-Host ""
    Write-Host "==================================================================" -ForegroundColor Cyan
    Write-Host " >> MCP ENTERPRISE CONTROL: $Title" -ForegroundColor Cyan
    Write-Host "==================================================================" -ForegroundColor Cyan
}

function Show-Help() {
    Show-Header "MANUAL DE USO E COMANDOS DISPONIVEIS"
    Write-Host "Endpoint Ativo: $Endpoint" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "COMANDOS DISPONIVEIS:" -ForegroundColor Cyan
    Write-Host "  1. discover" -ForegroundColor White
    Write-Host "     Consulta o catalogo dinamico de ferramentas e schemas no Cloudflare." -ForegroundColor Gray
    Write-Host "     Exemplo: powershell -File control.ps1 -Action discover" -ForegroundColor Green
    Write-Host ""
    Write-Host "  2. call (ou invoke)" -ForegroundColor White
    Write-Host "     Invoca uma ferramenta deterministica via JSON-RPC 2.0." -ForegroundColor Gray
    Write-Host "     Ex (hello): powershell -File control.ps1 -Action call -Tool hello -ArgsJson '{""name"": ""Eduardo""}'" -ForegroundColor Green
    Write-Host "     Ex (calc):  powershell -File control.ps1 -Action call -Tool calc -ArgsJson '{""valor1"": 150, ""valor2"": 25, ""operacao"": ""/""}'" -ForegroundColor Green
    Write-Host "     Ex (disc):  powershell -File control.ps1 -Action call -Tool discover" -ForegroundColor Green
    Write-Host ""
    Write-Host "  3. status" -ForegroundColor White
    Write-Host "     Verifica a saude e metadados da instancia online no Cloudflare Edge." -ForegroundColor Gray
    Write-Host "     Exemplo: powershell -File control.ps1 -Action status" -ForegroundColor Green
    Write-Host ""
    Write-Host "  4. test" -ForegroundColor White
    Write-Host "     Executa o smoke test completo (4 testes protocolares remotos)." -ForegroundColor Gray
    Write-Host "     Exemplo: powershell -File control.ps1 -Action test" -ForegroundColor Green
    Write-Host ""
    Write-Host "  5. deploy (Apenas no repositorio fonte)" -ForegroundColor White
    Write-Host "     Roda pytest, wrangler deploy e validacao no Edge." -ForegroundColor Gray
    Write-Host "     Exemplo: powershell -File control.ps1 -Action deploy" -ForegroundColor Green
    Write-Host ""
    Write-Host "  6. logs" -ForegroundColor White
    Write-Host "     Abre streaming de logs em tempo real (wrangler tail)." -ForegroundColor Gray
    Write-Host "     Exemplo: powershell -File control.ps1 -Action logs" -ForegroundColor Green
    Write-Host ""
    Write-Host "==================================================================" -ForegroundColor Cyan
}

function Invoke-McpRpc([string]$Method, [hashtable]$Params = @{}) {
    $payload = @{
        jsonrpc = "2.0"
        id      = (Get-Date).Ticks % 100000
        method  = $Method
        params  = $Params
    } | ConvertTo-Json -Depth 10

    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    $response = Invoke-RestMethod -Uri $Endpoint -Method Post -Body $payload -ContentType "application/json; charset=utf-8" -TimeoutSec 15
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

    "discover" {
        Show-Header "DESCOBERTA DINAMICA DE FERRAMENTAS E SCHEMAS"
        Write-Host "[INFO] Invocando 'discover' diretamente no Cloudflare Workers..." -ForegroundColor Yellow
        try {
            $rpcParams = @{
                name      = "discover"
                arguments = @{}
            }
            $res = Invoke-McpRpc -Method "tools/call" -Params $rpcParams
            $elapsed = $res.Elapsed
            Write-Host "[OK] Catalogo retornado com sucesso! (Latencia: ${elapsed}ms)" -ForegroundColor Green
            Write-Host ""
            
            $cat = $res.Data.result.structuredContent
            Write-Host "Total de Ferramentas Registradas: $($cat.total)" -ForegroundColor Cyan
            Write-Host "------------------------------------------------------------------" -ForegroundColor DarkGray
            
            foreach ($t in $cat.tools) {
                Write-Host ""
                Write-Host " Ferramenta: $($t.name)" -ForegroundColor Yellow
                Write-Host "   Descricao : $($t.description)" -ForegroundColor White
                Write-Host "   Resumo    : $($t.documentation.summary)" -ForegroundColor Gray
                Write-Host "   Diretrizes: $($t.documentation.usageGuidelines)" -ForegroundColor DarkGray
                
                if ($t.documentation.examples) {
                    Write-Host "   Exemplos de Chamada:" -ForegroundColor Green
                    foreach ($ex in $t.documentation.examples) {
                        Write-Host "     - Cenario: $($ex.scenario)" -ForegroundColor DarkCyan
                        $inStr = $ex.input | ConvertTo-Json -Compress
                        $outStr = $ex.expectedOutput | ConvertTo-Json -Compress
                        Write-Host "       Input  : $inStr" -ForegroundColor Gray
                        Write-Host "       Output : $outStr" -ForegroundColor Gray
                    }
                }
            }
            Write-Host ""
            Write-Host "==================================================================" -ForegroundColor Cyan
        } catch {
            Write-Host "[ERRO] Falha ao consultar o catalogo discover: $_" -ForegroundColor Red
            exit 1
        }
    }

    "status" {
        Show-Header "STATUS E HEALTH CHECK DO SERVIDOR"
        Write-Host "[INFO] Consultando endpoint: $Endpoint" -ForegroundColor Yellow
        try {
            $sw = [System.Diagnostics.Stopwatch]::StartNew()
            $response = Invoke-RestMethod -Uri $Endpoint -Method Get -TimeoutSec 10
            $sw.Stop()
            $elapsed = $sw.ElapsedMilliseconds
            Write-Host "[OK] Servidor Online! (Latencia: ${elapsed}ms)" -ForegroundColor Green
            Write-Host ""
            $response | ConvertTo-Json -Depth 5 | Write-Host -ForegroundColor Green
        } catch {
            Write-Host "[ERRO] Nao foi possivel conectar ao servidor: $_" -ForegroundColor Red
            exit 1
        }
    }

    { $_ -in @("call", "invoke") } {
        Show-Header "INVOCACAO DETERMINISTICA DE TOOL"
        if (-not $Tool) {
            Write-Host "[ERRO] Especifique a ferramenta com: -Tool discover OU -Tool hello OU -Tool calc" -ForegroundColor Red
            Write-Host "Dica: Execute '.\control.ps1 -Action discover' para ver o catalogo completo." -ForegroundColor Yellow
            exit 1
        }

        $parsedArgs = Parse-ArgsJson -Raw $ArgsJson
        $argsCompressed = $parsedArgs | ConvertTo-Json -Compress
        Write-Host "[INFO] Invocando tool '$Tool' no Cloudflare Workers..." -ForegroundColor Yellow
        Write-Host "[INFO] Parametros: $argsCompressed" -ForegroundColor DarkGray

        try {
            $rpcParams = @{
                name      = $Tool
                arguments = $parsedArgs
            }
            $res = Invoke-McpRpc -Method "tools/call" -Params $rpcParams
            $elapsed = $res.Elapsed
            
            Write-Host "[OK] Resposta recebida! (Latencia: ${elapsed}ms)" -ForegroundColor Green
            Write-Host ""
            Write-Host "--- [Resultado Estruturado da Ferramenta] ---" -ForegroundColor Cyan

            if ($res.Data.result.structuredContent) {
                $res.Data.result.structuredContent | ConvertTo-Json -Depth 10 | Write-Host -ForegroundColor Green
            } elseif ($res.Data.result.content) {
                $res.Data.result.content | ConvertTo-Json -Depth 10 | Write-Host -ForegroundColor Green
            } else {
                $res.Data | ConvertTo-Json -Depth 10 | Write-Host -ForegroundColor Green
            }
        } catch {
            Write-Host "[ERRO] Falha na chamada da ferramenta '$Tool': $_" -ForegroundColor Red
            exit 1
        }
    }

    "test" {
        Show-Header "SMOKE TEST PROTOCOLAR COMPLETO (AUTO-CONTIDO)"
        Write-Host "[INFO] Executando validacao ponta a ponta contra $Endpoint..." -ForegroundColor Yellow
        
        # Teste 1: GET /
        Write-Host ""
        Write-Host "[1/4] Testando GET / (Metadados)..." -ForegroundColor Yellow
        $info = Invoke-RestMethod -Uri $Endpoint -Method Get
        if ($info.status -ne "online" -or $info.tools_count -ne 3) {
            $errStr = $info | ConvertTo-Json -Compress
            Write-Host "[ERRO] Falha no health check: $errStr" -ForegroundColor Red
            exit 1
        }
        Write-Host "  -> OK: status=$($info.status), tools=$($info.tools_count)" -ForegroundColor Green

        # Teste 2: initialize
        Write-Host ""
        Write-Host "[2/4] Testando RPC 'initialize'..." -ForegroundColor Yellow
        $initRes = Invoke-McpRpc -Method "initialize" -Params @{}
        $serverName = $initRes.Data.result.serverInfo.name
        $initElapsed = $initRes.Elapsed
        if ($serverName -ne "mcp-server-enterprise") {
            Write-Host "[ERRO] Nome do servidor inesperado no handshake." -ForegroundColor Red
            exit 1
        }
        Write-Host "  -> OK: server=$serverName (${initElapsed}ms)" -ForegroundColor Green

        # Teste 3: tools/list
        Write-Host ""
        Write-Host "[3/4] Testando RPC 'tools/list'..." -ForegroundColor Yellow
        $listRes = Invoke-McpRpc -Method "tools/list" -Params @{}
        $tools = $listRes.Data.result.tools
        if ($tools.Count -ne 3) {
            Write-Host "[ERRO] Quantidade de ferramentas diferente de 3." -ForegroundColor Red
            exit 1
        }
        $toolNames = $tools.name -join ', '
        Write-Host "  -> OK: $($tools.Count) ferramentas ativas ($toolNames)" -ForegroundColor Green

        # Teste 4: tools/call (calc)
        Write-Host ""
        Write-Host "[4/4] Testando RPC 'tools/call' (calc: 150 / 25)..." -ForegroundColor Yellow
        $calcRes = Invoke-McpRpc -Method "tools/call" -Params @{
            name      = "calc"
            arguments = @{ valor1 = 150; valor2 = 25; operacao = "/" }
        }
        $calcOutput = $calcRes.Data.result.structuredContent
        $calcElapsed = $calcRes.Elapsed
        if ($calcOutput.resultado -ne 6.0) {
            $calcErrStr = $calcOutput | ConvertTo-Json -Compress
            Write-Host "[ERRO] Resultado inesperado no calculo: $calcErrStr" -ForegroundColor Red
            exit 1
        }
        Write-Host "  -> OK: formula='$($calcOutput.formula)', resultado=$($calcOutput.resultado) (${calcElapsed}ms)" -ForegroundColor Green

        Write-Host ""
        Write-Host "==================================================================" -ForegroundColor Green
        Write-Host " [SUCESSO] TODOS OS TESTES PROTOCOLARES PASSARAM COM SUCESSO!" -ForegroundColor Green
        Write-Host "==================================================================" -ForegroundColor Green
    }

    "deploy" {
        Show-Header "DEPLOY DO SERVIDOR (REQUER CODIGO-FONTE)"
        if (-not (Test-Path "wrangler.toml")) {
            Write-Host "[AVISO] O arquivo 'wrangler.toml' nao foi encontrado no diretorio atual." -ForegroundColor Yellow
            Write-Host "[INFO] A funcao 'deploy' deve ser executada a partir do repositorio fonte 'mcp-server-enterprise-blueprint'." -ForegroundColor Yellow
            Write-Host "[INFO] Em outros projetos, utilize 'discover', 'call', 'status' ou 'test' para interagir com o servidor online." -ForegroundColor Cyan
            exit 1
        }

        Write-Host "[1/2] Executando testes unitarios locais (se pytest disponivel)..." -ForegroundColor Yellow
        if (Get-Command pytest -ErrorAction SilentlyContinue) {
            pytest -v
            if ($LASTEXITCODE -ne 0) {
                Write-Host "[ERRO] Testes unitarios locais falharam!" -ForegroundColor Red
                exit 1
            }
        }

        Write-Host "[2/2] Executando npx wrangler deploy..." -ForegroundColor Yellow
        npx --yes wrangler deploy
        if ($LASTEXITCODE -ne 0) {
            Write-Host "[ERRO] Falha durante o deploy no Cloudflare Workers!" -ForegroundColor Red
            exit 1
        }

        Write-Host ""
        Write-Host "==================================================================" -ForegroundColor Green
        Write-Host " [SUCESSO] DEPLOY CONCLUIDO NO CLOUDFLARE WORKERS!" -ForegroundColor Green
        Write-Host "==================================================================" -ForegroundColor Green
    }

    "logs" {
        Show-Header "STREAMING DE LOGS (WRANGLER TAIL)"
        npx --yes wrangler tail
    }
}

Write-Host ""
exit 0
