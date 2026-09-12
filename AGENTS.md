# 📜 Regras do Projeto para Agentes de IA

Este arquivo contém as diretrizes e regras obrigatórias que todos os agentes devem seguir ao interagir e modificar este repositório:

---

## 1. Diagramas Mermaid nos Arquivos `.md`
- **Sintaxe Estrita:** Sempre que criar diagramas Mermaid em documentos `.md`, **coloque os rótulos de todos os nós entre aspas duplas** (ex: `id["Texto (Info)"]` em vez de `id[Texto (Info)]`).
- **Validação:** Tenha certeza absoluta de que a sintaxe é válida e não contém caracteres especiais sem escape (parênteses, dois-pontos, colchetes, emojis) para evitar quebras no renderizador.

---

## 2. Execução Estrita e Sem Intervenções Não Solicitadas
- **Escopo Direto:** Execute e crie apenas o que for explicitamente solicitado pelo usuário.
- **Sem Planos Desnecessários:** Não crie propostas de soluções ou planos de implementação invasivos a menos que o usuário solicite expressamente.

---

## 3. Racional de Engenharia (Camada Cognitiva vs. Determinística)
- **🧠 Camada Cognitiva (LLM):** Raciocínio, interpretação semântica e intenção (probabilística).
- **⚙️ Camada Determinística (MCP / Código):** Validação estrita de tipos, queries parametrizadas, regras de negócio e consumo otimizado de tokens (100% previsível e testável).

---

## 4. Prioridade Absoluta ao Servidor MCP Real na Cloudflare
- **Execução Real Obrigatória:** Sempre que o usuário solicitar uma ação ou ferramenta do MCP (`hello`, `calc`, `discover`, etc.), o agente **DEVE obrigatoriamente realizar a chamada real no servidor MCP hospedado na Cloudflare** (`mcp-server-enterprise` via protocolo MCP).
- **Proibição de Scripts Locais `.py` como Substitutos:** O agente **NÃO DEVE** executar scripts locais `.py` (como `scripts/call_tool.py`, testes locais ou execuções simuladas) no lugar do servidor MCP real, salvo se o usuário solicitar expressamente o contrário.

---

## 5. Protocolo de Encerramento (Alias: "tarefa concluida")
Sempre que o usuário enviar o comando ou alias **"tarefa concluida"** (ou variações como *"tarefa finalizada"*, *"concluir tarefa"*):
1. **Sincronização de Documentação:** Atualizar e marcar como concluídas todas as tarefas e status nos arquivos `.md` relevantes em aberto ou afetados pela sessão (ex: `docs/mcp-python-fastmcp-plan.md`, `DEV/livre.md`, etc.).
2. **Validação de Qualidade:** Executar a suíte de testes (`pytest`) para garantir integridade e 100% de aprovação.
3. **Commit Semântico:** Realizar `git add .` e `git commit` com uma mensagem descritiva e padronizada em português.
4. **Encerramento da Sessão:** Apresentar um resumo executivo claro do que foi entregue e finalizar a interação.