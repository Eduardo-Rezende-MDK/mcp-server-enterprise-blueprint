# 📐 Template Canônico de MCP Tool

Este diretório serve como o **blueprint padrão** para criação de novas ferramentas determinísticas no servidor `mcp-server-enterprise`.

> **Nota:** Pastas iniciadas por `_` (como `_template/`) são automaticamente ignoradas pelo mecanismo de Auto-Discovery do servidor.

---

## 🏗️ Estrutura do Contrato (4 Arquivos Obrigatórios)

1. **`schema.py`**: Modelos Pydantic (`Input` e `Output`) com tipos estritos, descrições e exemplos.
2. **`handler.py`**: Função pura `execute(dados: Input) -> Output` contendo a lógica determinística de negócio.
3. **`meta.py`**: Dicionário `METADATA` com `name`, `description` e objeto `DocumentationDefinition` contendo resumo, diretrizes de uso e exemplos práticos para o LLM.
4. **`__init__.py`**: Exporta `execute`, classes de schema e `METADATA`.

---

## 🚀 Como Criar uma Nova Tool em 1 Segundo

### Opção 1: Via CLI (Recomendado)
Execute a partir da raiz do projeto:
```powershell
python scripts/create_tool.py <nome_da_tool> --desc "Descrição sucinta da ferramenta"
```

### Opção 2: Manualmente
1. Copie a pasta `src/mcp_server/tools/_template/` para `src/mcp_server/tools/<nome_da_tool>/`.
2. Renomeie as classes em `schema.py` (ex: `CotacaoInput`, `CotacaoOutput`).
3. Implemente a lógica em `handler.py`.
4. Atualize os metadados em `meta.py`.
5. Atualize as exportações em `__init__.py`.
6. **Pronto!** A ferramenta é imediatamente reconhecida pelo servidor e pelo `discover` sem precisar editar nenhum outro arquivo.
