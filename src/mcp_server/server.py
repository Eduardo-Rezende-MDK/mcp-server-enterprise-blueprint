"""Main entry point for MCP Enterprise Server using FastMCP."""

from fastmcp import FastMCP
from .registry import dispatch_tool
from .tools.auth.schema import AuthAction
from .tools.benchmark_cost.schema import SistemaAmortizacao
from .tools.calc.schema import OperacaoEnum
from .tools.redis.schema import RedisAction
from .tools.sqlite.schema import SqliteAction

# Inicialização do Servidor FastMCP
mcp = FastMCP(
    name="mcp-server-enterprise",
)



@mcp.tool(
    name="discover",
    description="Lista todas as ferramentas (tools) disponíveis no servidor MCP com seus respectivos schemas de entrada, saída e exemplos de uso.",
)
def discover() -> dict:
    """Lista todas as ferramentas do catálogo com documentação estendida."""
    return dispatch_tool("discover", {})


@mcp.tool(
    name="hello",
    description="Retorna uma mensagem de saudação personalizada com o nome fornecido, acompanhada da data e hora atual do sistema.",
)
def hello(name: str) -> dict:
    """Retorna saudação com carimbo de data e hora do sistema."""
    return dispatch_tool("hello", {"name": name})


@mcp.tool(
    name="calc",
    description="Calcula o resultado de uma operação matemática básica entre dois números (adição, subtração, multiplicação ou divisão).",
)
def calc(valor1: float, valor2: float, operacao: OperacaoEnum) -> dict:
    """Executa cálculo aritmético determinístico (+, -, *, /)."""
    return dispatch_tool("calc", {"valor1": valor1, "valor2": valor2, "operacao": operacao})


@mcp.tool(
    name="sqlite",
    description="Executa operações determinísticas em banco de dados SQLite (CRUD e consultas SQL parametrizadas).",
)
def sqlite(
    action: SqliteAction = SqliteAction.QUERY,
    query: str | None = None,
    table: str | None = None,
    data: dict | None = None,
    where: dict | str | None = None,
    params: list | dict | None = None,
    limit: int = 100,
    db_name: str = ":memory:",
) -> dict:
    """Executa operações CRUD e consultas no SQLite."""
    return dispatch_tool(
        "sqlite",
        {
            "action": action,
            "query": query,
            "table": table,
            "data": data,
            "where": where,
            "params": params,
            "limit": limit,
            "db_name": db_name,
        },
    )


@mcp.tool(
    name="redis",
    description="Executa operações determinísticas em Redis (chave-valor, hashes, sets, TTLs e verificação de conectividade PING).",
)
def redis(
    action: RedisAction = RedisAction.PING,
    key: str | None = None,
    value: str | int | float | dict | list | None = None,
    ex: int | None = None,
    field: str | None = None,
    fields: dict | None = None,
    pattern: str = "*",
    member: str | list | None = None,
) -> dict:
    """Executa operações no Redis (GET, SET, DEL, HGETALL, HSET, PING, etc.)."""
    return dispatch_tool(
        "redis",
        {
            "action": action,
            "key": key,
            "value": value,
            "ex": ex,
            "field": field,
            "fields": fields,
            "pattern": pattern,
            "member": member,
        },
    )


@mcp.tool(
    name="auth",
    description="Gerencia o ciclo de vida de autenticação, cadastro de usuários (nome e e-mail), emissão de tokens criptográficos e validação perimetral no Redis.",
)
def auth(
    action: AuthAction = AuthAction.GET_TOKEN,
    name: str | None = None,
    email: str | None = None,
    token: str | None = None,
    provider: str = "local",
    google_id: str | None = None,
) -> dict:
    """Executa operações de autenticação e gestão de tokens (set_token, get_token, setup, token_generator)."""
    return dispatch_tool(
        "auth",
        {
            "action": action,
            "name": name,
            "email": email,
            "token": token,
            "provider": provider,
            "google_id": google_id,
        },
    )


@mcp.tool(
    name="send_mail",
    description="Envia e-mails transacionais com Bearer Tokens de acesso e snippets de configuração via Gmail.",
)
def send_mail(
    to_email: str,
    recipient_name: str,
    token: str,
    subject: str = "Sua Chave de Acesso · MCP Server Enterprise",
    server_url: str = "https://mcp-server-enterprise.mardukasoft.online",
) -> dict:
    """Dispara e-mail transacional via Gmail com chave de acesso e instruções de configuração."""
    return dispatch_tool(
        "send_mail",
        {
            "to_email": to_email,
            "recipient_name": recipient_name,
            "token": token,
            "subject": subject,
            "server_url": server_url,
        },
    )


@mcp.tool(
    name="benchmark_cost",
    description="Simulador de amortização financeira (SAC/PRICE) de alta complexidade com telemetria determinística de economia de tokens.",
)
def benchmark_cost(
    principal: float | None = None,
    taxa_anual: float | None = None,
    meses: int | None = None,
    sistema: SistemaAmortizacao | None = None,
) -> dict:
    """Executa simulação financeira determinística e retorna métricas de amortização e economia de tokens."""
    return dispatch_tool(
        "benchmark_cost",
        {
            "principal": principal,
            "taxa_anual": taxa_anual,
            "meses": meses,
            "sistema": sistema,
        },
    )



def run_server() -> None:
    """Executa o servidor FastMCP nos modos stdio ou sse."""
    import argparse
    parser = argparse.ArgumentParser(description="MCP Enterprise Server (FastMCP)")
    parser.add_argument("--transport", choices=["stdio", "sse"], default="stdio", help="Transporte de comunicação (stdio ou sse)")
    parser.add_argument("--host", default="127.0.0.1", help="Host para o servidor SSE")
    parser.add_argument("--port", type=int, default=8000, help="Porta para o servidor SSE")
    args, _ = parser.parse_known_args()

    if args.transport == "sse":
        mcp.run(transport="sse", host=args.host, port=args.port)
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    run_server()
