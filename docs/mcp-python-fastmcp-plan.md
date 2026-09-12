# 📋 Especificação e Planejamento: Servidor MCP Enterprise em Python (FastMCP)

> **Status:** 100% Implementado, Testado e Deployado no Cloudflare Edge  
> **Nome do Servidor:** `mcp-server-enterprise`  
> **Diretório do Código:** `src/mcp_server/`  
> **Arquitetura:** Local-First (FastMCP Stdio) + Serverless Edge (Cloudflare Workers Python)  
> **Paradigma:** 100% Determinístico (Separação estrita entre Cognição e Execução)

---

## 🏛️ 1. Racional de Engenharia (Cognitivo vs. Determinístico)

- **🧠 Camada Cognitiva (LLM):** Responsável apenas por interpretação de linguagem natural, extração de intenções e decisão de qual ferramenta invocar (probabilístico).
- **⚙️ Camada Determinística (FastMCP / Python):** Responsável pela validação estrita de tipos (Pydantic v2), cálculos matemáticos exatos, formatações e regras de negócio sem risco de alucinação (100% determinístico e testável).

```mermaid
flowchart LR
    A["🧠 Usuário: 'Quanto é 150 dividido por 25?'"] --> B["🧠 LLM (Probabilístico): Extrai intenção e parâmetros"]
    B -->|"Payload JSON: valor1=150, valor2=25, operacao='/'"| C["⚙️ FastMCP (100% Determinístico): Executa 150 / 25"]
    C -->|"Retorno Exato: resultado=6, formula='150 / 25 = 6'"| B
    B --> D["🧠 Resposta Final: 'O resultado de 150 / 25 é 6.'"]
```

---

## 🛠️ 2. Stack Tecnológico

- **Linguagem:** Python 3.10+
- **Framework MCP:** `FastMCP` (via pacote oficial `mcp[cli]`)
- **Validação de Schemas e Tipagem:** `Pydantic v2`
- **Testes Unitários:** `pytest`
- **Transporte Padrão:** `stdio` (comunicação direta de processo via stdin/stdout)

---

## 📂 3. Estrutura de Pastas e Arquivos

```text
mcp-server-enterprise-blueprint/
├── src/
│   └── mcp_server/
│       ├── __init__.py             # Pacote Python
│       ├── server.py               # Ponto de entrada do FastMCP e registro das tools
│       ├── registry.py             # Catálogo estático de metadados, schemas e documentação
│       │
│       ├── schemas/                # 🛡️ Camada de Validação Estrita (Pydantic v2)
│       │   ├── __init__.py
│       │   ├── common.py           # Schemas compartilhados (Documentation, ToolMetadata)
│       │   ├── hello.py            # Schemas de entrada e saída da tool 'hello'
│       │   └── calc.py             # Schemas de entrada e saída da tool 'calc'
│       │
│       └── tools/                  # ⚙️ Camada Determinística (Lógica Pura de Execução)
│           ├── __init__.py
│           ├── discover.py         # Lógica da tool 'discover' (inspeção do registry)
│           ├── hello.py            # Lógica da tool 'hello' (saudação + timestamp ISO)
│           └── calc.py             # Lógica da tool 'calc' (operações aritméticas seguras)
│
├── tests/
│   ├── __init__.py
│   └── test_tools.py               # Testes unitários determinísticos das ferramentas (pytest)
│
├── requirements.txt                # Dependências do projeto
└── pyproject.toml                  # Metadados de empacotamento
```

---

## 🔧 4. Especificação Detalhada das Ferramentas (Tools)

### 1. `discover`
- **Objetivo:** Permite ao LLM inspecionar em tempo de execução o catálogo completo de ferramentas, contratos JSON Schema e diretrizes de uso.
- **Input Schema:** Vazio (`{}`).
- **Output Schema:**
```json
{
  "type": "object",
  "properties": {
    "tools": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "name": { "type": "string" },
          "description": { "type": "string" },
          "inputSchema": { "type": "object" },
          "outputSchema": { "type": "object" },
          "documentation": { "type": "object" }
        },
        "required": ["name", "description", "inputSchema", "outputSchema", "documentation"]
      }
    },
    "total": { "type": "integer" }
  },
  "required": ["tools", "total"]
}
```
- **Documentação & Exemplos:**
  - *Summary:* "Lista dinamicamente todas as ferramentas, seus contratos e exemplos de chamada."
  - *Usage Guidelines:* "Invoque no início de uma sessão para conhecer as capacidades ativas do servidor."

---

### 2. `hello`
- **Objetivo:** Gera saudação personalizada com carimbo de data e hora do sistema em formato ISO 8601.
- **Input Schema:**
```json
{
  "type": "object",
  "properties": {
    "name": {
      "type": "string",
      "description": "Nome da pessoa ou sistema a ser saudado",
      "minLength": 1
    }
  },
  "required": ["name"],
  "additionalProperties": false
}
```
- **Output Schema:**
```json
{
  "type": "object",
  "properties": {
    "message": { "type": "string", "description": "Mensagem formatada de saudação" },
    "timestamp": { "type": "string", "format": "date-time", "description": "Data e hora ISO 8601" }
  },
  "required": ["message", "timestamp"]
}
```
- **Documentação & Exemplos:**
  - *Summary:* "Gera saudação personalizada com carimbo temporal do sistema."
  - *Exemplo Input:* `{"name": "Eduardo"}`
  - *Exemplo Output:* `{"message": "Olá, Eduardo! Servidor MCP Enterprise operacional.", "timestamp": "2026-09-11T22:15:00.000Z"}`

---

### 3. `calc`
- **Objetivo:** Executa operações matemáticas determinísticas (`+`, `-`, `*`, `/`) entre dois números com tratamento estrito de divisão por zero.
- **Input Schema:**
```json
{
  "type": "object",
  "properties": {
    "valor1": { "type": "number", "description": "Primeiro valor numérico" },
    "valor2": { "type": "number", "description": "Segundo valor numérico (não pode ser zero em divisão)" },
    "operacao": {
      "type": "string",
      "description": "Operador matemático",
      "enum": ["+", "-", "*", "/", "soma", "subtracao", "multiplicacao", "divisao"]
    }
  },
  "required": ["valor1", "valor2", "operacao"],
  "additionalProperties": false
}
```
- **Output Schema:**
```json
{
  "type": "object",
  "properties": {
    "resultado": { "type": "number", "description": "Resultado numérico exato" },
    "formula": { "type": "string", "description": "Expressão resolvida (ex: '150 / 25 = 6')" }
  },
  "required": ["resultado", "formula"]
}
```
- **Documentação & Exemplos:**
  - *Summary:* "Calculadora aritmética determinística para cálculos exatos e seguros."
  - *Usage Guidelines:* "O LLM DEVE delegar qualquer cálculo para esta ferramenta para eliminar alucinações matemáticas."
  - *Exemplo 1:* `{"valor1": 150, "valor2": 25, "operacao": "/"}` ➔ `{"resultado": 6.0, "formula": "150 / 25 = 6"}`
  - *Exemplo 2:* `{"valor1": 10.5, "valor2": 3.2, "operacao": "+"}` ➔ `{"resultado": 13.7, "formula": "10.5 + 3.2 = 13.7"}`

---

## 🧪 5. Plano de Testes Unitários (`tests/test_tools.py`)

1. **`test_discover`**: Assegura que o retorno contém exatamente as 3 ferramentas (`discover`, `hello`, `calc`) com seus schemas e documentações íntegros.
2. **`test_hello`**: Assegura formatação da string e validade do timestamp ISO 8601 retornado.
3. **`test_calc_operacoes_validas`**: Testa soma, subtração, multiplicação e divisão com números inteiros e decimais.
4. **`test_calc_divisao_por_zero`**: Assegura que `valor2 = 0` na divisão levanta erro estruturado (`ValueError` tratado).
5. **`test_calc_operacao_invalida`**: Assegura que operadores fora do enum são rejeitados na validação do Pydantic.
