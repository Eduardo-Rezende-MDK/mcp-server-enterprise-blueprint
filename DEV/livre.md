gerar o codigo do mcp na pasta src/mcp/


o nome desse mcp vai ser 
mcp-server-enterprise


## Especificação Padronizada das Tools (MCP Standard / JSON Schema + Documentação Estendida)

Estrutura base padronizada de cada ferramenta no protocolo:
```json
{
  "name": "nome_da_tool",
  "description": "Descrição semântica para o LLM saber quando e como invocar a ferramenta",
  "inputSchema": {
    "type": "object",
    "properties": {},
    "required": [],
    "additionalProperties": false
  },
  "outputSchema": {
    "type": "object",
    "properties": {},
    "required": []
  },
  "documentation": {
    "summary": "Resumo funcional da ferramenta",
    "usageGuidelines": "Diretrizes e melhores práticas para o LLM decidir quando e como invocar",
    "examples": [
      {
        "scenario": "Cenário ilustrativo da chamada",
        "input": {},
        "expectedOutput": {}
      }
    ]
  }
}
```

---

### 1. `discover`
- **Descrição:** Lista o catálogo completo de ferramentas disponíveis no servidor MCP com seus respectivos schemas e exemplos de uso.
- **Request:** Sem parâmetros obrigatórios.
- **Definição JSON:**
```json
{
  "name": "discover",
  "description": "Lista todas as ferramentas (tools) disponíveis no servidor MCP com seus respectivos schemas de entrada, saída e exemplos de uso.",
  "inputSchema": {
    "type": "object",
    "properties": {},
    "required": [],
    "additionalProperties": false
  },
  "outputSchema": {
    "type": "object",
    "properties": {
      "tools": {
        "type": "array",
        "description": "Lista de definições completas das ferramentas disponíveis",
        "items": {
          "type": "object",
          "properties": {
            "name": { "type": "string", "description": "Nome da ferramenta" },
            "description": { "type": "string", "description": "Descrição da funcionalidade" },
            "inputSchema": { "type": "object", "description": "Schema JSON dos parâmetros de entrada" },
            "outputSchema": { "type": "object", "description": "Schema JSON do resultado retornado" },
            "documentation": { "type": "object", "description": "Guia de uso e exemplos práticos para o LLM" }
          },
          "required": ["name", "description", "inputSchema", "outputSchema", "documentation"]
        }
      },
      "total": {
        "type": "integer",
        "description": "Quantidade total de ferramentas disponíveis"
      }
    },
    "required": ["tools", "total"]
  },
  "documentation": {
    "summary": "Permite ao agente de IA inspecionar dinamicamente o catálogo de tools, seus contratos de dados e instruções de chamada.",
    "usageGuidelines": "Invoque esta tool no início de uma sessão ou quando precisar descobrir quais ferramentas estão ativas e quais parâmetros exatos elas esperam.",
    "examples": [
      {
        "scenario": "Agente consulta o catálogo de tools disponíveis no servidor",
        "input": {},
        "expectedOutput": {
          "total": 3,
          "tools": [
            { "name": "discover", "description": "Lista todas as ferramentas..." },
            { "name": "hello", "description": "Retorna uma mensagem de saudação..." },
            { "name": "calc", "description": "Calcula o resultado de uma operação matemática..." }
          ]
        }
      }
    ]
  }
}
```

---

### 2. `hello`
- **Descrição:** Recebe um nome e retorna uma saudação formatada acompanhada do timestamp ISO 8601 (data e hora atual).
- **Definição JSON:**
```json
{
  "name": "hello",
  "description": "Retorna uma mensagem de saudação personalizada com o nome fornecido, acompanhada da data e hora atual do sistema.",
  "inputSchema": {
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
  },
  "outputSchema": {
    "type": "object",
    "properties": {
      "message": {
        "type": "string",
        "description": "Mensagem de saudação formatada com nome, data e hora"
      },
      "timestamp": {
        "type": "string",
        "format": "date-time",
        "description": "Data e hora exatas da execução no formato ISO 8601"
      }
    },
    "required": ["message", "timestamp"]
  },
  "documentation": {
    "summary": "Gera saudação personalizada com carimbo de data e hora do sistema.",
    "usageGuidelines": "Invoque esta tool quando o usuário solicitar um teste de conectividade, uma saudação inicial ou quando for necessário obter o carimbo de data/hora atual do sistema para contextualização temporal.",
    "examples": [
      {
        "scenario": "Usuário pede para testar o servidor ou saudar 'Eduardo'",
        "input": {
          "name": "Eduardo"
        },
        "expectedOutput": {
          "message": "Olá, Eduardo! Servidor MCP Enterprise operacional.",
          "timestamp": "2026-09-11T22:10:00.000Z"
        }
      }
    ]
  }
}
```

---

### 3. `calc`
- **Descrição:** Executa operações matemáticas determinísticas (`+`, `-`, `*`, `/`) entre dois números.
- **Definição JSON:**
```json
{
  "name": "calc",
  "description": "Calcula o resultado de uma operação matemática básica entre dois números (adição, subtração, multiplicação ou divisão).",
  "inputSchema": {
    "type": "object",
    "properties": {
      "valor1": {
        "type": "number",
        "description": "Primeiro valor numérico da operação"
      },
      "valor2": {
        "type": "number",
        "description": "Segundo valor numérico da operação (não pode ser 0 em divisão)"
      },
      "operacao": {
        "type": "string",
        "description": "Operador matemático a ser aplicado",
        "enum": ["+", "-", "*", "/", "soma", "subtracao", "multiplicacao", "divisao"]
      }
    },
    "required": ["valor1", "valor2", "operacao"],
    "additionalProperties": false
  },
  "outputSchema": {
    "type": "object",
    "properties": {
      "resultado": {
        "type": "number",
        "description": "Resultado numérico exato da operação calculada"
      },
      "formula": {
        "type": "string",
        "description": "Expressão matemática resolvida (ex: '10 + 5 = 15')"
      }
    },
    "required": ["resultado", "formula"]
  },
  "documentation": {
    "summary": "Calculadora aritmética determinística para cálculos exatos e seguros.",
    "usageGuidelines": "O LLM DEVE delegar qualquer cálculo aritmético para esta ferramenta em vez de tentar calcular internamente, garantindo precisão numérica e eliminando alucinações matemáticas.",
    "examples": [
      {
        "scenario": "Divisão de valores: 150 dividido por 25",
        "input": {
          "valor1": 150,
          "valor2": 25,
          "operacao": "/"
        },
        "expectedOutput": {
          "resultado": 6,
          "formula": "150 / 25 = 6"
        }
      },
      {
        "scenario": "Soma com ponto flutuante: 10.5 + 3.2",
        "input": {
          "valor1": 10.5,
          "valor2": 3.2,
          "operacao": "+"
        },
        "expectedOutput": {
          "resultado": 13.7,
          "formula": "10.5 + 3.2 = 13.7"
        }
      }
    ]
  }
}
```




