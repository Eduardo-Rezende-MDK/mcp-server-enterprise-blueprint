# 📝 Rascunho / Brainstorming: Arquitetura Modular de Tools

> **Status da Ideia:** ✅ **100% Implementada e Integrada** (Estrutura modular de 4 arquivos, Auto-Discovery dinâmico via Pydantic `model_json_schema()`, template canônico `_template/` e script CLI `scripts/create_tool.py`).

---

## 💡 Proposta Original
Em vez de arquivos monolíticos e espalhados entre `schemas/`, `tools/` e `registry.py`:
- `../src/mcp_server/tools/hello/handler.py` (lógica de execução)
- `../src/mcp_server/tools/hello/schema.py` (contratos Pydantic Input/Output)
- `../src/mcp_server/tools/hello/meta.py` (metadados e diretrizes para o LLM)
- `../src/mcp_server/tools/hello/__init__.py` (exportador padrão)

## 🎯 Ganhos Obtidos
1. **Coesão por Domínio:** Cada tool é autocontida e expansível para cenários complexos.
2. **Auto-Discovery:** O servidor descobre automaticamente todas as subpastas em `tools/` (ignorando `_*`).
3. **Zero-Drift:** Schemas JSON extraídos nativamente do Pydantic (`InputModel.model_json_schema()`), sem escrita manual repetitiva de JSON Schema.
4. **Scaffolding Ágil:** `python scripts/create_tool.py <nome_da_tool>` gera uma nova tool em 1 segundo.