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

---

## 6. Protocolo de Comparativo de Tokens (Alias: "comparativo_token_cost")
Sempre que o usuário enviar o comando ou alias **"comparativo_token_cost"** (ou variações como *"comparativo token cost"*, *"benchmark token cost"*, *"testar custo de tokens"*):
1. **Passo 1 — Execução Real no Servidor MCP (`benchmark_cost`):** O agente deve obrigatoriamente chamar a tool `benchmark_cost` no servidor MCP real hospedado na Cloudflare (sem passar parâmetros fixos, permitindo que a tool gere os parâmetros aleatórios realistas).
2. **Passo 2 — Extração dos Parâmetros e Resultado Determinístico:** Receber a resposta do MCP contendo os parâmetros gerados (`principal`, `taxa_anual`, `meses`, `sistema`) e os valores calculados (parcelas, amortização, juros totais).
3. **Passo 3 — Execução Cognitiva Direta (LLM puro sem Tool):** Utilizar os exatos mesmos parâmetros retornados pelo MCP no Passo 2 e resolver a simulação financeira diretamente na camada cognitiva do LLM (demonstrando o raciocínio e cálculo textual).
4. **Passo 4 — Apresentação do Relatório Comparativo no Chat:** Exibir um relatório visual contendo:
   - **Tabela Comparativa de Tokens:** Tokens de Prompt (Entrada), Tokens de Raciocínio (Thinking/CoT), Tokens de Saída (Output), Total de Tokens, Risco de Alucinação e Latência.
   - **Cálculo da Economia Real:** Demonstrar a redução percentual de tokens obtida pela abordagem FastMCP (~80% a 95%).
   - **Diagrama Mermaid:** Fluxo comparativo com rótulos de nós entre aspas duplas.