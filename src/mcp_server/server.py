"""Main entry point for MCP Enterprise Server using FastMCP."""

from fastmcp import FastMCP

from .schemas.calc import CalcInput, OperacaoEnum
from .schemas.hello import HelloInput
from .tools.calc import execute_calc
from .tools.discover import execute_discover
from .tools.hello import execute_hello

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
    result = execute_discover()
    return result.model_dump()


@mcp.tool(
    name="hello",
    description="Retorna uma mensagem de saudação personalizada com o nome fornecido, acompanhada da data e hora atual do sistema.",
)
def hello(name: str) -> dict:
    """Retorna saudação com carimbo de data e hora do sistema."""
    input_data = HelloInput(name=name)
    result = execute_hello(input_data)
    return result.model_dump()


@mcp.tool(
    name="calc",
    description="Calcula o resultado de uma operação matemática básica entre dois números (adição, subtração, multiplicação ou divisão).",
)
def calc(valor1: float, valor2: float, operacao: OperacaoEnum) -> dict:
    """Executa cálculo aritmético determinístico (+, -, *, /)."""
    input_data = CalcInput(valor1=valor1, valor2=valor2, operacao=operacao)
    result = execute_calc(input_data)
    return result.model_dump()


def run_server() -> None:
    """Executa o servidor FastMCP no modo stdio."""
    mcp.run()


if __name__ == "__main__":
    run_server()
