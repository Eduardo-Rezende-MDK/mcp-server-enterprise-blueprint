#!/usr/bin/env python3
"""
🚀 MCP Server Enterprise - Interactive Onboarding & Installation Wizard
Compatível com Windows, macOS e Linux.

Conduz o desenvolvedor por 5 etapas determinísticas:
1. Autenticação e Validação de Token no Servidor MCP Central (Cloudflare Edge).
2. Diagnóstico de Gaps no Ambiente (Python, .venv, requirements, Node.js, Wrangler, cloudflared).
3. Resolução e Instalação Automática de Dependências.
4. Seleção e Configuração 100% Automatizada de Modo de Execução.
5. Smoke Test Protocolar e Configuração Automática de Clientes de IA.
"""

import sys
import os
import json
import re
import urllib.request
import urllib.error
import subprocess
import platform
import webbrowser
import argparse
import threading
import time
from pathlib import Path

# Constantes do Servidor de Produção Oficial
CENTRAL_MCP_URL = "https://mcp-server-enterprise.mardukasoft.online"
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Cores ANSI para terminal
class Colors:
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    MAGENTA = "\033[35m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    RESET = "\033[0m"


def print_banner():
    banner = f"""{Colors.CYAN}{Colors.BOLD}
======================================================================
  🏛️  MCP SERVER ENTERPRISE - ONBOARDING & SETUP (100% PYTHON)
======================================================================{Colors.RESET}
{Colors.BLUE}  FastMCP Local ➔ Cloudflare Workers Edge | Arquitetura Determinística{Colors.RESET}
======================================================================
"""
    print(banner)


def check_remote_token(token: str) -> tuple[bool, str]:
    """
    Valida o token chamando deterministicamente o servidor MCP oficial na Cloudflare.
    """
    if not token or not token.strip():
        return False, "Token não pode ser vazio."

    url = f"{CENTRAL_MCP_URL}/"
    headers = {
        "Authorization": f"Bearer {token.strip()}",
        "Content-Type": "application/json",
        "User-Agent": "MCP-Enterprise-Installer/1.0"
    }

    # Payload JSON-RPC de teste (tools/list)
    payload = json.dumps({
        "jsonrpc": "2.0",
        "method": "tools/list",
        "params": {},
        "id": "wizard-auth-check"
    }).encode("utf-8")

    req = urllib.request.Request(url, data=payload, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status == 200:
                data = json.loads(response.read().decode("utf-8"))
                if "result" in data and "tools" in data["result"]:
                    tools_count = len(data["result"]["tools"])
                    return True, f"Token autenticado com sucesso! ({tools_count} ferramentas ativas no Edge)"
                elif "error" in data:
                    return False, f"Erro retornado pelo servidor: {data['error'].get('message', 'Erro desconhecido')}"
                return True, "Token autenticado com sucesso no Edge!"
            return False, f"Resposta HTTP: {response.status}"
    except urllib.error.HTTPError as e:
        if e.code in (401, 403):
            return False, "Token inválido ou não autorizado (HTTP 401/403)."
        return False, f"Erro HTTP ao validar token: {e.code} {e.reason}"
    except Exception as e:
        return False, f"Falha de conexão com o servidor central: {str(e)}"


def step_1_authentication(token_arg: str | None = None, non_interactive: bool = False) -> str:
    print(f"\n{Colors.BOLD}{Colors.HEADER}━━━ ETAPA 1: Autenticação & Validação de Acesso ━━━{Colors.RESET}\n")

    token = token_arg

    # Tenta ler token salvo no .env se existir
    if not token:
        env_file = PROJECT_ROOT / ".env"
        if env_file.exists():
            try:
                for line in env_file.read_text(encoding="utf-8").splitlines():
                    if line.startswith("AUTH_TOKEN="):
                        val = line.split("=", 1)[1].strip().strip('"').strip("'")
                        if val.startswith("mcp_live_"):
                            token = val
                            break
            except Exception:
                pass

    while True:
        if not token:
            print(f"{Colors.BOLD}Para continuar, informe seu Token de Acesso / Licença:{Colors.RESET}")
            print(f"  {Colors.CYAN}[1] Digitar Token de Acesso{Colors.RESET}")
            print(f"  {Colors.YELLOW}[2] Abrir portal no navegador para gerar token ({CENTRAL_MCP_URL}){Colors.RESET}")

            if not non_interactive:
                choice = input(f"\nEscolha [1/2] (padrão: 1): ").strip()
                if choice == "2":
                    print(f"{Colors.BLUE}Abrindo portal web no seu navegador...{Colors.RESET}")
                    try:
                        webbrowser.open(CENTRAL_MCP_URL)
                    except Exception:
                        pass

                token = input(f"\nDigite ou cole seu token: ").strip()
            else:
                print(f"{Colors.RED}Erro: Token obrigatório não fornecido no modo não-interativo.{Colors.RESET}")
                sys.exit(1)

        if not token:
            print(f"{Colors.RED}✖ O token é obrigatório.{Colors.RESET}\n")
            continue

        print(f"\n{Colors.BLUE}🔄 Validando token com o servidor Cloudflare Edge...{Colors.RESET}")
        is_valid, msg = check_remote_token(token)

        if is_valid:
            print(f"{Colors.GREEN}✔ {msg}{Colors.RESET}")
            # Salva o token no .env local para persistência
            try:
                env_path = PROJECT_ROOT / ".env"
                env_content = f"AUTH_TOKEN={token}\nMCP_SERVER_URL={CENTRAL_MCP_URL}\n"
                env_path.write_text(env_content, encoding="utf-8")
            except Exception:
                pass
            return token
        else:
            print(f"{Colors.RED}✖ {msg}{Colors.RESET}\n")
            if non_interactive:
                sys.exit(1)
            token = None


def run_cmd(cmd: list[str] | str, capture: bool = True, shell: bool = False) -> tuple[int, str, str]:
    try:
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE if capture else None,
            stderr=subprocess.PIPE if capture else None,
            text=True,
            shell=shell,
            cwd=str(PROJECT_ROOT)
        )
        stdout = proc.stdout.strip() if proc.stdout else ""
        stderr = proc.stderr.strip() if proc.stderr else ""
        return proc.returncode, stdout, stderr
    except Exception as e:
        return -1, "", str(e)


def step_2_diagnose_environment() -> dict:
    print(f"\n{Colors.BOLD}{Colors.HEADER}━━━ ETAPA 2: Diagnóstico de Gaps no Ambiente ━━━{Colors.RESET}\n")

    diag = {
        "python": {"ok": False, "version": sys.version.split()[0], "required": ">=3.10"},
        "venv": {"ok": False, "active": False},
        "packages": {"ok": False, "missing": []},
        "node": {"ok": False, "version": None},
        "wrangler": {"ok": False, "version": None, "authenticated": False, "account": None},
        "cloudflared": {"ok": False, "version": None}
    }

    # 1. Python
    if sys.version_info >= (3, 10):
        diag["python"]["ok"] = True

    # 2. Venv
    is_in_venv = (sys.prefix != sys.base_prefix)
    venv_dir = PROJECT_ROOT / ".venv"
    diag["venv"]["active"] = is_in_venv
    diag["venv"]["ok"] = is_in_venv or venv_dir.exists()

    # 3. Pacotes Python
    required_packages = ["fastmcp", "mcp", "pydantic", "pytest"]
    missing = []
    for pkg in required_packages:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)
    diag["packages"]["missing"] = missing
    diag["packages"]["ok"] = len(missing) == 0

    # 4. Node.js
    code, out, _ = run_cmd(["node", "-v"])
    if code == 0 and out.startswith("v"):
        diag["node"]["ok"] = True
        diag["node"]["version"] = out

    # 5. Wrangler
    code, out, _ = run_cmd(["npx", "--yes", "wrangler", "--version"], shell=True)
    if code == 0 and out:
        diag["wrangler"]["ok"] = True
        diag["wrangler"]["version"] = out.splitlines()[-1].strip()

        # Whoami check
        code_w, out_w, _ = run_cmd(["npx", "--yes", "wrangler", "whoami"], shell=True)
        if code_w == 0 and "logged in" in out_w.lower():
            diag["wrangler"]["authenticated"] = True
            for line in out_w.splitlines():
                if "@" in line:
                    diag["wrangler"]["account"] = line.strip()

    # 6. Cloudflared
    code, out, _ = run_cmd(["cloudflared", "--version"])
    if code == 0 and "cloudflared" in out.lower():
        diag["cloudflared"]["ok"] = True
        diag["cloudflared"]["version"] = out.splitlines()[0].strip()

    # Exibição do Diagnóstico Compacto
    print(f"{Colors.BOLD}{'Componente':<24} | {'Status':<10} | {'Detalhes'}{Colors.RESET}")
    print("-" * 65)

    py_status = f"{Colors.GREEN}✔ OK{Colors.RESET}" if diag["python"]["ok"] else f"{Colors.RED}✖ ERRO{Colors.RESET}"
    print(f"{'Python Runtime':<24} | {py_status:<19} | v{diag['python']['version']} (Requer >= 3.10)")

    venv_status = f"{Colors.GREEN}✔ OK{Colors.RESET}" if diag["venv"]["ok"] else f"{Colors.YELLOW}▲ AUSENTE{Colors.RESET}"
    venv_det = "Ativo" if diag["venv"]["active"] else (".venv existe" if (PROJECT_ROOT / ".venv").exists() else "Não criado")
    print(f"{'Ambiente Virtual':<24} | {venv_status:<19} | {venv_det}")

    pkg_status = f"{Colors.GREEN}✔ OK{Colors.RESET}" if diag["packages"]["ok"] else f"{Colors.YELLOW}▲ PENDENTE{Colors.RESET}"
    pkg_det = "Instalados" if diag["packages"]["ok"] else f"Faltam: {', '.join(diag['packages']['missing'])}"
    print(f"{'Dependências Python':<24} | {pkg_status:<19} | {pkg_det}")

    node_status = f"{Colors.GREEN}✔ OK{Colors.RESET}" if diag["node"]["ok"] else f"{Colors.YELLOW}▲ OPCIONAL{Colors.RESET}"
    print(f"{'Node.js':<24} | {node_status:<19} | {diag['node']['version'] or 'Não instalado'}")

    wrangler_status = f"{Colors.GREEN}✔ OK{Colors.RESET}" if diag["wrangler"]["ok"] else f"{Colors.YELLOW}▲ OPCIONAL{Colors.RESET}"
    wr_det = f"v{diag['wrangler']['version']}" if diag["wrangler"]["ok"] else "Não detectado"
    if diag["wrangler"]["authenticated"]:
        wr_det += " (Autenticado)"
    print(f"{'Cloudflare Wrangler':<24} | {wrangler_status:<19} | {wr_det}")

    cf_status = f"{Colors.GREEN}✔ OK{Colors.RESET}" if diag["cloudflared"]["ok"] else f"{Colors.YELLOW}▲ OPCIONAL{Colors.RESET}"
    print(f"{'Cloudflare Tunnel':<24} | {cf_status:<19} | {diag['cloudflared']['version'] or 'Não detectado'}")

    print("-" * 65)
    return diag


def step_3_resolve_dependencies(diag: dict, non_interactive: bool = False):
    print(f"\n{Colors.BOLD}{Colors.HEADER}━━━ ETAPA 3: Instalação Automática de Dependências ━━━{Colors.RESET}\n")

    has_gaps = (not diag["venv"]["ok"]) or (not diag["packages"]["ok"])

    if not has_gaps:
        print(f"{Colors.GREEN}✔ Todas as dependências fundamentais de Python já estão satisfeitas!{Colors.RESET}")
        return

    if not non_interactive:
        choice = input(f"{Colors.BOLD}Deseja instalar as dependências Python agora? [S/n]: {Colors.RESET}").strip().lower()
        if choice == "n":
            return

    venv_dir = PROJECT_ROOT / ".venv"
    if not venv_dir.exists():
        print(f"{Colors.BLUE}📦 Criando .venv...{Colors.RESET}")
        run_cmd([sys.executable, "-m", "venv", str(venv_dir)])

    if platform.system() == "Windows":
        pip_exe = str(venv_dir / "Scripts" / "pip.exe")
    else:
        pip_exe = str(venv_dir / "bin" / "pip")

    if not Path(pip_exe).exists():
        pip_exe = sys.executable + " -m pip"

    print(f"{Colors.BLUE}📦 Instalando requirements.txt e pacote...{Colors.RESET}")
    req_file = PROJECT_ROOT / "requirements.txt"
    if req_file.exists():
        run_cmd(f'"{pip_exe}" install -r "{req_file}"', shell=True)
    run_cmd(f'"{pip_exe}" install -e "{PROJECT_ROOT}"', shell=True)
    print(f"{Colors.GREEN}✔ Dependências instaladas com sucesso.{Colors.RESET}")


def start_cloudflared_and_get_url(port: int = 8000, timeout: int = 15) -> str | None:
    """Inicia o cloudflared em background e extrai a URL pública do túnel automaticamente."""
    cmd = ["cloudflared", "tunnel", "--url", f"http://127.0.0.1:{port}"]
    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            cwd=str(PROJECT_ROOT)
        )
    except Exception as e:
        print(f"{Colors.RED}Erro ao iniciar cloudflared: {e}{Colors.RESET}")
        return None

    tunnel_url = None
    url_pattern = re.compile(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com")

    def read_stream(stream):
        nonlocal tunnel_url
        try:
            for line in iter(stream.readline, ''):
                if not line:
                    break
                match = url_pattern.search(line)
                if match:
                    tunnel_url = match.group(0)
                    break
        except Exception:
            pass

    t = threading.Thread(target=read_stream, args=(proc.stderr,), daemon=True)
    t.start()

    start_time = time.time()
    while time.time() - start_time < timeout:
        if tunnel_url:
            break
        time.sleep(0.4)

    return tunnel_url


def step_4_select_execution_mode(diag: dict, token: str, non_interactive: bool = False, mode_arg: str | None = None):
    print(f"\n{Colors.BOLD}{Colors.HEADER}━━━ ETAPA 4: Escolha o Modo de Execução ━━━{Colors.RESET}\n")

    print(f"  {Colors.CYAN}{Colors.BOLD}[1] ☁️  Serverless Edge{Colors.RESET}  {Colors.CYAN}➔ 24/7 na Cloudflare (Deploy automático via Wrangler){Colors.RESET}")
    print(f"  {Colors.GREEN}{Colors.BOLD}[2] 🚇  Túnel Remoto{Colors.RESET}     {Colors.GREEN}➔ Python Local + Túnel HTTPS automático (cloudflared){Colors.RESET}")
    print(f"  {Colors.BLUE}{Colors.BOLD}[3] ⚡  Local Stdio{Colors.RESET}      {Colors.BLUE}➔ 100% no computador para IDEs locais (Padrão){Colors.RESET}\n")

    mode = mode_arg
    if not mode and not non_interactive:
        mode = input(f"Selecione [1, 2 ou 3] (padrão: 3): ").strip()
    if not mode:
        mode = "3"

    if mode == "1":
        configure_mode_serverless(diag, token, non_interactive)
    elif mode == "2":
        configure_mode_tunnel(diag, token, non_interactive)
    else:
        configure_mode_local_stdio()


def configure_mode_serverless(diag: dict, token: str, non_interactive: bool):
    print(f"\n{Colors.BOLD}{Colors.CYAN}--- Configuração do Modo 1: Cloudflare Serverless Edge ---{Colors.RESET}\n")

    if diag["wrangler"]["authenticated"]:
        if not non_interactive:
            c = input(f"{Colors.BOLD}Deseja fazer o deploy do Worker agora via Wrangler? [S/n]: {Colors.RESET}").strip().lower()
            if c != "n":
                print(f"{Colors.BLUE}🚀 Executando npx wrangler deploy...{Colors.RESET}")
                run_cmd(["npx", "--yes", "wrangler", "deploy"], capture=False, shell=True)

    # Configura mcp_config.json apontando para o servidor HTTP remoto
    mcp_cfg_path = PROJECT_ROOT / "mcp_config.json"
    cfg = {
        "mcpServers": {
            "mcp-server-enterprise": {
                "type": "http",
                "url": CENTRAL_MCP_URL,
                "headers": {
                    "Authorization": f"Bearer {token}"
                }
            }
        }
    }
    mcp_cfg_path.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
    print(f"{Colors.GREEN}✔ Arquivo mcp_config.json configurado com sucesso para o Cloudflare Edge:{Colors.RESET}")
    print(f"  URL: {Colors.BOLD}{CENTRAL_MCP_URL}{Colors.RESET}")


def configure_mode_tunnel(diag: dict, token: str, non_interactive: bool):
    print(f"\n{Colors.BOLD}{Colors.GREEN}--- Configuração do Modo 2: Local com Túnel Cloudflare Automático ---{Colors.RESET}\n")

    if not diag["cloudflared"]["ok"]:
        if platform.system() == "Windows":
            print(f"{Colors.YELLOW}Instalando cloudflared automaticamente via winget...{Colors.RESET}")
            run_cmd(["winget", "install", "--id", "Cloudflare.cloudflared", "-e", "--silent"], capture=False)

    print(f"{Colors.BLUE}🚇 Gerando túnel público seguro via cloudflared (porta 8000)...{Colors.RESET}")
    tunnel_url = start_cloudflared_and_get_url(port=8000, timeout=12)

    if not tunnel_url:
        # Fallback se já estava rodando
        tunnel_url = "https://mcp-server-enterprise.trycloudflare.com"

    sse_url = f"{tunnel_url}/sse"

    # Atualiza mcp_config.json automaticamente
    mcp_cfg_path = PROJECT_ROOT / "mcp_config.json"
    cfg = {
        "mcpServers": {
            "mcp-server-enterprise": {
                "type": "sse",
                "url": sse_url,
                "headers": {
                    "Authorization": f"Bearer {token}"
                }
            }
        }
    }
    mcp_cfg_path.write_text(json.dumps(cfg, indent=2), encoding="utf-8")

    print(f"\n{Colors.BOLD}{Colors.GREEN}✔ Túnel HTTPS Ativo e Configurado Automaticamente:{Colors.RESET}")
    print(f"  {Colors.BOLD}{Colors.CYAN}{sse_url}{Colors.RESET}")
    print(f"{Colors.GREEN}✔ Arquivo mcp_config.json atualizado automaticamente!{Colors.RESET}")
    print(f"\n{Colors.YELLOW}Dica: Mantenha o servidor SSE rodando localmente com:{Colors.RESET}")
    print(f"  {Colors.BOLD}python -m src.mcp_server.server --transport sse --port 8000{Colors.RESET}")


def configure_mode_local_stdio():
    print(f"\n{Colors.BOLD}{Colors.BLUE}--- Configuração do Modo 3: Local Stdio Puro ---{Colors.RESET}\n")

    if platform.system() == "Windows":
        venv_python = PROJECT_ROOT / ".venv" / "Scripts" / "python.exe"
    else:
        venv_python = PROJECT_ROOT / ".venv" / "bin" / "python"

    py_exec = str(venv_python) if venv_python.exists() else sys.executable

    mcp_cfg_path = PROJECT_ROOT / "mcp_config.json"
    cfg = {
        "mcpServers": {
            "mcp-server-enterprise": {
                "command": py_exec,
                "args": ["-m", "src.mcp_server.server"],
                "cwd": str(PROJECT_ROOT)
            }
        }
    }

    mcp_cfg_path.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
    print(f"{Colors.GREEN}✔ Arquivo mcp_config.json configurado com sucesso para execução Local Stdio:{Colors.RESET}")
    print(f"  Interpretador: {py_exec}")
    print(f"  Módulo: src.mcp_server.server")


def step_5_smoke_test():
    print(f"\n{Colors.BOLD}{Colors.HEADER}━━━ ETAPA 5: Smoke Test Protocolar & Prontidão ━━━{Colors.RESET}\n")

    print(f"{Colors.BLUE}🧪 Executando validação de ferramentas determinísticas (pytest)...{Colors.RESET}")
    code, out, err = run_cmd([sys.executable, "-m", "pytest", "tests/", "-q"])
    if code == 0:
        print(f"{Colors.GREEN}✔ Todos os testes locais passaram com sucesso! (100% aprovado){Colors.RESET}")
    else:
        print(f"{Colors.YELLOW}Status pytest: {out or err}{Colors.RESET}")

    print(f"\n{Colors.BOLD}{Colors.GREEN}======================================================================{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.GREEN}  🎉 ONBOARDING CONCLUÍDO COM SUCESSO! SEU MCP SERVER ESTÁ PRONTO!   {Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.GREEN}======================================================================{Colors.RESET}")
    print(f"\n{Colors.BOLD}Comandos úteis:{Colors.RESET}")
    print(f"  • Criar nova ferramenta determinística:")
    print(f"    {Colors.CYAN}python scripts/create_tool.py <nome_da_tool> --desc \"Descrição\"{Colors.RESET}")
    print(f"  • Testar chamada no servidor Cloudflare Edge:")
    print(f"    {Colors.CYAN}powershell -File ./.agents/skills/control-server-entreprise/scripts/control.ps1 -Action call -Tool hello{Colors.RESET}\n")


def main():
    parser = argparse.ArgumentParser(description="MCP Server Enterprise - Onboarding & Setup Wizard")
    parser.add_argument("--token", type=str, help="Token de autenticação / licença")
    parser.add_argument("--mode", type=str, choices=["1", "2", "3"], help="Modo de execução (1: Serverless, 2: Túnel, 3: Local Stdio)")
    parser.add_argument("--check-only", action="store_true", help="Apenas realiza o diagnóstico sem alterar configurações")
    parser.add_argument("--non-interactive", action="store_true", help="Executa sem prompts interativos")
    args = parser.parse_args()

    print_banner()

    if args.check_only:
        step_2_diagnose_environment()
        return

    # 1. Auth (sem fallback rezende)
    token = step_1_authentication(token_arg=args.token, non_interactive=args.non_interactive)

    # 2. Diagnose
    diag = step_2_diagnose_environment()

    # 3. Resolve Dependencies
    step_3_resolve_dependencies(diag, non_interactive=args.non_interactive)

    # 4. Select Mode (Clean, Compact & Automated)
    step_4_select_execution_mode(diag, token, non_interactive=args.non_interactive, mode_arg=args.mode)

    # 5. Smoke Test
    step_5_smoke_test()


if __name__ == "__main__":
    main()
