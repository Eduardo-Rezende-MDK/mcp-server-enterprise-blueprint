eu quero gerar um teste que eu peço algo para oi IA LLM executar e vejo o custo de token dessa execução

e depois eu executo a mesma coisa , mas pelo mcp, e quero ver a diferença do custo de token


qual tarefa podemos usar, e vamos add uma tool nova



ok vamos fazer o seguinte 

a gente vai cria uma tool chamada BenchmarkCost

a gente vai fazer a opção 1 

🥇 Opção 1 (Recomendada): financial_simulator (Simulador de Amortização / Juros Compostos / ROI)

a gente prescisa acriar uma alias , pode ser no AGENTS.md

comparativo_token_cost

ele ele vai executar o seguinte


1 ele roda um prompt mocado com financial_simulator 

o prompt favi fazer o seguinte 
ele vai chama o MCP (mas serio , tem q ser o mcp real , sem mockar na linha do script, sem chamar py , real)

BenchmarkCost no mcp

essa tool , nao vai ter parametros
e ela vai gerar os parametros aleatorios , e executar

ai ela devolve a resposta do mcp com os parametros aleatorios , e o custo de token dessa execução

(vai ter algum custo ne , pois a chamada foi feita pelo LLM
)

na seguencia a gente usa os parametros que a tool nos deu , e peço pro LLM execultar a mesma coisa direto, sem usar a tool


e comparar os custos

e apresenta no chat


leva isso pro [text](../docs/mcp-python-fastmcp-plan.md)
cria o to-do , e depois implemant-plan