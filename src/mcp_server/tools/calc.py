from ..schemas.calc import CalcInput, CalcOutput, OperacaoEnum


def execute_calc(dados: CalcInput) -> CalcOutput:
    """Calcula operações aritméticas com exatidão determinística e proteção contra divisão por zero."""
    v1 = dados.valor1
    v2 = dados.valor2
    op = dados.operacao

    # Normalizar operador
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

    # Formatar números inteiros sem .0 desnecessário na fórmula visual
    v1_str = f"{int(v1)}" if v1.is_integer() else f"{v1}"
    v2_str = f"{int(v2)}" if v2.is_integer() else f"{v2}"
    res_str = f"{int(res)}" if isinstance(res, float) and res.is_integer() else f"{round(res, 6)}"

    formula = f"{v1_str} {simbolo} {v2_str} = {res_str}"
    return CalcOutput(resultado=round(res, 6), formula=formula)
