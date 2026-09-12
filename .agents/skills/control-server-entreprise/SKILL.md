---
name: control-server-entreprise
description: "Skill 100% auto-contida para invocar ferramentas determinísticas, criar novas tools, testar e gerenciar o servidor MCP Enterprise no Cloudflare Workers Edge a partir de QUALQUER projeto."
category: cloud-deployment
risk: low
source: workspace
date_added: "2026-09-11"
---

# 🎛️ Control Server Enterprise (Portátil, Auto-Contido & Extensível)

Skill **100% auto-contida e independente de código-fonte local**. Permite que qualquer projeto ou agente de IA descubra ferramentas, inspecione schemas, crie novas tools padronizadas, invoque cálculos determinísticos e consulte a integridade do servidor **`mcp-server-enterprise`** hospedado no Cloudflare Workers Edge.

---

## 🏛️ Racional de Engenharia (Cognitivo vs. Determinístico)

- **🧠 Camada Cognitiva (LLM):** Extrai a intenção do usuário em linguagem natural e delega a execução das ferramentas para a skill determinística.
- **⚙️ Camada Determinística (Scripts Auto-Contidos & FastMCP):** Conecta diretamente via JSON-RPC 2.0 / HTTP ao Cloudflare Workers Edge ou executa localmente, eliminando alucinações matemáticas ou de formatação temporal.

```mermaid
flowchart TD
    A["Qualquer Projeto / Workspace"] --> B["Skill: control-server-entreprise"]
    
    B -->|"discover"| C["Inspeção de Catálogo: Retorna tools, schemas e exemplos"]
    B -->|"call / invoke"| D["Invocação Determinística: tools/call (hello / calc / etc)"]
    B -->|"help"| E["Manual de Comandos: Sintaxe e exemplos prontos"]
    B -->|"status"| F["Health Check: Consulta GET / no Edge"]
    B -->|"test"| G["Smoke Test: Validação 100% remota do protocolo"]
    B -->|"create_tool"| H["Scaffold: Criação instantânea de nova Tool modular"]
    B -->|"deploy (no repo fonte)"| I["Publicação: wrangler deploy"]
    
    C --> J["Cloudflare Workers Edge (https://mcp-server-enterprise.mardukasoft.online)"]
    D --> J
    E --> K["Console Local Formatado"]
    F --> J
    G --> J
    H --> L["src/mcp_server/tools/<nova_tool>/"]
    I --> J
```

---

## 🏗️ Guia de Criação de Novas Ferramentas (Auto-Discovery & Template)

Quando o usuário ou agente precisar **criar uma nova ferramenta** no servidor MCP Enterprise:

### 1. O Contrato Estrito dos 4 Arquivos
Toda ferramenta deve residir em sua própria subpasta em `src/mcp_server/tools/<nome_da_tool>/`:

| Arquivo | Finalidade | Responsabilidade |
| :--- | :--- | :--- |
| **`schema.py`** | 🛡️ Contratos Pydantic | Classes `NomeInput` e `NomeOutput` com validações, `description` e `examples`. |
| **`handler.py`** | ⚙️ Lógica Pura | Função determinística `execute(dados: NomeInput) -> NomeOutput`. |
| **`meta.py`** | 🧠 Semântica LLM | Dicionário `METADATA` com `name`, `description`, `summary`, `usageGuidelines` e `examples`. |
| **`__init__.py`** | 📦 Exportador | `__all__ = ["execute", "NomeInput", "NomeOutput", "METADATA"]`. |

### 2. Criação Instantânea via CLI
Utilize o script de scaffold a partir da raiz do repositório:
```powershell
python scripts/create_tool.py <nome_da_tool> --desc "Descrição funcional da ferramenta"
```
*Exemplo:* `python scripts/create_tool.py cotacao_moeda --desc "Consulta cotações cambiais em tempo real"`

### 3. Auto-Discovery (Zero-Configuração)
- O servidor escaneia automaticamente todas as subpastas em `src/mcp_server/tools/`.
- **NÃO é necessário** editar `registry.py`, `server.py` ou `entry.py` manualmente.
- Pastas que começam com `_` (como `src/mcp_server/tools/_template/`) são modelos de referência e são ignoradas pelo carregador.

---

## 📦 Como Usar Esta Skill em Outros Projetos

Para disponibilizar o servidor MCP Enterprise e esta skill em qualquer outro repositório:

### 1. Registrar no Cliente MCP do Projeto (`mcp_config.json` ou `.agents/mcp_config.json`)
```json
{
  "mcpServers": {
    "mcp-server-enterprise": {
      "url": "https://mcp-server-enterprise.mardukasoft.online"
    }
  }
}
```

### 2. Copiar a pasta da Skill
Basta copiar a pasta `control-server-entreprise/` para a pasta de skills do seu projeto (`.agents/skills/control-server-entreprise/`) ou para as skills globais (`~/.gemini/config/skills/control-server-entreprise/`).

---

## 🛠️ Catálogo de Funções de Controle

### 1. `discover` (Descoberta Dinâmica de Ferramentas e Schemas)
Consulta o catálogo de ferramentas ativas no Edge e exibe de forma legível seus schemas JSON, resumos, diretrizes e exemplos de uso:

```powershell
powershell -ExecutionPolicy Bypass -File .\.agents\skills\control-server-entreprise\scripts\control.ps1 -Action discover
```

---

### 2. `help` (Manual de Uso e Exemplos Rápidos)
Exibe a lista de todos os comandos disponíveis com exemplos prontos para copiar e colar:

```powershell
powershell -ExecutionPolicy Bypass -File .\.agents\skills\control-server-entreprise\scripts\control.ps1 -Action help
```

---

### 3. `call` / `invoke` (Invocação Determinística de Ferramentas)
Invoca diretamente as ferramentas do Cloudflare Workers sem intermediários:

```powershell
# 1. Ferramenta 'hello' (Saudação com Timestamp ISO 8601 UTC)
powershell -ExecutionPolicy Bypass -File .\.agents\skills\control-server-entreprise\scripts\control.ps1 -Action call -Tool hello -ArgsJson "{'name': 'Eduardo Rezende'}"

# 2. Ferramenta 'calc' (Cálculo Determinístico Exato)
powershell -ExecutionPolicy Bypass -File .\.agents\skills\control-server-entreprise\scripts\control.ps1 -Action call -Tool calc -ArgsJson "{'valor1': 250, 'valor2': 5, 'operacao': '/'}"

# 3. Ferramenta 'discover'
powershell -ExecutionPolicy Bypass -File .\.agents\skills\control-server-entreprise\scripts\control.ps1 -Action call -Tool discover
```

---

### 4. `status` (Health Check Remoto)
Consulta o endpoint e exibe status, runtime, taxa de requisições e lista de tools ativas:

```powershell
powershell -ExecutionPolicy Bypass -File .\.agents\skills\control-server-entreprise\scripts\control.ps1 -Action status
```

---

### 5. `test` (Smoke Test Remoto Auto-Contido)
Executa 4 testes protocolares completos (`GET /`, `initialize`, `tools/list`, `tools/call`) diretamente contra o Cloudflare Workers:

```powershell
powershell -ExecutionPolicy Bypass -File .\.agents\skills\control-server-entreprise\scripts\control.ps1 -Action test
```

---

### 6. `deploy` (Atualização no Cloudflare Workers)
> **Nota:** Esta função requer os arquivos de código-fonte do servidor (`wrangler.toml`, `src/entry.py`) e é executada no repositório `mcp-server-enterprise-blueprint`.

```powershell
powershell -ExecutionPolicy Bypass -File .\.agents\skills\control-server-entreprise\scripts\control.ps1 -Action deploy
```

---

## 🌐 Endpoint de Produção

- **URL Oficial:** `https://mcp-server-enterprise.mardukasoft.online`
- **Ferramentas Nativas:** `discover`, `hello`, `calc`
- **Autenticação:** Header `Authorization: Bearer rezende`
- **Rate Limit:** Máximo de 60 requisições/hora por IP
