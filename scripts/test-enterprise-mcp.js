#!/usr/bin/env node
/**
 * scripts/test-enterprise-mcp.js
 * Cliente de Teste MCP Protocolar (Wire Protocol Tester).
 * Executa o servidor MCP via stdio e exibe os frames JSON-RPC 2.0 puros.
 */

const { spawn } = require('child_process');
const path = require('path');
const readline = require('readline');

const pythonExe = path.resolve(__dirname, '..', '.venv', 'Scripts', 'python.exe');
const projectRoot = path.resolve(__dirname, '..');

console.log('\x1b[36m%s\x1b[0m', '════════════════════════════════════════════════════════════════');
console.log('\x1b[36m%s\x1b[0m', '  🚀 INICIANDO TESTE DO CLIENTE MCP (PROTOCOLO WIRE JSON-RPC)  ');
console.log('\x1b[36m%s\x1b[0m', '════════════════════════════════════════════════════════════════');
console.log(`📡 Processo MCP: ${pythonExe} -m src.mcp_server.server\n`);

const child = spawn(pythonExe, ['-m', 'src.mcp_server.server'], {
  cwd: projectRoot,
  stdio: ['pipe', 'pipe', 'inherit'],
});

const rl = readline.createInterface({
  input: child.stdout,
  terminal: false,
});

let msgId = 0;

function sendRpc(msg) {
  const payload = JSON.stringify(msg);
  console.log('\x1b[33m%s\x1b[0m', `\n📤 [CLIENTE -> MCP SERVER (stdin)]:`);
  console.log(JSON.stringify(msg, null, 2));
  child.stdin.write(payload + '\n');
}

rl.on('line', (line) => {
  line = line.trim();
  if (!line) return;

  try {
    const json = JSON.parse(line);
    console.log('\x1b[32m%s\x1b[0m', `\n📥 [MCP SERVER -> CLIENTE (stdout)]:`);
    console.log(JSON.stringify(json, null, 2));

    // Passo 1: Handshake Inicial
    if (json.id === 1 && json.result) {
      console.log('\n✅ Handshake Concluído! Notificando inicialização...');
      sendRpc({
        jsonrpc: '2.0',
        method: 'notifications/initialized',
      });

      // Passo 2: Listar Ferramentas
      sendRpc({
        jsonrpc: '2.0',
        id: 2,
        method: 'tools/list',
        params: {},
      });
    }

    // Passo 2: Recebeu Lista de Tools -> Chamar 'hello'
    else if (json.id === 2 && json.result) {
      console.log(`\n✅ ${json.result.tools.length} Ferramentas Listadas no Protocolo!`);
      sendRpc({
        jsonrpc: '2.0',
        id: 3,
        method: 'tools/call',
        params: {
          name: 'hello',
          arguments: { name: 'Eduardo Rezende' },
        },
      });
    }

    // Passo 3: Recebeu 'hello' -> Chamar 'calc' (150 / 25)
    else if (json.id === 3 && json.result) {
      console.log('\n✅ Tool "hello" executada com sucesso!');
      sendRpc({
        jsonrpc: '2.0',
        id: 4,
        method: 'tools/call',
        params: {
          name: 'calc',
          arguments: { valor1: 150, valor2: 25, operacao: '/' },
        },
      });
    }

    // Passo 4: Recebeu 'calc' -> Chamar 'discover'
    else if (json.id === 4 && json.result) {
      console.log('\n✅ Tool "calc" (150 / 25) executada com sucesso!');
      sendRpc({
        jsonrpc: '2.0',
        id: 5,
        method: 'tools/call',
        params: {
          name: 'discover',
          arguments: {},
        },
      });
    }

    // Passo 5: Recebeu 'discover' -> Finalizar
    else if (json.id === 5 && json.result) {
      console.log('\n✅ Tool "discover" retornou todo o catálogo de schemas e documentação!');
      console.log('\n\x1b[36m%s\x1b[0m', '════════════════════════════════════════════════════════════════');
      console.log('\x1b[32m%s\x1b[0m', '  🎉 TODOS OS TESTES PROTOCOLARES MCP FORAM CONCLUÍDOS COM SUCESSO! ');
      console.log('\x1b[36m%s\x1b[0m', '════════════════════════════════════════════════════════════════');
      setTimeout(() => {
        child.kill();
        process.exit(0);
      }, 100);
    }
  } catch (err) {
    // Linha não-JSON (logs informativos do servidor)
  }
});

// Envia a primeira mensagem: initialize
sendRpc({
  jsonrpc: '2.0',
  id: 1,
  method: 'initialize',
  params: {
    protocolVersion: '2024-11-05',
    capabilities: {},
    clientInfo: {
      name: 'enterprise-mcp-smoke-client',
      version: '1.0.0',
    },
  },
});

setTimeout(() => {
  console.error('❌ Timeout aguardando resposta do servidor MCP');
  child.kill();
  process.exit(1);
}, 10000);
