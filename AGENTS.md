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