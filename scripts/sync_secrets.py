"""Script utilitário para sincronizar segredos locais (.dev.vars ou .env) diretamente para o Cloudflare Workers."""

import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent


def load_env_file(filepath: Path) -> dict:
    """Carrega variáveis de um arquivo .env ou .dev.vars."""
    env_vars = {}
    if not filepath.exists():
        return env_vars

    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, val = line.split("=", 1)
            key = key.strip()
            val = val.strip().strip("\"'")
            if key and val:
                env_vars[key] = val
    return env_vars


def sync_secrets():
    """Envia cada segredo para a Cloudflare via 'npx wrangler secret put'."""
    dev_vars_path = PROJECT_ROOT / ".dev.vars"
    env_path = PROJECT_ROOT / ".env"

    vars_to_sync = load_env_file(dev_vars_path)
    if not vars_to_sync:
        vars_to_sync = load_env_file(env_path)

    if not vars_to_sync:
        print("❌ Nenhum arquivo .dev.vars ou .env encontrado com credenciais.")
        sys.exit(1)

    print("═══════════════════════════════════════════════════════════════")
    print(" 🔐 SINCRONIZAÇÃO DE SEGREDOS -> CLOUDFLARE WORKERS")
    print("═══════════════════════════════════════════════════════════════\n")

    # Lista de chaves consideradas sensíveis para enviar como secret
    sensitive_keys = [
        "REDIS_URL",
        "GMAIL_USER",
        "GMAIL_APP_PASSWORD",
        "RESEND_API_KEY",
        "GOOGLE_CLIENT_ID",
        "GOOGLE_CLIENT_SECRET",
    ]

    for key in sensitive_keys:
        value = vars_to_sync.get(key)
        if not value:
            print(f"⚠️  [{key}]: não encontrado no arquivo local, ignorando.")
            continue

        print(f"🚀 Enviando secret [{key}] para o Cloudflare Worker...")
        try:
            # wrangler secret put <KEY> lê o valor do stdin
            process = subprocess.Popen(
                ["npx", "wrangler", "secret", "put", key],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                shell=True,
            )
            stdout, stderr = process.communicate(input=f"{value}\n")
            if process.returncode == 0:
                print(f"   ✅ [{key}] sincronizado com sucesso!")
            else:
                print(f"   ❌ Erro ao enviar [{key}]: {stderr.strip() or stdout.strip()}")
        except Exception as exc:
            print(f"   ❌ Falha na execução do wrangler: {exc}")

    print("\n🎉 Sincronização finalizada! Execute 'npx wrangler deploy' para atualizar o código.")


if __name__ == "__main__":
    sync_secrets()
