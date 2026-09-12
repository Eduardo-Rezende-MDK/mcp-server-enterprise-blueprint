"""Deterministic handler for the 'calc' MCP tool."""

from .schema import CalcInput, CalcOutput, OperacaoEnum


def execute(dados: CalcInput) -> CalcOutput:
    """Calcula deterministamente o resultado da operação aritmética entre dois números."""
    op = dados.operacao
    v1 = dados.valor1
    v2 = dados.valor2

    if op in (OperacaoEnum.ADICAO, OperacaoEnum.SOMA):
        res = v1 + v2
        simbolo = "+"
    elif op in (OperacaoEnum.SUBTRACAO, OperacaoEnum.SUBTRACAO_NOME):
        res = v1 - v2
        simbolo = "-"
    elif op in (OperacaoEnum.MULTIPLICACAO, OperacaoEnum.MULTIPLICACAO_NOME):
        res = v1 * v2
        simbolo = "*"
    elif op in (OperacaoEnum.DIVISAO, OperacaoEnum.DIVISAO_NOME):
        if v2 == 0:
            raise ValueError("Divisão por zero não é permitida.")
        res = v1 / v2
        simbolo = "/"
    else:
        raise ValueError(f"Operação não suportada: {op}")

    def _fmt(n: float) -> str:
        return str(int(n)) if n.is_integer() else str(n)

    formula = f"{_fmt(v1)} {simbolo} {_fmt(v2)} = {_fmt(res)}"
    return CalcOutput(resultado=res, formula=formula)
