#!/usr/bin/env node
/**
 * test-mcp.js
 * Deterministic smoke test for @cloudflare/mcp-server-cloudflare via JSON-RPC over stdio.
 */

const { spawn, execSync } = require('child_process');
const readline = require('readline');

function resolveAccountId(cliArg) {
  if (cliArg && /^[a-f0-9]{32}$/i.test(cliArg.trim())) {
    return cliArg.trim();
  }
  if (process.env.CLOUDFLARE_ACCOUNT_ID && /^[a-f0-9]{32}$/i.test(process.env.CLOUDFLARE_ACCOUNT_ID.trim())) {
    return process.env.CLOUDFLARE_ACCOUNT_ID.trim();
  }
  try {
    const isWindows = process.platform === 'win32';
    const output = execSync('npx --yes wrangler whoami', {
      encoding: 'utf-8',
      stdio: ['ignore', 'pipe', 'ignore'],
      shell: isWindows,
    });
    const match = output.match(/([a-f0-9]{32})/i);
    if (match) {
      return match[1];
    }
  } catch (_) {}
  return null;
}

async function testMcpServer(accountId, timeoutMs = 15000) {
  const startTime = Date.now();
  const isWindows = process.platform === 'win32';
  const command = isWindows ? 'npx.cmd' : 'npx';
  const args = ['-y', '@cloudflare/mcp-server-cloudflare', 'run'];
  if (accountId) {
    args.push(accountId);
  }

  return new Promise((resolve) => {
    let timeoutId;
    let resolved = false;

    const child = spawn(command, args, {
      stdio: ['pipe', 'pipe', 'pipe'],
      env: { ...process.env },
      shell: isWindows,
    });

    const result = {
      status: 'pending',
      accountId: accountId || null,
      serverInfo: null,
      protocolVersion: null,
      toolsCount: 0,
      tools: [],
      error: null,
      executionTimeMs: 0,
    };

    const cleanupAndResolve = (finalResult) => {
      if (resolved) return;
      resolved = true;
      clearTimeout(timeoutId);
      finalResult.executionTimeMs = Date.now() - startTime;
      try {
        child.kill();
      } catch (_) {}
      resolve(finalResult);
    };

    timeoutId = setTimeout(() => {
      result.status = 'error';
      result.error = `Timeout after ${timeoutMs}ms waiting for MCP server response`;
      cleanupAndResolve(result);
    }, timeoutMs);

    const rl = readline.createInterface({
      input: child.stdout,
      terminal: false,
    });

    rl.on('line', (line) => {
      line = line.trim();
      if (!line) return;

      try {
        const json = JSON.parse(line);

        // Step 1: Handle initialize response
        if (json.id === 1 && json.result) {
          result.serverInfo = json.result.serverInfo || null;
          result.protocolVersion = json.result.protocolVersion || null;

          // Send initialized notification
          const initNotification = JSON.stringify({
            jsonrpc: '2.0',
            method: 'notifications/initialized',
          }) + '\n';
          child.stdin.write(initNotification);

          // Request tools list
          const listToolsRequest = JSON.stringify({
            jsonrpc: '2.0',
            id: 2,
            method: 'tools/list',
            params: {},
          }) + '\n';
          child.stdin.write(listToolsRequest);
        }
        // Step 2: Handle tools/list response
        else if (json.id === 2 && json.result) {
          const tools = json.result.tools || [];
          result.status = 'success';
          result.toolsCount = tools.length;
          result.tools = tools.map((t) => ({
            name: t.name,
            description: t.description ? t.description.slice(0, 100) : '',
          }));
          cleanupAndResolve(result);
        } else if (json.error) {
          result.status = 'error';
          result.error = json.error.message || JSON.stringify(json.error);
          cleanupAndResolve(result);
        }
      } catch (_) {
        // Ignore non-JSON lines
      }
    });

    let stderrOutput = '';
    child.stderr.on('data', (data) => {
      stderrOutput += data.toString();
    });

    child.on('error', (err) => {
      result.status = 'error';
      result.error = `Failed to start process: ${err.message}`;
      cleanupAndResolve(result);
    });

    child.on('close', (code) => {
      if (!resolved) {
        result.status = 'error';
        result.error = `MCP Server closed prematurely with exit code ${code}. Stderr: ${stderrOutput.trim()}`;
        cleanupAndResolve(result);
      }
    });

    // Step 0: Send initialize request
    const initRequest = JSON.stringify({
      jsonrpc: '2.0',
      id: 1,
      method: 'initialize',
      params: {
        protocolVersion: '2024-11-05',
        capabilities: {},
        clientInfo: {
          name: 'mcp-smoke-tester',
          version: '1.0.0',
        },
      },
    }) + '\n';

    child.stdin.write(initRequest);
  });
}

(async () => {
  const accountId = resolveAccountId(process.argv[2]);
  if (!accountId) {
    console.error(JSON.stringify({
      status: 'error',
      error: 'Cloudflare Account ID could not be resolved from CLI argument, env, or wrangler session.',
    }, null, 2));
    process.exit(1);
  }

  const result = await testMcpServer(accountId);
  console.log(JSON.stringify(result, null, 2));
  if (result.status !== 'success') {
    process.exit(1);
  }
})();
