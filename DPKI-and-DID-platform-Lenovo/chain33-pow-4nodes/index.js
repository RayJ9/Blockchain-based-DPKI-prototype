const crypto = require("crypto");
const express = require("express");

const NODE_PORTS = [9701, 9702, 9703, 9704];
const CONTROL_PORT = 9799;
const DIFFICULTY = 4;
const HASH_PREFIX = "0".repeat(DIFFICULTY);
const BLOCK_REWARD = 50;
const MAX_TX_PER_BLOCK = 6;
const MINER_RESTART_DELAY_MS = 50;
const NETWORK_LATENCY_MS = 30;
const GENESIS_TIMESTAMP = 1710000000000;

function wait(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function setImmediateAsync() {
  return new Promise((resolve) => setImmediate(resolve));
}

function clone(data) {
  return JSON.parse(JSON.stringify(data));
}

function sha256(input) {
  return crypto.createHash("sha256").update(input).digest("hex");
}

function calculateBlockHash(block) {
  return sha256(
    JSON.stringify({
      index: block.index,
      previousHash: block.previousHash,
      timestamp: block.timestamp,
      transactions: block.transactions,
      nonce: block.nonce,
      difficulty: block.difficulty,
      miner: block.miner,
    })
  );
}

function createGenesisBlock() {
  const block = {
    index: 0,
    previousHash: "0".repeat(64),
    timestamp: GENESIS_TIMESTAMP,
    transactions: [
      {
        id: "genesis-tx",
        from: "system",
        to: "network",
        amount: 0,
        data: "genesis",
        timestamp: GENESIS_TIMESTAMP,
      },
    ],
    nonce: 0,
    difficulty: DIFFICULTY,
    miner: "genesis",
  };

  block.hash = calculateBlockHash(block);
  return block;
}

function createTransaction({ from, to, amount, data }) {
  const timestamp = Date.now();
  const normalized = {
    from: from || "anonymous",
    to: to || "anonymous",
    amount: Number(amount || 0),
    data: data || "",
    timestamp,
  };

  return {
    id: sha256(JSON.stringify(normalized)),
    ...normalized,
  };
}

async function mineBlock(candidate, shouldAbort) {
  let nonce = 0;
  let hash = "";
  const base = { ...candidate };

  while (true) {
    if (shouldAbort()) {
      return null;
    }

    for (let i = 0; i < 5000; i += 1) {
      const block = { ...base, nonce };
      hash = calculateBlockHash(block);

      if (hash.startsWith(HASH_PREFIX)) {
        return { ...block, hash };
      }

      nonce += 1;
    }

    await setImmediateAsync();
  }
}

class VirtualNode {
  constructor(nodeId, port, genesisBlock) {
    this.nodeId = nodeId;
    this.port = port;
    this.peers = [];
    this.chain = [clone(genesisBlock)];
    this.mempool = [];
    this.minedBlocks = 0;
    this.acceptedBlocks = 0;
    this.seenTxIds = new Set(["genesis-tx"]);
    this.miningEnabled = true;
    this.miningTaskRunning = false;
    this.chainVersion = 0;

    this.app = express();
    this.app.use(express.json());
    this.registerRoutes();
  }

  registerRoutes() {
    this.app.get("/status", (_req, res) => {
      res.json(this.getStatus());
    });

    this.app.get("/chain", (_req, res) => {
      res.json({
        nodeId: this.nodeId,
        length: this.chain.length,
        chain: this.chain,
      });
    });

    this.app.get("/mempool", (_req, res) => {
      res.json({
        nodeId: this.nodeId,
        pending: this.mempool.length,
        transactions: this.mempool,
      });
    });

    this.app.post("/transactions", async (req, res) => {
      const tx = createTransaction(req.body || {});
      this.receiveTransaction(tx, null);
      res.status(201).json({
        message: "transaction accepted",
        nodeId: this.nodeId,
        transaction: tx,
      });
    });

    this.app.post("/mine/start", (_req, res) => {
      this.miningEnabled = true;
      this.startMiningLoop();
      res.json({ message: "mining started", nodeId: this.nodeId });
    });

    this.app.post("/mine/stop", (_req, res) => {
      this.miningEnabled = false;
      res.json({ message: "mining stopped", nodeId: this.nodeId });
    });

    this.app.post("/sync", (_req, res) => {
      const replaced = this.syncFromPeers();
      res.json({
        nodeId: this.nodeId,
        replaced,
        length: this.chain.length,
      });
    });
  }

  listen() {
    return new Promise((resolve) => {
      this.server = this.app.listen(this.port, () => {
        console.log(`[${this.nodeId}] listening on http://127.0.0.1:${this.port}`);
        resolve();
      });
    });
  }

  setPeers(peers) {
    this.peers = peers.filter((peer) => peer.nodeId !== this.nodeId);
  }

  getLatestBlock() {
    return this.chain[this.chain.length - 1];
  }

  getStatus() {
    const latest = this.getLatestBlock();
    return {
      nodeId: this.nodeId,
      port: this.port,
      peers: this.peers.map((peer) => peer.nodeId),
      chainHeight: latest.index,
      chainLength: this.chain.length,
      latestHash: latest.hash,
      latestMiner: latest.miner,
      pendingTransactions: this.mempool.length,
      minedBlocks: this.minedBlocks,
      acceptedBlocks: this.acceptedBlocks,
      miningEnabled: this.miningEnabled,
      difficulty: DIFFICULTY,
    };
  }

  receiveTransaction(tx, sourceNodeId) {
    if (this.seenTxIds.has(tx.id)) {
      return false;
    }

    this.seenTxIds.add(tx.id);
    this.mempool.push(tx);
    console.log(`[${this.nodeId}] accepted tx ${tx.id.slice(0, 12)} from ${sourceNodeId || "api"}`);
    this.broadcastTransaction(tx, sourceNodeId);
    this.startMiningLoop();
    return true;
  }

  broadcastTransaction(tx, sourceNodeId) {
    for (const peer of this.peers) {
      if (peer.nodeId === sourceNodeId) {
        continue;
      }

      setTimeout(() => {
        peer.receiveTransaction(clone(tx), this.nodeId);
      }, NETWORK_LATENCY_MS);
    }
  }

  removeTransactionsFromMempool(transactions) {
    const txIds = new Set(transactions.map((tx) => tx.id));
    this.mempool = this.mempool.filter((tx) => !txIds.has(tx.id));
  }

  isValidBlock(block, previousBlock) {
    if (block.index !== previousBlock.index + 1) {
      return false;
    }

    if (block.previousHash !== previousBlock.hash) {
      return false;
    }

    if (block.difficulty !== DIFFICULTY) {
      return false;
    }

    if (!block.hash || !block.hash.startsWith(HASH_PREFIX)) {
      return false;
    }

    if (calculateBlockHash(block) !== block.hash) {
      return false;
    }

    return true;
  }

  isValidChain(candidateChain) {
    if (!Array.isArray(candidateChain) || candidateChain.length === 0) {
      return false;
    }

    const localGenesis = this.chain[0];
    const candidateGenesis = candidateChain[0];

    if (JSON.stringify(localGenesis) !== JSON.stringify(candidateGenesis)) {
      return false;
    }

    for (let i = 1; i < candidateChain.length; i += 1) {
      if (!this.isValidBlock(candidateChain[i], candidateChain[i - 1])) {
        return false;
      }
    }

    return true;
  }

  acceptBlock(block, sourceNodeId) {
    const latest = this.getLatestBlock();

    if (this.isValidBlock(block, latest)) {
      this.chain.push(clone(block));
      this.acceptedBlocks += 1;
      this.chainVersion += 1;
      this.removeTransactionsFromMempool(block.transactions);
      console.log(
        `[${this.nodeId}] accepted block #${block.index} mined by ${block.miner} from ${sourceNodeId || "self"}`
      );
      return true;
    }

    if (block.index > latest.index + 1) {
      return this.syncFromPeers();
    }

    return false;
  }

  broadcastBlock(block) {
    for (const peer of this.peers) {
      setTimeout(() => {
        peer.acceptBlock(clone(block), this.nodeId);
      }, NETWORK_LATENCY_MS);
    }
  }

  syncFromPeers() {
    let bestChain = this.chain;

    for (const peer of this.peers) {
      if (peer.chain.length > bestChain.length && this.isValidChain(peer.chain)) {
        bestChain = peer.chain;
      }
    }

    if (bestChain !== this.chain) {
      this.chain = clone(bestChain);
      this.chainVersion += 1;
      const chainTxIds = new Set(
        this.chain.flatMap((block) => block.transactions.map((tx) => tx.id))
      );
      this.mempool = this.mempool.filter((tx) => !chainTxIds.has(tx.id));
      console.log(`[${this.nodeId}] synced to chain height ${this.getLatestBlock().index}`);
      return true;
    }

    return false;
  }

  async startMiningLoop() {
    if (!this.miningEnabled || this.miningTaskRunning) {
      return;
    }

    this.miningTaskRunning = true;

    while (this.miningEnabled) {
      const latest = this.getLatestBlock();
      const chainVersion = this.chainVersion;
      const transactions = this.mempool.slice(0, MAX_TX_PER_BLOCK);

      const rewardTx = {
        id: sha256(`${this.nodeId}-${Date.now()}-${latest.index}`),
        from: "system",
        to: this.nodeId,
        amount: BLOCK_REWARD,
        data: "mining-reward",
        timestamp: Date.now(),
      };

      const candidate = {
        index: latest.index + 1,
        previousHash: latest.hash,
        timestamp: Date.now(),
        transactions: [...transactions, rewardTx],
        difficulty: DIFFICULTY,
        miner: this.nodeId,
      };

      const minedBlock = await mineBlock(candidate, () => {
        return !this.miningEnabled || this.chainVersion !== chainVersion;
      });

      if (!this.miningEnabled) {
        break;
      }

      if (!minedBlock) {
        await wait(MINER_RESTART_DELAY_MS);
        continue;
      }

      const accepted = this.acceptBlock(minedBlock, null);

      if (accepted) {
        this.minedBlocks += 1;
        this.broadcastBlock(minedBlock);
      } else {
        await wait(MINER_RESTART_DELAY_MS);
      }
    }

    this.miningTaskRunning = false;
  }
}

async function startNetwork() {
  const genesisBlock = createGenesisBlock();
  const nodes = NODE_PORTS.map((port, index) => new VirtualNode(`node${index + 1}`, port, genesisBlock));

  for (const node of nodes) {
    node.setPeers(nodes);
    await node.listen();
  }

  for (const node of nodes) {
    node.startMiningLoop();
  }

  const controlApp = express();
  controlApp.use(express.json());

  controlApp.get("/nodes", (_req, res) => {
    res.json(nodes.map((node) => node.getStatus()));
  });

  controlApp.get("/network/chain", (_req, res) => {
    const bestNode = nodes.reduce((currentBest, node) => {
      return node.chain.length > currentBest.chain.length ? node : currentBest;
    }, nodes[0]);

    res.json({
      sourceNode: bestNode.nodeId,
      length: bestNode.chain.length,
      chain: bestNode.chain,
    });
  });

  controlApp.post("/network/transactions", (req, res) => {
    const seedNode = nodes[0];
    const tx = createTransaction(req.body || {});
    seedNode.receiveTransaction(tx, null);
    res.status(201).json({
      message: "transaction injected to network",
      via: seedNode.nodeId,
      transaction: tx,
    });
  });

  controlApp.post("/network/sync", (_req, res) => {
    const results = nodes.map((node) => ({
      nodeId: node.nodeId,
      replaced: node.syncFromPeers(),
      chainLength: node.chain.length,
    }));

    res.json(results);
  });

  controlApp.listen(CONTROL_PORT, () => {
    console.log("");
    console.log(`PoW control API ready at http://127.0.0.1:${CONTROL_PORT}`);
    console.log(`Node APIs: ${NODE_PORTS.map((port) => `http://127.0.0.1:${port}/status`).join(" | ")}`);
    console.log("Try POST /network/transactions with JSON body: {\"from\":\"alice\",\"to\":\"bob\",\"amount\":10}");
  });
}

startNetwork().catch((error) => {
  console.error("Failed to start PoW network:", error);
  process.exit(1);
});
