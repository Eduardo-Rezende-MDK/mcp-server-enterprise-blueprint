"""Scaffolding and Generator for MCP Enterprise Tools."""

import argparse
import re
import sys
from pathlib import Path


def snake_to_pascal(name: str) -> str:
    """Converte 'minha_ferramenta' para 'MinhaFerramenta'."""
    return "".join(word.capitalize() for word in re.split(r"[_\-\s]+", name) if word)


def create_tool(tool_name: str, description: str | None = None) -> Path:
    """Clona o template canônico e cria o módulo completo da nova ferramenta."""
    # Validação do nome
    tool_name = tool_name.strip().lower()
    if not re.match(r"^[a-z][a-z0-9_]*$", tool_name):
        raise ValueError(
            f"Nome inválido '{tool_name}'. Utilize apenas letras minúsculas, números e sublinhados (ex: cotacao_dolar)."
        )

    tools_dir = Path(__file__).resolve().parent / "tools"
    template_dir = tools_dir / "_template"
    target_dir = tools_dir / tool_name

    if target_dir.exists():
        raise FileExistsError(f"A ferramenta '{tool_name}' já existe em: {target_dir}")

    if not template_dir.exists():
        raise FileNotFoundError(f"Diretório de template não encontrado em: {template_dir}")

    target_dir.mkdir(parents=True, exist_ok=False)

    pascal_name = snake_to_pascal(tool_name)
    desc = description or f"Executa a operação determinística para a ferramenta '{tool_name}'."

    replacements = {
        "TemplateInput": f"{pascal_name}Input",
        "TemplateOutput": f"{pascal_name}Output",
        "template_tool": tool_name,
        "Descrição semântica e objetiva do que a ferramenta realiza para o LLM decidir sua invocação.": desc,
    }

    files_to_copy = ["schema.py", "handler.py", "meta.py", "__init__.py"]

    for file_name in files_to_copy:
        src_file = template_dir / file_name
        dest_file = target_dir / file_name

        content = src_file.read_text(encoding="utf-8")
        for old_str, new_str in replacements.items():
            content = content.replace(old_str, new_str)

        dest_file.write_text(content, encoding="utf-8")

    return target_dir


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Gera uma nova MCP Tool modular e determinística no servidor MCP Enterprise."
    )
    parser.add_argument("name", help="Nome da nova ferramenta em snake_case (ex: consulta_saldo, cotacao_dolar)")
    parser.add_argument(
        "--desc",
        "-d",
        default=None,
        help="Descrição funcional da ferramenta para instrução do LLM",
    )

    args = parser.parse_args()

    try:
        created_path = create_tool(args.name, args.desc)
        pascal_name = snake_to_pascal(args.name)
        print("\n" + "=" * 70)
        print(f"✨ Ferramenta '{args.name}' criada com sucesso!")
        print(f"📂 Diretório: {created_path}")
        print("=" * 70)
        print("Arquivos criados:")
        print(f"  ├── schema.py   -> {pascal_name}Input / {pascal_name}Output")
        print(f"  ├── handler.py  -> execute({pascal_name}Input)")
        print(f"  ├── meta.py     -> METADATA com documentação e exemplos")
        print("  └── __init__.py -> exportador padrão")
        print("\n🚀 A ferramenta já é descoberta automaticamente pelo servidor!")
        print("=" * 70 + "\n")
    except Exception as exc:
        print(f"\n❌ Erro ao criar ferramenta: {exc}\n", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
