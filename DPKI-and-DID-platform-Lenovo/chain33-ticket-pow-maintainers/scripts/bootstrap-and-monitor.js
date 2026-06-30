"use strict";

const http = require("http");
const https = require("https");
const fs = require("fs");
const path = require("path");

const packageRoot = path.resolve(__dirname, "..");
const configPath = path.join(packageRoot, "maintainers.json");
const config = JSON.parse(fs.readFileSync(configPath, "utf8"));

const args = parseArgs(process.argv.slice(2));
const rpcUrl = args.rpc || process.env.CHAIN33_RPC_URL || config.rpcUrl;
const requiredMaintainers = Number(
  args.maintainers || process.env.MAINTAINERS || config.defaultMaintainerCount || 4
);
const watch = Boolean(args.watch);
const noBootstrap = Boolean(args["no-bootstrap"]);
const intervalMs = Number(args.interval || process.env.MONITOR_INTERVAL_MS || 5000);
const maintainers = config.maintainers.slice(0, requiredMaintainers);
const walletPassword = process.env.CHAIN33_WALLET_PASSWORD || config.walletPassword;
let rpcId = 1;

function parseArgs(rawArgs) {
  const out = {};
  for (let i = 0; i < rawArgs.length; i += 1) {
    const arg = rawArgs[i];
    if (!arg.startsWith("--")) {
      continue;
    }
    const key = arg.slice(2);
    const next = rawArgs[i + 1];
    if (!next || next.startsWith("--")) {
      out[key] = true;
      continue;
    }
    out[key] = next;
    i += 1;
  }
  return out;
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function rpcCall(method, params = []) {
  const endpoint = new URL(rpcUrl);
  const body = JSON.stringify({
    jsonrpc: "2.0",
    id: rpcId += 1,
    method,
    params: Array.isArray(params) ? params : [params],
  });
  const transport = endpoint.protocol === "https:" ? https : http;

  return new Promise((resolve, reject) => {
    const req = transport.request(
      {
        protocol: endpoint.protocol,
        hostname: endpoint.hostname,
        port: endpoint.port,
        path: endpoint.pathname || "/",
        method: "POST",
        headers: {
          "content-type": "application/json",
          "content-length": Buffer.byteLength(body),
        },
        timeout: 5000,
      },
      (res) => {
        let data = "";
        res.setEncoding("utf8");
        res.on("data", (chunk) => {
          data += chunk;
        });
        res.on("end", () => {
          try {
            const parsed = JSON.parse(data);
            if (parsed.error) {
              reject(new Error(formatRpcError(method, parsed.error)));
              return;
            }
            resolve(parsed.result);
          } catch (error) {
            reject(new Error(`${method} returned invalid JSON: ${error.message}`));
          }
        });
      }
    );

    req.on("timeout", () => {
      req.destroy(new Error(`${method} timed out`));
    });
    req.on("error", reject);
    req.write(body);
    req.end();
  });
}

function formatRpcError(method, error) {
  if (typeof error === "string") {
    return `${method}: ${error}`;
  }
  if (error && typeof error === "object") {
    return `${method}: ${error.message || JSON.stringify(error)}`;
  }
  return `${method}: ${String(error)}`;
}

function isOkReply(reply) {
  return Boolean(reply && (reply.isOK || reply.isOk || reply.IsOk));
}

async function waitForRpc() {
  const started = Date.now();
  while (Date.now() - started < 60000) {
    try {
      await rpcCall("Chain33.Version", []);
      return;
    } catch (error) {
      await sleep(1000);
    }
  }
  throw new Error(`RPC did not become ready at ${rpcUrl}`);
}

async function tryRpc(method, params, allowedMessages = []) {
  try {
    return await rpcCall(method, params);
  } catch (error) {
    const allowed = allowedMessages.some((message) => error.message.includes(message));
    if (!allowed) {
      throw error;
    }
    return { isOK: true, msg: error.message };
  }
}

async function bootstrapWallet() {
  let status = await rpcCall("Chain33.GetWalletStatus", []);

  if (!status || !status.isHasSeed) {
    const saved = await tryRpc(
      "Chain33.SaveSeed",
      [{ seed: config.seed, passwd: walletPassword }],
      ["ErrSeedExist", "seed has already"]
    );
    if (!isOkReply(saved)) {
      throw new Error(`SaveSeed failed: ${JSON.stringify(saved)}`);
    }
  }

  const unlock = await rpcCall("Chain33.UnLock", [
    {
      passwd: walletPassword,
      walletorticket: false,
      walletOrTicket: false,
      timeout: 0,
    },
  ]);
  if (!isOkReply(unlock)) {
    throw new Error(`Wallet unlock failed: ${JSON.stringify(unlock)}`);
  }

  const ticketUnlock = await rpcCall("Chain33.UnLock", [
    {
      passwd: walletPassword,
      walletorticket: true,
      walletOrTicket: true,
      timeout: 0,
    },
  ]);
  if (!isOkReply(ticketUnlock)) {
    throw new Error(`Ticket wallet unlock failed: ${JSON.stringify(ticketUnlock)}`);
  }

  for (const maintainer of maintainers) {
    await tryRpc(
      "Chain33.ImportPrivkey",
      [{ privkey: maintainer.privkey, label: maintainer.label }],
      ["ErrPrivkeyExist", "PrivkeyExist", "ErrLabelHasUsed", "LabelHasUsed", "already"]
    );
  }

  const mining = await rpcCall("ticket.SetAutoMining", [{ flag: 1 }]);
  if (!isOkReply(mining)) {
    throw new Error(`ticket.SetAutoMining failed: ${JSON.stringify(mining)}`);
  }

  status = await rpcCall("Chain33.GetWalletStatus", []);
  console.log(
    `[bootstrap] wallet unlocked=${!status.isWalletLock} ticketUnlocked=${!status.isTicketLock} ` +
      `autoMining=${status.isAutoMining} requiredMaintainers=${requiredMaintainers}`
  );
}

async function getAccounts() {
  const accounts = await rpcCall("Chain33.GetAccounts", [{ withoutBalance: true }]);
  const wallets = accounts && (accounts.wallets || accounts.Wallets);
  return Array.isArray(wallets) ? wallets : [];
}

async function getHeader() {
  return rpcCall("Chain33.GetLastHeader", []);
}

async function readStatus(previousHeight) {
  const [version, header, walletStatus, ticketCount, accounts] = await Promise.all([
    rpcCall("Chain33.Version", []),
    getHeader(),
    rpcCall("Chain33.GetWalletStatus", []),
    rpcCall("ticket.GetTicketCount", [{}]),
    getAccounts(),
  ]);
  const accountAddresses = new Set(
    accounts
      .map((wallet) => wallet.acc || wallet.Acc)
      .filter(Boolean)
      .map((account) => account.addr || account.Addr)
      .filter(Boolean)
  );
  const importedMaintainers = maintainers.filter((maintainer) =>
    accountAddresses.has(maintainer.minerAddr)
  );
  const height = Number(header && (header.height || header.Height || 0));
  const delta = previousHeight === null ? 0 : height - previousHeight;

  return {
    version: version && (version.chain33 || version.Chain33 || version),
    height,
    delta,
    hash: header && (header.hash || header.Hash || ""),
    walletStatus,
    ticketCount: Number(ticketCount && (ticketCount.data || ticketCount.Data || ticketCount || 0)),
    importedMaintainerCount: importedMaintainers.length,
  };
}

function printStatus(status) {
  const wallet = status.walletStatus || {};
  const marker = status.importedMaintainerCount >= requiredMaintainers ? "ok" : "warn";
  console.log(
    `[monitor:${marker}] height=${status.height} delta=${status.delta} ticketCount=${status.ticketCount} ` +
      `autoMining=${Boolean(wallet.isAutoMining)} walletLocked=${Boolean(wallet.isWalletLock)} ` +
      `maintainers=${status.importedMaintainerCount}/${requiredMaintainers}`
  );
}

async function main() {
  if (!Number.isInteger(requiredMaintainers) || requiredMaintainers < 1) {
    throw new Error("--maintainers must be a positive integer");
  }
  if (requiredMaintainers > config.maintainers.length) {
    throw new Error(`Only ${config.maintainers.length} test maintainers are configured`);
  }

  await waitForRpc();
  if (!noBootstrap) {
    await bootstrapWallet();
  }

  let previousHeight = null;
  do {
    const status = await readStatus(previousHeight);
    printStatus(status);
    previousHeight = status.height;
    if (!watch) {
      break;
    }
    await sleep(intervalMs);
  } while (true);
}

main().catch((error) => {
  console.error(`[error] ${error.message}`);
  process.exit(1);
});
