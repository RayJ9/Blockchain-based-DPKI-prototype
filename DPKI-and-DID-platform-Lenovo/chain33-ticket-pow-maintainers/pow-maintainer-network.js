"use strict";

const crypto = require("crypto");
const http = require("http");
const { URL } = require("url");

const DEFAULTS = {
  maintainers: 4,
  difficulty: 3,
  controlPort: 9899,
  blockDelayMs: 250,
  networkLatencyMs: 35,
  reward: 50,
  maxTxPerBlock: 0,
  miningBatchSize: 4000,
  mineEmpty: false,
  monitorIntervalMs: 10000,
  genesisTimestamp: 1710000000000,
};

function parseArgs(argv) {
  const options = { ...DEFAULTS };

  for (let index = 2; index < argv.length; index += 1) {
    const arg = argv[index];
    const next = argv[index + 1];

    if (arg === "--maintainers" && next) {
      options.maintainers = Number(next);
      index += 1;
    } else if (arg === "--difficulty" && next) {
      options.difficulty = Number(next);
      index += 1;
    } else if (arg === "--control-port" && next) {
      options.controlPort = Number(next);
      index += 1;
    } else if (arg === "--block-delay-ms" && next) {
      options.blockDelayMs = Number(next);
      index += 1;
    } else if (arg === "--network-latency-ms" && next) {
      options.networkLatencyMs = Number(next);
      index += 1;
    } else if (arg === "--max-tx-per-block" && next) {
      options.maxTxPerBlock = Number(next);
      index += 1;
    } else if (arg === "--mining-batch-size" && next) {
      options.miningBatchSize = Number(next);
      index += 1;
    } else if (arg === "--mine-empty") {
      options.mineEmpty = true;
    } else if (arg === "--no-mine-empty") {
      options.mineEmpty = false;
    }
  }

  if (!Number.isInteger(options.maintainers) || options.maintainers < 1) {
    throw new Error("--maintainers must be an integer >= 1");
  }

  if (!Number.isInteger(options.difficulty) || options.difficulty < 1) {
    throw new Error("--difficulty must be an integer >= 1");
  }

  if (!Number.isInteger(options.controlPort) || options.controlPort < 1) {
    throw new Error("--control-port must be an integer >= 1");
  }

  return options;
}

function wait(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function yieldToEventLoop() {
  return new Promise((resolve) => setImmediate(resolve));
}

function clone(value) {
  return JSON.parse(JSON.stringify(value));
}

function sha256(value) {
  return crypto.createHash("sha256").update(value).digest("hex");
}

function stableBlockData(block) {
  return JSON.stringify({
    index: block.index,
    previousHash: block.previousHash,
    timestamp: block.timestamp,
    transactions: block.transactions,
    nonce: block.nonce,
    difficulty: block.difficulty,
    miner: block.miner,
  });
}

function calculateBlockHash(block) {
  return sha256(stableBlockData(block));
}

function isRewardTx(tx) {
  return tx && tx.from === "system" && tx.data === "mining-reward";
}

function selectBlockTransactions(mempool, maxTxPerBlock) {
  if (!Number.isFinite(maxTxPerBlock) || maxTxPerBlock <= 0) {
    return mempool.slice();
  }
  return mempool.slice(0, maxTxPerBlock);
}

function isBetterChain(candidateChain, currentChain) {
  if (candidateChain.length !== currentChain.length) {
    return candidateChain.length > currentChain.length;
  }
  const candidateHash = candidateChain[candidateChain.length - 1].hash;
  const currentHash = currentChain[currentChain.length - 1].hash;
  return String(candidateHash).localeCompare(String(currentHash)) < 0;
}

function createGenesisBlock(options) {
  const block = {
    index: 0,
    previousHash: "0".repeat(64),
    timestamp: options.genesisTimestamp,
    transactions: [
      {
        id: "genesis",
        from: "system",
        to: "network",
        amount: 0,
        data: "chain33-ticket-pow-maintainers-genesis",
        timestamp: options.genesisTimestamp,
      },
    ],
    nonce: 0,
    difficulty: options.difficulty,
    miner: "genesis",
  };

  block.hash = calculateBlockHash(block);
  return block;
}

function createTransaction(body) {
  const timestamp = Date.now();
  const normalized = {
    from: String(body.from || "anonymous"),
    to: String(body.to || "anonymous"),
    amount: Number(body.amount || 0),
    data: String(body.data || ""),
    timestamp,
  };

  return {
    id: sha256(JSON.stringify(normalized)),
    ...normalized,
  };
}

function createDpkiState() {
  return {
    roots: new Map(),
    certificates: new Map(),
    authRecords: new Map(),
  };
}

function applyDpkiTransaction(state, tx) {
  let envelope;
  try {
    envelope = JSON.parse(tx.data || "{}");
  } catch (_error) {
    return;
  }
  if (!envelope || envelope.protocol !== "dpki-real-experiment") return;

  const payload = envelope.payload || {};
  if (envelope.kind === "putDomainRoot") {
    state.roots.set(payload.domainId, payload.repoRoot);
  } else if (envelope.kind === "putCertificate") {
    state.certificates.set(payload.certKey, payload);
  } else if (envelope.kind === "putCertificateAndDomainRoot") {
    state.certificates.set(payload.certKey, payload);
    state.roots.set(payload.domainId, payload.repoRoot);
  } else if (envelope.kind === "authenticate") {
    state.authRecords.set(payload.requestId, payload);
  }
}

async function mineBlock(candidate, options, shouldAbort) {
  const prefix = "0".repeat(options.difficulty);
  let nonce = 0;

  while (!shouldAbort()) {
    for (let count = 0; count < options.miningBatchSize; count += 1) {
      const block = { ...candidate, nonce };
      const hash = calculateBlockHash(block);

      if (hash.startsWith(prefix)) {
        return { ...block, hash };
      }

      nonce += 1;
    }

    await yieldToEventLoop();
  }

  return null;
}

class Maintainer {
  constructor(id, options, genesisBlock) {
    this.id = id;
    this.options = options;
    this.chain = [clone(genesisBlock)];
    this.mempool = [];
    this.mempoolVersion = 0;
    this.seenTxIds = new Set(["genesis"]);
    this.peers = [];
    this.miningEnabled = true;
    this.miningLoopRunning = false;
    this.chainVersion = 0;
    this.minedBlocks = 0;
    this.acceptedBlocks = 0;
    this.rejectedBlocks = 0;
    this.lastBlockAt = null;
    this.lastSeenTxAt = null;
    this.dpkiState = createDpkiState();
  }

  setPeers(peers) {
    this.peers = peers.filter((peer) => peer.id !== this.id);
  }

  latestBlock() {
    return this.chain[this.chain.length - 1];
  }

  status() {
    const latest = this.latestBlock();
    return {
      id: this.id,
      active: this.miningEnabled,
      miningLoopRunning: this.miningLoopRunning,
      peers: this.peers.map((peer) => peer.id),
      chainHeight: latest.index,
      chainLength: this.chain.length,
      latestHash: latest.hash,
      latestMiner: latest.miner,
      pendingTransactions: this.mempool.length,
      minedBlocks: this.minedBlocks,
      acceptedBlocks: this.acceptedBlocks,
      rejectedBlocks: this.rejectedBlocks,
      lastBlockAt: this.lastBlockAt,
      lastSeenTxAt: this.lastSeenTxAt,
    };
  }

  startMining() {
    this.miningEnabled = true;
    this.startMiningLoop();
  }

  stopMining() {
    this.miningEnabled = false;
  }

  receiveTransaction(tx, sourceMaintainerId) {
    if (this.seenTxIds.has(tx.id)) {
      return false;
    }

    this.seenTxIds.add(tx.id);
    this.mempool.push(clone(tx));
    this.mempoolVersion += 1;
    this.lastSeenTxAt = new Date().toISOString();
    this.broadcastTransaction(tx, sourceMaintainerId);
    this.startMiningLoop();
    return true;
  }

  broadcastTransaction(tx, sourceMaintainerId) {
    for (const peer of this.peers) {
      if (peer.id === sourceMaintainerId) {
        continue;
      }

      setTimeout(() => {
        peer.receiveTransaction(tx, this.id);
      }, this.options.networkLatencyMs);
    }
  }

  removeMinedTransactions(transactions) {
    const txIds = new Set(transactions.map((tx) => tx.id));
    this.mempool = this.mempool.filter((tx) => !txIds.has(tx.id));
  }

  isValidBlock(block, previousBlock) {
    if (!block || !previousBlock) {
      return false;
    }

    if (block.index !== previousBlock.index + 1) {
      return false;
    }

    if (block.previousHash !== previousBlock.hash) {
      return false;
    }

    if (block.difficulty !== this.options.difficulty) {
      return false;
    }

    if (!block.hash || !block.hash.startsWith("0".repeat(this.options.difficulty))) {
      return false;
    }

    return calculateBlockHash(block) === block.hash;
  }

  isValidChain(candidateChain) {
    if (!Array.isArray(candidateChain) || candidateChain.length === 0) {
      return false;
    }

    if (JSON.stringify(candidateChain[0]) !== JSON.stringify(this.chain[0])) {
      return false;
    }

    for (let index = 1; index < candidateChain.length; index += 1) {
      if (!this.isValidBlock(candidateChain[index], candidateChain[index - 1])) {
        return false;
      }
    }

    return true;
  }

  acceptBlock(block, sourceMaintainerId) {
    const latest = this.latestBlock();

    if (this.isValidBlock(block, latest)) {
      this.chain.push(clone(block));
      this.chainVersion += 1;
      this.acceptedBlocks += 1;
      this.lastBlockAt = new Date().toISOString();
      this.applyBlockToDpkiState(block);
      this.removeMinedTransactions(block.transactions);
      return true;
    }

    const previous = this.chain[this.chain.length - 2];
    if (
      previous &&
      block &&
      block.index === latest.index &&
      block.previousHash === previous.hash &&
      this.isValidBlock(block, previous) &&
      String(block.hash).localeCompare(String(latest.hash)) < 0
    ) {
      const newTxIds = new Set(block.transactions.map((tx) => tx.id));
      for (const tx of latest.transactions) {
        if (!isRewardTx(tx) && !newTxIds.has(tx.id) && !this.mempool.some((item) => item.id === tx.id)) {
          this.mempool.push(clone(tx));
        }
      }
      this.chain[this.chain.length - 1] = clone(block);
      this.rebuildDpkiState();
      this.chainVersion += 1;
      this.acceptedBlocks += 1;
      this.lastBlockAt = new Date().toISOString();
      this.removeMinedTransactions(block.transactions);
      return true;
    }

    if (block && block.index > latest.index + 1) {
      return this.syncFromPeers();
    }

    this.rejectedBlocks += 1;
    return false;
  }

  broadcastBlock(block) {
    for (const peer of this.peers) {
      setTimeout(() => {
        peer.acceptBlock(block, this.id);
      }, this.options.networkLatencyMs);
    }
  }

  syncFromPeers() {
    let bestChain = this.chain;

    for (const peer of this.peers) {
      if (isBetterChain(peer.chain, bestChain) && this.isValidChain(peer.chain)) {
        bestChain = peer.chain;
      }
    }

    if (bestChain !== this.chain) {
      this.chain = clone(bestChain);
      this.rebuildDpkiState();
      this.chainVersion += 1;
      const minedTxIds = new Set(
        this.chain.flatMap((block) => block.transactions.map((tx) => tx.id))
      );
      this.mempool = this.mempool.filter((tx) => !minedTxIds.has(tx.id));
      return true;
    }

    return false;
  }

  applyBlockToDpkiState(block) {
    for (const tx of block.transactions || []) {
      applyDpkiTransaction(this.dpkiState, tx);
    }
  }

  rebuildDpkiState() {
    this.dpkiState = createDpkiState();
    for (const block of this.chain) {
      this.applyBlockToDpkiState(block);
    }
  }

  async startMiningLoop() {
    if (!this.miningEnabled || this.miningLoopRunning) {
      return;
    }

    this.miningLoopRunning = true;

    while (this.miningEnabled) {
      const latest = this.latestBlock();
      const chainVersion = this.chainVersion;
      const mempoolVersion = this.mempoolVersion;
      const timestamp = Date.now();
      const transactions = selectBlockTransactions(this.mempool, this.options.maxTxPerBlock);
      if (!this.options.mineEmpty && transactions.length === 0) {
        break;
      }
      const rewardTx = {
        id: sha256(`${this.id}:${latest.hash}:${timestamp}:reward`),
        from: "system",
        to: this.id,
        amount: this.options.reward,
        data: "mining-reward",
        timestamp,
      };

      const candidate = {
        index: latest.index + 1,
        previousHash: latest.hash,
        timestamp,
        transactions: [...transactions, rewardTx],
        difficulty: this.options.difficulty,
        miner: this.id,
      };

      const minedBlock = await mineBlock(candidate, this.options, () => {
        return !this.miningEnabled ||
          this.chainVersion !== chainVersion ||
          this.mempoolVersion !== mempoolVersion;
      });

      if (!this.miningEnabled) {
        break;
      }

      if (!minedBlock) {
        await wait(this.options.blockDelayMs);
        continue;
      }

      if (this.mempoolVersion !== mempoolVersion) {
        continue;
      }

      if (this.acceptBlock(minedBlock, this.id)) {
        this.minedBlocks += 1;
        this.broadcastBlock(minedBlock);
      }

      await wait(this.options.blockDelayMs);
    }

    this.miningLoopRunning = false;
  }
}

function bestMaintainer(maintainers) {
  return maintainers.reduce((best, maintainer) => {
    if (isBetterChain(maintainer.chain, best.chain)) {
      return maintainer;
    }
    return best;
  }, maintainers[0]);
}

function networkStatus(options, maintainers) {
  const best = bestMaintainer(maintainers);
  const bestHash = best.latestBlock().hash;
  const consistent = maintainers.every((maintainer) => maintainer.latestBlock().hash === bestHash);

  return {
    ok: true,
    consensus: "local-pow",
    chain33TargetConsensus: "ticket",
    configuredMaintainers: options.maintainers,
    activeMaintainers: maintainers.filter((maintainer) => maintainer.miningEnabled).length,
    difficulty: options.difficulty,
    blockDelayMs: options.blockDelayMs,
    networkLatencyMs: options.networkLatencyMs,
    maxTxPerBlock: options.maxTxPerBlock,
    mineEmpty: options.mineEmpty,
    bestHeight: best.latestBlock().index,
    bestHash,
    bestMiner: best.latestBlock().miner,
    chainConsistent: consistent,
    controlPort: options.controlPort,
  };
}

function sendJson(response, statusCode, payload) {
  response.writeHead(statusCode, {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
    "Content-Type": "application/json",
  });
  response.end(JSON.stringify(payload, null, 2));
}

function sendText(response, statusCode, payload) {
  response.writeHead(statusCode, {
    "Access-Control-Allow-Origin": "*",
    "Content-Type": "text/plain; charset=utf-8",
  });
  response.end(payload);
}

function readJson(request) {
  return new Promise((resolve, reject) => {
    const chunks = [];

    request.on("data", (chunk) => chunks.push(chunk));
    request.on("end", () => {
      const raw = Buffer.concat(chunks).toString("utf8").trim();

      if (!raw) {
        resolve({});
        return;
      }

      try {
        resolve(JSON.parse(raw));
      } catch (error) {
        reject(error);
      }
    });
  });
}

function metrics(options, maintainers) {
  const status = networkStatus(options, maintainers);
  const totalMined = maintainers.reduce((sum, maintainer) => sum + maintainer.minedBlocks, 0);
  const totalRejected = maintainers.reduce((sum, maintainer) => sum + maintainer.rejectedBlocks, 0);

  return [
    `pow_maintainers_total ${status.configuredMaintainers}`,
    `pow_maintainers_active ${status.activeMaintainers}`,
    `pow_best_height ${status.bestHeight}`,
    `pow_difficulty ${status.difficulty}`,
    `pow_mined_blocks_total ${totalMined}`,
    `pow_rejected_blocks_total ${totalRejected}`,
    `pow_chain_consistent ${status.chainConsistent ? 1 : 0}`,
    "",
  ].join("\n");
}

function findTransactionStatus(maintainers, txId) {
  const confirmations = [];
  for (const maintainer of maintainers) {
    for (const block of maintainer.chain) {
      const tx = block.transactions.find((item) => item.id === txId);
      if (tx) {
        confirmations.push({
          maintainer: maintainer.id,
          blockNumber: block.index,
          blockHash: block.hash,
          miner: block.miner,
          transaction: tx,
        });
        break;
      }
    }
  }

  confirmations.sort((a, b) => a.blockNumber - b.blockNumber || a.maintainer.localeCompare(b.maintainer));
  return {
    txId,
    confirmedMaintainers: confirmations.length,
    requiredMaintainers: maintainers.length,
    allConfirmed: confirmations.length === maintainers.length,
    firstBlockNumber: confirmations.length ? confirmations[0].blockNumber : null,
    firstBlockHash: confirmations.length ? confirmations[0].blockHash : null,
    confirmations,
  };
}

function startControlServer(options, maintainers) {
  const server = http.createServer(async (request, response) => {
    const requestUrl = new URL(request.url, `http://127.0.0.1:${options.controlPort}`);
    const path = requestUrl.pathname;

    if (request.method === "OPTIONS") {
      sendJson(response, 204, {});
      return;
    }

    try {
      if (request.method === "GET" && (path === "/" || path === "/health")) {
        sendJson(response, 200, networkStatus(options, maintainers));
        return;
      }

      if (request.method === "GET" && path === "/maintainers") {
        sendJson(response, 200, maintainers.map((maintainer) => maintainer.status()));
        return;
      }

      if (request.method === "GET" && path === "/chain") {
        const best = bestMaintainer(maintainers);
        const fromRaw = requestUrl.searchParams.get("from");
        const fromIndex = fromRaw === null ? null : Number(fromRaw);
        const chain = Number.isFinite(fromIndex)
          ? best.chain.filter((block) => block.index >= fromIndex)
          : best.chain;
        sendJson(response, 200, {
          sourceMaintainer: best.id,
          length: best.chain.length,
          bestHeight: best.latestBlock().index,
          bestHash: best.latestBlock().hash,
          from: Number.isFinite(fromIndex) ? fromIndex : null,
          chain,
        });
        return;
      }

      if (request.method === "GET" && path === "/mempool") {
        sendJson(response, 200, maintainers.map((maintainer) => ({
          id: maintainer.id,
          pending: maintainer.mempool.length,
          transactions: maintainer.mempool,
        })));
        return;
      }

      const rootStatus = path.match(/^\/dpki\/domain-roots\/([^/]+)$/);
      if (request.method === "GET" && rootStatus) {
        const best = bestMaintainer(maintainers);
        const domainId = decodeURIComponent(rootStatus[1]);
        sendJson(response, 200, {
          domainId,
          repoRoot:
            best.dpkiState.roots.get(domainId) ||
            "0x0000000000000000000000000000000000000000000000000000000000000000",
          sourceMaintainer: best.id,
          blockNumber: best.latestBlock().index,
          blockHash: best.latestBlock().hash,
        });
        return;
      }

      const certStatus = path.match(/^\/dpki\/certificates\/([^/]+)$/);
      if (request.method === "GET" && certStatus) {
        const best = bestMaintainer(maintainers);
        const certKey = decodeURIComponent(certStatus[1]);
        const certificate = best.dpkiState.certificates.get(certKey) || null;
        sendJson(response, 200, {
          certKey,
          exists: Boolean(certificate),
          certificate,
          sourceMaintainer: best.id,
          blockNumber: best.latestBlock().index,
          blockHash: best.latestBlock().hash,
        });
        return;
      }

      const authRecordStatus = path.match(/^\/dpki\/auth-records\/([^/]+)$/);
      if (request.method === "GET" && authRecordStatus) {
        const best = bestMaintainer(maintainers);
        const requestId = decodeURIComponent(authRecordStatus[1]);
        const stored = best.dpkiState.authRecords.get(requestId) || null;
        const authRecord = stored ? { ...stored, exists: true } : null;
        sendJson(response, 200, {
          requestId,
          exists: Boolean(authRecord),
          authRecord,
          sourceMaintainer: best.id,
          blockNumber: best.latestBlock().index,
          blockHash: best.latestBlock().hash,
        });
        return;
      }

      if (request.method === "GET" && path === "/metrics") {
        sendText(response, 200, metrics(options, maintainers));
        return;
      }

      const txStatus = path.match(/^\/transactions\/([0-9a-fA-F]+)$/);
      if (request.method === "GET" && txStatus) {
        sendJson(response, 200, findTransactionStatus(maintainers, txStatus[1]));
        return;
      }

      if (request.method === "POST" && (path === "/transactions" || path === "/network/transactions")) {
        const body = await readJson(request);
        const tx = createTransaction(body);
        maintainers[0].receiveTransaction(tx, null);
        sendJson(response, 201, {
          message: "transaction accepted",
          transaction: tx,
        });
        return;
      }

      if (request.method === "POST" && path === "/sync") {
        const results = maintainers.map((maintainer) => ({
          id: maintainer.id,
          synced: maintainer.syncFromPeers(),
          height: maintainer.latestBlock().index,
        }));
        sendJson(response, 200, results);
        return;
      }

      const maintainerAction = path.match(/^\/maintainers\/([^/]+)\/(start|stop)$/);
      if (request.method === "POST" && maintainerAction) {
        const [, maintainerId, action] = maintainerAction;
        const maintainer = maintainers.find((item) => item.id === maintainerId);

        if (!maintainer) {
          sendJson(response, 404, { error: `unknown maintainer ${maintainerId}` });
          return;
        }

        if (action === "start") {
          maintainer.startMining();
        } else {
          maintainer.stopMining();
        }

        sendJson(response, 200, maintainer.status());
        return;
      }

      sendJson(response, 404, { error: "route not found" });
    } catch (error) {
      sendJson(response, 500, { error: error.message });
    }
  });

  server.listen(options.controlPort, "127.0.0.1", () => {
    console.log(`PoW maintainer control API ready at http://127.0.0.1:${options.controlPort}`);
    console.log(`Maintainers: ${maintainers.map((maintainer) => maintainer.id).join(", ")}`);
  });

  return server;
}

async function main() {
  const options = parseArgs(process.argv);
  const genesisBlock = createGenesisBlock(options);
  const maintainers = Array.from({ length: options.maintainers }, (_, index) => {
    return new Maintainer(`maintainer${index + 1}`, options, genesisBlock);
  });

  for (const maintainer of maintainers) {
    maintainer.setPeers(maintainers);
  }

  startControlServer(options, maintainers);

  for (const maintainer of maintainers) {
    maintainer.startMining();
  }

  setInterval(() => {
    const status = networkStatus(options, maintainers);
    console.log(
      `[monitor] height=${status.bestHeight} active=${status.activeMaintainers}/${status.configuredMaintainers} ` +
        `consistent=${status.chainConsistent} miner=${status.bestMiner}`
    );
  }, options.monitorIntervalMs);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
