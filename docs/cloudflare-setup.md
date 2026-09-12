# 🛠️ Guia de Setup: Cloudflare do Zero

Este guia passo a passo foi elaborado para qualquer desenvolvedor que clonar este repositório e precisar configurar o ambiente Cloudflare do zero, permitindo que ferramentas CLI e agentes de IA/MCP interajam com a conta de forma automatizada.

---

## 1. Criação de Conta (Caso não possua)

1. Acesse o portal de cadastro: [dash.cloudflare.com/sign-up](https://dash.cloudflare.com/sign-up).
2. Crie uma conta gratuita e valide seu e-mail.
3. No painel principal da Cloudflare, localize e copie o seu **Account ID** (disponível na barra lateral direita ou na URL do dashboard).

---

## 2. Instalação das Ferramentas Essenciais

### 2.1. Wrangler CLI (Gerenciador de Workers, D1, KV e APIs)
Não é obrigatório instalar globalmente; você pode executá-lo diretamente via Node.js (`npx`):

```bash
# Validar execução direta
npx wrangler --version
```

*(Opcional: Para instalar globalmente)*
```bash
npm install -g wrangler
# ou
pnpm add -g wrangler
```

### 2.2. Cloudflared (Opcional - Criação de Túneis Seguros para MCP Local)
O `cloudflared` permite expor servidores MCP locais diretamente para a internet com terminação TLS segura sem abrir portas em roteadores.

- **Windows (PowerShell)**:
  ```powershell
  winget install --id Cloudflare.cloudflared
  ```
- **macOS (Homebrew)**:
  ```bash
  brew install cloudflared
  ```
- **Linux (Debian/Ubuntu)**:
  ```bash
  sudo apt-get update && sudo apt-get install cloudflared
  ```

---

## 3. Autenticação da Conta

Você pode escolher entre autenticação interativa (Dev Local) ou via Token (Headless/CI/CD):

### Opção A: Login Interativo via Navegador (Recomendado para Dev Local)
Execute no terminal:
```bash
npx wrangler login
```
> O comando abrirá uma janela do navegador. Clique em **Authorize** para salvar o token OAuth no seu perfil local.

### Opção B: API Token via Variáveis de Ambiente (Headless / CI/CD)
1. Acesse [dash.cloudflare.com/profile/api-tokens](https://dash.cloudflare.com/profile/api-tokens).
2. Clique em **Create Token** > use o template **Edit Cloudflare Workers** (ou personalize com permissões de Workers, D1, KV e AI).
3. Configure as variáveis de ambiente na sua sessão ou arquivo `.env`:

- **Linux / macOS**:
  ```bash
  export CLOUDFLARE_API_TOKEN="seu_token_aqui"
  export CLOUDFLARE_ACCOUNT_ID="seu_account_id_aqui"
  ```
- **Windows (PowerShell)**:
  ```powershell
  $env:CLOUDFLARE_API_TOKEN="seu_token_aqui"
  $env:CLOUDFLARE_ACCOUNT_ID="seu_account_id_aqui"
  ```

---

## 4. Validação do Acesso

Execute o comando abaixo para confirmar que o ambiente está autenticado e pronto para uso:

```bash
npx wrangler whoami
```

**Exemplo de saída esperada:**
```text
 ⛅️ wrangler 4.x.x
────────────────────
👋 You are logged in with an OAuth Token, associated with the email usuario@exemplo.com.
┌──────────────────────────────┬──────────────────────────────────┐
│ Account Name                 │ Account ID                       │
├──────────────────────────────┼──────────────────────────────────┤
│ Minha Conta Cloudflare       │ a9fee41e7bebab9da4c5dea4727d1e7f │
└──────────────────────────────┴──────────────────────────────────┘
```

---

## 5. Conectando a IA / Servidor MCP ao Cloudflare

Para permitir que clientes de IA (Claude Desktop, Cursor, Antigravity, etc.) gerenciem recursos do Cloudflare automaticamente via MCP:

Adicione a configuração abaixo ao seu arquivo de configuração de servidores MCP (ex: `claude_desktop_config.json` ou `mcp_config.json`):

### Configuração com Autenticação do Wrangler (Padrão)
```json
{
  "mcpServers": {
    "cloudflare": {
      "command": "npx",
      "args": ["-y", "@cloudflare/mcp-server-cloudflare", "run"]
    }
  }
}
```

### Configuração com API Token Explícito
```json
{
  "mcpServers": {
    "cloudflare": {
      "command": "npx",
      "args": ["-y", "@cloudflare/mcp-server-cloudflare", "run"],
      "env": {
        "CLOUDFLARE_API_TOKEN": "seu_token_aqui",
        "CLOUDFLARE_ACCOUNT_ID": "seu_account_id_aqui"
      }
    }
  }
}
```
