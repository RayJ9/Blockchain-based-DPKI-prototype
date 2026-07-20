const fs = require("fs");
const path = require("path");
const http = require("http");
const crypto = require("crypto");
const childProcess = require("child_process");
const { performance } = require("perf_hooks");

const ROOT = path.resolve(__dirname, "..", "..", "..");
const EXPERIMENT_NODE_MODULES = path.join(ROOT, "blockchain", "dpki-experiment", "node_modules");
const CONTRACT_PATH = path.join(__dirname, "contracts", "Fig4BaselineBenchmark.sol");
const CONTRACT_NAME = "Fig4BaselineBenchmark";
const PLATFORM_REGISTRY = require(path.join(ROOT, "blockchain", "platform_registry"));
const VERBOSE_TRACE = /^(1|true|yes|on)$/i.test(process.env.DPKI_VERBOSE_TRACE || "");

function traceEvent(kind, payload) {
  if (!VERBOSE_TRACE) return;
  console.log(`[TRACE][${kind}] ${JSON.stringify(payload)}`);
}

const solc = require(path.join(EXPERIMENT_NODE_MODULES, "solc"));
const Web3 = require(path.join(EXPERIMENT_NODE_MODULES, "web3"));

const NOOP_CONTRACT_SOURCE = `
pragma solidity ^0.5.17;

contract Fig4NoopProbe {
    uint256 public counter;
    event Ping(bytes32 indexed tag, uint256 counter);

    function ping(bytes32 tag) public {
        counter += 1;
        emit Ping(tag, counter);
    }
}
`;

const DEFAULTS = {
  requests: 2000,
  rpc: "http://127.0.0.1:8545",
  account: "0xab7F5238cbEfB02062241cf979e4994b656FB944",
  privateKey: "0x73e66f099144f820753aa3a5e131785b528081da572e16339fcd02de05de719e",
  gas: 8000000,
  gasPrice: "1",
  out: path.join(__dirname, "outputs", `run_${timestampForPath(new Date())}`),
  noChain: false,
  thresholdK: 4,
  thresholdN: 6,
  noopProbes: null,
  seed: 20260706,
};

const REQUEST_CLASSES = [
  ["traditional-pki", "management"],
  ["traditional-pki", "intra-auth"],
  ["traditional-pki", "cross-auth"],
  ["threshold-validation-dpki", "management"],
  ["threshold-validation-dpki", "intra-auth"],
  ["threshold-validation-dpki", "cross-auth"],
  ["full-contract-onchain", "management"],
  ["full-contract-onchain", "intra-on-chain"],
  ["full-contract-onchain", "cross-on-chain"],
  ["proposed-dpki", "management"],
  ["proposed-dpki", "intra-off-chain"],
  ["proposed-dpki", "intra-on-chain"],
  ["proposed-dpki", "cross-on-chain"],
];

function timestampForPath(date) {
  const pad = (value) => String(value).padStart(2, "0");
  return [
    date.getFullYear(),
    pad(date.getMonth() + 1),
    pad(date.getDate()),
    "_",
    pad(date.getHours()),
    pad(date.getMinutes()),
    pad(date.getSeconds()),
  ].join("");
}

function parseArgs() {
  const args = { ...DEFAULTS };
  for (let i = 2; i < process.argv.length; i += 1) {
    const key = process.argv[i];
    const next = process.argv[i + 1];
    if (key === "--requests" && next) args.requests = Number(next), i += 1;
    else if (key === "--rpc" && next) args.rpc = next, i += 1;
    else if (key === "--account" && next) args.account = next, i += 1;
    else if (key === "--private-key" && next) args.privateKey = next, i += 1;
    else if (key === "--gas" && next) args.gas = Number(next), i += 1;
    else if (key === "--gas-price" && next) args.gasPrice = String(next), i += 1;
    else if (key === "--out" && next) args.out = path.resolve(next), i += 1;
    else if (key === "--seed" && next) args.seed = Number(next), i += 1;
    else if (key === "--threshold-k" && next) args.thresholdK = Number(next), i += 1;
    else if (key === "--threshold-n" && next) args.thresholdN = Number(next), i += 1;
    else if (key === "--noop-probes" && next) args.noopProbes = Number(next), i += 1;
    else if (key === "--no-chain") args.noChain = true;
    else if (key === "--help") {
      console.log([
        "Usage:",
        "  node run_prototype_baseline_benchmark.js --requests 2000",
        "",
        "Notes:",
        "  - On-chain transactions are executed and receipts are saved.",
        "  - Request classes are mixed by seeded shuffle for each index.",
        "  - On-chain stage latency subtracts a no-op PoW confirmation probe from receipt waiting.",
        "  - receiptWaitMs is written separately for audit.",
      ].join("\n"));
      process.exit(0);
    }
  }
  if (!args.privateKey.startsWith("0x")) args.privateKey = `0x${args.privateKey}`;
  args.requests = Math.max(1, Math.floor(args.requests));
  args.thresholdK = Math.max(1, Math.floor(args.thresholdK));
  args.thresholdN = Math.max(args.thresholdK, Math.floor(args.thresholdN));
  args.noopProbes = args.noopProbes === null
    ? args.requests
    : Math.max(1, Math.floor(args.noopProbes));
  return args;
}

function makeRng(seed) {
  let state = (seed >>> 0) || 1;
  return () => {
    state = (1664525 * state + 1013904223) >>> 0;
    return state / 0x100000000;
  };
}

function shuffledRequestClasses(rng) {
  const order = REQUEST_CLASSES.slice();
  for (let i = order.length - 1; i > 0; i -= 1) {
    const j = Math.floor(rng() * (i + 1));
    [order[i], order[j]] = [order[j], order[i]];
  }
  return order;
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function sha256(data) {
  return crypto.createHash("sha256").update(data).digest();
}

function sha256Hex(data) {
  return crypto.createHash("sha256").update(data).digest("hex");
}

function safeLabel(label) {
  return String(label).replace(/[^a-zA-Z0-9_.-]/g, "_");
}

function keccakBytes32(web3, label) {
  return web3.utils.keccak256(`0x${sha256Hex(label)}`);
}

function signBuffer(privateKey, data) {
  return crypto.sign("sha256", Buffer.isBuffer(data) ? data : Buffer.from(String(data)), privateKey);
}

function verifyBuffer(publicKey, data, signature) {
  return crypto.verify("sha256", Buffer.isBuffer(data) ? data : Buffer.from(String(data)), publicKey, signature);
}

function generateKeyPair() {
  return crypto.generateKeyPairSync("ec", { namedCurve: "prime256v1" });
}

function csvEscape(value) {
  if (value === null || value === undefined) return "";
  const text = String(value);
  return /[",\n\r]/.test(text) ? `"${text.replace(/"/g, '""')}"` : text;
}

function bytesOfUtf8(value) {
  return Buffer.byteLength(String(value || ""), "utf8");
}

function bytesStorageFootprint(byteLength) {
  const length = Math.max(0, Number(byteLength || 0));
  if (length <= 31) return 32;
  return 32 + (Math.ceil(length / 32) * 32);
}

function proposedCertificateStorageBytes(certBytes) {
  return Math.max(0, Number(certBytes || 0)) + 32;
}

function authRecordStorageBytes() {
  return 9 * 32;
}

function signedAuthRecordStorageBytes() {
  return authRecordStorageBytes() + (2 * 32);
}

function thresholdCertificateStorageBytes(certBytes, signatureBlobBytes) {
  return proposedCertificateStorageBytes(certBytes) + Math.max(0, Number(signatureBlobBytes || 0));
}

function fullCertificateStorageBytes(csrBytes, certBytes, statusBytes) {
  return Math.max(0, Number(csrBytes || 0))
    + Math.max(0, Number(certBytes || 0))
    + Math.max(0, Number(statusBytes || 0))
    + 32;
}

function addMetric(row, key, delta) {
  row[key] = Number(row[key] || 0) + Number(delta || 0);
}

function metricValue(row, key) {
  return Number(row[key] || 0);
}

function addPayloadBytes(row, bytes) {
  addMetric(row, "payloadBytes", bytes);
}

function addExternalPayloadBytes(row, bytes) {
  addMetric(row, "externalPayloadBytes", bytes);
}

function addInternalPayloadBytes(row, bytes) {
  addMetric(row, "internalPayloadBytes", bytes);
}

function addMsgCount(row, count = 1) {
  addMetric(row, "msgCount", count);
}

function addSigOps(row, count = 1) {
  addMetric(row, "sigOps", count);
}

function addIssueKeyOps(row, count = 1) {
  addMetric(row, "issueKeyOps", count);
}

function addCertStatusChecks(row, count = 1) {
  addMetric(row, "certStatusChecks", count);
}

function addMptProofCount(row, count = 1) {
  addMetric(row, "mptProofCount", count);
}

function addCaNodeExec(row, count = 1) {
  addMetric(row, "caNodeExec", count);
}

function writeCsv(filePath, rows, columns) {
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
  const lines = [columns.join(",")];
  for (const row of rows) {
    lines.push(columns.map((column) => csvEscape(row[column])).join(","));
  }
  fs.writeFileSync(filePath, `${lines.join("\n")}\n`);
}

function stats(values) {
  const clean = values.filter((value) => Number.isFinite(value));
  if (!clean.length) {
    return {
      count: 0,
      mean: 0,
      variance: 0,
      std: 0,
      mad: 0,
      min: 0,
      p50: 0,
      p90: 0,
      p95: 0,
      p99: 0,
      max: 0,
    };
  }
  const sorted = [...clean].sort((a, b) => a - b);
  const mean = clean.reduce((sum, value) => sum + value, 0) / clean.length;
  const variance = clean.reduce((sum, value) => sum + (value - mean) ** 2, 0) / clean.length;
  const pick = (p) => {
    const pos = (sorted.length - 1) * p;
    const lo = Math.floor(pos);
    const hi = Math.ceil(pos);
    if (lo === hi) return sorted[lo];
    return sorted[lo] * (hi - pos) + sorted[hi] * (pos - lo);
  };
  return {
    count: clean.length,
    mean,
    variance,
    std: Math.sqrt(variance),
    mad: clean.reduce((sum, value) => sum + Math.abs(value - mean), 0) / clean.length,
    min: sorted[0],
    p50: pick(0.5),
    p90: pick(0.9),
    p95: pick(0.95),
    p99: pick(0.99),
    max: sorted[sorted.length - 1],
  };
}

async function measure(row, stageName, fn) {
  const t0 = performance.now();
  const result = await fn();
  const dt = performance.now() - t0;
  row.stages[stageName] = (row.stages[stageName] || 0) + dt;
  return result;
}

function runOpenSsl(args, cwd) {
  childProcess.execFileSync("openssl", args, {
    cwd,
    stdio: "ignore",
    windowsHide: true,
  });
}

function prepareOpenSslWorkspace(workDir) {
  fs.mkdirSync(workDir, { recursive: true });
  const issuedDir = path.join(workDir, "issued");
  const evidenceDir = path.join(workDir, "threshold_evidence");
  fs.mkdirSync(issuedDir, { recursive: true });
  fs.mkdirSync(evidenceDir, { recursive: true });
  const caKey = path.join(workDir, "ca.key");
  const caCert = path.join(workDir, "ca.crt");
  const leafKey = path.join(workDir, "leaf.key");
  const leafCsr = path.join(workDir, "leaf.csr");
  const leafCert = path.join(workDir, "leaf.crt");
  const leafPub = path.join(workDir, "leaf.pub");
  const payload = path.join(workDir, "payload.txt");
  fs.writeFileSync(payload, "fig4-prototype-baseline-payload\n");
  if (!fs.existsSync(caKey)) {
    runOpenSsl(["ecparam", "-name", "prime256v1", "-genkey", "-noout", "-out", caKey], workDir);
    runOpenSsl(["req", "-x509", "-new", "-key", caKey, "-sha256", "-days", "3650", "-subj", "/CN=Fig4-CA", "-out", caCert], workDir);
    runOpenSsl(["ecparam", "-name", "prime256v1", "-genkey", "-noout", "-out", leafKey], workDir);
    runOpenSsl(["req", "-new", "-key", leafKey, "-subj", "/CN=Fig4-Leaf", "-out", leafCsr], workDir);
    runOpenSsl(["x509", "-req", "-in", leafCsr, "-CA", caCert, "-CAkey", caKey, "-CAcreateserial", "-out", leafCert, "-days", "3650", "-sha256"], workDir);
    runOpenSsl(["pkey", "-in", leafKey, "-pubout", "-out", leafPub], workDir);
  }
  return {
    workDir,
    issuedDir,
    evidenceDir,
    caKey,
    caCert,
    leafKey,
    leafCsr,
    leafCert,
    leafPub,
    payload,
    signature: path.join(workDir, "payload.sig"),
    issueSignature: path.join(workDir, "issue.sig"),
    statusDb: path.join(workDir, "ocsp_status.csv"),
    mptRepoDb: path.join(workDir, "mpt_repo.csv"),
  };
}

function opensslVerifyCert(ctx) {
  runOpenSsl(["verify", "-CAfile", ctx.caCert, ctx.leafCert], ctx.workDir);
}

function opensslAssertion(ctx, label) {
  fs.writeFileSync(ctx.payload, `${label}:${Date.now()}:${crypto.randomBytes(8).toString("hex")}\n`);
  runOpenSsl(["dgst", "-sha256", "-sign", ctx.leafKey, "-out", ctx.signature, ctx.payload], ctx.workDir);
  runOpenSsl(["dgst", "-sha256", "-verify", ctx.leafPub, "-signature", ctx.signature, ctx.payload], ctx.workDir);
  return {
    payloadBytes: fs.statSync(ctx.payload).size,
    signatureBytes: fs.statSync(ctx.signature).size,
  };
}

function opensslIssue(ctx, label, options = {}) {
  const id = safeLabel(label);
  const leafKey = path.join(ctx.issuedDir, `issued_${id}.key`);
  const leafCsr = path.join(ctx.issuedDir, `issued_${id}.csr`);
  const leafCert = path.join(ctx.issuedDir, `issued_${id}.crt`);
  const keyOnly = options.persistMode === "key-only";
  const persistNone = options.persistMode === "none";
  const persistAll = !options.persistMode || options.persistMode === "all";
  const persistStatus = options.persistStatus !== false;
  runOpenSsl(["ecparam", "-name", "prime256v1", "-genkey", "-noout", "-out", leafKey], ctx.workDir);
  runOpenSsl(["req", "-new", "-key", leafKey, "-subj", `/CN=Fig4-Issued-${id}`, "-out", leafCsr], ctx.workDir);
  runOpenSsl([
    "x509",
    "-req",
    "-in",
    leafCsr,
    "-CA",
    ctx.caCert,
    "-CAkey",
    ctx.caKey,
    "-set_serial",
    String(100000 + Math.abs(parseInt(sha256Hex(label).slice(0, 8), 16))),
    "-out",
    leafCert,
    "-days",
    "3650",
    "-sha256",
  ], ctx.workDir);
  const keyBuffer = fs.readFileSync(leafKey);
  const csrBuffer = fs.readFileSync(leafCsr);
  const certBuffer = fs.readFileSync(leafCert);
  const statusLine = `${id},valid,${Math.floor(Date.now() / 1000)}\n`;
  const statusBuffer = Buffer.from(statusLine, "utf8");
  traceEvent("CERTIFICATE", {
    label,
    subject: `Fig4-Issued-${id}`,
    issuer: "Fig4-CA",
    keyBytes: keyBuffer.length,
    csrBytes: csrBuffer.length,
    certificateBytes: certBuffer.length,
    statusBytes: statusBuffer.length,
    certificateSha256: sha256Hex(certBuffer),
  });
  if (persistStatus) {
    fs.appendFileSync(ctx.statusDb, statusLine);
  }

  const offchainStorageBytes = persistAll
    ? keyBuffer.length + csrBuffer.length + certBuffer.length + (persistStatus ? statusBuffer.length : 0)
    : keyOnly
      ? keyBuffer.length
      : 0;

  if (!persistAll) {
    if (fs.existsSync(leafCsr)) fs.unlinkSync(leafCsr);
    if (fs.existsSync(leafCert)) fs.unlinkSync(leafCert);
    if ((persistNone || !keyOnly) && fs.existsSync(leafKey)) fs.unlinkSync(leafKey);
  }

  return {
    keyBytes: keyBuffer.length,
    csrBytes: csrBuffer.length,
    certBytes: certBuffer.length,
    statusBytes: persistStatus ? statusBuffer.length : 0,
    keyBuffer,
    csrBuffer,
    certBuffer,
    statusBuffer,
    offchainStorageBytes,
  };
}

function merkleTree(leaves) {
  let level = leaves.map((leaf) => sha256(Buffer.from(leaf)));
  const levels = [level];
  while (level.length > 1) {
    const next = [];
    for (let i = 0; i < level.length; i += 2) {
      const left = level[i];
      const right = level[i + 1] || left;
      next.push(sha256(Buffer.concat([left, right])));
    }
    level = next;
    levels.push(level);
  }
  return levels;
}

function merkleProof(levels, index) {
  const proof = [];
  let idx = index;
  for (let level = 0; level < levels.length - 1; level += 1) {
    const layer = levels[level];
    const pairIndex = idx ^ 1;
    proof.push({
      side: idx % 2 === 0 ? "right" : "left",
      hash: (layer[pairIndex] || layer[idx]).toString("hex"),
    });
    idx = Math.floor(idx / 2);
  }
  return proof;
}

function verifyMerkleProof(leaf, proof, rootHex) {
  let digest = sha256(Buffer.from(leaf));
  for (const item of proof) {
    const other = Buffer.from(item.hash, "hex");
    digest = item.side === "right"
      ? sha256(Buffer.concat([digest, other]))
      : sha256(Buffer.concat([other, digest]));
  }
  return digest.toString("hex") === rootHex;
}

function makeJsonServer(port, handler) {
  const server = http.createServer(async (req, res) => {
    try {
      const chunks = [];
      req.on("data", (chunk) => chunks.push(chunk));
      req.on("end", async () => {
        try {
          const body = chunks.length ? JSON.parse(Buffer.concat(chunks).toString("utf8")) : {};
          const payload = await handler(req.url, body);
          res.writeHead(200, { "content-type": "application/json" });
          res.end(JSON.stringify(payload));
        } catch (error) {
          res.writeHead(500, { "content-type": "application/json" });
          res.end(JSON.stringify({ error: error.message }));
        }
      });
    } catch (error) {
      res.writeHead(500, { "content-type": "application/json" });
      res.end(JSON.stringify({ error: error.message }));
    }
  });
  return new Promise((resolve) => {
    server.listen(port, "127.0.0.1", () => resolve(server));
  });
}

async function postJson(port, url, body) {
  const response = await fetch(`http://127.0.0.1:${port}${url}`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(body || {}),
  });
  if (!response.ok) throw new Error(`HTTP ${response.status} from ${url}`);
  return response.json();
}

async function postJsonTracked(row, port, url, body, messageCount = 2, scope = "external") {
  const requestText = JSON.stringify(body || {});
  const requestBytes = bytesOfUtf8(requestText);
  addPayloadBytes(row, requestBytes);
  if (scope === "internal") addInternalPayloadBytes(row, requestBytes);
  else addExternalPayloadBytes(row, requestBytes);
  addMsgCount(row, messageCount);
  const response = await fetch(`http://127.0.0.1:${port}${url}`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: requestText,
  });
  const responseText = await response.text();
  const responseBytes = bytesOfUtf8(responseText);
  addPayloadBytes(row, responseBytes);
  if (scope === "internal") addInternalPayloadBytes(row, responseBytes);
  else addExternalPayloadBytes(row, responseBytes);
  if (!response.ok) throw new Error(`HTTP ${response.status} from ${url}`);
  return JSON.parse(responseText);
}

async function prepareNetworkServices(args, rng) {
  const serviceKey = generateKeyPair();
  const ocspKey = generateKeyPair();
  const thresholdKeys = Array.from({ length: args.thresholdN }, () => generateKeyPair());
  const leaves = Array.from({ length: 2048 }, (_, i) => `cert:${i}:valid`);
  const levels = merkleTree(leaves);
  const rootHex = levels[levels.length - 1][0].toString("hex");
  const servers = [];

  servers.push(await makeJsonServer(18341, async (_url, body) => {
    await sleep(0.8 + rng() * 1.8);
    const msg = Buffer.from(`ocsp:${body.cert || "leaf"}:valid:${body.nonce || ""}`);
    const signature = signBuffer(ocspKey.privateKey, msg).toString("base64");
    return { status: "valid", msg: msg.toString("base64"), signature };
  }));

  servers.push(await makeJsonServer(18342, async (_url, body) => {
    await sleep(0.8 + rng() * 1.8);
    const index = Math.abs(Number(body.index || 0)) % leaves.length;
    const leaf = leaves[index];
    const proofStart = performance.now();
    const proof = merkleProof(levels, index);
    const proofGenerationMs = performance.now() - proofStart;
    const msg = Buffer.from(`${leaf}:${rootHex}:${body.nonce || ""}`);
    const signature = signBuffer(serviceKey.privateKey, msg).toString("base64");
    return {
      leaf,
      index,
      rootHex,
      proof,
      msg: msg.toString("base64"),
      signature,
      proofGenerationMs,
    };
  }));

  servers.push(await makeJsonServer(18343, async (url, body) => {
    if (url === "/threshold-dkg") {
      const fromNodeId = Math.abs(Number(body.fromNodeId || 0)) % args.thresholdN;
      const toNodeId = Math.abs(Number(body.toNodeId || 0)) % args.thresholdN;
      await sleep(0.5 + rng() * 1.5 + toNodeId * 0.05);
      const msg = Buffer.from(`${body.phase || "phase"}:${fromNodeId}:${toNodeId}:${body.payloadB64 || ""}`);
      const signature = Buffer.from(body.signature || "", "base64");
      if (!verifyBuffer(thresholdKeys[fromNodeId].publicKey, msg, signature)) {
        throw new Error(`bad dkg signature ${fromNodeId}->${toNodeId}`);
      }
      const ackMsg = Buffer.from(`ack:${body.phase || "phase"}:${fromNodeId}:${toNodeId}:${sha256Hex(body.payloadB64 || "")}`);
      const ackSignature = signBuffer(thresholdKeys[toNodeId].privateKey, ackMsg).toString("base64");
      return {
        ok: true,
        toNodeId,
        ackMsg: ackMsg.toString("base64"),
        ackSignature,
      };
    }
    const id = Math.abs(Number(body.nodeId || 0)) % args.thresholdN;
    await sleep(1.2 + rng() * 4.5 + id * 0.12);
    const msg = Buffer.from(`threshold:${id}:${body.cert || "leaf"}:valid:${body.nonce || ""}`);
    const signature = signBuffer(thresholdKeys[id].privateKey, msg).toString("base64");
    return {
      nodeId: id,
      state: "valid",
      msg: msg.toString("base64"),
      signature,
    };
  }));

  return {
    ocspPublicKey: ocspKey.publicKey,
    servicePublicKey: serviceKey.publicKey,
    thresholdPublicKeys: thresholdKeys.map((item) => item.publicKey),
    thresholdKeyPairs: thresholdKeys,
    rootHex,
    servers,
  };
}

async function ocspVerify(row, services, count, requestLabel) {
  for (let i = 0; i < count; i += 1) {
    await measure(row, "statusValidation", async () => {
      const before = metricValue(row, "externalPayloadBytes");
      const response = await postJsonTracked(row, 18341, "/ocsp", {
        cert: requestLabel,
        nonce: `${row.index}:${i}`,
      });
      addMetric(row, "ocspPayloadBytes", metricValue(row, "externalPayloadBytes") - before);
      const msg = Buffer.from(response.msg, "base64");
      const signature = Buffer.from(response.signature, "base64");
      if (response.status !== "valid" || !verifyBuffer(services.ocspPublicKey, msg, signature)) {
        throw new Error("OCSP verification failed");
      }
      addCertStatusChecks(row, 1);
      addCaNodeExec(row, 1);
      addSigOps(row, 2);
    });
  }
}

async function mptVerify(row, services, chain, count, requestLabel) {
  for (let i = 0; i < count; i += 1) {
    await measure(row, "mptValidation", async () => {
      const before = metricValue(row, "externalPayloadBytes");
      const response = await postJsonTracked(row, 18342, "/mpt", {
        index: row.index + i * 97,
        nonce: `${requestLabel}:${row.index}:${i}`,
      });
      addMetric(row, "mptPayloadBytes", metricValue(row, "externalPayloadBytes") - before);

      addMetric(row, "mptProofGenerationMs", Number(response.proofGenerationMs || 0));
      const rootQueryStart = performance.now();
      const finalizedRoot = chain
        ? await chain.contract.methods.domainRoots(chain.service.domainId).call()
        : `0x${response.rootHex}`;
      addMetric(row, "mptRootQueryMs", performance.now() - rootQueryStart);
      if (String(finalizedRoot).toLowerCase() !== `0x${response.rootHex}`.toLowerCase()) {
        throw new Error("MPT root does not match the finalized on-chain root");
      }

      const verificationStart = performance.now();
      const msg = Buffer.from(response.msg, "base64");
      const signature = Buffer.from(response.signature, "base64");
      if (!verifyBuffer(services.servicePublicKey, msg, signature)) {
        throw new Error("MPT proof signature failed");
      }
      if (!verifyMerkleProof(response.leaf, response.proof, response.rootHex)) {
        throw new Error("MPT/Merkle proof failed");
      }
      addMetric(row, "mptProofVerificationMs", performance.now() - verificationStart);
      addMptProofCount(row, 1);
      addSigOps(row, 2);
    });
  }
}

async function thresholdValidate(row, services, args, requestLabel) {
  await measure(row, "thresholdValidation", async () => {
    const controllers = [];
    const promises = [];
    for (let nodeId = 0; nodeId < args.thresholdN; nodeId += 1) {
      const controller = new AbortController();
      controllers.push(controller);
      promises.push(
        fetch("http://127.0.0.1:18343/threshold", {
          method: "POST",
          headers: { "content-type": "application/json" },
          body: JSON.stringify({
            nodeId,
            cert: requestLabel,
            nonce: `${requestLabel}:${row.index}:${nodeId}`,
          }),
          signal: controller.signal,
        })
          .then((response) => response.json())
          .then((response) => {
            const msg = Buffer.from(response.msg, "base64");
            const sig = Buffer.from(response.signature, "base64");
            const key = services.thresholdPublicKeys[response.nodeId];
            if (response.state !== "valid" || !verifyBuffer(key, msg, sig)) {
              throw new Error(`bad threshold response ${response.nodeId}`);
            }
            return response;
          }),
      );
    }
    const accepted = [];
    const pending = [...promises];
    while (accepted.length < args.thresholdK && pending.length) {
      const wrapped = pending.map((promise, index) =>
        promise.then((value) => ({ index, value })).catch((error) => ({ index, error })),
      );
      const next = await Promise.race(wrapped);
      pending.splice(next.index, 1);
      if (!next.error) accepted.push(next.value);
    }
    controllers.forEach((controller) => controller.abort());
    promises.forEach((promise) => promise.catch(() => null));
    if (accepted.length < args.thresholdK) {
      throw new Error("threshold validation failed");
    }
  });
}

function compileSource(sourceName, source, contractName) {
  const input = {
    language: "Solidity",
    sources: { [sourceName]: { content: source } },
    settings: { outputSelection: { "*": { "*": ["abi", "evm.bytecode"] } } },
  };
  const output = JSON.parse(solc.compile(JSON.stringify(input)));
  const fatal = (output.errors || []).filter((item) => item.severity === "error");
  if (fatal.length) throw new Error(fatal.map((item) => item.formattedMessage).join("\n"));
  const compiled = output.contracts[sourceName][contractName];
  return { abi: compiled.abi, bytecode: `0x${compiled.evm.bytecode.object}` };
}

function compileContract() {
  return compileSource(
    path.basename(CONTRACT_PATH),
    fs.readFileSync(CONTRACT_PATH, "utf8"),
    CONTRACT_NAME,
  );
}

function compileNoopContract() {
  return compileSource("Fig4NoopProbe.sol", NOOP_CONTRACT_SOURCE, "Fig4NoopProbe");
}

async function waitRpc(web3) {
  await web3.eth.net.isListening();
}

function receiptOk(receipt) {
  return receipt.status === true || receipt.status === 1 || receipt.status === "0x1";
}

function bytesOfHex(hex) {
  return Math.max(0, ((hex || "0x").length - 2) / 2);
}

function receiptLogBytes(receipt) {
  return (receipt.logs || []).reduce((sum, log) => {
    return sum + ((log.topics || []).length * 32) + bytesOfHex(log.data);
  }, 0);
}

function contractAddressFrom(web3, sender, nonce) {
  const rlp = require(path.join(EXPERIMENT_NODE_MODULES, "rlp"));
  const encoded = rlp.encode([Buffer.from(sender.slice(2), "hex"), nonce]);
  const digest = web3.utils.keccak256(`0x${Buffer.from(encoded).toString("hex")}`);
  return web3.utils.toChecksumAddress(`0x${digest.slice(-40)}`);
}

async function sendRawTx(args, rawTransaction) {
  const body = JSON.stringify({
    jsonrpc: "2.0",
    id: Date.now(),
    method: "eth_sendRawTransaction",
    params: [rawTransaction],
  });
  const response = await fetch(args.rpc, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body,
  });
  const payload = await response.json();
  if (payload.error) throw new Error(payload.error.message || JSON.stringify(payload.error));
  return payload.result;
}

async function waitReceipt(args, hash) {
  const deadline = Date.now() + 120000;
  while (Date.now() < deadline) {
    const response = await fetch(args.rpc, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        jsonrpc: "2.0",
        id: Date.now(),
        method: "eth_getTransactionReceipt",
        params: [hash],
      }),
    });
    const payload = await response.json();
    if (payload.result) return payload.result;
    await sleep(10);
  }
  throw new Error(`receipt timeout for ${hash}`);
}

function rpcHexToNumber(value) {
  if (typeof value === "number") return value;
  if (typeof value === "string" && value.startsWith("0x")) return Number.parseInt(value, 16);
  return Number(value || 0);
}

function certRecord(web3, domain, subject, account, certHash = null) {
  return {
    certKey: keccakBytes32(web3, `cert-key:${domain}:${subject}`),
    domainId: keccakBytes32(web3, `domain:${domain}`),
    subjectId: keccakBytes32(web3, `subject:${subject}`),
    subjectAddress: account.address,
    certHash: certHash || keccakBytes32(web3, `cert-hash:${domain}:${subject}`),
  };
}

async function prepareChain(args, finalizedMptRootHex, openssl) {
  if (args.noChain) return null;
  const web3 = new Web3(new Web3.providers.HttpProvider(args.rpc));
  web3.eth.transactionPollingInterval = 5;
  await waitRpc(web3);
  const compiled = compileContract();
  const noopCompiled = compileNoopContract();
  const thresholdCommittee = Array.from({ length: args.thresholdN }, (_, index) =>
    web3.eth.accounts.privateKeyToAccount(`0x${sha256Hex(`fig4-threshold-chain:${index}`)}`),
  );
  let nonce = await web3.eth.getTransactionCount(args.account, "pending");
  const signAndSend = async (method, to = null) => {
    const serviceStart = performance.now();
    let gasEstimate = 0;
    let estimateGasMs = 0;
    try {
      const estimateStart = performance.now();
      gasEstimate = Number(await method.estimateGas({ from: args.account }));
      estimateGasMs = performance.now() - estimateStart;
    } catch (_) {
      gasEstimate = 0;
      estimateGasMs = performance.now() - serviceStart;
    }
    const data = method.encodeABI();
    const tx = {
      from: args.account,
      to,
      data,
      gas: Math.max(args.gas, gasEstimate > 0 ? Math.ceil(gasEstimate * 2) + 100000 : 0),
      gasPrice: String(args.gasPrice),
      nonce,
    };
    const thisNonce = nonce;
    nonce += 1;
    const signed = await web3.eth.accounts.signTransaction(tx, args.privateKey);
    const hash = await sendRawTx(args, signed.rawTransaction);
    const serviceMs = performance.now() - serviceStart;
    const receiptStart = performance.now();
    const receipt = await waitReceipt(args, hash);
    const receiptWaitMs = performance.now() - receiptStart;
    const normalizedReceipt = {
      ...receipt,
      gasUsed: rpcHexToNumber(receipt.gasUsed),
      status: rpcHexToNumber(receipt.status) !== 0,
    };
    if (!receiptOk(normalizedReceipt)) throw new Error(`tx failed ${hash}`);
    traceEvent("RECEIPT", {
      transactionHash: hash,
      blockNumber: rpcHexToNumber(receipt.blockNumber),
      transactionIndex: rpcHexToNumber(receipt.transactionIndex),
      gasUsed: normalizedReceipt.gasUsed,
      status: normalizedReceipt.status,
      inputBytes: bytesOfHex(data),
      rawTransactionBytes: bytesOfHex(signed.rawTransaction),
      receiptLogBytes: receiptLogBytes(normalizedReceipt),
      serviceMs,
      receiptWaitMs,
    });
    return {
      hash,
      nonce: thisNonce,
      serviceMs,
      estimateGasMs,
      receiptWaitMs,
      estimatedGas: gasEstimate,
      gasUsed: normalizedReceipt.gasUsed,
      receiptGasUsed: normalizedReceipt.gasUsed,
      txInputBytes: bytesOfHex(data),
      rawTxBytes: bytesOfHex(signed.rawTransaction),
      receiptLogBytes: receiptLogBytes(normalizedReceipt),
    };
  };

  const deployContract = new web3.eth.Contract(compiled.abi);
  const deployment = await signAndSend(deployContract.deploy({
    data: compiled.bytecode,
    arguments: [thresholdCommittee.map((item) => item.address)],
  }));
  const address = deployment.receiptContractAddress || contractAddressFrom(web3, args.account, deployment.nonce);
  const contract = new web3.eth.Contract(compiled.abi, address);
  const noopDeployContract = new web3.eth.Contract(noopCompiled.abi);
  const noopDeployment = await signAndSend(noopDeployContract.deploy({ data: noopCompiled.bytecode }));
  const noopAddress = noopDeployment.receiptContractAddress || contractAddressFrom(web3, args.account, noopDeployment.nonce);
  const noopContract = new web3.eth.Contract(noopCompiled.abi, noopAddress);
  const sourceAccount = web3.eth.accounts.privateKeyToAccount(`0x${sha256Hex("fig4-source")}`);
  const targetAccount = web3.eth.accounts.privateKeyToAccount(`0x${sha256Hex("fig4-target")}`);
  const serviceAccount = web3.eth.accounts.privateKeyToAccount(`0x${sha256Hex("fig4-service")}`);
  const now = Math.floor(Date.now() / 1000);
  const notAfter = now + 10 * 365 * 24 * 60 * 60;
  const initialCsr = fs.readFileSync(openssl.leafCsr);
  const initialCert = fs.readFileSync(openssl.leafCert);
  const initialCertHash = web3.utils.keccak256(`0x${initialCert.toString("hex")}`);
  const source = certRecord(web3, "a", "entity-a", sourceAccount, initialCertHash);
  const target = certRecord(web3, "b", "entity-b", targetAccount, initialCertHash);
  const service = certRecord(web3, "main", "service-a", serviceAccount, initialCertHash);
  const repoRoot = finalizedMptRootHex
    ? `0x${String(finalizedMptRootHex).replace(/^0x/i, "")}`
    : keccakBytes32(web3, "repo-root");
  for (const record of [source, target, service]) {
    const statusBlob = Buffer.from(`valid:${record.domainId}:${record.subjectId}`, "utf8");
    await signAndSend(contract.methods.putFullCertificateBundleAndDomainRoot(
      record.certKey,
      record.domainId,
      record.subjectId,
      record.subjectAddress,
      record.certHash,
      0,
      notAfter,
      repoRoot,
      `0x${initialCsr.toString("hex")}`,
      `0x${initialCert.toString("hex")}`,
      `0x${statusBlob.toString("hex")}`,
    ), contract.options.address);
  }
  return {
    web3,
    rpc: args.rpc,
    contract,
    noopContract,
    signAndSend,
    source,
    target,
    service,
    notAfter,
    sourceAccount,
    serviceAccount,
    thresholdCommittee,
    noopReceiptWaitMeanMs: 0,
    noopProbeRows: [],
  };
}

async function runNoopProbes(chain, args) {
  if (!chain || !chain.noopContract) return [];
  const rows = [];
  for (let i = 0; i < args.noopProbes; i += 1) {
    const result = await chain.signAndSend(
      chain.noopContract.methods.ping(keccakBytes32(chain.web3, `noop:${i}`)),
      chain.noopContract.options.address,
    );
    rows.push({
      index: i,
      serviceMs: result.serviceMs,
      estimateGasMs: result.estimateGasMs,
      receiptWaitMs: result.receiptWaitMs,
      gasUsed: result.gasUsed,
      txInputBytes: result.txInputBytes,
      rawTxBytes: result.rawTxBytes,
      receiptLogBytes: result.receiptLogBytes,
      txHash: result.hash,
    });
  }
  chain.noopProbeRows = rows;
  chain.noopReceiptWaitMeanMs = stats(rows.map((row) => row.receiptWaitMs)).mean;
  return rows;
}

function signContractAssertion(chain, requestId, crossDomain, certs, timestamp) {
  const web3 = chain.web3;
  const data = [
    requestId,
    chain.source.domainId,
    chain.target.domainId,
    chain.source.subjectId,
    chain.target.subjectId,
    keccakBytes32(web3, `nonce:${requestId}`),
  ];
  const certKeys = certs.map((cert) => cert.certKey);
  const certHashes = certs.map((cert) => cert.certHash);
  const checkHash = web3.utils.keccak256(web3.eth.abi.encodeParameters(["bytes32[]", "bytes32[]"], [certKeys, certHashes]));
  const digest = web3.utils.soliditySha3(
    { type: "address", value: chain.contract.options.address },
    { type: "bytes32", value: data[0] },
    { type: "bytes32", value: data[1] },
    { type: "bytes32", value: data[2] },
    { type: "bytes32", value: data[3] },
    { type: "bytes32", value: data[4] },
    { type: "bytes32", value: data[5] },
    { type: "address", value: chain.source.subjectAddress },
    { type: "uint256", value: timestamp },
    { type: "bool", value: crossDomain },
    { type: "bytes32", value: checkHash },
  );
  return {
    data,
    certKeys,
    certHashes,
    signature: chain.serviceAccount.sign(digest).signature,
  };
}

function persistMptRepositoryEntry(ctx, label, subjectId, certHash) {
  const line = `${safeLabel(label)},${subjectId},${certHash},valid\n`;
  fs.appendFileSync(ctx.mptRepoDb, line, "utf8");
  return bytesOfUtf8(line);
}

function persistThresholdEvidence(ctx, label, blob) {
  const filePath = path.join(ctx.evidenceDir, `${safeLabel(label)}.sigbundle`);
  fs.writeFileSync(filePath, blob);
  return fs.statSync(filePath).size;
}

function signThresholdCertificateBundle(chain, certKey, domainId, subjectId, subjectAddress, certHash, notBefore, notAfter, repoRoot, quorumK) {
  const digest = chain.web3.utils.soliditySha3(
    { type: "address", value: chain.contract.options.address },
    { type: "string", value: "threshold-cert" },
    { type: "bytes32", value: certKey },
    { type: "bytes32", value: domainId },
    { type: "bytes32", value: subjectId },
    { type: "address", value: subjectAddress },
    { type: "bytes32", value: certHash },
    { type: "uint256", value: notBefore },
    { type: "uint256", value: notAfter },
    { type: "bytes32", value: repoRoot },
  );
  const signatures = chain.thresholdCommittee
    .slice(0, Math.max(1, quorumK))
    .map((account) => account.sign(digest).signature);
  const blob = Buffer.concat(signatures.map((signature) => Buffer.from(signature.slice(2), "hex")));
  return {
    quorumK,
    signatures,
    blob,
    blobHex: `0x${blob.toString("hex")}`,
    signerCount: signatures.length,
  };
}

async function chainRecord(row, chain, stageName, method, options = {}) {
  if (!chain) {
    row.notes.push(`${stageName}:skipped-no-chain`);
    return;
  }
  const result = await chain.signAndSend(method, chain.contract.options.address);
  const adjustedReceiptMs = Math.max(
    0,
    Number(result.receiptWaitMs || 0) - Number(chain.noopReceiptWaitMeanMs || 0),
  );
  row.stages[stageName] = (row.stages[stageName] || 0)
    + Number(result.serviceMs || 0)
    + adjustedReceiptMs;
  row.gasUsed += Number(result.gasUsed || 0);
  row.estimatedGas += Number(result.estimatedGas || 0);
  row.txInputBytes += Number(result.txInputBytes || 0);
  row.rawTxBytes += Number(result.rawTxBytes || 0);
  addMetric(row, "chainWritePayloadBytes", Number(result.rawTxBytes || 0));
  row.receiptLogBytes += Number(result.receiptLogBytes || 0);
  addExternalPayloadBytes(row, Number(result.rawTxBytes || 0));
  row.receiptWaitMs += Number(result.receiptWaitMs || 0);
  row.estimateGasMs += Number(result.estimateGasMs || 0);
  row.noopAdjustedReceiptMs += adjustedReceiptMs;
  row.noopReceiptBaselineMs += Number(chain.noopReceiptWaitMeanMs || 0);
  row.txCount += 1;
  row.onChainStorageBytes += Number(options.onChainStorageBytes || 0);
  row.onChainSigVerifyOps += Number(options.onChainSigVerifyOps || 0);
}

async function chainStateRead(row, chain, requestId) {
  if (!chain) {
    row.notes.push("chainStateRead:skipped-no-chain");
    return;
  }
  await measure(row, "chainStateRead", async () => {
    const data = chain.contract.methods.authRecordExists(requestId).encodeABI();
    const body = JSON.stringify({
      jsonrpc: "2.0",
      id: Date.now(),
      method: "eth_call",
      params: [{ to: chain.contract.options.address, data }, "latest"],
    });
    addMetric(row, "chainReadOps", 1);
    addMetric(row, "chainReadBytes", bytesOfUtf8(body));
    addExternalPayloadBytes(row, bytesOfUtf8(body));
    const response = await fetch(chain.rpc, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body,
    });
    const responseText = await response.text();
    addMetric(row, "chainReadBytes", bytesOfUtf8(responseText));
    addExternalPayloadBytes(row, bytesOfUtf8(responseText));
    addMetric(row, "chainReadPayloadBytes", bytesOfUtf8(body) + bytesOfUtf8(responseText));
    const payload = JSON.parse(responseText);
    const ok = !!(payload.result && payload.result !== "0x" && payload.result !== "0x0");
    if (!ok) throw new Error("auth record not found");
  });
}

async function certificateVerification(row, ctx, count) {
  for (let i = 0; i < count; i += 1) {
    await measure(row, "certificateVerification", () => opensslVerifyCert(ctx));
    addCertStatusChecks(row, 1);
  }
}

async function fullContractCertificateValidation(row, ctx, count) {
  await measure(row, "contractExecution", async () => {
    for (let i = 0; i < count; i += 1) {
      opensslVerifyCert(ctx);
      addCertStatusChecks(row, 1);
    }
  });
}

async function assertion(row, ctx, count) {
  for (let i = 0; i < count; i += 1) {
    const result = await measure(
      row,
      "assertion",
      () => opensslAssertion(ctx, `${row.mechanism}:${row.requestClass}:${row.index}:${i}`),
    );
    addSigOps(row, 2);
    addMsgCount(row, 2);
    const payload = Number(result.payloadBytes || 0) + Number(result.signatureBytes || 0);
    addPayloadBytes(row, payload);
    addExternalPayloadBytes(row, payload);
    addMetric(row, "assertionPayloadBytes", payload);
  }
}

async function issue(row, ctx, count, options = {}) {
  const results = [];
  const countOffchainStorage = options.countOffchainStorage !== false;
  for (let i = 0; i < count; i += 1) {
    const result = await measure(
      row,
      "issueUpdate",
      () => opensslIssue(ctx, `${row.mechanism}:${row.requestClass}:${row.index}:${i}`, options),
    );
    addIssueKeyOps(row, 3);
    addCertStatusChecks(row, 1);
    addCaNodeExec(row, 1);
    addSigOps(row, 2);
    addMsgCount(row, 2);
    const payload = Number(result.csrBytes || 0) + Number(result.certBytes || 0);
    addPayloadBytes(row, payload);
    addExternalPayloadBytes(row, payload);
    addMetric(row, "issuePayloadBytes", payload);
    addMetric(row, "issuedKeyBytes", Number(result.keyBytes || 0));
    addMetric(row, "issuedCsrBytes", Number(result.csrBytes || 0));
    addMetric(row, "issuedCertBytes", Number(result.certBytes || 0));
    addMetric(row, "issuedStatusBytes", Number(result.statusBytes || 0));
    if (countOffchainStorage) {
      addMetric(row, "offChainStorageBytes", Number(result.offchainStorageBytes || 0));
    }
    results.push(result);
  }
  return count === 1 ? results[0] : results;
}

function newRow(mechanism, requestClass, index) {
  return {
    mechanism,
    requestClass,
    index,
    stages: {},
    notes: [],
    gasUsed: 0,
    estimatedGas: 0,
    txInputBytes: 0,
    rawTxBytes: 0,
    receiptLogBytes: 0,
    receiptWaitMs: 0,
    estimateGasMs: 0,
    txCount: 0,
    issueKeyOps: 0,
    certStatusChecks: 0,
    mptProofCount: 0,
    caNodeExec: 0,
    sigOps: 0,
    msgCount: 0,
    payloadBytes: 0,
    externalPayloadBytes: 0,
    internalPayloadBytes: 0,
    issuePayloadBytes: 0,
    assertionPayloadBytes: 0,
    ocspPayloadBytes: 0,
    mptPayloadBytes: 0,
    mptProofGenerationMs: 0,
    mptRootQueryMs: 0,
    mptProofVerificationMs: 0,
    thresholdPayloadBytes: 0,
    thresholdInternalPayloadBytes: 0,
    chainWritePayloadBytes: 0,
    chainReadPayloadBytes: 0,
    chainReadOps: 0,
    chainReadBytes: 0,
    onChainStorageBytes: 0,
    offChainStorageBytes: 0,
    onChainSigVerifyOps: 0,
    issuedKeyBytes: 0,
    issuedCsrBytes: 0,
    issuedCertBytes: 0,
    issuedStatusBytes: 0,
  };
}

function buildBaselineHelpers() {
  return {
    measure,
    postJson,
    issue,
    assertion,
    certificateVerification,
    fullContractCertificateValidation,
    ocspVerify,
    mptVerify,
    thresholdValidate,
    chainRecord,
    chainStateRead,
    signThresholdCertificateBundle,
    signContractAssertion,
    proposedCertificateStorageBytes,
    thresholdCertificateStorageBytes,
    fullCertificateStorageBytes,
    authRecordStorageBytes,
    signedAuthRecordStorageBytes,
    keccakBytes32,
    addCertStatusChecks,
  };
}

async function runWorkflow(row, ctx) {
  const { mechanism, requestClass } = row;
  const label = `${mechanism}:${requestClass}:${row.index}`;
  const chain = ctx.chain;
  const requestId = chain ? keccakBytes32(chain.web3, label) : null;
  const platform = PLATFORM_REGISTRY[mechanism];
  if (!platform) {
    throw new Error(`Unsupported mechanism: ${mechanism}`);
  }
  if (platform.requestClasses && !platform.requestClasses.includes(requestClass)) {
    throw new Error(`Unsupported request class ${requestClass} for ${mechanism}`);
  }
  await platform.execute({
    row,
    ctx,
    label,
    requestId,
    helpers: buildBaselineHelpers(),
  });
}

function flattenRow(row) {
  const totalServiceMs = Object.values(row.stages).reduce((sum, value) => sum + value, 0);
  return {
    mechanism: row.mechanism,
    requestClass: row.requestClass,
    index: row.index,
    totalServiceMs,
    issueUpdateMs: row.stages.issueUpdate || 0,
    certificateVerificationMs: row.stages.certificateVerification || 0,
    statusValidationMs: row.stages.statusValidation || 0,
    mptValidationMs: row.stages.mptValidation || 0,
    mptProofGenerationMs: row.mptProofGenerationMs,
    mptRootQueryMs: row.mptRootQueryMs,
    mptProofVerificationMs: row.mptProofVerificationMs,
    thresholdValidationMs: row.stages.thresholdValidation || 0,
    thresholdIssueMs: row.stages.thresholdIssue || 0,
    chainRecordMs: row.stages.chainRecord || 0,
    chainStateReadMs: row.stages.chainStateRead || 0,
    contractExecutionMs: row.stages.contractExecution || 0,
    assertionMs: row.stages.assertion || 0,
    gasUsed: row.gasUsed,
    estimatedGas: row.estimatedGas,
    txInputBytes: row.txInputBytes,
    rawTxBytes: row.rawTxBytes,
    receiptLogBytes: row.receiptLogBytes,
    receiptWaitMs: row.receiptWaitMs,
    estimateGasMs: row.estimateGasMs,
    txCount: row.txCount,
    issueKeyOps: row.issueKeyOps,
    certStatusChecks: row.certStatusChecks,
    mptProofCount: row.mptProofCount,
    caNodeExec: row.caNodeExec,
    sigOps: row.sigOps,
    msgCount: row.msgCount,
    payloadBytes: row.payloadBytes,
    externalPayloadBytes: row.externalPayloadBytes,
    internalPayloadBytes: row.internalPayloadBytes,
    issuePayloadBytes: row.issuePayloadBytes,
    assertionPayloadBytes: row.assertionPayloadBytes,
    ocspPayloadBytes: row.ocspPayloadBytes,
    mptPayloadBytes: row.mptPayloadBytes,
    thresholdPayloadBytes: row.thresholdPayloadBytes,
    thresholdInternalPayloadBytes: row.thresholdInternalPayloadBytes,
    chainWritePayloadBytes: row.chainWritePayloadBytes,
    chainReadPayloadBytes: row.chainReadPayloadBytes,
    chainReadOps: row.chainReadOps,
    chainReadBytes: row.chainReadBytes,
    onChainStorageBytes: row.onChainStorageBytes,
    offChainStorageBytes: row.offChainStorageBytes,
    onChainSigVerifyOps: row.onChainSigVerifyOps,
    issuedKeyBytes: row.issuedKeyBytes,
    issuedCsrBytes: row.issuedCsrBytes,
    issuedCertBytes: row.issuedCertBytes,
    issuedStatusBytes: row.issuedStatusBytes,
    notes: row.notes.join(";"),
  };
}

function summarizeRows(rows) {
  const groups = new Map();
  for (const row of rows) {
    const key = `${row.mechanism}\t${row.requestClass}`;
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(row);
  }
  const columns = [
    "totalServiceMs",
    "issueUpdateMs",
    "certificateVerificationMs",
    "statusValidationMs",
    "mptValidationMs",
    "mptProofGenerationMs",
    "mptRootQueryMs",
    "mptProofVerificationMs",
    "thresholdValidationMs",
    "thresholdIssueMs",
    "chainRecordMs",
    "chainStateReadMs",
    "contractExecutionMs",
    "assertionMs",
    "receiptWaitMs",
  ];
  const summary = [];
  for (const [key, group] of groups) {
    const [mechanism, requestClass] = key.split("\t");
    const base = { mechanism, requestClass, count: group.length };
    for (const column of columns) {
      const s = stats(group.map((row) => Number(row[column] || 0)));
      base[`${column}_mean`] = s.mean;
      base[`${column}_variance`] = s.variance;
      base[`${column}_std`] = s.std;
      base[`${column}_mad`] = s.mad;
      base[`${column}_p50`] = s.p50;
      base[`${column}_p95`] = s.p95;
      base[`${column}_min`] = s.min;
      base[`${column}_max`] = s.max;
    }
    summary.push(base);
  }
  return summary;
}

async function main() {
  const args = parseArgs();
  fs.mkdirSync(args.out, { recursive: true });
  const rng = makeRng(args.seed);
  const openssl = prepareOpenSslWorkspace(path.join(args.out, "openssl_work"));
  const services = await prepareNetworkServices(args, rng);
  let chain = null;
  try {
    chain = await prepareChain(args, services.rootHex, openssl);
  } catch (error) {
    if (!args.noChain) throw error;
  }

  const ctx = { args, openssl, services, chain };
  const metricColumns = [
    "mechanism",
    "requestClass",
    "index",
    "totalServiceMs",
    "issueUpdateMs",
    "certificateVerificationMs",
    "statusValidationMs",
    "mptValidationMs",
    "mptProofGenerationMs",
    "mptRootQueryMs",
    "mptProofVerificationMs",
    "thresholdValidationMs",
    "thresholdIssueMs",
    "chainRecordMs",
    "chainStateReadMs",
    "contractExecutionMs",
    "assertionMs",
    "receiptWaitMs",
    "notes",
  ];
  const flattenedRows = [];
  try {
    console.log(`Running ${REQUEST_CLASSES.length} request classes with mixed seeded order: ${args.requests} rounds`);
    for (let i = 0; i < args.requests; i += 1) {
      const roundOrder = shuffledRequestClasses(rng);
      for (const [mechanism, requestClass] of roundOrder) {
        const row = newRow(mechanism, requestClass, i);
        await runWorkflow(row, ctx);
        const flattened = flattenRow(row);
        flattenedRows.push(flattened);
        traceEvent("REQUEST", Object.fromEntries(
          metricColumns.map((column) => [column, flattened[column]]),
        ));
      }
    }
  } finally {
    for (const server of services.servers) {
      server.close();
    }
  }

  const summaryRows = summarizeRows(flattenedRows);
  const summaryColumns = Object.keys(summaryRows[0] || { mechanism: "", requestClass: "", count: "" });

  writeCsv(path.join(args.out, "request_metrics.csv"), flattenedRows, metricColumns);
  writeCsv(path.join(args.out, "summary_by_request_class.csv"), summaryRows, summaryColumns);
  fs.writeFileSync(path.join(args.out, "manifest.json"), `${JSON.stringify({
    generatedAt: new Date().toISOString(),
    requests: args.requests,
    threshold: `${args.thresholdK}-of-${args.thresholdN}`,
    rpc: args.rpc,
    noChain: args.noChain,
    executionOrder: "mixed seeded shuffle by request index",
    note: "On-chain stage latency includes estimateGas/local contract execution simulation, signing, and tx submission. PoW mining/receipt waiting is preserved separately as receiptWaitMs.",
  }, null, 2)}\n`);
  console.log(`Saved ${args.out}`);
}

main().catch((error) => {
  console.error(error && error.stack ? error.stack : error);
  process.exit(1);
});
