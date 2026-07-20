const fs = require("fs");
const os = require("os");
const path = require("path");
const crypto = require("crypto");
const childProcess = require("child_process");
const http = require("http");
const https = require("https");
const net = require("net");
const { URL } = require("url");
const { performance } = require("perf_hooks");

const solc = require("solc");
const Web3 = require("web3");

const ROOT = path.resolve(__dirname, "..", "..");
const EXPERIMENT_DIR = __dirname;
const OUT_DIR = path.join(EXPERIMENT_DIR, "outputs");
const CONTRACT_PATH = path.join(EXPERIMENT_DIR, "contracts", "DPKIExperiment.sol");
const SIMU2_DIR = process.env.DPKI_COMPAT_OUTPUT_DIR
  ? path.resolve(process.env.DPKI_COMPAT_OUTPUT_DIR)
  : path.join(ROOT, "blockchain", ".internal", "old-ver-simulations", "simu2_tail_prob");
const OPENSSL_RUNTIME_ROOT = path.join(os.tmpdir(), "chain33-dpki-http-runtime");
const VERBOSE_TRACE = /^(1|true|yes|on)$/i.test(process.env.DPKI_VERBOSE_TRACE || "");

function traceEvent(kind, payload) {
  if (!VERBOSE_TRACE) return;
  console.log(`[TRACE][${kind}] ${JSON.stringify(payload)}`);
}

const DEFAULTS = {
  rpc: "http://127.0.0.1:8545",
  account: "0xab7F5238cbEfB02062241cf979e4994b656FB944",
  privateKey: "0x73e66f099144f820753aa3a5e131785b528081da572e16339fcd02de05de719e",
  consensusBackend: "pow",
  powRpc: "http://127.0.0.1:8801",
  powRuntime: path.join(ROOT, "blockchain", "pow-4nodes-runtime", "runtime"),
  powWarmupMs: 65000,
  epsilonPoints: "0.1,0.15,0.2,0.25,0.3,0.35,0.4,0.45,0.5",
  requestsPerEpsilon: 200,
  lambdaArrival: 0.8,
  pManage: 0.1,
  gammaOnChain: 0.1,
  qManage: 0.3,
  lambdaBlock: 200,
  lambdaExecute: 200,
  muAuth: 8.5,
  serviceCAs: 6,
  dpkiOffchainWorkers: 0,
  timeScaleMs: 1000,
  maxOnchainInFlight: 4,
  txSenders: 4,
  receiptPollMs: 5,
  fixedGasLimit: 800000,
  fixedGasPriceWei: "1",
  chainId: 0,
  estimateGas: false,
  rawTxSubmitTimeoutMs: 250,
  rawTxSubmitRetries: 4,
  rawTxReceiptTimeoutMs: 15000,
  serviceShapeMode: "target-exponential",
  dpkiAuthShapeMeanMs: 0,
  dpkiCrossShapeMeanMs: 0,
  dpkiOnchainShapeMeanMs: 0,
  dpkiIntraOffchainShapeMeanMs: 0,
  dpkiOffchainShapeMeanMs: 0,
  dpkiManagementShapeMeanMs: 0,
  pkiAuthShapeMeanMs: 0,
  pkiCrossShapeMeanMs: 0,
  pkiIntraShapeMeanMs: 0,
  pkiManagementShapeMeanMs: 0,
  ocspBasePort: 19080,
  dpkiProofBasePort: 20080,
  pkiServiceBasePort: 21080,
  httpShapeSegments: 1,
  httpShapeTailProbability: 0.2,
  httpShapeTailMultiplier: 4.0,
  dpkiProofHttpMeanMs: 7.5,
  dpkiProofHttpHops: 1,
  dpkiProofHttpSegments: 1,
  dpkiProofHttpTailProbability: 0.05,
  dpkiProofHttpTailMultiplier: 15.0,
  dpkiAuthTransferHttpMeanMs: 12,
  dpkiAuthTransferHttpHops: 1,
  dpkiAuthTransferHttpSegments: 1,
  dpkiAuthTransferHttpTailProbability: 0.22,
  dpkiAuthTransferHttpTailMultiplier: 6.0,
  dpkiOnchainExtraHttpMeanMs: 0,
  dpkiOnchainExtraHttpHops: 1,
  dpkiOnchainExtraHttpSegments: 1,
  dpkiOnchainExtraHttpTailProbability: 0.0,
  dpkiOnchainExtraHttpTailMultiplier: 1.0,
  dpkiCrossExtraHttpMeanMs: 0,
  dpkiCrossExtraHttpHops: 1,
  dpkiCrossExtraHttpSegments: 1,
  dpkiCrossExtraHttpTailProbability: 0.0,
  dpkiCrossExtraHttpTailMultiplier: 1.0,
  dpkiManagementHttpMeanMs: 6,
  dpkiManagementHttpHops: 1,
  dpkiManagementHttpSegments: 1,
  dpkiManagementHttpTailProbability: 0.15,
  dpkiManagementHttpTailMultiplier: 3.0,
  dpkiManagementTransferHttpMeanMs: 10,
  dpkiManagementTransferHttpHops: 1,
  dpkiManagementTransferHttpSegments: 1,
  dpkiManagementTransferHttpTailProbability: 0.22,
  dpkiManagementTransferHttpTailMultiplier: 5.0,
  dpkiManagementExtraHttpMeanMs: 0,
  dpkiManagementExtraHttpHops: 1,
  dpkiManagementExtraHttpSegments: 1,
  dpkiManagementExtraHttpTailProbability: 0.0,
  dpkiManagementExtraHttpTailMultiplier: 1.0,
  pkiAuthHttpMeanMs: 5,
  pkiAuthHttpHops: 1,
  pkiAuthHttpSegments: 1,
  pkiAuthHttpTailProbability: 0.15,
  pkiAuthHttpTailMultiplier: 3.0,
  pkiAuthTransferHttpMeanMs: 0,
  pkiAuthTransferHttpHops: 1,
  pkiAuthTransferHttpSegments: 1,
  pkiAuthTransferHttpTailProbability: 0.2,
  pkiAuthTransferHttpTailMultiplier: 4.0,
  pkiCrossExtraHttpMeanMs: 0,
  pkiCrossExtraHttpHops: 1,
  pkiCrossExtraHttpSegments: 1,
  pkiCrossExtraHttpTailProbability: 0.0,
  pkiCrossExtraHttpTailMultiplier: 1.0,
  pkiManagementHttpMeanMs: 6,
  pkiManagementHttpHops: 1,
  pkiManagementHttpSegments: 1,
  pkiManagementHttpTailProbability: 0.15,
  pkiManagementHttpTailMultiplier: 3.0,
  pkiManagementTransferHttpMeanMs: 8,
  pkiManagementTransferHttpHops: 1,
  pkiManagementTransferHttpSegments: 1,
  pkiManagementTransferHttpTailProbability: 0.2,
  pkiManagementTransferHttpTailMultiplier: 4.0,
  pkiManagementExtraHttpMeanMs: 0,
  pkiManagementExtraHttpHops: 1,
  pkiManagementExtraHttpSegments: 1,
  pkiManagementExtraHttpTailProbability: 0.0,
  pkiManagementExtraHttpTailMultiplier: 1.0,
  resetPerEpsilon: false,
  skipPki: false,
  arrivalMode: "wall",
  kindPlanMode: "fixed",
  dpkiRootReadMode: "chain",
  dpkiProofReadMode: "http",
  actualExecutionMode: "serial",
  seed: 3302,
};

const PKI_AUTH_NETWORK_SETUP_MS = 1.48386291;
const PKI_OCSP_NETWORK_RTT_MS = 1.40121465;
const PKI_CROSS_DOMAIN_CHAIN_STEPS = 3;
const MANAGEMENT_DOMAIN = "management";
const MANAGEMENT_POOL_SIZE = 8;

const chainTxBreakdowns = [];
let chainTxSequence = 0;
let ACTIVE_ARGS = { ...DEFAULTS };
let ACTIVE_CHAIN_ID = null;
let JSON_RPC_ID = 1;
const OPENSSL_OCSP_PLATFORMS = new Set();
const DPKI_PROOF_PLATFORMS = new Set();
const PKI_SERVICE_PLATFORMS = new Set();

function parseArgs() {
  const args = { ...DEFAULTS };
  for (let i = 2; i < process.argv.length; i += 1) {
    const arg = process.argv[i];
    const next = process.argv[i + 1];
    if (arg === "--rpc" && next) args.rpc = next;
    else if (arg === "--consensus-backend" && next) args.consensusBackend = next;
    else if (arg === "--pow-rpc" && next) args.powRpc = next;
    else if (arg === "--pow-runtime" && next) args.powRuntime = next;
    else if (arg === "--pow-warmup-ms" && next) args.powWarmupMs = Number(next);
    else if (arg === "--requests-per-epsilon" && next) args.requestsPerEpsilon = Number(next);
    else if (arg === "--epsilon-points" && next) args.epsilonPoints = next;
    else if (arg === "--lambda-arrival" && next) args.lambdaArrival = Number(next);
    else if (arg === "--p-manage" && next) args.pManage = Number(next);
    else if (arg === "--gamma-on-chain" && next) args.gammaOnChain = Number(next);
    else if (arg === "--q-manage" && next) args.qManage = Number(next);
    else if (arg === "--lambda-block" && next) args.lambdaBlock = Number(next);
    else if (arg === "--lambda-execute" && next) args.lambdaExecute = Number(next);
    else if (arg === "--mu-auth" && next) args.muAuth = Number(next);
    else if (arg === "--service-cas" && next) args.serviceCAs = Number(next);
    else if (arg === "--dpki-offchain-workers" && next) args.dpkiOffchainWorkers = Number(next);
    else if (arg === "--time-scale-ms" && next) args.timeScaleMs = Number(next);
    else if (arg === "--max-onchain-in-flight" && next) args.maxOnchainInFlight = Number(next);
    else if (arg === "--tx-senders" && next) args.txSenders = Number(next);
    else if (arg === "--receipt-poll-ms" && next) args.receiptPollMs = Number(next);
    else if (arg === "--fixed-gas-limit" && next) args.fixedGasLimit = Number(next);
    else if (arg === "--fixed-gas-price-wei" && next) args.fixedGasPriceWei = String(next);
    else if (arg === "--chain-id" && next) args.chainId = Number(next);
    else if (arg === "--raw-tx-submit-timeout-ms" && next) args.rawTxSubmitTimeoutMs = Number(next);
    else if (arg === "--raw-tx-submit-retries" && next) args.rawTxSubmitRetries = Number(next);
    else if (arg === "--raw-tx-receipt-timeout-ms" && next) args.rawTxReceiptTimeoutMs = Number(next);
    else if (arg === "--estimate-gas") {
      args.estimateGas = true;
      continue;
    }
    else if (arg === "--no-estimate-gas") {
      args.estimateGas = false;
      continue;
    }
    else if (arg === "--service-shape-mode" && next) args.serviceShapeMode = next;
    else if (arg === "--dpki-auth-shape-mean-ms" && next) args.dpkiAuthShapeMeanMs = Number(next);
    else if (arg === "--dpki-cross-shape-mean-ms" && next) args.dpkiCrossShapeMeanMs = Number(next);
    else if (arg === "--dpki-onchain-shape-mean-ms" && next) args.dpkiOnchainShapeMeanMs = Number(next);
    else if (arg === "--dpki-intra-offchain-shape-mean-ms" && next) args.dpkiIntraOffchainShapeMeanMs = Number(next);
    else if (arg === "--dpki-offchain-shape-mean-ms" && next) args.dpkiOffchainShapeMeanMs = Number(next);
    else if (arg === "--dpki-management-shape-mean-ms" && next) args.dpkiManagementShapeMeanMs = Number(next);
    else if (arg === "--pki-auth-shape-mean-ms" && next) args.pkiAuthShapeMeanMs = Number(next);
    else if (arg === "--pki-cross-shape-mean-ms" && next) args.pkiCrossShapeMeanMs = Number(next);
    else if (arg === "--pki-intra-shape-mean-ms" && next) args.pkiIntraShapeMeanMs = Number(next);
    else if (arg === "--pki-management-shape-mean-ms" && next) args.pkiManagementShapeMeanMs = Number(next);
    else if (arg === "--ocsp-base-port" && next) args.ocspBasePort = Number(next);
    else if (arg === "--dpki-proof-base-port" && next) args.dpkiProofBasePort = Number(next);
    else if (arg === "--pki-service-base-port" && next) args.pkiServiceBasePort = Number(next);
    else if (arg === "--http-shape-segments" && next) args.httpShapeSegments = Number(next);
    else if (arg === "--http-shape-tail-probability" && next) args.httpShapeTailProbability = Number(next);
    else if (arg === "--http-shape-tail-multiplier" && next) args.httpShapeTailMultiplier = Number(next);
    else if (arg === "--dpki-proof-http-mean-ms" && next) args.dpkiProofHttpMeanMs = Number(next);
    else if (arg === "--dpki-proof-http-hops" && next) args.dpkiProofHttpHops = Number(next);
    else if (arg === "--dpki-proof-http-segments" && next) args.dpkiProofHttpSegments = Number(next);
    else if (arg === "--dpki-proof-http-tail-probability" && next) args.dpkiProofHttpTailProbability = Number(next);
    else if (arg === "--dpki-proof-http-tail-multiplier" && next) args.dpkiProofHttpTailMultiplier = Number(next);
    else if (arg === "--dpki-auth-transfer-http-mean-ms" && next) args.dpkiAuthTransferHttpMeanMs = Number(next);
    else if (arg === "--dpki-auth-transfer-http-hops" && next) args.dpkiAuthTransferHttpHops = Number(next);
    else if (arg === "--dpki-auth-transfer-http-segments" && next) args.dpkiAuthTransferHttpSegments = Number(next);
    else if (arg === "--dpki-auth-transfer-http-tail-probability" && next) args.dpkiAuthTransferHttpTailProbability = Number(next);
    else if (arg === "--dpki-auth-transfer-http-tail-multiplier" && next) args.dpkiAuthTransferHttpTailMultiplier = Number(next);
    else if (arg === "--dpki-onchain-extra-http-mean-ms" && next) args.dpkiOnchainExtraHttpMeanMs = Number(next);
    else if (arg === "--dpki-onchain-extra-http-hops" && next) args.dpkiOnchainExtraHttpHops = Number(next);
    else if (arg === "--dpki-onchain-extra-http-segments" && next) args.dpkiOnchainExtraHttpSegments = Number(next);
    else if (arg === "--dpki-onchain-extra-http-tail-probability" && next) args.dpkiOnchainExtraHttpTailProbability = Number(next);
    else if (arg === "--dpki-onchain-extra-http-tail-multiplier" && next) args.dpkiOnchainExtraHttpTailMultiplier = Number(next);
    else if (arg === "--dpki-cross-extra-http-mean-ms" && next) args.dpkiCrossExtraHttpMeanMs = Number(next);
    else if (arg === "--dpki-cross-extra-http-hops" && next) args.dpkiCrossExtraHttpHops = Number(next);
    else if (arg === "--dpki-cross-extra-http-segments" && next) args.dpkiCrossExtraHttpSegments = Number(next);
    else if (arg === "--dpki-cross-extra-http-tail-probability" && next) args.dpkiCrossExtraHttpTailProbability = Number(next);
    else if (arg === "--dpki-cross-extra-http-tail-multiplier" && next) args.dpkiCrossExtraHttpTailMultiplier = Number(next);
    else if (arg === "--dpki-management-http-mean-ms" && next) args.dpkiManagementHttpMeanMs = Number(next);
    else if (arg === "--dpki-management-http-hops" && next) args.dpkiManagementHttpHops = Number(next);
    else if (arg === "--dpki-management-http-segments" && next) args.dpkiManagementHttpSegments = Number(next);
    else if (arg === "--dpki-management-http-tail-probability" && next) args.dpkiManagementHttpTailProbability = Number(next);
    else if (arg === "--dpki-management-http-tail-multiplier" && next) args.dpkiManagementHttpTailMultiplier = Number(next);
    else if (arg === "--dpki-management-transfer-http-mean-ms" && next) args.dpkiManagementTransferHttpMeanMs = Number(next);
    else if (arg === "--dpki-management-transfer-http-hops" && next) args.dpkiManagementTransferHttpHops = Number(next);
    else if (arg === "--dpki-management-transfer-http-segments" && next) args.dpkiManagementTransferHttpSegments = Number(next);
    else if (arg === "--dpki-management-transfer-http-tail-probability" && next) args.dpkiManagementTransferHttpTailProbability = Number(next);
    else if (arg === "--dpki-management-transfer-http-tail-multiplier" && next) args.dpkiManagementTransferHttpTailMultiplier = Number(next);
    else if (arg === "--dpki-management-extra-http-mean-ms" && next) args.dpkiManagementExtraHttpMeanMs = Number(next);
    else if (arg === "--dpki-management-extra-http-hops" && next) args.dpkiManagementExtraHttpHops = Number(next);
    else if (arg === "--dpki-management-extra-http-segments" && next) args.dpkiManagementExtraHttpSegments = Number(next);
    else if (arg === "--dpki-management-extra-http-tail-probability" && next) args.dpkiManagementExtraHttpTailProbability = Number(next);
    else if (arg === "--dpki-management-extra-http-tail-multiplier" && next) args.dpkiManagementExtraHttpTailMultiplier = Number(next);
    else if (arg === "--pki-auth-http-mean-ms" && next) args.pkiAuthHttpMeanMs = Number(next);
    else if (arg === "--pki-auth-http-hops" && next) args.pkiAuthHttpHops = Number(next);
    else if (arg === "--pki-auth-http-segments" && next) args.pkiAuthHttpSegments = Number(next);
    else if (arg === "--pki-auth-http-tail-probability" && next) args.pkiAuthHttpTailProbability = Number(next);
    else if (arg === "--pki-auth-http-tail-multiplier" && next) args.pkiAuthHttpTailMultiplier = Number(next);
    else if (arg === "--pki-auth-transfer-http-mean-ms" && next) args.pkiAuthTransferHttpMeanMs = Number(next);
    else if (arg === "--pki-auth-transfer-http-hops" && next) args.pkiAuthTransferHttpHops = Number(next);
    else if (arg === "--pki-auth-transfer-http-segments" && next) args.pkiAuthTransferHttpSegments = Number(next);
    else if (arg === "--pki-auth-transfer-http-tail-probability" && next) args.pkiAuthTransferHttpTailProbability = Number(next);
    else if (arg === "--pki-auth-transfer-http-tail-multiplier" && next) args.pkiAuthTransferHttpTailMultiplier = Number(next);
    else if (arg === "--pki-cross-extra-http-mean-ms" && next) args.pkiCrossExtraHttpMeanMs = Number(next);
    else if (arg === "--pki-cross-extra-http-hops" && next) args.pkiCrossExtraHttpHops = Number(next);
    else if (arg === "--pki-cross-extra-http-segments" && next) args.pkiCrossExtraHttpSegments = Number(next);
    else if (arg === "--pki-cross-extra-http-tail-probability" && next) args.pkiCrossExtraHttpTailProbability = Number(next);
    else if (arg === "--pki-cross-extra-http-tail-multiplier" && next) args.pkiCrossExtraHttpTailMultiplier = Number(next);
    else if (arg === "--pki-management-http-mean-ms" && next) args.pkiManagementHttpMeanMs = Number(next);
    else if (arg === "--pki-management-http-hops" && next) args.pkiManagementHttpHops = Number(next);
    else if (arg === "--pki-management-http-segments" && next) args.pkiManagementHttpSegments = Number(next);
    else if (arg === "--pki-management-http-tail-probability" && next) args.pkiManagementHttpTailProbability = Number(next);
    else if (arg === "--pki-management-http-tail-multiplier" && next) args.pkiManagementHttpTailMultiplier = Number(next);
    else if (arg === "--pki-management-transfer-http-mean-ms" && next) args.pkiManagementTransferHttpMeanMs = Number(next);
    else if (arg === "--pki-management-transfer-http-hops" && next) args.pkiManagementTransferHttpHops = Number(next);
    else if (arg === "--pki-management-transfer-http-segments" && next) args.pkiManagementTransferHttpSegments = Number(next);
    else if (arg === "--pki-management-transfer-http-tail-probability" && next) args.pkiManagementTransferHttpTailProbability = Number(next);
    else if (arg === "--pki-management-transfer-http-tail-multiplier" && next) args.pkiManagementTransferHttpTailMultiplier = Number(next);
    else if (arg === "--pki-management-extra-http-mean-ms" && next) args.pkiManagementExtraHttpMeanMs = Number(next);
    else if (arg === "--pki-management-extra-http-hops" && next) args.pkiManagementExtraHttpHops = Number(next);
    else if (arg === "--pki-management-extra-http-segments" && next) args.pkiManagementExtraHttpSegments = Number(next);
    else if (arg === "--pki-management-extra-http-tail-probability" && next) args.pkiManagementExtraHttpTailProbability = Number(next);
    else if (arg === "--pki-management-extra-http-tail-multiplier" && next) args.pkiManagementExtraHttpTailMultiplier = Number(next);
    else if (arg === "--arrival-mode" && next) args.arrivalMode = next;
    else if (arg === "--kind-plan-mode" && next) args.kindPlanMode = next;
    else if (arg === "--dpki-root-read-mode" && next) args.dpkiRootReadMode = next;
    else if (arg === "--dpki-proof-read-mode" && next) args.dpkiProofReadMode = next;
    else if (arg === "--actual-execution-mode" && next) args.actualExecutionMode = next;
    else if (arg === "--reset-per-epsilon") {
      args.resetPerEpsilon = true;
      continue;
    }
    else if (arg === "--skip-pki") {
      args.skipPki = true;
      continue;
    }
    else if (arg === "--seed" && next) args.seed = Number(next);
    else continue;
    i += 1;
  }
  args.epsilonValues = args.epsilonPoints.split(",").map((value) => Number(value.trim()));
  return args;
}

function configureWeb3ForFastReceipts(web3, args) {
  if (!web3 || !web3.eth) return;
  web3.eth.transactionPollingInterval = Math.max(1, Number(args.receiptPollMs) || 5);
  web3.eth.transactionConfirmationBlocks = 1;
  web3.eth.transactionBlockTimeout = 100000;
  web3.eth.transactionPollingTimeout = 600;
}

function mulberry32(seed) {
  let t = seed >>> 0;
  return function rand() {
    t += 0x6d2b79f5;
    let x = t;
    x = Math.imul(x ^ (x >>> 15), x | 1);
    x ^= x + Math.imul(x ^ (x >>> 7), x | 61);
    return ((x ^ (x >>> 14)) >>> 0) / 4294967296;
  };
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, Math.max(0, ms)));
}

async function sleepPrecise(ms) {
  const totalMs = Math.max(0, Number(ms) || 0);
  if (!totalMs) return;
  const target = performance.now() + totalMs;
  if (totalMs > 6) {
    await sleep(Math.max(0, totalMs - 3));
  }
  while (performance.now() < target) {
    // Busy-wait only for the final few milliseconds to avoid coarse timer quantization.
  }
}

function requestJsonRpc(method, params = [], timeoutMs = 1000) {
  const endpoint = new URL(ACTIVE_ARGS.rpc);
  const deadlineMs = Math.max(1, Number(timeoutMs) || 1000);
  const body = JSON.stringify({
    jsonrpc: "2.0",
    id: JSON_RPC_ID += 1,
    method,
    params,
  });
  const transport = endpoint.protocol === "https:" ? https : http;

  return new Promise((resolve, reject) => {
    let settled = false;
    let req;
    const hardTimer = setTimeout(() => {
      if (settled) return;
      settled = true;
      const error = new Error(`${method} hard timed out after ${deadlineMs}ms`);
      error.code = "RPC_TIMEOUT";
      if (req) req.destroy(error);
      reject(error);
    }, deadlineMs);
    function finishResolve(value) {
      if (settled) return;
      settled = true;
      clearTimeout(hardTimer);
      resolve(value);
    }
    function finishReject(error) {
      if (settled) return;
      settled = true;
      clearTimeout(hardTimer);
      reject(error);
    }
    req = transport.request(
      {
        protocol: endpoint.protocol,
        hostname: endpoint.hostname,
        port: endpoint.port,
        path: `${endpoint.pathname || "/"}${endpoint.search || ""}`,
        method: "POST",
        headers: {
          "content-type": "application/json",
          "content-length": Buffer.byteLength(body),
          "connection": "close",
        },
        timeout: deadlineMs,
      },
      (res) => {
        const chunks = [];
        res.on("data", (chunk) => chunks.push(chunk));
        res.on("end", () => {
          if (settled) return;
          const text = Buffer.concat(chunks).toString("utf8");
          try {
            const parsed = text ? JSON.parse(text) : {};
            if (parsed.error) {
              const error = new Error(parsed.error.message || JSON.stringify(parsed.error));
              error.rpcError = parsed.error;
              finishReject(error);
              return;
            }
            finishResolve(parsed.result);
          } catch (error) {
            finishReject(new Error(`${method} returned invalid JSON: ${error.message}; body=${text.slice(0, 200)}`));
          }
        });
      }
    );

    req.on("timeout", () => {
      const error = new Error(`${method} timed out after ${deadlineMs}ms`);
      error.code = "RPC_TIMEOUT";
      req.destroy(error);
    });
    req.on("error", finishReject);
    req.write(body);
    req.end();
  });
}

function rpcErrorMessage(error) {
  return String(error && error.message ? error.message : error || "").toLowerCase();
}

function isTransientRpcError(error) {
  const message = rpcErrorMessage(error);
  return (
    message.includes("invalid json rpc response") ||
    message.includes("returned invalid json") ||
    message.includes("empty response") ||
    message.includes("connection error") ||
    message.includes("socket hang up") ||
    message.includes("econnreset") ||
    message.includes("econnrefused") ||
    message.includes("network error") ||
    message.includes("gateway timeout") ||
    message.includes("rpc_timeout") ||
    message.includes("timed out")
  );
}

async function withRpcRetry(label, fn, options = {}) {
  const attempts = Math.max(1, Number(options.attempts) || 5);
  const baseDelayMs = Math.max(10, Number(options.baseDelayMs) || 200);
  let lastError;
  for (let attempt = 1; attempt <= attempts; attempt += 1) {
    try {
      return await fn(attempt);
    } catch (error) {
      lastError = error;
      if (!isTransientRpcError(error) || attempt >= attempts) {
        throw error;
      }
      console.warn(
        `${label} transient RPC failure on attempt ${attempt}/${attempts}: ${
          error && error.message ? error.message : String(error)
        }`
      );
      await sleep(baseDelayMs * attempt);
    }
  }
  throw lastError;
}

function expSample(rand, rate) {
  if (rate <= 0) return Infinity;
  const u = Math.max(rand(), Number.EPSILON);
  return -Math.log(u) / rate;
}

function hashSeed(text) {
  let value = 2166136261;
  for (let i = 0; i < text.length; i += 1) {
    value ^= text.charCodeAt(i);
    value = Math.imul(value, 16777619);
  }
  return value >>> 0;
}

function deterministicExpMs(params, request, label, meanMs) {
  const seed =
    (Number(params.seed) >>> 0) ^
    hashSeed(`${label}:${request.epsilonLabel}:${request.index}:${request.requestId || ""}`);
  const rand = mulberry32(seed);
  return expSample(rand, 1 / meanMs);
}

function deterministicHttpDelayMs(shapeKey, meanMs, options = {}) {
  const safeMeanMs = positiveOrZero(meanMs);
  if (!safeMeanMs) return 0;
  const safeSegments = Math.max(1, Math.floor(Number(options.segments) || 1));
  const seed = Number(options.seed) >>> 0;
  const tailProbability = Math.min(0.95, Math.max(0, Number(options.tailProbability) || 0));
  const maxTailMultiplier = tailProbability > 0 ? (0.999 / tailProbability) : Infinity;
  const tailMultiplier = Math.max(1, Math.min(maxTailMultiplier, Number(options.tailMultiplier) || 1));
  const useTail = tailProbability > 0 && tailMultiplier > 1;
  const rand = mulberry32(((Number(seed) >>> 0) ^ hashSeed(String(shapeKey))) >>> 0);
  let total = 0;
  const meanPerSegmentMs = safeMeanMs / safeSegments;
  const shortMultiplier =
    useTail ? Math.max(0.001, (1 - tailProbability * tailMultiplier) / (1 - tailProbability)) : 1;
  for (let i = 0; i < safeSegments; i += 1) {
    let segmentMeanMs = meanPerSegmentMs;
    if (useTail) {
      segmentMeanMs *= rand() < tailProbability ? tailMultiplier : shortMultiplier;
    }
    total += expSample(rand, 1 / segmentMeanMs);
  }
  return total;
}

function buildHttpShapeQuery(request, label, config = {}) {
  const search = new URLSearchParams();
  search.set("shapeKey", `${label}:${request.epsilonLabel}:${request.index}:${request.requestId || ""}`);
  search.set("meanMs", String(positiveOrZero(config.meanMs)));
  search.set("segments", String(Math.max(1, Math.floor(Number(config.segments) || 1))));
  search.set("tailProbability", String(Math.min(0.95, Math.max(0, Number(config.tailProbability) || 0))));
  search.set("tailMultiplier", String(Math.max(1, Number(config.tailMultiplier) || 1)));
  return search.toString();
}

async function requestHttpWindowSeries(baseUrl, request, label, config = {}) {
  const hops = Math.max(1, Math.floor(Number(config.hops) || 1));
  const hopMeanMs = positiveOrZero(config.meanMs) / hops;
  for (let hop = 0; hop < hops; hop += 1) {
    const hopConfig = {
      ...config,
      meanMs: hopMeanMs,
      hops: 1,
    };
    const shape = buildHttpShapeQuery(request, `${label}:hop${hop + 1}`, hopConfig);
    await requestJson("GET", `${baseUrl}/shape/window?${shape}`);
  }
}

function httpDelayConfigFromUrl(url, fallbackLabel = "http-window") {
  const meanMs = positiveOrZero(url.searchParams.get("meanMs"));
  const segments = Math.max(1, Math.floor(Number(url.searchParams.get("segments")) || 1));
  const tailProbability = Math.min(0.95, Math.max(0, Number(url.searchParams.get("tailProbability")) || 0));
  const tailMultiplier = Math.max(1, Number(url.searchParams.get("tailMultiplier")) || 1);
  const shapeKey = url.searchParams.get("shapeKey") || `${fallbackLabel}:${Date.now()}`;
  return {
    meanMs,
    segments,
    tailProbability,
    tailMultiplier,
    shapeKey,
  };
}

async function applyHttpDelayFromUrl(url, fallbackLabel) {
  const config = httpDelayConfigFromUrl(url, fallbackLabel);
  const delayMs = deterministicHttpDelayMs(config.shapeKey, config.meanMs, {
    segments: config.segments,
    tailProbability: config.tailProbability,
    tailMultiplier: config.tailMultiplier,
    seed: ACTIVE_ARGS.seed,
  });
  if (delayMs > 0) await sleepPrecise(delayMs);
  return delayMs;
}

function httpShapeConfigFromParams(prefix, meanKey, params) {
  const prefixKey = meanKey.replace(/MeanMs$/, "");
  return {
    label: prefix,
    meanMs: positiveOrZero(params[meanKey]),
    hops: Math.max(1, Math.floor(Number(params[`${prefixKey}Hops`]) || 1)),
    segments: Math.max(1, Math.floor(Number(params[`${prefixKey}Segments`]) || Number(params.httpShapeSegments) || 1)),
    tailProbability: Math.min(
      0.95,
      Math.max(0, Number(params[`${prefixKey}TailProbability`]) || Number(params.httpShapeTailProbability) || 0)
    ),
    tailMultiplier: Math.max(
      1,
      Number(params[`${prefixKey}TailMultiplier`]) || Number(params.httpShapeTailMultiplier) || 1
    ),
  };
}

function dpkiProofHttpShapeConfig(params, request) {
  if (!request || request.kind === "management") return { label: "dpki-proof", meanMs: 0, hops: 1, segments: 1, tailProbability: 0, tailMultiplier: 1 };
  return httpShapeConfigFromParams("dpki-proof", "dpkiProofHttpMeanMs", params);
}

function dpkiAuthTransferHttpShapeConfig(params, request) {
  if (!request || request.kind === "management") {
    return { label: "dpki-auth-transfer", meanMs: 0, hops: 1, segments: 1, tailProbability: 0, tailMultiplier: 1 };
  }
  return httpShapeConfigFromParams("dpki-auth-transfer", "dpkiAuthTransferHttpMeanMs", params);
}

function dpkiOnchainExtraHttpShapeConfig(params, request) {
  if (!request || request.kind === "management" || !request.onChain || request.crossDomain) {
    return { label: "dpki-onchain-extra", meanMs: 0, hops: 1, segments: 1, tailProbability: 0, tailMultiplier: 1 };
  }
  return httpShapeConfigFromParams("dpki-onchain-extra", "dpkiOnchainExtraHttpMeanMs", params);
}

function dpkiCrossExtraHttpShapeConfig(params, request) {
  if (!request || request.kind === "management" || !request.crossDomain) {
    return { label: "dpki-cross-extra", meanMs: 0, hops: 1, segments: 1, tailProbability: 0, tailMultiplier: 1 };
  }
  return httpShapeConfigFromParams("dpki-cross-extra", "dpkiCrossExtraHttpMeanMs", params);
}

function dpkiManagementHttpShapeConfig(params) {
  return httpShapeConfigFromParams("dpki-management-verify", "dpkiManagementHttpMeanMs", params);
}

function dpkiManagementTransferHttpShapeConfig(params) {
  return httpShapeConfigFromParams("dpki-management-transfer", "dpkiManagementTransferHttpMeanMs", params);
}

function dpkiManagementExtraHttpShapeConfig(params) {
  return httpShapeConfigFromParams("dpki-management-extra", "dpkiManagementExtraHttpMeanMs", params);
}

function pkiAuthHttpShapeConfig(params, request) {
  if (!request || request.kind === "management") return { label: "pki-auth", meanMs: 0, hops: 1, segments: 1, tailProbability: 0, tailMultiplier: 1 };
  return httpShapeConfigFromParams("pki-auth", "pkiAuthHttpMeanMs", params);
}

function pkiAuthTransferHttpShapeConfig(params, request) {
  if (!request || request.kind === "management") {
    return { label: "pki-auth-transfer", meanMs: 0, hops: 1, segments: 1, tailProbability: 0, tailMultiplier: 1 };
  }
  return httpShapeConfigFromParams("pki-auth-transfer", "pkiAuthTransferHttpMeanMs", params);
}

function pkiCrossExtraHttpShapeConfig(params, request) {
  if (!request || request.kind === "management" || !request.crossDomain) {
    return { label: "pki-cross-extra", meanMs: 0, hops: 1, segments: 1, tailProbability: 0, tailMultiplier: 1 };
  }
  return httpShapeConfigFromParams("pki-cross-extra", "pkiCrossExtraHttpMeanMs", params);
}

function pkiManagementHttpShapeConfig(params) {
  return httpShapeConfigFromParams("pki-management-verify", "pkiManagementHttpMeanMs", params);
}

function pkiManagementTransferHttpShapeConfig(params) {
  return httpShapeConfigFromParams("pki-management-transfer", "pkiManagementTransferHttpMeanMs", params);
}

function pkiManagementExtraHttpShapeConfig(params) {
  return httpShapeConfigFromParams("pki-management-extra", "pkiManagementExtraHttpMeanMs", params);
}

function positiveOrZero(value) {
  const number = Number(value);
  return Number.isFinite(number) && number > 0 ? number : 0;
}

function modelAuthMeanMs(params) {
  const mu = Number(params.muAuth);
  const scaleMs = Number(params.timeScaleMs) || 1000;
  return mu > 0 ? scaleMs / mu : 0;
}

function modelManagementMeanMs(params) {
  const authMeanMs = modelAuthMeanMs(params);
  const q = Number(params.qManage);
  return authMeanMs > 0 && q > 0 ? authMeanMs / q : 0;
}

function requestServiceShapeMeanMs(params, modelName, request) {
  const mode = String(params.serviceShapeMode || "none").toLowerCase();
  if (mode === "none" || mode === "off" || mode === "disabled" || mode === "false") return 0;

  const authFallback = modelAuthMeanMs(params);
  const managementFallback = modelManagementMeanMs(params);

  if (modelName === "DPKI") {
    if (request.kind === "management") {
      return positiveOrZero(params.dpkiManagementShapeMeanMs) || managementFallback;
    }
    if (request.kind === "cross-domain") {
      return (
        positiveOrZero(params.dpkiCrossShapeMeanMs) ||
        positiveOrZero(params.dpkiOnchainShapeMeanMs) ||
        positiveOrZero(params.dpkiAuthShapeMeanMs) ||
        authFallback
      );
    }
    if (request.onChain) {
      return (
        positiveOrZero(params.dpkiOnchainShapeMeanMs) ||
        positiveOrZero(params.dpkiAuthShapeMeanMs) ||
        authFallback
      );
    }
    return (
      positiveOrZero(params.dpkiIntraOffchainShapeMeanMs) ||
      positiveOrZero(params.dpkiOffchainShapeMeanMs) ||
      positiveOrZero(params.dpkiAuthShapeMeanMs) ||
      authFallback
    );
  }

  if (modelName === "PKI") {
    if (request.kind === "management") {
      return positiveOrZero(params.pkiManagementShapeMeanMs) || managementFallback;
    }
    if (request.kind === "cross-domain") {
      return positiveOrZero(params.pkiCrossShapeMeanMs) || positiveOrZero(params.pkiAuthShapeMeanMs) || authFallback;
    }
    if (request.kind === "intra-pki") {
      return positiveOrZero(params.pkiIntraShapeMeanMs) || positiveOrZero(params.pkiAuthShapeMeanMs) || authFallback;
    }
    return positiveOrZero(params.pkiAuthShapeMeanMs) || authFallback;
  }

  return 0;
}

async function shapeElapsedServiceToTargetExponential(params, modelName, request, startMs, stageTimings) {
  const meanMs = requestServiceShapeMeanMs(params, modelName, request);
  if (!Number.isFinite(meanMs) || meanMs <= 0) return;
  const stageName = `${modelName.toLowerCase()}${request.kind
    .split("-")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join("")}TargetExponentialWait`;
  const targetMs = deterministicExpMs(params, request, `${stageName}:target`, meanMs);
  const elapsedMs = performance.now() - startMs;
  const waitMs = Math.max(0, targetMs - elapsedMs);
  if (waitMs > 0) {
    await timeStage(stageTimings, stageName, () => sleepPrecise(waitMs));
  } else {
    addStage(stageTimings, stageName, 0);
  }
}

function stableStringify(value) {
  if (Array.isArray(value)) {
    return `[${value.map(stableStringify).join(",")}]`;
  }
  if (value && typeof value === "object") {
    return `{${Object.keys(value)
      .sort()
      .map((key) => `${JSON.stringify(key)}:${stableStringify(value[key])}`)
      .join(",")}}`;
  }
  return JSON.stringify(value);
}

function ensureDir(dir) {
  fs.mkdirSync(dir, { recursive: true });
}

function csvEscape(value) {
  if (value === null || value === undefined || Number.isNaN(value)) return "";
  const text = String(value);
  return /[",\n]/.test(text) ? `"${text.replace(/"/g, '""')}"` : text;
}

function writeCsv(filePath, rows, columns) {
  const lines = [columns.join(",")];
  for (const row of rows) {
    lines.push(columns.map((col) => csvEscape(row[col])).join(","));
  }
  fs.writeFileSync(filePath, `${lines.join("\n")}\n`);
}

function addStage(stageTimings, name, durationMs) {
  stageTimings[name] = (stageTimings[name] || 0) + durationMs;
}

async function timeStage(stageTimings, name, fn) {
  const start = performance.now();
  try {
    return await fn();
  } finally {
    addStage(stageTimings, name, performance.now() - start);
  }
}

function timeStageSync(stageTimings, name, fn) {
  const start = performance.now();
  try {
    return fn();
  } finally {
    addStage(stageTimings, name, performance.now() - start);
  }
}

function mergeStageTimings(target, source) {
  if (!source || typeof source !== "object") return target;
  for (const [name, duration] of Object.entries(source)) {
    const numeric = Number(duration);
    if (Number.isFinite(numeric)) {
      addStage(target, name, numeric);
    }
  }
  return target;
}

async function applyDeterministicHttpWindowStage(stageTimings, stageName, request, label, config = {}) {
  const meanMs = positiveOrZero(config.meanMs);
  if (!meanMs) {
    addStage(stageTimings, stageName, 0);
    return 0;
  }
  const segments = Math.max(
    1,
    Math.floor((Number(config.segments) || 1) * Math.max(1, Math.floor(Number(config.hops) || 1)))
  );
  const shapeKey = `${label}:${request.epsilonLabel}:${request.index}:${request.requestId || ""}`;
  return timeStage(stageTimings, stageName, async () => {
    const delayMs = deterministicHttpDelayMs(shapeKey, meanMs, {
      segments,
      tailProbability: Math.min(0.95, Math.max(0, Number(config.tailProbability) || 0)),
      tailMultiplier: Math.max(1, Number(config.tailMultiplier) || 1),
      seed: ACTIVE_ARGS.seed,
    });
    if (delayMs > 0) await sleepPrecise(delayMs);
    return delayMs;
  });
}

async function requestHttpWindowStage(stageTimings, stageName, baseUrl, request, label, config = {}) {
  const meanMs = positiveOrZero(config.meanMs);
  if (!baseUrl || !meanMs) {
    addStage(stageTimings, stageName, 0);
    return 0;
  }
  return timeStage(stageTimings, stageName, () => requestHttpWindowSeries(baseUrl, request, label, config));
}

function median(values) {
  if (!values.length) return 0;
  const sorted = [...values].sort((a, b) => a - b);
  const middle = Math.floor(sorted.length / 2);
  return sorted.length % 2 ? sorted[middle] : (sorted[middle - 1] + sorted[middle]) / 2;
}

function ensurePlatformCaches(platform) {
  if (!platform.treeCache) platform.treeCache = new Map();
  if (!platform.proofCache) platform.proofCache = new Map();
}

function invalidateDomainCache(platform, domain) {
  ensurePlatformCaches(platform);
  platform.treeCache.delete(domain);
  for (const key of [...platform.proofCache.keys()]) {
    if (key.startsWith(`${domain}:`)) platform.proofCache.delete(key);
  }
}

function beginManagementUpdate(platform) {
  platform.managementInFlight = (platform.managementInFlight || 0) + 1;
}

function finishManagementUpdate(platform) {
  platform.managementInFlight = Math.max(0, (platform.managementInFlight || 0) - 1);
}

async function serializeManagementUpdate(platform, fn) {
  const previous = platform.managementChain || Promise.resolve();
  const current = previous.then(fn);
  platform.managementChain = current.catch(() => {});
  return current;
}

function compileContract() {
  const source = fs.readFileSync(CONTRACT_PATH, "utf8");
  const input = {
    language: "Solidity",
    sources: {
      "DPKIExperiment.sol": { content: source },
    },
    settings: {
      outputSelection: {
        "*": {
          "*": ["abi", "evm.bytecode.object"],
        },
      },
    },
  };
  const output = JSON.parse(solc.compile(JSON.stringify(input)));
  if (output.errors) {
    const serious = output.errors.filter((item) => item.severity === "error");
    for (const item of output.errors) {
      console.error(item.formattedMessage);
    }
    if (serious.length > 0) {
      throw new Error("Solidity compilation failed");
    }
  }
  const compiled = output.contracts["DPKIExperiment.sol"].DPKIExperiment;
  return {
    abi: compiled.abi,
    bytecode: `0x${compiled.evm.bytecode.object}`,
  };
}

class NonceManager {
  constructor(web3, address) {
    this.web3 = web3;
    this.address = address;
    this.nextNonce = null;
    this.initPromise = null;
    this.txChain = Promise.resolve();
  }

  async getNonce() {
    if (this.nextNonce === null) {
      if (!this.initPromise) {
        this.initPromise = this.web3.eth.getTransactionCount(this.address, "pending");
      }
      this.nextNonce = await this.initPromise;
    }
    const nonce = this.nextNonce;
    this.nextNonce += 1;
    return nonce;
  }

  async syncPending() {
    this.initPromise = this.web3.eth.getTransactionCount(this.address, "pending");
    this.nextNonce = await this.initPromise;
    this.initPromise = null;
    return this.nextNonce;
  }

  async runSerialized(fn) {
    const next = this.txChain.then(fn);
    this.txChain = next.catch(() => {});
    return next;
  }
}

function normalizePrivateKey(privateKey) {
  return privateKey.startsWith("0x") ? privateKey : `0x${privateKey}`;
}

function transactionSigningFields() {
  const chainId = Math.max(1, Math.floor(Number(ACTIVE_ARGS.chainId || ACTIVE_CHAIN_ID || 1)));
  return {
    chainId,
    gasPrice: String(ACTIVE_ARGS.fixedGasPriceWei ?? DEFAULTS.fixedGasPriceWei),
    common: {
      baseChain: "mainnet",
      hardfork: "istanbul",
      customChain: {
        name: "omnilink-local",
        networkId: chainId,
        chainId,
      },
    },
  };
}

function derivePrivateKey(seed) {
  return `0x${crypto.createHash("sha256").update(seed).digest("hex")}`;
}

function makeTxSenders(web3, args) {
  const count = Math.max(1, Math.floor(args.txSenders || 1));
  const privateKeys = [normalizePrivateKey(args.privateKey)];
  for (let index = 1; index < count; index += 1) {
    privateKeys.push(derivePrivateKey(`${args.privateKey}:chain33-dpki-sender:${index}`));
  }

  const seen = new Set();
  return privateKeys
    .map((privateKey, index) => {
      const account = web3.eth.accounts.privateKeyToAccount(privateKey);
      return {
        id: `sender-${index + 1}`,
        account: account.address,
        privateKey,
        nonceManager: new NonceManager(web3, account.address),
      };
    })
    .filter((sender) => {
      const key = sender.account.toLowerCase();
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    });
}

async function sendValueTx(web3, from, privateKey, nonceManager, to, valueWei) {
  return nonceManager.runSerialized(async () => {
    const nonce = await nonceManager.getNonce();
    const signed = await web3.eth.accounts.signTransaction(
      {
        from,
        to,
        value: valueWei,
        gas: 100000,
        nonce,
        ...transactionSigningFields(),
      },
      privateKey
    );
    return web3.eth.sendSignedTransaction(signed.rawTransaction);
  });
}

async function ensureTxSenderBalances(web3, args, txSenders, fundingNonceManager) {
  const minWei = web3.utils.toBN(web3.utils.toWei("5", "ether"));
  const fundWei = web3.utils.toWei("100", "ether");
  const fundingBalance = web3.utils.toBN(await web3.eth.getBalance(args.account));
  if (fundingBalance.lt(minWei)) {
    throw new Error(
      `funding account ${args.account} balance is too low for fixed-gas transactions: ${web3.utils.fromWei(
        fundingBalance,
        "ether"
      )} ETH`
    );
  }
  for (const sender of txSenders) {
    if (sender.account.toLowerCase() === args.account.toLowerCase()) continue;
    const balance = web3.utils.toBN(await web3.eth.getBalance(sender.account));
    if (balance.gte(minWei)) continue;
    console.log(`Funding ${sender.id} ${sender.account} for EVM workload transactions...`);
    await sendValueTx(web3, args.account, normalizePrivateKey(args.privateKey), fundingNonceManager, sender.account, fundWei);
  }
}

async function syncTxSenderNonces(txSenders) {
  for (const sender of txSenders) {
    const nonce = await sender.nonceManager.syncPending();
    console.log(`Synced ${sender.id} ${sender.account} pending nonce=${nonce}`);
  }
}

function requestJson(method, url, payload = null) {
  const endpoint = new URL(url);
  const body = payload === null ? null : JSON.stringify(payload);
  const transport = endpoint.protocol === "https:" ? https : http;

  return new Promise((resolve, reject) => {
    const req = transport.request(
      {
        protocol: endpoint.protocol,
        hostname: endpoint.hostname,
        port: endpoint.port,
        path: `${endpoint.pathname}${endpoint.search}`,
        method,
        headers: body
          ? {
              "content-type": "application/json",
              "content-length": Buffer.byteLength(body),
            }
          : {},
        timeout: 15000,
      },
      (res) => {
        const chunks = [];
        res.on("data", (chunk) => chunks.push(chunk));
        res.on("end", () => {
          const text = Buffer.concat(chunks).toString("utf8");
          try {
            const parsed = text ? JSON.parse(text) : {};
            if (res.statusCode >= 400) {
              reject(new Error(`${method} ${url} failed: ${text}`));
              return;
            }
            resolve(parsed);
          } catch (error) {
            reject(new Error(`${method} ${url} returned invalid JSON: ${error.message}`));
          }
        });
      }
    );

    req.on("timeout", () => req.destroy(new Error(`${method} ${url} timed out`)));
    req.on("error", reject);
    if (body) req.write(body);
    req.end();
  });
}

function readJsonRequestBody(req) {
  return new Promise((resolve, reject) => {
    const chunks = [];
    req.on("data", (chunk) => chunks.push(chunk));
    req.on("end", () => {
      if (!chunks.length) {
        resolve({});
        return;
      }
      try {
        resolve(JSON.parse(Buffer.concat(chunks).toString("utf8")));
      } catch (error) {
        reject(new Error(`invalid JSON request body: ${error.message}`));
      }
    });
    req.on("error", reject);
  });
}

function writeJsonResponse(res, statusCode, payload) {
  res.writeHead(statusCode, { "content-type": "application/json" });
  res.end(JSON.stringify(payload));
}

function isProcessAlive(pid) {
  if (!Number.isInteger(pid) || pid <= 0) return false;
  try {
    process.kill(pid, 0);
    return true;
  } catch (error) {
    return error && error.code === "EPERM";
  }
}

function readPid(pidPath) {
  try {
    const value = Number(String(fs.readFileSync(pidPath, "utf8")).trim());
    return Number.isInteger(value) ? value : null;
  } catch {
    return null;
  }
}

function sleepMs(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function waitForOmnilinkPowReady(web3, args, runtime) {
  const readyFile = path.join(runtime, "ready.txt");
  let lastBlockNumber = null;
  if (fs.existsSync(readyFile)) {
    try {
      lastBlockNumber = Number(await web3.eth.getBlockNumber());
    } catch {
      lastBlockNumber = null;
    }
    return { blockNumber: lastBlockNumber, warmedBy: "ready-file" };
  }
  const deadline = Date.now() + Math.max(0, Number(args.powWarmupMs) || 0);
  while (Date.now() < deadline) {
    try {
      lastBlockNumber = Number(await web3.eth.getBlockNumber());
      if (lastBlockNumber > 0) {
        return { blockNumber: lastBlockNumber, warmedBy: "block" };
      }
    } catch {
      // Keep polling until the node finishes RPC startup.
    }
    await sleepMs(500);
  }
  return { blockNumber: lastBlockNumber || 0, warmedBy: "warmup-timeout" };
}

function readOmnilinkPowRuntimeConfig(runtime) {
  const sidechainConfig = path.join(runtime, "configs", "side-a.toml");
  const configPath = fs.existsSync(sidechainConfig)
    ? sidechainConfig
    : path.join(runtime, "configs", "node0.toml");
  const config = {
    path: configPath,
    exists: fs.existsSync(configPath),
    mineEmpty: null,
    meanBlockMs: null,
    configuredLambdaBlockPerSec: null,
  };
  if (!config.exists) return config;
  const text = fs.readFileSync(configPath, "utf8");
  const mineEmptyMatch = text.match(/^\s*mineEmpty\s*=\s*(true|false)\s*$/im);
  const meanBlockMatch = text.match(/^\s*meanBlockMs\s*=\s*([0-9]+(?:\.[0-9]+)?)\s*$/im);
  if (mineEmptyMatch) config.mineEmpty = mineEmptyMatch[1].toLowerCase() === "true";
  if (meanBlockMatch) {
    config.meanBlockMs = Number(meanBlockMatch[1]);
    if (config.meanBlockMs > 0) {
      config.configuredLambdaBlockPerSec = 1000 / config.meanBlockMs;
    }
  }
  return config;
}

async function checkOmnilinkPowProcesses(web3, args) {
  const runtime = path.resolve(args.powRuntime);
  const runtimeConfig = readOmnilinkPowRuntimeConfig(runtime);
  if (runtimeConfig.mineEmpty !== true) {
    throw new Error(
      `Paper-faithful PoW measurement requires empty blocks (mineEmpty=true), got mineEmpty=${runtimeConfig.mineEmpty}. ` +
        `Restart Omnilink with omnilink-pow-4nodes/scripts/start-omnilink-pow-4nodes.ps1 -MineEmpty ` +
        `and keep MeanBlockMs at the target Poisson interval. Config=${runtimeConfig.path}`
    );
  }
  const chainManifestPath = path.join(runtime, "chains.json");
  const chainManifest = fs.existsSync(chainManifestPath)
    ? JSON.parse(fs.readFileSync(chainManifestPath, "utf8").replace(/^\uFEFF/, ""))
    : null;
  const nodes = [];
  if (Array.isArray(chainManifest) && chainManifest.length > 0) {
    for (const chain of chainManifest) {
      const pidPath = path.join(runtime, `${chain.name}.pid`);
      const pid = readPid(pidPath);
      nodes.push({ id: chain.name, pid, alive: isProcessAlive(pid), pidPath });
    }
  } else {
    for (let index = 0; index < 4; index += 1) {
      const pidPath = path.join(runtime, `node${index}.pid`);
      const pid = readPid(pidPath);
      nodes.push({ id: index, pid, alive: isProcessAlive(pid), pidPath });
    }
  }
  const configuredMaintainers = nodes.length;
  const activeMaintainers = nodes.filter((node) => node.alive).length;
  if (activeMaintainers !== configuredMaintainers) {
    throw new Error(
      `Omnilink requires every configured chain process to be active, got ` +
        `${activeMaintainers}/${configuredMaintainers}. Runtime=${runtime}`
    );
  }
  const ready = await waitForOmnilinkPowReady(web3, args, runtime);
  return {
    backend: "omnilink-pow",
    configuredMaintainers,
    activeMaintainers,
    rpc: args.rpc,
    chainJsonRpc: args.powRpc,
    runtime,
    runtimeConfig,
    currentBlockNumber: ready.blockNumber,
    readiness: ready.warmedBy,
    nodes: nodes.map((node) => ({ id: node.id, pid: node.pid, alive: node.alive })),
  };
}

async function observeChainBlockPosition(web3) {
  for (let attempt = 0; attempt < 10; attempt += 1) {
    try {
      return {
        blockNumber: Number(await web3.eth.getBlockNumber()),
        wallMs: Date.now(),
        monotonicMs: performance.now(),
      };
    } catch (error) {
      if (attempt === 9) {
        console.warn(`Warning: failed to observe chain block position after retries: ${error.message}`);
        break;
      }
      await sleepMs(250);
    }
  }
  return {
    blockNumber: 0,
    wallMs: Date.now(),
    monotonicMs: performance.now(),
  };
}

class PowChainClient {
  constructor(baseUrl) {
    this.baseUrl = baseUrl.replace(/\/+$/, "");
    this.isPow = true;
    this.state = {
      roots: new Map(),
      certificates: new Map(),
      authRecords: new Map(),
    };
    this.lastAppliedHash = null;
    this.lastAppliedHeight = -1;
  }

  async health() {
    const status = await requestJson("GET", `${this.baseUrl}/health`);
    if (!status || !status.ok) {
      throw new Error(`PoW backend is not healthy at ${this.baseUrl}`);
    }
    if (Number(status.configuredMaintainers) !== 4 || Number(status.activeMaintainers) !== 4) {
      throw new Error(
        `PoW backend must run 4 active maintainers, got ${status.activeMaintainers}/${status.configuredMaintainers}`
      );
    }
    return status;
  }

  async sendDpkiTx(kind, payload) {
    const submitted = await requestJson("POST", `${this.baseUrl}/transactions`, {
      from: "dpki-experiment",
      to: "pow-dpki-ledger",
      amount: 0,
      data: JSON.stringify({
        protocol: "dpki-real-experiment",
        kind,
        payload,
      }),
    });
    const tx = submitted.transaction;
    const status = await this.waitForTx(tx.id);
    await this.refreshState();
    return {
      transactionHash: tx.id,
      blockNumber: status.firstBlockNumber,
      blockHash: status.firstBlockHash,
      transactionIndex: 0,
      gasUsed: 0,
      powConfirmedMaintainers: status.confirmedMaintainers,
      powRequiredMaintainers: status.requiredMaintainers,
      powAllConfirmed: status.allConfirmed,
    };
  }

  async waitForTx(txId) {
    const deadline = performance.now() + 15000;
    let lastStatus = null;
    while (performance.now() < deadline) {
      lastStatus = await requestJson("GET", `${this.baseUrl}/transactions/${txId}`);
      if (lastStatus && lastStatus.allConfirmed) {
        return lastStatus;
      }
      await sleep(5);
    }
    throw new Error(`PoW transaction ${txId} was not confirmed by all maintainers: ${JSON.stringify(lastStatus)}`);
  }

  async refreshState() {
    const suffix = this.lastAppliedHeight >= 0 ? `?from=${this.lastAppliedHeight + 1}` : "";
    const best = await requestJson("GET", `${this.baseUrl}/chain${suffix}`);
    const chain = best.chain || [];
    const bestHeight = Number.isFinite(Number(best.bestHeight))
      ? Number(best.bestHeight)
      : (chain.length ? Number(chain[chain.length - 1].index) : this.lastAppliedHeight);
    const latestHash = best.bestHash || (chain.length ? chain[chain.length - 1].hash : null);
    if (latestHash && latestHash === this.lastAppliedHash) {
      return;
    }

    const roots = this.lastAppliedHeight >= 0 ? this.state.roots : new Map();
    const certificates = this.lastAppliedHeight >= 0 ? this.state.certificates : new Map();
    const authRecords = this.lastAppliedHeight >= 0 ? this.state.authRecords : new Map();
    for (const block of chain) {
      if (Number(block.index) <= this.lastAppliedHeight) continue;
      for (const tx of block.transactions || []) {
        let envelope;
        try {
          envelope = JSON.parse(tx.data || "{}");
        } catch (_error) {
          continue;
        }
        if (!envelope || envelope.protocol !== "dpki-real-experiment") continue;
        const payload = envelope.payload || {};
        if (envelope.kind === "putDomainRoot") {
          roots.set(payload.domainId, payload.repoRoot);
        } else if (envelope.kind === "putCertificate") {
          certificates.set(payload.certKey, payload);
        } else if (envelope.kind === "putCertificateAndDomainRoot") {
          certificates.set(payload.certKey, payload);
          roots.set(payload.domainId, payload.repoRoot);
        } else if (envelope.kind === "authenticate") {
          authRecords.set(payload.requestId, payload);
        }
      }
    }

    this.state = { roots, certificates, authRecords };
    this.lastAppliedHash = latestHash;
    this.lastAppliedHeight = bestHeight;
  }

  async putDomainRoot(domainId, repoRoot, domain) {
    return this.sendDpkiTx("putDomainRoot", { domainId, repoRoot, domain });
  }

  async putCertificate(web3, record) {
    return this.sendDpkiTx("putCertificate", this.certificatePayload(web3, record));
  }

  async putCertificateAndDomainRoot(web3, record, repoRoot) {
    return this.sendDpkiTx("putCertificateAndDomainRoot", {
      ...this.certificatePayload(web3, record),
      repoRoot,
    });
  }

  async authenticate(payload) {
    for (let index = 0; index < payload.certKeys.length; index += 1) {
      const cert = await this.certificate(payload.certKeys[index]);
      if (!cert || cert.certHash !== payload.certHashes[index]) {
        throw new Error(`PoW chain rejected auth before submit: invalid certificate ${payload.certKeys[index]}`);
      }
    }
    return this.sendDpkiTx("authenticate", payload);
  }

  async domainRoot(domainId) {
    const status = await requestJson("GET", `${this.baseUrl}/dpki/domain-roots/${encodeURIComponent(domainId)}`);
    return status.repoRoot || "0x0000000000000000000000000000000000000000000000000000000000000000";
  }

  async certificate(certKey) {
    const status = await requestJson("GET", `${this.baseUrl}/dpki/certificates/${encodeURIComponent(certKey)}`);
    return status && status.exists ? status.certificate : null;
  }

  async authRecord(requestId) {
    const status = await requestJson("GET", `${this.baseUrl}/dpki/auth-records/${encodeURIComponent(requestId)}`);
    return status && status.exists ? status.authRecord : null;
  }

  certificatePayload(web3, record) {
    return {
      certKey: record.key,
      domainId: web3.utils.keccak256(record.domain),
      subjectId: web3.utils.keccak256(record.subject),
      domain: record.domain,
      subject: record.subject,
      subjectAddress: record.account.address,
      certHash: record.certHash,
      state: "Valid",
      notBefore: record.cert.notBefore,
      notAfter: record.cert.notAfter,
    };
  }
}

async function deployContract(web3, abi, bytecode, account, privateKey, nonceManager) {
  const contract = new web3.eth.Contract(abi);
  const deploy = contract.deploy({ data: bytecode });
  const gasEstimate = await withRpcRetry("deployContract estimateGas", () => deploy.estimateGas({ from: account }));
  const tx = {
    from: account,
    data: deploy.encodeABI(),
    gas: Math.ceil(gasEstimate * 1.2),
    nonce: await withRpcRetry("deployContract nonce", () => nonceManager.getNonce()),
    ...transactionSigningFields(),
  };
  const signed = await web3.eth.accounts.signTransaction(tx, privateKey);
  const row = {
    method: "__deploy__",
    from: account,
    queuedWallMs: performance.now(),
  };
  const submitted = sendSignedTransactionWithBreakdown(web3, signed, row);
  await submitted.hashPromise;
  const receipt = await submitted.receiptPromise;
  return new web3.eth.Contract(abi, receipt.contractAddress);
}

function methodLabel(method) {
  if (method && method._method && method._method.name) return method._method.name;
  if (method && method._method && method._method.signature) return method._method.signature;
  return "unknown";
}

function rpcQuantityToNumber(value) {
  if (typeof value === "number") return value;
  if (typeof value === "string" && value.startsWith("0x")) return Number.parseInt(value, 16);
  return Number(value || 0);
}

function normalizeRpcReceipt(receipt) {
  return {
    ...receipt,
    blockNumber: rpcQuantityToNumber(receipt.blockNumber),
    transactionIndex: rpcQuantityToNumber(receipt.transactionIndex),
    gasUsed: rpcQuantityToNumber(receipt.gasUsed),
    status: typeof receipt.status === "boolean" ? receipt.status : rpcQuantityToNumber(receipt.status) !== 0,
  };
}

function isAcceptedRawTxError(error) {
  const message = String(error && error.message ? error.message : error).toLowerCase();
  return (
    message.includes("already known") ||
    message.includes("known transaction") ||
    message.includes("already imported") ||
    message.includes("transaction already") ||
    message.includes("already exists")
  );
}

async function submitRawTransactionFast(rawTransaction, localHash, row) {
  const startMs = performance.now();
  const attempts = Math.max(1, Math.floor(Number(ACTIVE_ARGS.rawTxSubmitRetries) || DEFAULTS.rawTxSubmitRetries));
  const timeoutMs = Math.max(1, Number(ACTIVE_ARGS.rawTxSubmitTimeoutMs) || DEFAULTS.rawTxSubmitTimeoutMs);
  row.submitAttempts = 0;
  row.submitTimeouts = 0;
  row.transactionHash = localHash;

  for (let attempt = 1; attempt <= attempts; attempt += 1) {
    row.submitAttempts = attempt;
    try {
      const result = await requestJsonRpc("eth_sendRawTransaction", [rawTransaction], timeoutMs);
      row.submitToHashMs = performance.now() - startMs;
      row.rpcTransactionHash = result || "";
      if (result && String(result).toLowerCase() !== String(localHash).toLowerCase()) {
        row.transactionHashMismatch = result;
      }
      return localHash;
    } catch (error) {
      row.lastSubmitError = error && error.message ? error.message : String(error);
      if (error && error.code === "RPC_TIMEOUT") {
        row.submitTimeouts += 1;
      } else if (isAcceptedRawTxError(error)) {
        row.submitAcceptedByError = true;
        row.submitToHashMs = performance.now() - startMs;
        return localHash;
      }
      if (attempt < attempts) await sleep(Math.min(10, timeoutMs));
    }
  }

  row.submitAssumedHash = true;
  row.submitToHashMs = performance.now() - startMs;
  return localHash;
}

async function waitForReceiptFast(transactionHash, row) {
  const timeoutMs = Math.max(1000, Number(ACTIVE_ARGS.rawTxReceiptTimeoutMs) || DEFAULTS.rawTxReceiptTimeoutMs);
  const pollMs = Math.max(1, Number(ACTIVE_ARGS.receiptPollMs) || DEFAULTS.receiptPollMs);
  const deadline = performance.now() + timeoutMs;
  row.receiptPolls = 0;
  while (performance.now() < deadline) {
    row.receiptPolls += 1;
    try {
      const receipt = await requestJsonRpc("eth_getTransactionReceipt", [transactionHash], Math.min(1000, timeoutMs));
      if (receipt) return normalizeRpcReceipt(receipt);
    } catch (error) {
      row.lastReceiptPollError = error && error.message ? error.message : String(error);
    }
    await sleep(pollMs);
  }
  throw new Error(`receipt not found for ${transactionHash} after ${timeoutMs}ms`);
}

function sendSignedTransactionWithBreakdown(web3, signedTransaction, row) {
  const sendStartMs = performance.now();
  row.sendStartMs = sendStartMs;
  const rawTransaction = signedTransaction.rawTransaction || signedTransaction;
  const localHash = signedTransaction.transactionHash || web3.utils.keccak256(rawTransaction);
  row.transactionHash = localHash;

  const hashPromise = submitRawTransactionFast(rawTransaction, localHash, row);
  const receiptPromise = hashPromise.then(async (hash) => {
    const hashMs = performance.now();
    row.hashWallMs = hashMs;
    const receipt = await waitForReceiptFast(hash, row);
    const receiptMs = performance.now();
    row.receiptWallMs = receiptMs;
    row.receiptTotalMs = receiptMs - sendStartMs;
    row.hashToReceiptMs = receiptMs - hashMs;
    row.blockNumber = receipt.blockNumber;
    row.transactionIndex = receipt.transactionIndex;
    row.gasUsed = receipt.gasUsed;
    row.status = receipt.status;
    traceEvent("RECEIPT", {
      sequence: row.sequence,
      method: row.method,
      transactionHash: receipt.transactionHash || hash,
      blockNumber: receipt.blockNumber,
      transactionIndex: receipt.transactionIndex,
      gasUsed: receipt.gasUsed,
      status: receipt.status,
      submitToHashMs: row.submitToHashMs,
      hashToReceiptMs: row.hashToReceiptMs,
      receiptPolls: row.receiptPolls,
    });
    return receipt;
  });

  return { hashPromise, receiptPromise };
}

async function sendContractTx(web3, method, account, privateKey, nonceManager) {
  const row = {
    sequence: chainTxSequence += 1,
    method: methodLabel(method),
    from: account,
    queuedWallMs: performance.now(),
  };
  chainTxBreakdowns.push(row);
  const submitted = await nonceManager.runSerialized(async () => {
    const lockStartMs = performance.now();
    row.serializationWaitMs = lockStartMs - row.queuedWallMs;
    let gasEstimate = "";
    let gasLimit = Math.max(21000, Math.floor(Number(ACTIVE_ARGS.fixedGasLimit) || DEFAULTS.fixedGasLimit));
    if (ACTIVE_ARGS.estimateGas) {
      const estimateStartMs = performance.now();
      gasEstimate = await method.estimateGas({ from: account });
      row.estimateGasMs = performance.now() - estimateStartMs;
      gasLimit = Math.max(Math.ceil(Number(gasEstimate) * 2) + 100000, gasLimit);
      row.gasMode = "estimated";
    } else {
      row.estimateGasMs = 0;
      row.gasMode = "fixed";
    }
    const nonceStartMs = performance.now();
    const nonce = await nonceManager.getNonce();
    row.nonceMs = performance.now() - nonceStartMs;
    const encodeStartMs = performance.now();
    const data = method.encodeABI();
    row.encodeMs = performance.now() - encodeStartMs;
    const tx = {
      from: account,
      to: method._parent._address,
      data,
      gas: gasLimit,
      nonce,
      ...transactionSigningFields(),
    };
    row.gasEstimate = gasEstimate;
    row.gasLimit = tx.gas;
    row.nonce = nonce;
    row.to = tx.to;
    const signStartMs = performance.now();
    const signed = await web3.eth.accounts.signTransaction(tx, privateKey);
    row.signMs = performance.now() - signStartMs;
    row.rawTxBytes = signed.rawTransaction ? (signed.rawTransaction.length - 2) / 2 : "";
    const submitted = sendSignedTransactionWithBreakdown(web3, signed, row);
    await submitted.hashPromise;
    row.lockHeldMs = performance.now() - lockStartMs;
    return { receiptPromise: submitted.receiptPromise };
  });
  const receipt = await submitted.receiptPromise;
  row.totalMs = performance.now() - row.queuedWallMs;
  return receipt;
}

function makeHasher(web3) {
  return {
    text(value) {
      return web3.utils.keccak256(String(value));
    },
    object(value) {
      return web3.utils.keccak256(stableStringify(value));
    },
    pair(left, right) {
      return web3.utils.soliditySha3(
        { type: "bytes32", value: left },
        { type: "bytes32", value: right }
      );
    },
  };
}

function deterministicAccount(web3, label) {
  const digest = crypto.createHash("sha256").update(`chain33-dpki:${label}`).digest("hex");
  return web3.eth.accounts.privateKeyToAccount(`0x${digest}`);
}

function certKey(hash, domain, subject) {
  return hash.text(`${domain}:${subject}`);
}

function x509PemHash(hash, x509Record) {
  if (!x509Record) return null;
  return hash.text(fs.readFileSync(x509Record.certPath, "utf8"));
}

function makeCertificate(web3, hash, domain, subject, issuer, role, x509Record = null) {
  const account = deterministicAccount(web3, `${domain}:${subject}`);
  const now = Math.floor(Date.now() / 1000);
  const cert = {
    version: "DPKI-paper-experiment-v1",
    domain,
    subject,
    issuer,
    role,
    address: account.address,
    publicKeyRef: hash.text(account.address),
    x509PemHash: x509PemHash(hash, x509Record),
    notBefore: now - 60,
    notAfter: now + 86400,
  };
  const record = {
    domain,
    subject,
    issuer,
    role,
    account,
    x509: x509Record,
    cert,
    key: certKey(hash, domain, subject),
    certHash: hash.object(cert),
  };
  traceEvent("CERTIFICATE", {
    domain,
    subject,
    issuer,
    role,
    address: account.address,
    certKey: record.key,
    certHash: record.certHash,
    x509PemHash: cert.x509PemHash,
    notBefore: cert.notBefore,
    notAfter: cert.notAfter,
  });
  return record;
}

function certificateBody(record) {
  return {
    version: record.cert.version,
    domain: record.cert.domain,
    subject: record.cert.subject,
    issuer: record.cert.issuer,
    role: record.cert.role,
    address: record.cert.address,
    publicKeyRef: record.cert.publicKeyRef,
    x509PemHash: record.cert.x509PemHash,
    notBefore: record.cert.notBefore,
    notAfter: record.cert.notAfter,
  };
}

function signCertificateRecord(web3, hash, record, issuerRecord) {
  const body = certificateBody(record);
  const message = stableStringify(body);
  record.cert.tbsHash = hash.object(body);
  record.cert.issuerAddress = issuerRecord.account.address;
  record.cert.issuerSignature = issuerRecord.account.sign(message).signature;
  record.certHash = hash.object({
    ...body,
    tbsHash: record.cert.tbsHash,
    issuerAddress: record.cert.issuerAddress,
    issuerSignature: record.cert.issuerSignature,
  });
  return record;
}

function findIssuerForCert(platform, record) {
  if (record.subject === record.issuer) {
    return record;
  }
  for (const records of platform.repos.values()) {
    const issuer = records.find((item) => item.subject === record.issuer);
    if (issuer) return issuer;
  }
  throw new Error(`missing issuer ${record.issuer} for ${record.subject}`);
}

function attachCertificateSignatures(web3, hash, platform) {
  const allRecords = [...platform.repos.values()].flat();
  for (const record of allRecords) {
    signCertificateRecord(web3, hash, record, findIssuerForCert(platform, record));
  }
}

function verifyCertificateSignature(web3, record, issuerRecord) {
  const now = Math.floor(Date.now() / 1000);
  if (now < record.cert.notBefore || now > record.cert.notAfter) return false;
  const recovered = web3.eth.accounts.recover(
    stableStringify(certificateBody(record)),
    record.cert.issuerSignature
  );
  return recovered.toLowerCase() === issuerRecord.account.address.toLowerCase();
}

function verifyCertificateIssuedBy(web3, platform, record) {
  return verifyCertificateSignature(web3, record, findIssuerForCert(platform, record));
}

function mptValueHash(hash, record) {
  return hash.object({
    key: record.key,
    certHash: record.certHash,
    state: "Valid",
  });
}

function mptNode() {
  return {
    valueHash: null,
    children: new Map(),
  };
}

function normalizeMptKey(key) {
  return key.replace(/^0x/i, "").toLowerCase();
}

function mptNodeHash(hash, valueHash, children) {
  return hash.object({
    valueHash: valueHash || null,
    children: [...children]
      .map(([nibble, childHash]) => ({ nibble, hash: childHash }))
      .sort((a, b) => a.nibble.localeCompare(b.nibble)),
  });
}

function insertMpt(root, key, valueHash) {
  let node = root;
  for (const nibble of normalizeMptKey(key)) {
    if (!node.children.has(nibble)) {
      node.children.set(nibble, mptNode());
    }
    node = node.children.get(nibble);
  }
  node.valueHash = valueHash;
}

function finalizeMpt(node, hash) {
  const childHashes = new Map();
  for (const [nibble, child] of node.children.entries()) {
    childHashes.set(nibble, finalizeMpt(child, hash));
  }
  node.hash = mptNodeHash(hash, node.valueHash, childHashes);
  return node.hash;
}

function buildMpt(records, hash) {
  const root = mptNode();
  for (const record of records) {
    insertMpt(root, record.key, mptValueHash(hash, record));
  }
  return {
    type: "mpt-hexary",
    root: finalizeMpt(root, hash),
    rootNode: root,
  };
}

function proofNode(node) {
  return {
    valueHash: node.valueHash,
    children: [...node.children.entries()]
      .map(([nibble, child]) => ({ nibble, hash: child.hash }))
      .sort((a, b) => a.nibble.localeCompare(b.nibble)),
  };
}

function mptProof(tree, key) {
  const proof = [];
  let node = tree.rootNode;
  proof.push(proofNode(node));
  for (const nibble of normalizeMptKey(key)) {
    node = node.children.get(nibble);
    if (!node) throw new Error(`missing MPT path for ${key}`);
    proof.push(proofNode(node));
  }
  return proof;
}

function verifyMpt(hash, key, expectedValueHash, proof, root) {
  const path = normalizeMptKey(key);
  let expectedNodeHash = root;
  for (let depth = 0; depth < proof.length; depth += 1) {
    const node = proof[depth];
    const childEntries = (node.children || []).map((child) => [child.nibble, child.hash]);
    const actualNodeHash = mptNodeHash(hash, node.valueHash || null, childEntries);
    if (actualNodeHash !== expectedNodeHash) {
      return false;
    }
    if (depth === path.length) {
      return node.valueHash === expectedValueHash;
    }
    const nextNibble = path[depth];
    const child = (node.children || []).find((item) => item.nibble === nextNibble);
    if (!child) {
      return false;
    }
    expectedNodeHash = child.hash;
  }
  return false;
}

function makePlatform(web3, hash, x509Platform) {
  const domains = ["main", "domain-a", "domain-b", MANAGEMENT_DOMAIN];
  const certs = [];
  certs.push(makeCertificate(web3, hash, "main", "G", "G", "governing-ca", findOpenSslCert(x509Platform, "main", "G")));
  certs.push(makeCertificate(web3, hash, "main", "S-A", "G", "service-ca", findOpenSslCert(x509Platform, "main", "S-A")));
  certs.push(makeCertificate(web3, hash, "main", "S-B", "G", "service-ca", findOpenSslCert(x509Platform, "main", "S-B")));
  for (let i = 1; i <= 8; i += 1) {
    certs.push(
      makeCertificate(web3, hash, "domain-a", `EA-${i}`, "S-A", "entity", findOpenSslCert(x509Platform, "domain-a", `EA-${i}`))
    );
    certs.push(
      makeCertificate(web3, hash, "domain-b", `EB-${i}`, "S-B", "entity", findOpenSslCert(x509Platform, "domain-b", `EB-${i}`))
    );
  }
  for (let i = 1; i <= MANAGEMENT_POOL_SIZE; i += 1) {
    const subject = `MGMT-SLOT-${i}`;
    certs.push(
      makeCertificate(
        web3,
        hash,
        MANAGEMENT_DOMAIN,
        subject,
        "S-A",
        "entity",
        findOpenSslCert(x509Platform, MANAGEMENT_DOMAIN, subject)
      )
    );
  }
  const repos = new Map();
  for (const domain of domains) {
    repos.set(domain, certs.filter((cert) => cert.domain === domain));
  }
  const platform = { certs, repos, x509: x509Platform };
  attachCertificateSignatures(web3, hash, platform);
  return platform;
}

function getRepoTree(platform, hash, domain) {
  ensurePlatformCaches(platform);
  if (!platform.treeCache.has(domain)) {
    platform.treeCache.set(domain, buildMpt(platform.repos.get(domain) || [], hash));
  }
  return platform.treeCache.get(domain);
}

function getRepoProof(platform, hash, domain, record) {
  ensurePlatformCaches(platform);
  const key = `${domain}:${record.key}`;
  if (!platform.proofCache.has(key)) {
    platform.proofCache.set(key, mptProof(getRepoTree(platform, hash, domain), record.key));
  }
  return platform.proofCache.get(key);
}

function dpkiProofResponseBody(payload) {
  return {
    domain: payload.domain,
    certKey: payload.certKey,
    root: payload.root,
    items: payload.items,
    signerDomain: payload.signerDomain,
    signerSubject: payload.signerSubject,
  };
}

function signDpkiProofPayload(payload, signerRecord) {
  if (!signerRecord || !signerRecord.x509 || !signerRecord.x509.keyPath) {
    throw new Error(`missing DPKI proof signer key for ${signerRecord ? `${signerRecord.domain}/${signerRecord.subject}` : "unknown signer"}`);
  }
  const sign = crypto.createSign("sha256");
  sign.update(stableStringify(dpkiProofResponseBody(payload)));
  sign.end();
  return sign.sign(fs.readFileSync(signerRecord.x509.keyPath), "base64");
}

function buildDpkiProofPayload(platform, hash, domain, certKey) {
  const record = (platform.repos.get(domain) || []).find((item) => item.key === certKey);
  if (!record) {
    const error = new Error(`missing DPKI proof target ${domain}/${certKey}`);
    error.statusCode = 404;
    throw error;
  }
  const tree = getRepoTree(platform, hash, domain);
  const proof = getRepoProof(platform, hash, domain, record);
  const signer = findIssuerForCert(platform, record);
  const payload = {
    domain,
    certKey,
    root: tree.root,
    items: proof,
    proofNodes: proof.length,
    signerDomain: signer.domain,
    signerSubject: signer.subject,
  };
  payload.signatureBase64 = signDpkiProofPayload(payload, signer);
  return payload;
}

function verifyDpkiProofPayload(platform, source, payload, stageTimings, stageNames = {}) {
  const expectedSignerDomain = source.x509 ? source.x509.issuerDomain : null;
  const expectedSignerSubject = source.x509 ? source.x509.issuerSubject : null;
  if (
    expectedSignerDomain &&
    expectedSignerSubject &&
    (payload.signerDomain !== expectedSignerDomain || payload.signerSubject !== expectedSignerSubject)
  ) {
    return false;
  }
  const signer = findOpenSslCert(platform.x509, payload.signerDomain, payload.signerSubject);
  if (!signer || !signer.pubKeyPath) {
    throw new Error(`missing DPKI proof signer public key for ${payload.signerDomain}/${payload.signerSubject}`);
  }
  verifyOpenSslCertificateStep(
    platform.x509,
    payload.signerDomain,
    payload.signerSubject,
    stageTimings,
    stageNames.signerCertVerify || "dpkiMptProofSignerCertVerify"
  );
  return timeStageSync(stageTimings, stageNames.responseVerify || "dpkiMptProofResponseVerify", () => {
    const verify = crypto.createVerify("sha256");
    verify.update(stableStringify(dpkiProofResponseBody(payload)));
    verify.end();
    return verify.verify(
      fs.readFileSync(signer.pubKeyPath),
      Buffer.from(String(payload.signatureBase64 || ""), "base64")
    );
  });
}

function dpkiProofEnvelopeToProof(payload) {
  return {
    type: "mpt-hexary",
    root: payload.root,
    items: payload.items || [],
  };
}

async function chooseDpkiProofPort(platform) {
  const base = Number(platform.dpkiProofBasePort) || 20080;
  for (let offset = 0; offset < 5000; offset += 1) {
    const port = base + platform.dpkiProofPortOffset + offset;
    if (await canListen(port)) {
      platform.dpkiProofPortOffset += offset + 1;
      return port;
    }
  }
  throw new Error(`could not find a free DPKI proof port near ${base}`);
}

async function startDpkiProofResponder(platform, hash, args) {
  if (platform.dpkiProofResponder) return platform.dpkiProofResponder;
  platform.dpkiProofBasePort = Number(args.dpkiProofBasePort) || 20080;
  platform.dpkiProofPortOffset = platform.dpkiProofPortOffset || 0;
  const port = await chooseDpkiProofPort(platform);
  const server = http.createServer((req, res) => {
    (async () => {
      const url = new URL(req.url || "/", `http://127.0.0.1:${port}`);
      const parts = url.pathname.split("/").filter(Boolean).map((part) => decodeURIComponent(part));
      if (req.method === "GET" && parts.length === 2 && parts[0] === "shape" && parts[1] === "window") {
        const delayMs = await applyHttpDelayFromUrl(url, "dpki-http-window");
        writeJsonResponse(res, 200, { ok: true, delayMs });
        return;
      }
      if (req.method === "GET" && parts.length === 4 && parts[0] === "dpki" && parts[1] === "proofs") {
        await applyHttpDelayFromUrl(url, "dpki-proof");
        const payload = buildDpkiProofPayload(platform, hash, parts[2], parts[3]);
        writeJsonResponse(res, 200, payload);
        return;
      }
      if (req.method === "POST" && parts.length === 2 && parts[0] === "dpki" && parts[1] === "auth-execute") {
        const body = await readJsonRequestBody(req);
        const request = body.request || {};
        const stageTimings = {};
        const localParams = {
          ...ACTIVE_ARGS,
          dpkiProofReadMode: "local",
        };
        const stageNames = body.stageNames || {};
        await applyDeterministicHttpWindowStage(
          stageTimings,
          "dpkiOnchainExtraHttpWindow",
          request,
          "dpki-onchain-extra",
          dpkiOnchainExtraHttpShapeConfig(ACTIVE_ARGS, request)
        );
        await applyDeterministicHttpWindowStage(
          stageTimings,
          "dpkiCrossExtraHttpWindow",
          request,
          "dpki-cross-extra",
          dpkiCrossExtraHttpShapeConfig(ACTIVE_ARGS, request)
        );
        const httpWindowStage = body.httpWindowStage || stageNames.httpWindow || "dpkiAuthHttpWindow";
        await applyDeterministicHttpWindowStage(
          stageTimings,
          httpWindowStage,
          request,
          "dpki-auth",
          dpkiProofHttpShapeConfig(ACTIVE_ARGS, request)
        );
        if (!platform.runtimeWeb3 || !platform.runtimeContract) {
          throw new Error("DPKI auth executor is missing runtime web3/contract context");
        }
        const { proof } = await runDpkiMerkleAuthExecution(
          platform.runtimeWeb3,
          platform.runtimeContract,
          platform,
          hash,
          request,
          localParams,
          stageTimings,
          stageNames,
          body.canRetry !== false,
          (source, currentRequest, currentStageTimings, currentStageNames) =>
            responderLocalSignedProofForDpkiExecution(
              platform,
              hash,
              source,
              currentRequest,
              currentStageTimings,
              currentStageNames
            )
        );
        writeJsonResponse(res, 200, {
          ok: true,
          stageTimings,
          proofNodes: proof.items.length,
          chainReads: 1,
          verifiedCertificateSteps: 1,
        });
        return;
      }
      if (req.method === "POST" && parts.length === 2 && parts[0] === "dpki" && parts[1] === "management-execute") {
        const body = await readJsonRequestBody(req);
        const request = body.request || {};
        const stageTimings = {};
        await applyDeterministicHttpWindowStage(
          stageTimings,
          "dpkiManagementExtraHttpWindow",
          request,
          "dpki-management-extra",
          dpkiManagementExtraHttpShapeConfig(ACTIVE_ARGS)
        );
        await applyDeterministicHttpWindowStage(
          stageTimings,
          "dpkiManagementHttpWindow",
          request,
          "dpki-management",
          dpkiManagementHttpShapeConfig(ACTIVE_ARGS)
        );
        if (!platform.runtimeWeb3 || !platform.runtimeContract || !platform.runtimeNonceManager) {
          throw new Error("DPKI management executor is missing runtime context");
        }
        const result = await managementRequestCore(
          platform.runtimeWeb3,
          platform.runtimeContract,
          platform.runtimeAccount,
          platform.runtimePrivateKey,
          platform.runtimeNonceManager,
          platform,
          hash,
          request,
          stageTimings,
          { includePostHttpWindow: false }
        );
        writeJsonResponse(res, 200, {
          ok: true,
          stageTimings: result.stageTimings,
          receipts: result.receipts || [],
          chainReads: result.chainReads || 0,
          verifiedCertificateSteps: result.verifiedCertificateSteps || 2,
        });
        return;
      }
      writeJsonResponse(res, 404, { error: "not found" });
    })().catch((error) => {
      writeJsonResponse(res, error.statusCode || 500, { error: error.message });
    });
  });
  await new Promise((resolve, reject) => {
    server.once("error", reject);
    server.listen(port, "127.0.0.1", () => {
      server.off("error", reject);
      resolve();
    });
  });
  const responder = {
    server,
    port,
    baseUrl: `http://127.0.0.1:${port}`,
  };
  platform.dpkiProofResponder = responder;
  DPKI_PROOF_PLATFORMS.add(platform);
  return responder;
}

function stopDpkiProofResponder(platform) {
  if (!platform || !platform.dpkiProofResponder) return;
  const responder = platform.dpkiProofResponder;
  platform.dpkiProofResponder = null;
  DPKI_PROOF_PLATFORMS.delete(platform);
  try {
    responder.server.close();
  } catch (_error) {
    // Best-effort cleanup.
  }
}

function cleanupDpkiProofResponders() {
  for (const platform of [...DPKI_PROOF_PLATFORMS]) {
    stopDpkiProofResponder(platform);
  }
}

async function choosePkiServicePort(platform) {
  const base = Number(platform.pkiServiceBasePort) || 21080;
  for (let offset = 0; offset < 5000; offset += 1) {
    const port = base + (platform.pkiServicePortOffset || 0) + offset;
    if (await canListen(port)) {
      platform.pkiServicePortOffset = (platform.pkiServicePortOffset || 0) + offset + 1;
      return port;
    }
  }
  throw new Error(`could not find a free PKI service port near ${base}`);
}

async function startPkiServiceResponder(platform, args) {
  if (platform.pkiServiceResponder) return platform.pkiServiceResponder;
  platform.pkiServiceBasePort = Number(args.pkiServiceBasePort) || 21080;
  platform.pkiServicePortOffset = platform.pkiServicePortOffset || 0;
  const port = await choosePkiServicePort(platform);
  const server = http.createServer((req, res) => {
    (async () => {
      const url = new URL(req.url || "/", `http://127.0.0.1:${port}`);
      const parts = url.pathname.split("/").filter(Boolean).map((part) => decodeURIComponent(part));
      if (req.method === "GET" && parts.length === 2 && parts[0] === "shape" && parts[1] === "window") {
        const delayMs = await applyHttpDelayFromUrl(url, "pki-http-window");
        writeJsonResponse(res, 200, { ok: true, delayMs });
        return;
      }
      if (req.method === "POST" && parts.length === 2 && parts[0] === "pki" && parts[1] === "auth-execute") {
        const body = await readJsonRequestBody(req);
        const request = body.request || {};
        const stageTimings = {};
        await applyDeterministicHttpWindowStage(
          stageTimings,
          "pkiCrossExtraHttpWindow",
          request,
          "pki-cross-extra",
          pkiCrossExtraHttpShapeConfig(ACTIVE_ARGS, request)
        );
        await applyDeterministicHttpWindowStage(
          stageTimings,
          "pkiAuthHttpWindow",
          request,
          "pki-auth",
          pkiAuthHttpShapeConfig(ACTIVE_ARGS, request)
        );
        const result = await pkiAuthRequestCore(platform, request, ACTIVE_ARGS, stageTimings);
        writeJsonResponse(res, 200, {
          ok: true,
          stageTimings: result.stageTimings,
          verifiedCertificateSteps: result.verifiedCertificateSteps,
        });
        return;
      }
      if (req.method === "POST" && parts.length === 2 && parts[0] === "pki" && parts[1] === "management-execute") {
        const body = await readJsonRequestBody(req);
        const request = body.request || {};
        const stageTimings = {};
        await applyDeterministicHttpWindowStage(
          stageTimings,
          "pkiManagementExtraHttpWindow",
          request,
          "pki-management-extra",
          pkiManagementExtraHttpShapeConfig(ACTIVE_ARGS)
        );
        await applyDeterministicHttpWindowStage(
          stageTimings,
          "pkiManagementHttpWindow",
          request,
          "pki-management",
          pkiManagementHttpShapeConfig(ACTIVE_ARGS)
        );
        const result = await pkiManagementRequestCore(platform, request, stageTimings, { includeHttpWindow: false });
        writeJsonResponse(res, 200, {
          ok: true,
          stageTimings: result.stageTimings,
          verifiedCertificateSteps: result.verifiedCertificateSteps,
        });
        return;
      }
      writeJsonResponse(res, 404, { error: "not found" });
    })().catch((error) => {
      writeJsonResponse(res, error.statusCode || 500, { error: error.message });
    });
  });
  await new Promise((resolve, reject) => {
    server.once("error", reject);
    server.listen(port, "127.0.0.1", () => {
      server.off("error", reject);
      resolve();
    });
  });
  const responder = {
    server,
    port,
    baseUrl: `http://127.0.0.1:${port}`,
  };
  platform.pkiServiceResponder = responder;
  PKI_SERVICE_PLATFORMS.add(platform);
  return responder;
}

function stopPkiServiceResponder(platform) {
  if (!platform || !platform.pkiServiceResponder) return;
  const responder = platform.pkiServiceResponder;
  platform.pkiServiceResponder = null;
  PKI_SERVICE_PLATFORMS.delete(platform);
  try {
    responder.server.close();
  } catch (_error) {
    // Best-effort cleanup.
  }
}

function cleanupPkiServiceResponders() {
  for (const platform of [...PKI_SERVICE_PLATFORMS]) {
    stopPkiServiceResponder(platform);
  }
}

function findCert(platform, domain, subject) {
  const cert = (platform.repos.get(domain) || []).find((item) => item.subject === subject);
  if (!cert) throw new Error(`missing cert ${domain}/${subject}`);
  return cert;
}

async function putCertOnChain(web3, contract, account, privateKey, nonceManager, record) {
  if (contract && contract.isPow) {
    return contract.putCertificate(web3, record);
  }
  return sendContractTx(
    web3,
    contract.methods.putCertificate(
      record.key,
      web3.utils.keccak256(record.domain),
      web3.utils.keccak256(record.subject),
      record.account.address,
      record.certHash,
      record.cert.notBefore,
      record.cert.notAfter
    ),
    account,
    privateKey,
    nonceManager
  );
}

async function putCertAndRootOnChain(web3, contract, account, privateKey, nonceManager, record, repoRoot) {
  if (contract && contract.isPow) {
    return contract.putCertificateAndDomainRoot(web3, record, repoRoot);
  }
  return sendContractTx(
    web3,
    contract.methods.putCertificateAndDomainRoot(
      record.key,
      web3.utils.keccak256(record.domain),
      web3.utils.keccak256(record.subject),
      record.account.address,
      record.certHash,
      record.cert.notBefore,
      record.cert.notAfter,
      repoRoot
    ),
    account,
    privateKey,
    nonceManager
  );
}

async function verifyDpkiManagementRepositoryUpdate(web3, contract, platform, hash, record, expectedRoot, request, stageTimings) {
  return timeStage(stageTimings, "dpkiManagementRepositoryHttpVerify", async () => {
    if (platform.dpkiProofResponder && platform.dpkiProofResponder.baseUrl) {
      await requestHttpWindowSeries(
        platform.dpkiProofResponder.baseUrl,
        request,
        "dpki-management-verify",
        dpkiManagementHttpShapeConfig(ACTIVE_ARGS)
      );
    }
    const records = platform.repos.get(MANAGEMENT_DOMAIN) || [];
    const stored = records.find((item) => item.subject === record.subject);
    if (!stored || stored.certHash !== record.certHash) {
      throw new Error(`DPKI management repo does not contain updated cert ${record.subject}`);
    }

    const tree = buildMpt(records, hash);
    if (tree.root.toLowerCase() !== expectedRoot.toLowerCase()) {
      throw new Error(`DPKI management repo root mismatch after updating ${record.subject}`);
    }
    const proof = mptProof(tree, record.key);
    const okProof = verifyMpt(hash, record.key, mptValueHash(hash, record), proof, expectedRoot);
    if (!okProof) {
      throw new Error(`DPKI management repo proof failed after updating ${record.subject}`);
    }

    const cachedRoot = domainRootFromCache(platform, hash, MANAGEMENT_DOMAIN);
    if (cachedRoot.toLowerCase() !== expectedRoot.toLowerCase()) {
      throw new Error(`DPKI management cached root mismatch after updating ${record.subject}`);
    }
    return true;
  });
}

async function syncRootsAndCerts(web3, contract, account, privateKey, nonceManager, platform, hash) {
  for (const [domain, records] of platform.repos.entries()) {
    const tree = buildMpt(records, hash);
    if (contract && contract.isPow) {
      await contract.putDomainRoot(web3.utils.keccak256(domain), tree.root, domain);
    } else {
      await sendContractTx(
        web3,
        contract.methods.putDomainRoot(web3.utils.keccak256(domain), tree.root),
        account,
        privateKey,
        nonceManager
      );
    }
    for (const record of records) {
      await putCertOnChain(web3, contract, account, privateKey, nonceManager, record);
    }
  }
}

function signAuthMessage(web3, sourceCert, targetCert, proof, nonce) {
  const message = stableStringify({
    source: sourceCert.subject,
    target: targetCert.subject,
    sourceDomain: sourceCert.domain,
    targetDomain: targetCert.domain,
    certHash: sourceCert.certHash,
    proofRoot: proof.root,
    nonce,
  });
  return {
    message,
    signature: sourceCert.account.sign(message).signature,
  };
}

function verifySignedAuth(web3, sourceCert, signed) {
  const recovered = web3.eth.accounts.recover(signed.message, signed.signature);
  return recovered.toLowerCase() === sourceCert.account.address.toLowerCase();
}

function dpkiOpenSslAssertion(source, target, request, stageTimings, stagePrefix) {
  if (!source.x509 || !source.x509.keyPath || !source.x509.pubKeyPath) {
    throw new Error(`missing DPKI X.509 key material for ${source.domain}/${source.subject}`);
  }
  const safeId = opensslName(
    `${request.epsilon}_${request.index}_${request.nonce}_${stagePrefix}_${source.domain}_${source.subject}`
  );
  const messagePath = path.join(path.dirname(source.x509.certPath), `${safeId}.msg.txt`);
  const signaturePath = path.join(path.dirname(source.x509.certPath), `${safeId}.sig.bin`);
  fs.writeFileSync(
    messagePath,
    stableStringify({
      source: source.subject,
      target: target.subject,
      sourceDomain: source.domain,
      targetDomain: target.domain,
      sourceCertHash: source.certHash,
      targetCertHash: target.certHash,
      assertionStage: stagePrefix,
      nonce: request.nonce,
    })
  );
  runOpenSsl(["dgst", "-sha256", "-sign", source.x509.keyPath, "-out", signaturePath, messagePath], stageTimings, `${stagePrefix}Sign`);
  runOpenSsl(
    ["dgst", "-sha256", "-verify", source.x509.pubKeyPath, "-signature", signaturePath, messagePath],
    stageTimings,
    `${stagePrefix}Verify`
  );
  return true;
}

async function domainRootOnChain(web3, contract, hash, domain) {
  if (contract && contract.isPow) {
    return contract.domainRoot(web3.utils.keccak256(domain));
  }
  return contract.methods.domainRoots(web3.utils.keccak256(domain)).call();
}

function domainRootFromCache(platform, hash, domain) {
  if (!platform.domainRootCache) platform.domainRootCache = new Map();
  if (!platform.domainRootCache.has(domain)) {
    platform.domainRootCache.set(domain, getRepoTree(platform, hash, domain).root);
  }
  return platform.domainRootCache.get(domain);
}

async function domainRootForDpkiExecution(web3, contract, platform, hash, domain, params, stageTimings, stageNames = {}) {
  const mode = String(params.dpkiRootReadMode || "chain").toLowerCase();
  if (mode === "cache" || mode === "cached") {
    return timeStageSync(
      stageTimings,
      stageNames.cachedRootRead || "dpkiCachedRootRead",
      () => domainRootFromCache(platform, hash, domain)
    );
  }
  return timeStage(
    stageTimings,
    stageNames.chainRootRead || "dpkiChainRootRead",
    () => domainRootOnChain(web3, contract, hash, domain)
  );
}

async function proofForDpkiExecution(platform, hash, source, request, params, stageTimings, stageNames = {}) {
  const mode = String(params.dpkiProofReadMode || "http").toLowerCase();
  if (mode === "local" || mode === "cache" || mode === "cached") {
    return timeStageSync(stageTimings, stageNames.localProof || "dpkiMptCacheAndProof", () => {
      const tree = getRepoTree(platform, hash, source.domain);
      return {
        type: tree.type,
        root: tree.root,
        items: getRepoProof(platform, hash, source.domain, source),
      };
    });
  }
  if (!platform.dpkiProofResponder || !platform.dpkiProofResponder.baseUrl) {
    throw new Error("DPKI proof responder is not running; use --dpki-proof-read-mode local to disable HTTP proof reads");
  }
  const proofConfig = dpkiProofHttpShapeConfig(params, request);
  const response = await timeStage(stageTimings, stageNames.httpProof || "dpkiMptProofHttpQuery", async () => {
    const hops = Math.max(1, Math.floor(Number(proofConfig.hops) || 1));
    if (hops > 1) {
      await requestHttpWindowSeries(
        platform.dpkiProofResponder.baseUrl,
        request,
        stageNames.httpProof || "dpkiMptProofHttpQuery",
        {
          ...proofConfig,
          meanMs: proofConfig.meanMs * ((hops - 1) / hops),
          hops: hops - 1,
        }
      );
    }
    const shape = buildHttpShapeQuery(request, stageNames.httpProof || "dpkiMptProofHttpQuery", {
      ...proofConfig,
      meanMs: proofConfig.meanMs / hops,
      hops: 1,
    });
    const url =
      `${platform.dpkiProofResponder.baseUrl}/dpki/proofs/` +
      `${encodeURIComponent(source.domain)}/${encodeURIComponent(source.key)}?${shape}`;
    return requestJson("GET", url);
  });
  const ok = verifyDpkiProofPayload(platform, source, response, stageTimings, {
    signerCertVerify: stageNames.proofSignerCertVerify,
    responseVerify: stageNames.proofResponseVerify,
  });
  if (!ok) {
    throw new Error(`DPKI proof signer mismatch for ${source.domain}/${source.subject}`);
  }
  return dpkiProofEnvelopeToProof(response);
}

async function responderLocalSignedProofForDpkiExecution(platform, hash, source, request, stageTimings, stageNames = {}) {
  const payload = timeStageSync(stageTimings, stageNames.localProof || "dpkiMptCacheAndProof", () =>
    buildDpkiProofPayload(platform, hash, source.domain, source.key)
  );
  const ok = verifyDpkiProofPayload(platform, source, payload, stageTimings, {
    signerCertVerify: stageNames.proofSignerCertVerify,
    responseVerify: stageNames.proofResponseVerify,
  });
  if (!ok) {
    throw new Error(`DPKI proof signer mismatch for ${source.domain}/${source.subject}`);
  }
  return dpkiProofEnvelopeToProof(payload);
}

async function waitForPlatformStable(platform) {
  const deadline = performance.now() + 5000;
  while ((platform.managementInFlight || 0) > 0 && performance.now() < deadline) {
    await sleep(10);
  }
  if (platform.managementChain) {
    await platform.managementChain.catch(() => {});
  }
  return platform;
}

async function runDpkiMerkleAuthExecution(
  web3,
  contract,
  platform,
  hash,
  request,
  params,
  stageTimings,
  stageNames = {},
  canRetry = true,
  proofLoader = null
) {
  let source;
  let target;
  let proof;
  let okProof = false;
  let okCertificate = false;
  let okAssertion = false;
  let okSignature = false;

  async function verifyAttempt(allowRetry) {
    source = findCert(platform, request.sourceDomain, request.sourceSubject);
    target = findCert(platform, request.targetDomain, request.targetSubject);
    proof = proofLoader
      ? await proofLoader(source, request, stageTimings, stageNames)
      : await proofForDpkiExecution(platform, hash, source, request, params, stageTimings, stageNames);
    const onChainRoot = await domainRootForDpkiExecution(
      web3,
      contract,
      platform,
      hash,
      source.domain,
      params,
      stageTimings,
      stageNames
    );
    const okRoot = String(onChainRoot).toLowerCase() === String(proof.root).toLowerCase();
    if (!okRoot && allowRetry) {
      addStage(stageTimings, stageNames.rootMismatchRetry || "dpkiRootMismatchRetry", 1);
      await timeStage(
        stageTimings,
        stageNames.waitManagementOnRootMismatch || "dpkiWaitManagementOnRootMismatch",
        () => waitForPlatformStable(platform)
      );
      invalidateDomainCache(platform, source.domain);
      if (platform.domainRootCache) platform.domainRootCache.delete(source.domain);
      return verifyAttempt(false);
    }
    okProof =
      okRoot &&
      timeStageSync(
        stageTimings,
        stageNames.mptVerify || "dpkiMptVerify",
        () => verifyMpt(hash, source.key, mptValueHash(hash, source), proof.items, proof.root)
      );
    okCertificate = Boolean(
      verifyOpenSslCertificateStep(
        platform.x509,
        source.domain,
        source.subject,
        stageTimings,
        stageNames.certVerify || "dpkiOpenSslVerifyCert"
      )
    );
    okAssertion = dpkiOpenSslAssertion(
      source,
      target,
      request,
      stageTimings,
      stageNames.assertionPrefix || "dpkiOffchainAssertion"
    );
    okSignature = timeStageSync(stageTimings, stageNames.authSignature || "dpkiAuthSignature", () => {
      const signed = signAuthMessage(web3, source, target, proof, request.nonce);
      return verifySignedAuth(web3, source, signed);
    });
  }

  await verifyAttempt(canRetry);
  if (!okProof || !okCertificate || !okAssertion || !okSignature) {
    throw new Error("DPKI Merkle authentication execution failed");
  }
  return { source, target, proof };
}

async function offchainAuth(web3, contract, platform, hash, request, params) {
  if (platform.dpkiProofResponder && platform.dpkiProofResponder.baseUrl) {
    const stageTimings = {};
    await requestHttpWindowStage(
      stageTimings,
      "dpkiOffchainCertTransferHttp",
      platform.dpkiProofResponder.baseUrl,
      request,
      "dpki-auth-transfer",
      dpkiAuthTransferHttpShapeConfig(params, request)
    );
    const response = await requestJson("POST", `${platform.dpkiProofResponder.baseUrl}/dpki/auth-execute`, {
      request,
      canRetry: true,
      httpWindowStage: "dpkiOffchainHttpWindow",
    });
    return {
      stageTimings: mergeStageTimings(stageTimings, response.stageTimings || {}),
      proofNodes: Number(response.proofNodes) || 0,
      chainReads: Number(response.chainReads) || 1,
      verifiedCertificateSteps: Number(response.verifiedCertificateSteps) || 1,
    };
  }
  const stageTimings = {};
  const { proof } = await runDpkiMerkleAuthExecution(
    web3,
    contract,
    platform,
    hash,
    request,
    params,
    stageTimings
  );
  return {
    stageTimings,
    proofNodes: proof.items.length,
    chainReads: 1,
    verifiedCertificateSteps: 1,
  };
}

async function putAuthRecord(web3, contract, account, privateKey, nonceManager, hash, request, source) {
  return sendContractTx(
    web3,
    contract.methods.putAuthRecord(
      request.requestId,
      web3.utils.keccak256(request.sourceDomain),
      web3.utils.keccak256(request.targetDomain),
      web3.utils.keccak256(request.sourceSubject),
      web3.utils.keccak256(request.targetSubject),
      source.certHash,
      hash.text(request.nonce),
      source.account.address,
      Math.floor(Date.now() / 1000),
      request.crossDomain
    ),
    account,
    privateKey,
    nonceManager
  );
}

function sourceServiceCa(platform, request) {
  return findCert(platform, "main", request.sourceDomain === "domain-a" ? "S-A" : "S-B");
}

function authRecordBody(web3, hash, request, source, timestamp, valid) {
  return {
    requestId: request.requestId,
    sourceDomainId: web3.utils.keccak256(request.sourceDomain),
    targetDomainId: web3.utils.keccak256(request.targetDomain),
    sourceSubjectId: web3.utils.keccak256(request.sourceSubject),
    targetSubjectId: web3.utils.keccak256(request.targetSubject),
    certHash: source.certHash,
    nonceHash: hash.text(request.nonce),
    sourceAddress: source.account.address,
    timestamp,
    crossDomain: request.crossDomain,
    valid,
  };
}

function signServiceAuthRecord(web3, serviceCa, recordBody) {
  const message = stableStringify(recordBody);
  return {
    message,
    signer: serviceCa.account.address,
    signature: serviceCa.account.sign(message).signature,
  };
}

function splitEthereumSignature(signature) {
  const clean = String(signature || "").replace(/^0x/i, "");
  if (clean.length !== 130) {
    throw new Error("expected 65-byte Ethereum signature");
  }
  let v = Number.parseInt(clean.slice(128, 130), 16);
  if (v < 27) v += 27;
  return {
    r: `0x${clean.slice(0, 64)}`,
    s: `0x${clean.slice(64, 128)}`,
    v,
  };
}

function certificateCheckHash(web3, certificateChecks) {
  return web3.utils.keccak256(
    web3.eth.abi.encodeParameters(
      ["bytes32[]", "bytes32[]"],
      [
        certificateChecks.map((record) => record.key),
        certificateChecks.map((record) => record.certHash),
      ]
    )
  );
}

function authAssertionDigest(web3, contract, hash, request, source, certificateChecks, timestamp) {
  const contractAddress =
    contract && contract.options && contract.options.address
      ? contract.options.address
      : "0x0000000000000000000000000000000000000000";
  return web3.utils.soliditySha3(
    { type: "address", value: contractAddress },
    { type: "bytes32", value: request.requestId },
    { type: "bytes32", value: web3.utils.keccak256(request.sourceDomain) },
    { type: "bytes32", value: web3.utils.keccak256(request.targetDomain) },
    { type: "bytes32", value: web3.utils.keccak256(request.sourceSubject) },
    { type: "bytes32", value: web3.utils.keccak256(request.targetSubject) },
    { type: "bytes32", value: hash.text(request.nonce) },
    { type: "address", value: source.account.address },
    { type: "uint256", value: String(timestamp) },
    { type: "bool", value: Boolean(request.crossDomain) },
    { type: "bytes32", value: certificateCheckHash(web3, certificateChecks) }
  );
}

function signContractAuthAssertion(web3, contract, hash, request, source, certificateChecks, timestamp, serviceCa) {
  const digest = authAssertionDigest(web3, contract, hash, request, source, certificateChecks, timestamp);
  const signature = serviceCa.account.sign(digest).signature;
  return {
    digest,
    signer: serviceCa.account.address,
    signature,
    signatureHash: web3.utils.keccak256(signature),
    ...splitEthereumSignature(signature),
  };
}

function signEntityTxId(source, txId) {
  return source.account.sign(String(txId)).signature;
}

function verifySignatureAddress(web3, message, signature, expectedAddress) {
  const recovered = web3.eth.accounts.recover(message, signature);
  return recovered.toLowerCase() === expectedAddress.toLowerCase();
}

async function resolveAuthRecordOnChain(web3, contract, requestId) {
  if (contract && contract.isPow) {
    const record = await contract.authRecord(requestId);
    return {
      record,
      serviceSigner: record ? record.serviceSigner : null,
      serviceSignatureHash: record ? record.serviceSignatureHash : null,
    };
  }
  const [record, commitment] = await Promise.all([
    contract.methods.authRecords(requestId).call(),
    contract.methods.getAuthRecordSignatureCommitment(requestId).call(),
  ]);
  return {
    record,
    serviceSigner: commitment[0],
    serviceSignatureHash: commitment[1],
  };
}

function verifyResolvedAuthRecord(
  web3,
  hash,
  request,
  source,
  serviceCa,
  timestamp,
  resolved,
  serviceSignature,
  entityTxIdSignature,
  txId
) {
  if (!resolved || !resolved.record || !resolved.record.exists) return false;
  const record = resolved.record;
  const expected = authRecordBody(web3, hash, request, source, timestamp, true);
  const serviceMessage = stableStringify(expected);
  const serviceSignatureHash = web3.utils.keccak256(serviceSignature);
  return (
    String(record.sourceDomainId).toLowerCase() === expected.sourceDomainId.toLowerCase() &&
    String(record.targetDomainId).toLowerCase() === expected.targetDomainId.toLowerCase() &&
    String(record.sourceSubjectId).toLowerCase() === expected.sourceSubjectId.toLowerCase() &&
    String(record.targetSubjectId).toLowerCase() === expected.targetSubjectId.toLowerCase() &&
    String(record.certHash).toLowerCase() === expected.certHash.toLowerCase() &&
    String(record.nonceHash).toLowerCase() === expected.nonceHash.toLowerCase() &&
    String(record.sourceAddress).toLowerCase() === expected.sourceAddress.toLowerCase() &&
    Number(record.timestamp) === timestamp &&
    Boolean(record.crossDomain) === Boolean(request.crossDomain) &&
    String(resolved.serviceSigner).toLowerCase() === serviceCa.account.address.toLowerCase() &&
    String(resolved.serviceSignatureHash).toLowerCase() === serviceSignatureHash.toLowerCase() &&
    verifySignatureAddress(web3, serviceMessage, serviceSignature, serviceCa.account.address) &&
    verifySignatureAddress(web3, String(txId), entityTxIdSignature, source.account.address)
  );
}

async function verifyCrossDomainServiceCaMainProof(web3, contract, platform, hash, serviceCa, stageTimings) {
  const proof = timeStageSync(stageTimings, "dpkiCrossMainMptCacheAndProof", () => {
    const tree = getRepoTree(platform, hash, "main");
    return {
      type: tree.type,
      root: tree.root,
      items: getRepoProof(platform, hash, "main", serviceCa),
    };
  });
  const mainRoot = await timeStage(stageTimings, "dpkiCrossMainRootRead", () =>
    domainRootOnChain(web3, contract, hash, "main")
  );
  if (String(mainRoot).toLowerCase() !== String(proof.root).toLowerCase()) {
    return false;
  }
  return timeStageSync(stageTimings, "dpkiCrossMainMptVerify", () =>
    verifyMpt(hash, serviceCa.key, mptValueHash(hash, serviceCa), proof.items, proof.root)
  );
}

async function authenticateOnChain(
  web3,
  contract,
  account,
  privateKey,
  nonceManager,
  hash,
  request,
  source,
  certificateChecks,
  timestamp,
  serviceAssertion
) {
  const hasSignedService = Boolean(serviceAssertion && serviceAssertion.signer && serviceAssertion.signature);
  if (contract && contract.isPow) {
    const payload = {
      requestId: request.requestId,
      sourceDomainId: web3.utils.keccak256(request.sourceDomain),
      targetDomainId: web3.utils.keccak256(request.targetDomain),
      sourceSubjectId: web3.utils.keccak256(request.sourceSubject),
      targetSubjectId: web3.utils.keccak256(request.targetSubject),
      nonceHash: hash.text(request.nonce),
      sourceAddress: source.account.address,
      timestamp,
      crossDomain: request.crossDomain,
      certKeys: certificateChecks.map((record) => record.key),
      certHashes: certificateChecks.map((record) => record.certHash),
    };
    if (hasSignedService) {
      payload.serviceSigner = serviceAssertion.signer;
      payload.serviceSignatureHash = serviceAssertion.signatureHash;
      payload.serviceSignature = serviceAssertion.signature;
    }
    return contract.authenticate(payload);
  }
  if (contract.methods.authenticateSigned && hasSignedService) {
    return sendContractTx(
      web3,
      contract.methods.authenticateSigned(
        [
          request.requestId,
          web3.utils.keccak256(request.sourceDomain),
          web3.utils.keccak256(request.targetDomain),
          web3.utils.keccak256(request.sourceSubject),
          web3.utils.keccak256(request.targetSubject),
          hash.text(request.nonce),
        ],
        source.account.address,
        timestamp,
        request.crossDomain,
        certificateChecks.map((record) => record.key),
        certificateChecks.map((record) => record.certHash),
        serviceAssertion.signer,
        serviceAssertion.signature
      ),
      account,
      privateKey,
      nonceManager
    );
  }
  return sendContractTx(
    web3,
    contract.methods.authenticate(
      request.requestId,
      web3.utils.keccak256(request.sourceDomain),
      web3.utils.keccak256(request.targetDomain),
      web3.utils.keccak256(request.sourceSubject),
      web3.utils.keccak256(request.targetSubject),
      hash.text(request.nonce),
      source.account.address,
      timestamp,
      request.crossDomain,
      certificateChecks.map((record) => record.key),
      certificateChecks.map((record) => record.certHash)
    ),
    account,
    privateKey,
    nonceManager
  );
}

async function onchainAuth(web3, contract, account, privateKey, nonceManager, platform, hash, request) {
  const stageTimings = {};
  const source = findCert(platform, request.sourceDomain, request.sourceSubject);
  const certificateChecks = [source];
  const timestamp = Math.floor(Date.now() / 1000);
  const serviceAssertion = signContractAuthAssertion(
    web3,
    contract,
    hash,
    request,
    source,
    certificateChecks,
    timestamp,
    sourceServiceCa(platform, request)
  );
  const txStage = contract && contract.isPow ? "dpkiPowOnchainAuthenticateTx" : "dpkiOnchainAuthenticateTx";
  const receipt = await timeStage(stageTimings, txStage, () =>
    authenticateOnChain(
      web3,
      contract,
      account,
      privateKey,
      nonceManager,
      hash,
      request,
      source,
      certificateChecks,
      timestamp,
      serviceAssertion
    )
  );
  const onchainStageNames = {
    cachedRootRead: "dpkiOnchainCachedRootRead",
    chainRootRead: "dpkiOnchainRootRead",
    localProof: "dpkiOnchainMptCacheAndProof",
    httpProof: "dpkiOnchainMptProofHttpQuery",
    proofSignerCertVerify: "dpkiOnchainMptProofSignerCertVerify",
    proofResponseVerify: "dpkiOnchainMptProofResponseVerify",
    mptVerify: "dpkiOnchainMptVerify",
    certVerify: "dpkiOnchainOpenSslVerifyCert",
    assertionPrefix: "dpkiOnchainAssertion",
    authSignature: "dpkiOnchainAuthSignature",
    rootMismatchRetry: "dpkiOnchainRootMismatchRetry",
    waitManagementOnRootMismatch: "dpkiOnchainWaitManagementOnRootMismatch",
  };
  let proofNodes = 0;
  let chainReads = 1;
  let verifiedCertificateSteps = certificateChecks.length;
  if (platform.dpkiProofResponder && platform.dpkiProofResponder.baseUrl) {
    await requestHttpWindowStage(
      stageTimings,
      "dpkiOnchainCertTransferHttp",
      platform.dpkiProofResponder.baseUrl,
      request,
      "dpki-auth-transfer",
      dpkiAuthTransferHttpShapeConfig(ACTIVE_ARGS, request)
    );
    await requestHttpWindowStage(
      stageTimings,
      "dpkiOnchainRelayHttp",
      platform.dpkiProofResponder.baseUrl,
      request,
      "dpki-onchain-extra",
      dpkiOnchainExtraHttpShapeConfig(ACTIVE_ARGS, request)
    );
    await requestHttpWindowStage(
      stageTimings,
      "dpkiCrossRelayHttp",
      platform.dpkiProofResponder.baseUrl,
      request,
      "dpki-cross-extra",
      dpkiCrossExtraHttpShapeConfig(ACTIVE_ARGS, request)
    );
    const response = await requestJson("POST", `${platform.dpkiProofResponder.baseUrl}/dpki/auth-execute`, {
      request,
      canRetry: false,
      httpWindowStage: "dpkiOnchainHttpWindow",
      stageNames: onchainStageNames,
    });
    mergeStageTimings(stageTimings, response.stageTimings || {});
    proofNodes = Number(response.proofNodes) || 0;
    chainReads = Number(response.chainReads) || 1;
    verifiedCertificateSteps = Number(response.verifiedCertificateSteps) || 1;
  } else {
    const { proof } = await runDpkiMerkleAuthExecution(
      web3,
      contract,
      platform,
      hash,
      request,
      ACTIVE_ARGS,
      stageTimings,
      onchainStageNames,
      false
    );
    proofNodes = proof.items.length;
  }
  return {
    stageTimings,
    receipts: [receipt],
    chainReads,
    proofNodes,
    verifiedCertificateSteps,
  };
}

async function managementRequestCore(
  web3,
  contract,
  account,
  privateKey,
  nonceManager,
  platform,
  hash,
  request,
  stageTimings,
  options = {}
) {
  const target = findOpenSslCert(platform.x509, "domain-a", "EA-1");
  const subject = `MGMT-SLOT-${(request.index % MANAGEMENT_POOL_SIZE) + 1}`;
  const { record, x509Record } = timeStageSync(stageTimings, "dpkiManagementIssueCertificate", () => {
    const updatedX509 = createOpenSslSignedCert(
      platform.x509,
      MANAGEMENT_DOMAIN,
      subject,
      "main",
      "S-A",
      "entity",
      stageTimings,
      "dpkiManagementOpenSslIssue"
    );
    const newRecord = makeCertificate(web3, hash, MANAGEMENT_DOMAIN, subject, "S-A", "entity", updatedX509);
    signCertificateRecord(web3, hash, newRecord, findCert(platform, "main", "S-A"));
    return { record: newRecord, x509Record: updatedX509 };
  });
  const issued = verifyOpenSslCertificateThenAssertion(
    platform.x509,
    MANAGEMENT_DOMAIN,
    subject,
    target,
    request,
    stageTimings,
    "dpkiManagementOpenSslVerifyLeaf",
    "dpkiManagementLeafAssertion"
  );
  verifyOpenSslCertificateThenAssertion(
    platform.x509,
    "main",
    "S-A",
    issued,
    request,
    stageTimings,
    "dpkiManagementOpenSslVerifyIssuerCA",
    "dpkiManagementIssuerAssertion"
  );
  timeStageSync(stageTimings, "dpkiManagementVerifyRepositoryUpdateLocal", () => {
    const stored = findOpenSslCert(platform.x509, x509Record.domain, x509Record.subject);
    if (
      stored.certPath !== x509Record.certPath ||
      stored.keyPath !== x509Record.keyPath ||
      stored.serialHex !== x509Record.serialHex
    ) {
      throw new Error(`DPKI management OpenSSL repository does not contain updated cert ${x509Record.domain}/${x509Record.subject}`);
    }
    return true;
  });
  const currentRecords = platform.repos.get(MANAGEMENT_DOMAIN);
  let replaced = false;
  const updatedRecords = currentRecords.map((item) => {
    if (item.subject !== subject) return item;
    replaced = true;
    return record;
  });
  if (!replaced) updatedRecords.push(record);
  const tree = timeStageSync(stageTimings, "dpkiManagementBuildMpt", () => buildMpt(updatedRecords, hash));
  const txStage = contract && contract.isPow ? "dpkiPowManagementPutCertAndRootTx" : "dpkiManagementPutCertAndRootTx";
  beginManagementUpdate(platform);
  let receipt;
  try {
    receipt = await timeStage(stageTimings, txStage, () =>
      putCertAndRootOnChain(web3, contract, account, privateKey, nonceManager, record, tree.root)
    );
    const existingIndex = currentRecords.findIndex((item) => item.subject === subject);
    if (existingIndex >= 0) currentRecords[existingIndex] = record;
    else currentRecords.push(record);
    invalidateDomainCache(platform, MANAGEMENT_DOMAIN);
    if (platform.domainRootCache) platform.domainRootCache.set(MANAGEMENT_DOMAIN, tree.root);
    await verifyDpkiManagementRepositoryUpdate(
      web3,
      contract,
      platform,
      hash,
      record,
      tree.root,
      request,
      stageTimings,
      { includeHttpWindow: options.includePostHttpWindow !== false }
    );
  } finally {
    finishManagementUpdate(platform);
  }
  return {
    stageTimings,
    receipts: [receipt],
    chainReads: 0,
    verifiedCertificateSteps: 2,
  };
}

async function managementRequest(web3, contract, account, privateKey, nonceManager, platform, hash, request) {
  return serializeManagementUpdate(platform, async () => {
    if (platform.dpkiProofResponder && platform.dpkiProofResponder.baseUrl) {
      const stageTimings = {};
      await requestHttpWindowStage(
        stageTimings,
        "dpkiManagementDispatchHttp",
        platform.dpkiProofResponder.baseUrl,
        request,
        "dpki-management-transfer",
        dpkiManagementTransferHttpShapeConfig(ACTIVE_ARGS)
      );
      await requestHttpWindowStage(
        stageTimings,
        "dpkiManagementRelayHttp",
        platform.dpkiProofResponder.baseUrl,
        request,
        "dpki-management-extra",
        dpkiManagementExtraHttpShapeConfig(ACTIVE_ARGS)
      );
      const response = await requestJson("POST", `${platform.dpkiProofResponder.baseUrl}/dpki/management-execute`, {
        request,
      });
      return {
        stageTimings: mergeStageTimings(stageTimings, response.stageTimings || {}),
        receipts: response.receipts || [],
        chainReads: Number(response.chainReads) || 0,
        verifiedCertificateSteps: Number(response.verifiedCertificateSteps) || 2,
      };
    }
    const stageTimings = {};
    return managementRequestCore(
      web3,
      contract,
      account,
      privateKey,
      nonceManager,
      platform,
      hash,
      request,
      stageTimings,
      { includePostHttpWindow: true }
    );
  });
}

function chooseEntity(rand, prefix, count) {
  return `${prefix}-${1 + Math.floor(rand() * count)}`;
}

function allocateFixedCounts(total, specs) {
  const rows = specs.map((spec, index) => {
    const raw = Math.max(0, Number(spec.weight) || 0) * total;
    const count = Math.floor(raw);
    return {
      ...spec,
      index,
      raw,
      count,
      remainder: raw - count,
    };
  });
  let remaining = total - rows.reduce((sum, row) => sum + row.count, 0);
  const byRemainder = [...rows].sort((a, b) => {
    if (b.remainder !== a.remainder) return b.remainder - a.remainder;
    return a.index - b.index;
  });
  for (let i = 0; i < remaining; i += 1) {
    byRemainder[i % byRemainder.length].count += 1;
  }
  while (rows.reduce((sum, row) => sum + row.count, 0) > total) {
    const candidates = [...rows].filter((row) => row.count > 0).sort((a, b) => {
      if (a.remainder !== b.remainder) return a.remainder - b.remainder;
      return b.index - a.index;
    });
    candidates[0].count -= 1;
  }
  return rows.map((row) => ({ kind: row.kind, count: row.count }));
}

function interleaveFixedPlan(counts) {
  const entries = counts.filter((entry) => entry.count > 0).map((entry, index) => ({
    ...entry,
    index,
    used: 0,
    score: 0,
  }));
  const total = entries.reduce((sum, entry) => sum + entry.count, 0);
  const plan = [];
  for (let slot = 0; slot < total; slot += 1) {
    for (const entry of entries) {
      if (entry.used < entry.count) entry.score += entry.count;
    }
    const available = entries.filter((entry) => entry.used < entry.count);
    available.sort((a, b) => {
      if (b.score !== a.score) return b.score - a.score;
      return a.index - b.index;
    });
    const chosen = available[0];
    chosen.used += 1;
    chosen.score -= total;
    plan.push(chosen.kind);
  }
  return plan;
}

function buildKindPlan(rand, epsilon, params) {
  const total = params.requestsPerEpsilon;
  if (String(params.kindPlanMode || "fixed").toLowerCase() === "random") {
    return Array.from({ length: total }, () => {
      if (rand() < params.pManage) return "management";
      if (rand() < epsilon) return "cross-domain";
      if (rand() < params.gammaOnChain) return "intra-on-chain";
      return "intra-off-chain";
    });
  }
  return interleaveFixedPlan(
    allocateFixedCounts(total, [
      { kind: "management", weight: params.pManage },
      { kind: "cross-domain", weight: (1 - params.pManage) * epsilon },
      { kind: "intra-on-chain", weight: (1 - params.pManage) * (1 - epsilon) * params.gammaOnChain },
      { kind: "intra-off-chain", weight: (1 - params.pManage) * (1 - epsilon) * (1 - params.gammaOnChain) },
    ])
  );
}

function buildRequest(web3, hash, rand, epsilon, index, params, plannedKind) {
  const request = {
    index,
    epsilon,
    epsilonLabel: String(epsilon).replace(".", "p"),
    nonce: crypto.randomBytes(16).toString("hex"),
    arrivalAt: performance.now(),
  };
  request.requestId = hash.text(`${epsilon}:${index}:${request.nonce}`);

  if (plannedKind === "management") {
    const subject = `MGMT-SLOT-${(index % MANAGEMENT_POOL_SIZE) + 1}`;
    return {
      ...request,
      kind: "management",
      onChain: true,
      crossDomain: false,
      sourceDomain: MANAGEMENT_DOMAIN,
      targetDomain: MANAGEMENT_DOMAIN,
      sourceSubject: subject,
      targetSubject: subject,
    };
  }

  if (plannedKind === "cross-domain") {
    return {
      ...request,
      kind: "cross-domain",
      onChain: true,
      crossDomain: true,
      sourceDomain: "domain-a",
      targetDomain: "domain-b",
      sourceSubject: chooseEntity(rand, "EA", 8),
      targetSubject: chooseEntity(rand, "EB", 8),
    };
  }

  if (plannedKind === "intra-on-chain") {
    return {
      ...request,
      kind: "intra-on-chain",
      onChain: true,
      crossDomain: false,
      sourceDomain: "domain-a",
      targetDomain: "domain-a",
      sourceSubject: chooseEntity(rand, "EA", 8),
      targetSubject: chooseEntity(rand, "EA", 8),
    };
  }

  return {
    ...request,
    kind: "intra-off-chain",
    onChain: false,
    crossDomain: false,
    sourceDomain: "domain-a",
    targetDomain: "domain-a",
    sourceSubject: chooseEntity(rand, "EA", 8),
    targetSubject: chooseEntity(rand, "EA", 8),
  };
}

async function executeRequest(web3, contract, account, privateKey, nonceManager, platform, hash, request, params) {
  if (request.kind === "management") {
    return managementRequest(web3, contract, account, privateKey, nonceManager, platform, hash, request);
  } else if (request.onChain) {
    return onchainAuth(web3, contract, account, privateKey, nonceManager, platform, hash, request);
  } else {
    return offchainAuth(web3, contract, platform, hash, request, params);
  }
}

async function runEpsilon(web3, contract, account, privateKey, nonceManager, platform, hash, epsilon, params) {
  const rand = mulberry32(params.seed + Math.round(epsilon * 1000) * 97);
  const scaleSec = params.timeScaleMs / 1000;
  const lambdaTotal = params.lambdaArrival / scaleSec;
  const lambdaBlock = params.lambdaBlock / scaleSec;
  const mu = params.muAuth / scaleSec;
  const qMu = params.qManage * mu;
  const kindPlan = buildKindPlan(rand, epsilon, params);
  const arrivals = [];
  const mempool = [];
  const completed = [];
  const offchainServerAvailable = Array.from({ length: params.serviceCAs }, () => 0);
  let executorAvailable = 0;
  let nextBlock = Infinity;
  let nextArrival = expSample(rand, lambdaTotal);
  let arrivalIndex = 0;

  function completeOffchain(request) {
    const workerId = offchainServerAvailable.indexOf(Math.min(...offchainServerAvailable));
    const startSec = Math.max(request.modelArrivalSec, offchainServerAvailable[workerId]);
    const serviceSec = expSample(rand, mu);
    const finishSec = startSec + serviceSec;
    offchainServerAvailable[workerId] = finishSec;
    completed.push({
      ...request,
      workerId,
      stage: "offchain",
      modelFinishSec: finishSec,
      offchainQueueMs: (startSec - request.modelArrivalSec) * 1000,
      offchainServiceDelayMs: serviceSec * 1000,
      serviceMs: serviceSec * 1000,
      latencyMs: (finishSec - request.modelArrivalSec) * 1000,
    });
  }

  function formBlock(blockSec) {
    const batch = mempool.splice(0, mempool.length);
    nextBlock = Infinity;
    if (!batch.length) return;

    const executionStartSec = Math.max(blockSec, executorAvailable);
    let executionServiceSec = 0;
    for (const request of batch) {
      executionServiceSec += expSample(rand, request.kind === "management" ? qMu : mu);
    }
    const finishSec = executionStartSec + executionServiceSec;
    executorAvailable = finishSec;

    for (const request of batch) {
      completed.push({
        ...request,
        stage: "onchain",
        modelBlockSec: blockSec,
        modelExecutionStartSec: executionStartSec,
        modelFinishSec: finishSec,
        blockWaitMs: (blockSec - request.modelArrivalSec) * 1000,
        executionQueueMs: (executionStartSec - blockSec) * 1000,
        serviceMs: executionServiceSec * 1000,
        latencyMs: (finishSec - request.modelArrivalSec) * 1000,
      });
    }
  }

  while (arrivalIndex < params.requestsPerEpsilon || mempool.length > 0) {
    if (arrivalIndex < params.requestsPerEpsilon && nextArrival <= nextBlock) {
      const request = buildRequest(web3, hash, rand, epsilon, arrivalIndex, params, kindPlan[arrivalIndex]);
      request.modelArrivalSec = nextArrival;
      request.arrivalOffsetMs = nextArrival * 1000;
      arrivals.push(request);
      if (request.onChain) {
        const wasEmpty = mempool.length === 0;
        mempool.push(request);
        if (wasEmpty) nextBlock = nextArrival + expSample(rand, lambdaBlock);
      } else {
        completeOffchain(request);
      }
      arrivalIndex += 1;
      nextArrival += expSample(rand, lambdaTotal);
    } else {
      formBlock(nextBlock);
    }
  }

  completed.sort((a, b) => a.modelFinishSec - b.modelFinishSec || a.index - b.index);
  for (const request of completed) {
    await executeRequest(web3, contract, account, privateKey, nonceManager, platform, hash, request, params);
  }

  const averageMs = completed.reduce((sum, item) => sum + item.latencyMs, 0) / completed.length;
  const onChain = completed.filter((item) => item.onChain);
  const offChain = completed.filter((item) => !item.onChain);
  const cross = completed.filter((item) => item.crossDomain);
  const sortedArrivals = [...arrivals].sort((a, b) => a.arrivalOffsetMs - b.arrivalOffsetMs);
  const arrivalSpanSec =
    sortedArrivals.length > 1
      ? (sortedArrivals[sortedArrivals.length - 1].arrivalOffsetMs - sortedArrivals[0].arrivalOffsetMs) / 1000
      : 0;
  const lambdaTotalReal = params.lambdaArrival / (params.timeScaleMs / 1000);
  const targetLambdaOffchain =
    (1 - params.pManage) * (1 - params.gammaOnChain) * (1 - epsilon) * lambdaTotalReal;
  const targetLambdaOnchain =
    (params.pManage + (1 - params.pManage) * epsilon + (1 - params.pManage) * (1 - epsilon) * params.gammaOnChain) *
    lambdaTotalReal;
  return {
    epsilon,
    DPKI_sim: averageMs / 1000,
    completed: completed.length,
    onChainCount: onChain.length,
    offChainCount: offChain.length,
    crossDomainCount: cross.length,
    actualOnChainRatio: onChain.length / completed.length,
    actualCrossDomainRatio: cross.length / completed.length,
    arrivalSpanSec,
    targetLambdaOffchain,
    targetLambdaOnchain,
    observedLambdaOffchain: arrivalSpanSec > 0 ? offChain.length / arrivalSpanSec : 0,
    observedLambdaOnchain: arrivalSpanSec > 0 ? onChain.length / arrivalSpanSec : 0,
    avgBlockWaitMs: average(onChain.map((item) => item.blockWaitMs || 0)),
    avgExecutionQueueMs: average(onChain.map((item) => item.executionQueueMs || 0)),
    avgChainServiceMs: average(onChain.map((item) => item.serviceMs || 0)),
    avgOffchainQueueMs: average(offChain.map((item) => item.offchainQueueMs || 0)),
    avgOffchainServiceDelayMs: average(offChain.map((item) => item.offchainServiceDelayMs || 0)),
    avgOffchainProofMs: average(offChain.map((item) => item.serviceMs || 0)),
    rows: completed,
  };
}

function createLimiter(maxActive) {
  let active = 0;
  const queue = [];

  function drain() {
    while (active < maxActive && queue.length > 0) {
      const item = queue.shift();
      active += 1;
      Promise.resolve()
        .then(item.fn)
        .then(item.resolve, item.reject)
        .finally(() => {
          active -= 1;
          drain();
        });
    }
  }

  return function limit(fn) {
    return new Promise((resolve, reject) => {
      queue.push({ fn, resolve, reject });
      drain();
    });
  };
}

async function sleepUntil(originMs, offsetMs) {
  await sleep(originMs + offsetMs - performance.now());
}

function generateArrivalOffsets(rand, count, lambdaArrival, timeScaleMs) {
  const offsets = [];
  let offsetMs = 0;
  for (let i = 0; i < count; i += 1) {
    if (i > 0) {
      offsetMs += expSample(rand, lambdaArrival) * timeScaleMs;
    }
    offsets.push(offsetMs);
  }
  return offsets;
}

function minIndex(values) {
  let best = 0;
  for (let i = 1; i < values.length; i += 1) {
    if (values[i] < values[best]) best = i;
  }
  return best;
}

function stageDurationMs(record, key) {
  const timings = record && record.stageTimings ? record.stageTimings : {};
  const value = Number(timings[key]);
  return Number.isFinite(value) && value > 0 ? value : 0;
}

function assertionDurationMs(record, prefix) {
  return stageDurationMs(record, `${prefix}Sign`) + stageDurationMs(record, `${prefix}Verify`);
}

function pkiPrimaryQueueServiceMs(record, fallbackMs) {
  if (record.kind === "management") return fallbackMs;
  if (record.crossDomain) {
    return fallbackMs / (1 + PKI_CROSS_DOMAIN_CHAIN_STEPS);
  }
  return fallbackMs;
}

function dpkiOnchainQueueServiceMs(record, fallbackMs) {
  const authTx =
    stageDurationMs(record, "dpkiPowOnchainAuthenticateTx") +
    stageDurationMs(record, "dpkiOnchainAuthenticateTx");
  const managementTx =
    stageDurationMs(record, "dpkiPowManagementPutCertAndRootTx") +
    stageDurationMs(record, "dpkiManagementPutCertAndRootTx");
  const txMs = authTx + managementTx;
  return txMs > 0 ? txMs : fallbackMs;
}

function replayDpkiVirtualQueue(records, arrivalOffsets, originMs, params) {
  const offchainWorkers = Math.max(1, Math.floor(Number(params.dpkiOffchainWorkers) || Number(params.serviceCAs) || 1));
  const offchainAvailable = Array.from({ length: offchainWorkers }, () => 0);
  let onchainAvailable = 0;

  for (const record of [...records].sort((a, b) => a.index - b.index)) {
    const arrivalOffsetMs = Number(arrivalOffsets[record.index] || 0);
    const serviceMs = Math.max(0, Number(record.serviceMs) || 0);
    const queueServiceMs = record.onChain ? dpkiOnchainQueueServiceMs(record, serviceMs) : serviceMs;
    let startOffsetMs;
    if (record.onChain) {
      startOffsetMs = Math.max(arrivalOffsetMs, onchainAvailable);
      onchainAvailable = startOffsetMs + queueServiceMs;
      record.workerId = -1;
    } else {
      const workerId = minIndex(offchainAvailable);
      startOffsetMs = Math.max(arrivalOffsetMs, offchainAvailable[workerId]);
      offchainAvailable[workerId] = startOffsetMs + queueServiceMs;
      record.workerId = workerId;
    }
    record.arrivalOffsetMs = arrivalOffsetMs;
    record.arrivalWallMs = originMs + arrivalOffsetMs;
    record.queueMs = Math.max(0, startOffsetMs - arrivalOffsetMs);
    record.latencyMs = record.queueMs + serviceMs;
    record.finishWallMs = originMs + startOffsetMs + serviceMs;
  }
}

function replayPkiVirtualQueue(records, arrivalOffsets, originMs, params) {
  const workerCount = Math.max(1, Math.floor(Number(params.serviceCAs) || 1));
  const available = Array.from({ length: workerCount }, () => 0);

  for (const record of [...records].sort((a, b) => a.index - b.index)) {
    const arrivalOffsetMs = Number(arrivalOffsets[record.index] || 0);
    const serviceMs = Math.max(0, Number(record.serviceMs) || 0);
    const queueServiceMs = pkiPrimaryQueueServiceMs(record, serviceMs);
    const workerId = pkiWorkerIdForRequest(record, params);
    const startOffsetMs = Math.max(arrivalOffsetMs, available[workerId]);
    available[workerId] = startOffsetMs + queueServiceMs;
    record.workerId = workerId;
    record.arrivalOffsetMs = arrivalOffsetMs;
    record.arrivalWallMs = originMs + arrivalOffsetMs;
    record.queueMs = Math.max(0, startOffsetMs - arrivalOffsetMs);
    record.latencyMs = record.queueMs + serviceMs;
    record.finishWallMs = originMs + startOffsetMs + serviceMs;
  }
}

function summarizeReceiptBlocks(records) {
  const blockCounts = new Map();
  const seenTx = new Set();
  let txCount = 0;
  let gasUsed = 0;
  for (const record of records) {
    for (const receipt of record.receipts || []) {
      const txHash = String(receipt.transactionHash || `${receipt.blockNumber}:${receipt.transactionIndex}:${txCount}`);
      if (seenTx.has(txHash)) continue;
      seenTx.add(txHash);
      txCount += 1;
      gasUsed += Number(receipt.gasUsed || 0);
      const blockNumber = String(receipt.blockNumber);
      blockCounts.set(blockNumber, (blockCounts.get(blockNumber) || 0) + 1);
    }
  }
  const blocks = [...blockCounts.values()];
  return {
    chainTxCount: txCount,
    chainBlockCount: blockCounts.size,
    avgTxPerChainBlock: blocks.length ? average(blocks) : 0,
    maxTxPerChainBlock: blocks.length ? Math.max(...blocks) : 0,
    gasUsed,
  };
}

function pkiNetworkCompensationSec(completed, authCount, ocspCount) {
  if (!completed) return 0;
  const totalMs = authCount * PKI_AUTH_NETWORK_SETUP_MS + ocspCount * PKI_OCSP_NETWORK_RTT_MS;
  return totalMs / completed / 1000;
}

function summarizeMeasuredRecords(epsilon, records, params, modelName) {
  const onChain = records.filter((item) => item.onChain);
  const offChain = records.filter((item) => !item.onChain && modelName === "DPKI");
  const cross = records.filter((item) => item.crossDomain);
  const management = records.filter((item) => item.kind === "management");
  const latencies = records.map((item) => item.latencyMs);
  const serviceTimes = records.map((item) => item.serviceMs || 0);
  const arrivals = [...records].sort((a, b) => a.arrivalWallMs - b.arrivalWallMs);
  const arrivalSpanSec =
    arrivals.length > 1 ? (arrivals[arrivals.length - 1].arrivalWallMs - arrivals[0].arrivalWallMs) / 1000 : 0;
  const receiptStats = summarizeReceiptBlocks(records);
  const rawSimSec = average(latencies) / 1000;
  const authCount = modelName === "PKI" ? Math.max(0, records.length - management.length) : 0;
  const ocspCount = modelName === "PKI" ? authCount + PKI_CROSS_DOMAIN_CHAIN_STEPS * cross.length : 0;
  const pkiCompensationSec =
    modelName === "PKI" ? pkiNetworkCompensationSec(records.length, authCount, ocspCount) : 0;
  const pkiCompensationMs = pkiCompensationSec * 1000;
  const simSec = modelName === "PKI" ? rawSimSec + pkiCompensationSec : rawSimSec;
  const targetLambdaOffchain =
    modelName === "DPKI"
      ? (1 - params.pManage) * (1 - params.gammaOnChain) * (1 - epsilon) * params.lambdaArrival
      : 0;
  const targetLambdaOnchain =
    modelName === "DPKI"
      ? (params.pManage + (1 - params.pManage) * epsilon + (1 - params.pManage) * (1 - epsilon) * params.gammaOnChain) *
        params.lambdaArrival
      : 0;

  return {
    epsilon,
    [`${modelName}_sim`]: simSec,
    [`${modelName}_sim_raw`]: rawSimSec,
    completed: records.length,
    onChainCount: onChain.length,
    offChainCount: offChain.length,
    crossDomainCount: cross.length,
    managementCount: management.length,
    actualOnChainRatio: records.length ? onChain.length / records.length : 0,
    actualOffChainRatio: records.length ? offChain.length / records.length : 0,
    actualCrossDomainRatio: records.length ? cross.length / records.length : 0,
    actualManagementRatio: records.length ? management.length / records.length : 0,
    arrivalSpanSec,
    targetLambdaOffchain,
    targetLambdaOnchain,
    observedLambdaOffchain: arrivalSpanSec > 0 ? offChain.length / arrivalSpanSec : 0,
    observedLambdaOnchain: arrivalSpanSec > 0 ? onChain.length / arrivalSpanSec : 0,
    avgLatencyMs: average(latencies) + pkiCompensationMs,
    avgLatencyRawMs: average(latencies),
    avgQueueMs: average(records.map((item) => item.queueMs || 0)),
    avgServiceMs: average(serviceTimes) + pkiCompensationMs,
    avgServiceRawMs: average(serviceTimes),
    avgOffchainProofMs: average(records.filter((item) => item.kind === "intra-off-chain").map((item) => item.serviceMs || 0)),
    avgPkiChainVerifyMs:
      average(records.filter((item) => modelName === "PKI").map((item) => item.serviceMs || 0)) + pkiCompensationMs,
    pkiNetworkCompensationSec: pkiCompensationSec,
    pkiNetworkCompensationMs: pkiCompensationMs,
    pkiAuthNetworkSetupMs: modelName === "PKI" ? PKI_AUTH_NETWORK_SETUP_MS : 0,
    pkiOcspNetworkRttMs: modelName === "PKI" ? PKI_OCSP_NETWORK_RTT_MS : 0,
    pkiAuthCount: authCount,
    pkiOcspCount: ocspCount,
    ...receiptStats,
  };
}

async function runRealDpkiEpsilon(web3, contract, txSenders, platform, hash, epsilon, params) {
  const rand = mulberry32(params.seed + Math.round(epsilon * 1000) * 97);
  const kindPlan = buildKindPlan(rand, epsilon, params);
  const arrivalOffsets = generateArrivalOffsets(rand, params.requestsPerEpsilon, params.lambdaArrival, params.timeScaleMs);
  const originMs = performance.now() + 100;
  const virtualArrivals = String(params.arrivalMode || "wall").toLowerCase() === "virtual";
  const completed = [];
  const tasks = [];
  const serialExecution = String(params.actualExecutionMode || "parallel").toLowerCase() === "serial";
  const chainConcurrency = Math.max(1, Math.min(params.maxOnchainInFlight, txSenders.length));
  const limitOnchain = createLimiter(chainConcurrency);
  const offchainWorkers = Math.max(1, Math.floor(Number(params.dpkiOffchainWorkers) || Number(params.serviceCAs) || 1));
  const workerChains = Array.from({ length: offchainWorkers }, () => Promise.resolve());
  const workerDepth = Array.from({ length: offchainWorkers }, () => 0);
  let senderIndex = 0;

  function nextSender() {
    const sender = txSenders[senderIndex % txSenders.length];
    senderIndex += 1;
    return sender;
  }

  function recordCompletion(request, workerId, startMs, finishMs, result, error) {
    if (error) throw error;
    completed.push({
      ...request,
      workerId,
      finishWallMs: finishMs,
      queueMs: startMs - request.arrivalWallMs,
      serviceMs: finishMs - startMs,
      latencyMs: finishMs - request.arrivalWallMs,
      receipts: result && result.receipts ? result.receipts : [],
      chainReads: result && result.chainReads ? result.chainReads : 0,
      verifiedCertificateSteps: result && result.verifiedCertificateSteps ? result.verifiedCertificateSteps : 0,
      proofNodes: result && result.proofNodes ? result.proofNodes : 0,
      stageTimings: result && result.stageTimings ? result.stageTimings : {},
    });
  }

  for (let i = 0; i < params.requestsPerEpsilon; i += 1) {
    if (!virtualArrivals) {
      await sleepUntil(originMs, arrivalOffsets[i]);
    }
    const request = buildRequest(web3, hash, rand, epsilon, i, params, kindPlan[i]);
    request.arrivalOffsetMs = arrivalOffsets[i];
    request.arrivalWallMs = virtualArrivals ? originMs + arrivalOffsets[i] : performance.now();

    if (request.onChain) {
      const task = limitOnchain(async () => {
        const sender = nextSender();
        const startMs = performance.now();
        const result = await executeRequest(
          web3,
          contract,
          sender.account,
          sender.privateKey,
          sender.nonceManager,
          platform,
          hash,
          request,
          params
        );
        result.stageTimings = result.stageTimings || {};
        await shapeElapsedServiceToTargetExponential(params, "DPKI", request, startMs, result.stageTimings);
        const finishMs = performance.now();
        recordCompletion(request, -1, startMs, finishMs, result, null);
      });
      if (serialExecution) await task;
      else tasks.push(task);
    } else {
      const workerId = workerDepth.indexOf(Math.min(...workerDepth));
      workerDepth[workerId] += 1;
      const task = workerChains[workerId]
        .then(async () => {
          const startMs = performance.now();
          const sender = txSenders[0];
          const result = await executeRequest(
            web3,
            contract,
            sender.account,
            sender.privateKey,
            sender.nonceManager,
            platform,
            hash,
            request,
            params
          );
          result.stageTimings = result.stageTimings || {};
          await shapeElapsedServiceToTargetExponential(params, "DPKI", request, startMs, result.stageTimings);
          const finishMs = performance.now();
          recordCompletion(request, workerId, startMs, finishMs, result, null);
        })
        .finally(() => {
          workerDepth[workerId] -= 1;
        });
      workerChains[workerId] = task.catch(() => {});
      if (serialExecution) await task;
      else tasks.push(task);
    }
  }

  await Promise.all(tasks);
  completed.sort((a, b) => a.index - b.index);
  if (virtualArrivals) {
    replayDpkiVirtualQueue(completed, arrivalOffsets, originMs, params);
    completed.sort((a, b) => a.index - b.index);
  }
  const summary = summarizeMeasuredRecords(epsilon, completed, params, "DPKI");
  return { ...summary, rows: completed };
}

function buildPkiKindPlan(rand, epsilon, params) {
  const total = params.requestsPerEpsilon;
  if (String(params.kindPlanMode || "fixed").toLowerCase() === "random") {
    return Array.from({ length: total }, () => {
      if (rand() < params.pManage) return "management";
      return rand() < epsilon ? "cross-domain" : "intra-pki";
    });
  }
  return interleaveFixedPlan(
    allocateFixedCounts(total, [
      { kind: "management", weight: params.pManage },
      { kind: "cross-domain", weight: (1 - params.pManage) * epsilon },
      { kind: "intra-pki", weight: (1 - params.pManage) * (1 - epsilon) },
    ])
  );
}

function buildPkiRequest(web3, hash, rand, epsilon, index, plannedKind) {
  const nonce = crypto.randomBytes(16).toString("hex");
  const request = {
    index,
    epsilon,
    kind: plannedKind,
    onChain: false,
    crossDomain: plannedKind === "cross-domain",
    nonce,
    requestId: hash.text(`pki:${epsilon}:${index}:${nonce}`),
    sourceDomain: "domain-a",
    targetDomain: plannedKind === "cross-domain" ? "domain-b" : "domain-a",
    sourceSubject: chooseEntity(rand, "EA", 8),
    targetSubject: plannedKind === "cross-domain" ? chooseEntity(rand, "EB", 8) : chooseEntity(rand, "EA", 8),
  };
  if (plannedKind === "management") {
    const subject = `MGMT-SLOT-${(index % MANAGEMENT_POOL_SIZE) + 1}`;
    request.sourceDomain = MANAGEMENT_DOMAIN;
    request.targetDomain = MANAGEMENT_DOMAIN;
    request.sourceSubject = subject;
    request.targetSubject = subject;
  }
  return request;
}

function pkiWorkerIdForRequest(request, params) {
  const workerCount = Math.max(1, Math.floor(Number(params.serviceCAs) || 1));
  const key = `${request.sourceDomain}:${request.sourceSubject}`;
  return hashSeed(`pki-fixed-ca:${key}`) % workerCount;
}

function opensslName(value) {
  return String(value).replace(/[^a-zA-Z0-9_.-]/g, "_");
}

function runOpenSsl(args, stageTimings, stageName) {
  const run = () => {
    const child = childProcess.spawnSync("openssl", args, {
      cwd: EXPERIMENT_DIR,
      encoding: "utf8",
      maxBuffer: 1024 * 1024 * 8,
      timeout: 15000,
    });
    if (child.error) {
      throw child.error;
    }
    if (child.status !== 0) {
      throw new Error(`openssl ${args.join(" ")} failed\n${child.stdout || ""}\n${child.stderr || ""}`);
    }
    return child;
  };
  return stageTimings ? timeStageSync(stageTimings, stageName, run) : run();
}

function canListen(port) {
  return new Promise((resolve) => {
    const server = net.createServer();
    server.once("error", () => resolve(false));
    server.once("listening", () => {
      server.close(() => resolve(true));
    });
    server.listen(port, "127.0.0.1");
  });
}

async function chooseOcspPort(platform) {
  const base = Number(platform.ocspBasePort) || 19080;
  for (let offset = 0; offset < 5000; offset += 1) {
    const port = base + platform.ocspPortOffset + offset;
    if (await canListen(port)) {
      platform.ocspPortOffset += offset + 1;
      return port;
    }
  }
  throw new Error(`could not find a free OCSP port near ${base}`);
}

function probeOcspHttp(port, timeoutMs = 1000) {
  return new Promise((resolve) => {
    const socket = net.createConnection({ host: "127.0.0.1", port });
    let settled = false;
    let connected = false;
    const done = (ready) => {
      if (settled) return;
      settled = true;
      try {
        socket.destroy();
      } catch (_error) {
        // Best-effort probe cleanup.
      }
      resolve(ready);
    };
    socket.setTimeout(timeoutMs);
    socket.once("connect", () => {
      connected = true;
      socket.write("GET / HTTP/1.0\r\nHost: 127.0.0.1\r\nConnection: close\r\n\r\n");
    });
    socket.once("data", () => done(true));
    socket.once("end", () => done(connected));
    socket.once("close", () => done(connected));
    socket.once("timeout", () => done(false));
    socket.once("error", () => done(false));
  });
}

async function waitForOcspHttpReady(port, timeoutMs = 3000) {
  const start = performance.now();
  while (performance.now() - start <= timeoutMs) {
    if (await probeOcspHttp(port)) return;
    await sleep(50);
  }
  throw new Error(`OCSP responder did not become HTTP-ready on port ${port}`);
}

function ocspIssuerKey(issuer) {
  return `${issuer.domain}:${issuer.subject}`;
}

function stopOpenSslOcspResponderProcess(responder) {
  if (!responder || !responder.process) return;
  try {
    if (responder.process.exitCode === null && !responder.process.killed) responder.process.kill();
  } catch (_error) {
    // Best-effort cleanup; the next run will choose another free port if needed.
  }
}

function stopOpenSslOcspResponder(platform, issuer) {
  if (!platform || !platform.ocspResponders) return;
  const key = ocspIssuerKey(issuer);
  const existing = platform.ocspResponders.get(key);
  if (!existing) return;
  stopOpenSslOcspResponderProcess(existing);
  platform.ocspResponders.delete(key);
}

function stopAllOpenSslOcspResponders(platform) {
  if (!platform || !platform.ocspResponders) return;
  for (const responder of platform.ocspResponders.values()) {
    stopOpenSslOcspResponderProcess(responder);
  }
  platform.ocspResponders.clear();
}

function cleanupOpenSslOcspResponders() {
  for (const platform of OPENSSL_OCSP_PLATFORMS) {
    stopAllOpenSslOcspResponders(platform);
  }
}

async function serializeOpenSslOcsp(platform, fn) {
  const previous = platform.ocspChain || Promise.resolve();
  const current = previous.then(fn);
  platform.ocspChain = current.catch(() => {});
  return current;
}

async function startOpenSslOcspResponderProcess(platform, issuer) {
  if (!platform.ocspResponders) platform.ocspResponders = new Map();
  const key = ocspIssuerKey(issuer);
  const indexPath = writeOpenSslOcspIndex(platform, issuer);
  const port = await chooseOcspPort(platform);
  const stdoutPath = path.join(platform.ocspDir, `responder-${opensslName(key)}-${port}.stdout.log`);
  const stderrPath = path.join(platform.ocspDir, `responder-${opensslName(key)}-${port}.stderr.log`);
  const stdoutFd = fs.openSync(stdoutPath, "a");
  const stderrFd = fs.openSync(stderrPath, "a");
  const child = childProcess.spawn(
    "openssl",
    [
      "ocsp",
      "-index",
      indexPath,
      "-port",
      String(port),
      "-rsigner",
      issuer.certPath,
      "-rkey",
      issuer.keyPath,
      "-CA",
      issuer.certPath,
      "-nmin",
      "5",
      "-ignore_err",
    ],
    {
      cwd: EXPERIMENT_DIR,
      windowsHide: true,
      stdio: ["ignore", stdoutFd, stderrFd],
    }
  );
  child.once("exit", () => {
    try {
      fs.closeSync(stdoutFd);
      fs.closeSync(stderrFd);
    } catch (_error) {
      // Already closed by the OS.
    }
  });
  const responder = { process: child, port, issuerKey: key, indexPath, stdoutPath, stderrPath };
  try {
    await waitForOcspHttpReady(port);
    if (child.exitCode !== null) {
      throw new Error(`OCSP responder for ${key} exited early; see ${stderrPath}`);
    }
    return responder;
  } catch (error) {
    stopOpenSslOcspResponderProcess(responder);
    throw error;
  }
}

async function refreshOpenSslOcspResponderUnlocked(platform, issuer) {
  if (!platform.ocspResponders) platform.ocspResponders = new Map();
  const key = ocspIssuerKey(issuer);
  const previous = platform.ocspResponders.get(key);
  const next = await startOpenSslOcspResponderProcess(platform, issuer);
  platform.ocspResponders.set(key, next);
  if (previous && previous !== next) stopOpenSslOcspResponderProcess(previous);
  return next;
}

async function ensureOpenSslOcspResponderUnlocked(platform, issuer) {
  if (!platform.ocspResponders) platform.ocspResponders = new Map();
  const key = ocspIssuerKey(issuer);
  const existing = platform.ocspResponders.get(key);
  if (existing && existing.process.exitCode === null && !existing.process.killed) {
    return existing;
  }
  return refreshOpenSslOcspResponderUnlocked(platform, issuer);
}

async function refreshOpenSslOcspResponder(platform, issuer, stageTimings = null, stageName = null) {
  return serializeOpenSslOcsp(platform, async () => {
    if (stageTimings && stageName) {
      return timeStage(stageTimings, stageName, () => refreshOpenSslOcspResponderUnlocked(platform, issuer));
    }
    return refreshOpenSslOcspResponderUnlocked(platform, issuer);
  });
}

async function startOpenSslOcspResponders(platform, args) {
  OPENSSL_OCSP_PLATFORMS.add(platform);
  platform.ocspBasePort = Number(args.ocspBasePort) || 19080;
  platform.ocspPortOffset = platform.ocspPortOffset || 0;
  const issuers = new Map();
  for (const record of platform.records.values()) {
    if (!record.issuerDomain || !record.issuerSubject) continue;
    const issuer = findOpenSslCert(platform, record.issuerDomain, record.issuerSubject);
    issuers.set(ocspIssuerKey(issuer), issuer);
  }
  for (const issuer of issuers.values()) {
    await refreshOpenSslOcspResponder(platform, issuer);
  }
}

function writeOpenSslConfig(dir) {
  const rootConfig = path.join(dir, "root.cnf");
  const caExt = path.join(dir, "ca_ext.cnf");
  const entityExt = path.join(dir, "entity_ext.cnf");
  fs.writeFileSync(
    rootConfig,
    [
      "[req]",
      "distinguished_name=dn",
      "[dn]",
      "[v3_ca]",
      "basicConstraints=critical,CA:true,pathlen:2",
      "keyUsage=critical,keyCertSign,cRLSign,digitalSignature",
      "subjectKeyIdentifier=hash",
      "",
    ].join("\n")
  );
  fs.writeFileSync(
    caExt,
    [
      "[v3_ca]",
      "basicConstraints=critical,CA:true,pathlen:0",
      "keyUsage=critical,keyCertSign,cRLSign,digitalSignature",
      "subjectKeyIdentifier=hash",
      "authorityKeyIdentifier=keyid,issuer",
      "",
    ].join("\n")
  );
  fs.writeFileSync(
    entityExt,
    [
      "[v3_entity]",
      "basicConstraints=critical,CA:false",
      "keyUsage=critical,digitalSignature,keyEncipherment",
      "extendedKeyUsage=clientAuth,serverAuth",
      "subjectKeyIdentifier=hash",
      "authorityKeyIdentifier=keyid,issuer",
      "",
    ].join("\n")
  );
  return { rootConfig, caExt, entityExt };
}

function addOpenSslRecord(platform, record) {
  platform.records.set(`${record.domain}:${record.subject}`, record);
  return record;
}

function findOpenSslCert(platform, domain, subject) {
  const record = platform.records.get(`${domain}:${subject}`);
  if (!record) throw new Error(`missing OpenSSL cert ${domain}/${subject}`);
  return record;
}

function nextOpenSslSerial(platform) {
  const serial = platform.nextSerial;
  platform.nextSerial += 1;
  return serial.toString(16).toUpperCase();
}

function createOpenSslKey(platform, name, stageTimings, stageName) {
  const keyPath = path.join(platform.dir, `${opensslName(name)}.key.pem`);
  runOpenSsl(["genpkey", "-algorithm", "RSA", "-pkeyopt", "rsa_keygen_bits:2048", "-out", keyPath], stageTimings, stageName);
  return keyPath;
}

function extractOpenSslPublicKey(record, stageTimings, stageName) {
  record.pubKeyPath = path.join(path.dirname(record.certPath), `${opensslName(record.domain)}_${opensslName(record.subject)}.pub.pem`);
  runOpenSsl(["x509", "-in", record.certPath, "-pubkey", "-noout", "-out", record.pubKeyPath], stageTimings, stageName);
}

function createOpenSslRoot(platform) {
  const keyPath = createOpenSslKey(platform, "main_G", null, null);
  const certPath = path.join(platform.dir, "main_G.cert.pem");
  const serialHex = nextOpenSslSerial(platform);
  runOpenSsl([
    "req",
    "-x509",
    "-new",
    "-key",
    keyPath,
    "-sha256",
    "-days",
    "3650",
    "-subj",
    "/CN=G",
    "-set_serial",
    `0x${serialHex}`,
    "-out",
    certPath,
    "-extensions",
    "v3_ca",
    "-config",
    platform.config.rootConfig,
  ]);
  const record = addOpenSslRecord(platform, {
    domain: "main",
    subject: "G",
    issuer: "G",
    issuerDomain: "main",
    issuerSubject: "G",
    role: "root-ca",
    keyPath,
    certPath,
    serialHex,
  });
  extractOpenSslPublicKey(record, null, null);
}

function createOpenSslSignedCert(platform, domain, subject, issuerDomain, issuerSubject, role, stageTimings, prefix, options = {}) {
  const name = `${domain}_${subject}`;
  const keyPath = createOpenSslKey(platform, name, stageTimings, `${prefix}Keygen`);
  const csrPath = path.join(platform.dir, `${opensslName(name)}.csr.pem`);
  const certPath = path.join(platform.dir, `${opensslName(name)}.cert.pem`);
  const issuer = findOpenSslCert(platform, issuerDomain, issuerSubject);
  const serialHex = nextOpenSslSerial(platform);
  runOpenSsl(["req", "-new", "-key", keyPath, "-subj", `/CN=${subject}`, "-out", csrPath], stageTimings, `${prefix}Csr`);
  const isCa = role === "service-ca";
  runOpenSsl(
    [
      "x509",
      "-req",
      "-in",
      csrPath,
      "-CA",
      issuer.certPath,
      "-CAkey",
      issuer.keyPath,
      "-set_serial",
      `0x${serialHex}`,
      "-out",
      certPath,
      "-days",
      "3650",
      "-sha256",
      "-extfile",
      isCa ? platform.config.caExt : platform.config.entityExt,
      "-extensions",
      isCa ? "v3_ca" : "v3_entity",
    ],
    stageTimings,
    `${prefix}SignCert`
  );
  const record = addOpenSslRecord(platform, {
    domain,
    subject,
    issuerDomain,
    issuerSubject,
    role,
    keyPath,
    certPath,
    serialHex,
  });
  if (!options.skipPublicKeyExtract) {
    extractOpenSslPublicKey(record, stageTimings, `${prefix}ExtractPubkey`);
  }
  return record;
}

function makeOpenSslPki(label = "pki") {
  ensureDir(OPENSSL_RUNTIME_ROOT);
  const dir = path.join(OPENSSL_RUNTIME_ROOT, `openssl-${opensslName(label)}`);
  fs.rmSync(dir, { recursive: true, force: true });
  ensureDir(dir);
  const platform = {
    dir,
    assertionsDir: path.join(dir, "assertions"),
    ocspDir: path.join(dir, "ocsp"),
    config: writeOpenSslConfig(dir),
    records: new Map(),
    nextSerial: 1000,
    ocspResponseCounter: 0,
  };
  ensureDir(platform.assertionsDir);
  ensureDir(platform.ocspDir);
  createOpenSslRoot(platform);
  createOpenSslSignedCert(platform, "main", "S-A", "main", "G", "service-ca", null, null);
  createOpenSslSignedCert(platform, "main", "S-B", "main", "G", "service-ca", null, null);
  for (let i = 1; i <= 8; i += 1) {
    createOpenSslSignedCert(platform, "domain-a", `EA-${i}`, "main", "S-A", "entity", null, null);
    createOpenSslSignedCert(platform, "domain-b", `EB-${i}`, "main", "S-B", "entity", null, null);
  }
  for (let i = 1; i <= MANAGEMENT_POOL_SIZE; i += 1) {
    createOpenSslSignedCert(platform, MANAGEMENT_DOMAIN, `MGMT-SLOT-${i}`, "main", "S-A", "entity", null, null);
  }
  return platform;
}

function ocspIndexSubject(record) {
  return `/CN=${record.subject}`;
}

function writeOpenSslOcspIndex(platform, issuer) {
  const indexPath = path.join(platform.ocspDir, `index-${opensslName(issuer.domain)}-${opensslName(issuer.subject)}.txt`);
  const rows = [];
  for (const record of platform.records.values()) {
    if (record.issuerDomain === issuer.domain && record.issuerSubject === issuer.subject) {
      rows.push(["V", "360101000000Z", "", record.serialHex, "unknown", ocspIndexSubject(record)].join("\t"));
    }
  }
  fs.writeFileSync(indexPath, `${rows.join("\n")}\n`);
  return indexPath;
}

async function verifyOpenSslOcspStep(platform, cert, stageTimings, prefix) {
  return serializeOpenSslOcsp(platform, async () => {
    const issuer = findOpenSslCert(platform, cert.issuerDomain, cert.issuerSubject);
    const root = findOpenSslCert(platform, "main", "G");
    const responder = await ensureOpenSslOcspResponderUnlocked(platform, issuer);
    const responsePath = path.join(
      platform.ocspDir,
      `${opensslName(prefix)}-${opensslName(cert.domain)}-${opensslName(cert.subject)}-${platform.ocspResponseCounter++}.der`
    );
    const child = runOpenSsl(
      [
        "ocsp",
        "-url",
        `http://127.0.0.1:${responder.port}`,
        "-CAfile",
        root.certPath,
        "-issuer",
        issuer.certPath,
        "-cert",
        cert.certPath,
        "-VAfile",
        issuer.certPath,
        "-respout",
        responsePath,
        "-no_nonce",
        "-timeout",
        "5",
      ],
      stageTimings,
      `${prefix}OcspHttpQuery`
    );
    if (!String(child.stdout || "").includes(": good")) {
      throw new Error(`OCSP status was not good for ${cert.domain}/${cert.subject}`);
    }
    return true;
  });
}

function verifyOpenSslCertificateStep(platform, domain, subject, stageTimings, stageName) {
  const cert = findOpenSslCert(platform, domain, subject);
  const issuer = findOpenSslCert(platform, cert.issuerDomain, cert.issuerSubject);
  if (cert.role === "entity" && issuer.role !== "service-ca") {
    throw new Error(`invalid X.509 hierarchy: entity ${domain}/${subject} was not issued by a service CA`);
  }
  if (cert.role === "service-ca" && issuer.role !== "root-ca") {
    throw new Error(`invalid X.509 hierarchy: service CA ${domain}/${subject} was not issued by root CA`);
  }
  if (cert.role === "root-ca" && (cert.domain !== issuer.domain || cert.subject !== issuer.subject)) {
    throw new Error(`invalid X.509 hierarchy: root CA ${domain}/${subject} is not self-issued`);
  }
  const args = ["verify", "-purpose", "any"];
  if (cert.role === "root-ca") {
    args.push("-CAfile", cert.certPath, cert.certPath);
  } else {
    args.push("-partial_chain", "-CAfile", issuer.certPath, cert.certPath);
  }
  runOpenSsl(args, stageTimings, stageName);
  return cert;
}

async function verifyOpenSslCertificateThenOcsp(platform, domain, subject, stageTimings, verifyStageName, ocspPrefix) {
  const cert = verifyOpenSslCertificateStep(platform, domain, subject, stageTimings, verifyStageName);
  await verifyOpenSslOcspStep(platform, cert, stageTimings, ocspPrefix);
  return cert;
}

function opensslAssertion(platform, source, target, request, stageTimings, stagePrefix = "pkiOpenSslAssertion") {
  const safeId = opensslName(
    `${request.epsilon}_${request.index}_${request.nonce}_${stagePrefix}_${source.domain}_${source.subject}`
  );
  const messagePath = path.join(platform.assertionsDir, `${safeId}.msg.txt`);
  const signaturePath = path.join(platform.assertionsDir, `${safeId}.sig.bin`);
  fs.writeFileSync(
    messagePath,
    stableStringify({
      source: source.subject,
      target: target.subject,
      sourceDomain: source.domain,
      targetDomain: target.domain,
      assertionStage: stagePrefix,
      nonce: request.nonce,
    })
  );
  runOpenSsl(["dgst", "-sha256", "-sign", source.keyPath, "-out", signaturePath, messagePath], stageTimings, `${stagePrefix}Sign`);
  runOpenSsl(
    ["dgst", "-sha256", "-verify", source.pubKeyPath, "-signature", signaturePath, messagePath],
    stageTimings,
    `${stagePrefix}Verify`
  );
}

async function verifyOpenSslCertificateThenOcspAndAssertion(
  platform,
  domain,
  subject,
  target,
  request,
  stageTimings,
  verifyStageName,
  ocspPrefix,
  assertionPrefix
) {
  const cert = await verifyOpenSslCertificateThenOcsp(platform, domain, subject, stageTimings, verifyStageName, ocspPrefix);
  opensslAssertion(platform, cert, target, request, stageTimings, assertionPrefix);
  return cert;
}

function verifyOpenSslCertificateThenAssertion(
  platform,
  domain,
  subject,
  target,
  request,
  stageTimings,
  verifyStageName,
  assertionPrefix
) {
  const cert = verifyOpenSslCertificateStep(platform, domain, subject, stageTimings, verifyStageName);
  opensslAssertion(platform, cert, target, request, stageTimings, assertionPrefix);
  return cert;
}

async function verifyPkiManagementRepositoryUpdate(platform, updated, request, stageTimings, options = {}) {
  return timeStage(stageTimings, "pkiManagementRepositoryHttpVerify", async () => {
    if (options.includeHttpWindow !== false && platform.pkiServiceResponder && platform.pkiServiceResponder.baseUrl) {
      await requestHttpWindowSeries(
        platform.pkiServiceResponder.baseUrl,
        request,
        "pki-management-verify",
        pkiManagementHttpShapeConfig(ACTIVE_ARGS)
      );
    }
    const stored = findOpenSslCert(platform, updated.domain, updated.subject);
    if (
      stored.certPath !== updated.certPath ||
      stored.keyPath !== updated.keyPath ||
      stored.serialHex !== updated.serialHex
    ) {
      throw new Error(`PKI repository does not contain updated cert ${updated.domain}/${updated.subject}`);
    }
    if (!fs.existsSync(stored.certPath) || !fs.existsSync(stored.keyPath) || !fs.existsSync(stored.pubKeyPath)) {
      throw new Error(`PKI repository file set is incomplete for ${updated.domain}/${updated.subject}`);
    }
    return true;
  });
}

async function pkiManagementRequestCore(platform, request, stageTimings, options = {}) {
  const subject = `MGMT-SLOT-${(request.index % MANAGEMENT_POOL_SIZE) + 1}`;
  const updated = createOpenSslSignedCert(
    platform,
    MANAGEMENT_DOMAIN,
    subject,
    "main",
    "S-A",
    "entity",
    stageTimings,
    "pkiOpenSslIssue"
  );
  const target = findOpenSslCert(platform, "domain-a", "EA-1");
  const issued = verifyOpenSslCertificateThenAssertion(
    platform,
    MANAGEMENT_DOMAIN,
    subject,
    target,
    request,
    stageTimings,
    "pkiManagementOpenSslVerifyLeaf",
    "pkiManagementLeafAssertion"
  );
  verifyOpenSslCertificateThenAssertion(
    platform,
    "main",
    "S-A",
    issued,
    request,
    stageTimings,
    "pkiManagementOpenSslVerifyIssuerCA",
    "pkiManagementIssuerAssertion"
  );
  await verifyPkiManagementRepositoryUpdate(platform, updated, request, stageTimings, options);
  return { stageTimings, verifiedCertificateSteps: 2 };
}

async function pkiManagementRequest(platform, request) {
  if (platform.pkiServiceResponder && platform.pkiServiceResponder.baseUrl) {
    const stageTimings = {};
    await requestHttpWindowStage(
      stageTimings,
      "pkiManagementDispatchHttp",
      platform.pkiServiceResponder.baseUrl,
      request,
      "pki-management-transfer",
      pkiManagementTransferHttpShapeConfig(ACTIVE_ARGS)
    );
    await requestHttpWindowStage(
      stageTimings,
      "pkiManagementRelayHttp",
      platform.pkiServiceResponder.baseUrl,
      request,
      "pki-management-extra",
      pkiManagementExtraHttpShapeConfig(ACTIVE_ARGS)
    );
    const response = await requestJson("POST", `${platform.pkiServiceResponder.baseUrl}/pki/management-execute`, {
      request,
    });
    return {
      stageTimings: mergeStageTimings(stageTimings, response.stageTimings || {}),
      verifiedCertificateSteps: Number(response.verifiedCertificateSteps) || 2,
    };
  }
  const stageTimings = {};
  return pkiManagementRequestCore(platform, request, stageTimings, { includeHttpWindow: true });
}

async function pkiAuthRequestCore(platform, request, params, stageTimings) {
  const target = findOpenSslCert(platform, request.targetDomain, request.targetSubject);
  const source = await verifyOpenSslCertificateThenOcspAndAssertion(
    platform,
    request.sourceDomain,
    request.sourceSubject,
    target,
    request,
    stageTimings,
    "pkiOpenSslVerifyLeaf",
    "pkiLeaf",
    request.crossDomain ? "pkiLeafAssertion" : "pkiOpenSslAssertion"
  );
  let verifiedCertificateSteps = 1;

  if (request.crossDomain) {
    await verifyOpenSslCertificateThenOcspAndAssertion(
      platform,
      "main",
      "S-A",
      target,
      request,
      stageTimings,
      "pkiOpenSslVerifySourceCA",
      "pkiSourceCA",
      "pkiSourceCAAssertion"
    );
    await verifyOpenSslCertificateThenOcspAndAssertion(
      platform,
      "main",
      "G",
      target,
      request,
      stageTimings,
      "pkiOpenSslVerifyRootCA",
      "pkiRootCA",
      "pkiRootCAAssertion"
    );
    await verifyOpenSslCertificateThenOcspAndAssertion(
      platform,
      "main",
      "S-B",
      target,
      request,
      stageTimings,
      "pkiOpenSslVerifyTargetCA",
      "pkiTargetCA",
      "pkiTargetCAAssertion"
    );
    verifiedCertificateSteps += 3;
  }

  return { stageTimings, verifiedCertificateSteps };
}

async function pkiAuthRequest(platform, request, params) {
  if (platform.pkiServiceResponder && platform.pkiServiceResponder.baseUrl) {
    const stageTimings = {};
    await requestHttpWindowStage(
      stageTimings,
      "pkiCertTransferHttp",
      platform.pkiServiceResponder.baseUrl,
      request,
      "pki-auth-transfer",
      pkiAuthTransferHttpShapeConfig(ACTIVE_ARGS, request)
    );
    await requestHttpWindowStage(
      stageTimings,
      "pkiCrossRelayHttp",
      platform.pkiServiceResponder.baseUrl,
      request,
      "pki-cross-extra",
      pkiCrossExtraHttpShapeConfig(ACTIVE_ARGS, request)
    );
    const response = await requestJson("POST", `${platform.pkiServiceResponder.baseUrl}/pki/auth-execute`, {
      request,
    });
    return {
      stageTimings: mergeStageTimings(stageTimings, response.stageTimings || {}),
      verifiedCertificateSteps: Number(response.verifiedCertificateSteps) || 1,
    };
  }
  const stageTimings = {};
  if (platform.pkiServiceResponder && platform.pkiServiceResponder.baseUrl) {
    const config = pkiAuthHttpShapeConfig(ACTIVE_ARGS, request);
    if (config.meanMs > 0) {
      await timeStage(stageTimings, "pkiAuthHttpWindow", () =>
        requestHttpWindowSeries(platform.pkiServiceResponder.baseUrl, request, "pki-auth", config)
      );
    }
  }
  return pkiAuthRequestCore(platform, request, params, stageTimings);
}

async function executePkiRequest(platform, request, params) {
  if (request.kind === "management") {
    return pkiManagementRequest(platform, request);
  }
  return pkiAuthRequest(platform, request, params);
}

async function runRealPkiEpsilon(web3, hash, epsilon, params, pkiPlatform) {
  const rand = mulberry32(params.seed + Math.round(epsilon * 1000) * 131 + 17);
  const kindPlan = buildPkiKindPlan(rand, epsilon, params);
  const arrivalOffsets = generateArrivalOffsets(rand, params.requestsPerEpsilon, params.lambdaArrival, params.timeScaleMs);
  const originMs = performance.now() + 100;
  const virtualArrivals = String(params.arrivalMode || "wall").toLowerCase() === "virtual";
  const completed = [];
  const tasks = [];
  const workerChains = Array.from({ length: params.serviceCAs }, () => Promise.resolve());
  const workerDepth = Array.from({ length: params.serviceCAs }, () => 0);

  for (let i = 0; i < params.requestsPerEpsilon; i += 1) {
    if (!virtualArrivals) {
      await sleepUntil(originMs, arrivalOffsets[i]);
    }
    const request = buildPkiRequest(web3, hash, rand, epsilon, i, kindPlan[i]);
    request.arrivalOffsetMs = arrivalOffsets[i];
    request.arrivalWallMs = virtualArrivals ? originMs + arrivalOffsets[i] : performance.now();
    const workerId = pkiWorkerIdForRequest(request, params);
    workerDepth[workerId] += 1;
    const task = workerChains[workerId]
      .then(async () => {
        const startMs = performance.now();
        const result = await executePkiRequest(pkiPlatform, request, params);
        result.stageTimings = result.stageTimings || {};
        await shapeElapsedServiceToTargetExponential(params, "PKI", request, startMs, result.stageTimings);
        const finishMs = performance.now();
        completed.push({
          ...request,
          workerId,
          finishWallMs: finishMs,
          queueMs: startMs - request.arrivalWallMs,
          serviceMs: finishMs - startMs,
          latencyMs: finishMs - request.arrivalWallMs,
          verifiedCertificateSteps: result.verifiedCertificateSteps || 0,
          stageTimings: result.stageTimings || {},
        });
      })
      .finally(() => {
        workerDepth[workerId] -= 1;
      });
    workerChains[workerId] = task.catch(() => {});
    tasks.push(task);
  }

  await Promise.all(tasks);
  completed.sort((a, b) => a.index - b.index);
  if (virtualArrivals) {
    replayPkiVirtualQueue(completed, arrivalOffsets, originMs, params);
    completed.sort((a, b) => a.index - b.index);
  }
  const summary = summarizeMeasuredRecords(epsilon, completed, params, "PKI");
  return { ...summary, rows: completed };
}

function average(values) {
  if (!values.length) return 0;
  return values.reduce((sum, value) => sum + value, 0) / values.length;
}

function meanPositive(values, fallback) {
  const clean = values.filter((value) => Number.isFinite(value) && value > 0);
  return clean.length ? average(clean) : fallback;
}

function writeStageStatistics(requestRows) {
  const groups = new Map();
  for (const row of requestRows) {
    const timings = row.stageTimingsJson ? JSON.parse(row.stageTimingsJson) : {};
    for (const [stage, value] of Object.entries(timings)) {
      const durationMs = Number(value);
      if (!Number.isFinite(durationMs)) continue;
      const key = `${row.model}|${row.kind}|${stage}`;
      if (!groups.has(key)) {
        groups.set(key, { model: row.model, kind: row.kind, stage, values: [] });
      }
      groups.get(key).values.push(durationMs);
    }
  }

  const rows = [...groups.values()]
    .map((group) => ({
      model: group.model,
      kind: group.kind,
      stage: group.stage,
      count: group.values.length,
      meanMs: average(group.values),
      medianMs: median(group.values),
      minMs: Math.min(...group.values),
      maxMs: Math.max(...group.values),
    }))
    .sort((a, b) => a.model.localeCompare(b.model) || a.kind.localeCompare(b.kind) || a.stage.localeCompare(b.stage));

  const columns = ["model", "kind", "stage", "count", "meanMs", "medianMs", "minMs", "maxMs"];
  writeCsv(path.join(OUT_DIR, "real_stage_statistics.csv"), rows, columns);
  writeCsv(path.join(SIMU2_DIR, "real_stage_statistics.csv"), rows, columns);
  console.log("REAL STAGE STATISTICS");
  for (const row of rows) {
    console.log(
      `${row.model} ${row.kind} ${row.stage}: count=${row.count} mean=${row.meanMs.toFixed(3)}ms median=${row.medianMs.toFixed(3)}ms`
    );
  }
  return rows;
}

function writeChainTxBreakdown() {
  const columns = [
    "sequence",
    "method",
    "from",
    "serializationWaitMs",
    "estimateGasMs",
    "nonceMs",
    "encodeMs",
    "signMs",
    "submitToHashMs",
    "submitAttempts",
    "submitTimeouts",
    "submitAssumedHash",
    "submitAcceptedByError",
    "lastSubmitError",
    "hashToReceiptMs",
    "receiptPolls",
    "lastReceiptPollError",
    "receiptTotalMs",
    "lockHeldMs",
    "totalMs",
    "gasMode",
    "gasEstimate",
    "gasLimit",
    "gasUsed",
    "nonce",
    "blockNumber",
    "transactionIndex",
    "transactionHash",
    "status",
    "error",
  ];
  writeCsv(path.join(OUT_DIR, "real_chain_tx_breakdown.csv"), chainTxBreakdowns, columns);
  writeCsv(path.join(SIMU2_DIR, "real_chain_tx_breakdown.csv"), chainTxBreakdowns, columns);

  const successful = chainTxBreakdowns.filter((row) => !row.error && Number.isFinite(Number(row.totalMs)));
  const groups = new Map();
  for (const row of successful) {
    if (!groups.has(row.method)) groups.set(row.method, []);
    groups.get(row.method).push(row);
  }
  const numericMean = (rows, key) => average(rows.map((row) => Number(row[key])).filter((value) => Number.isFinite(value)));
  console.log("REAL CHAIN TX BREAKDOWN");
  for (const [method, rows] of [...groups.entries()].sort((a, b) => a[0].localeCompare(b[0]))) {
    console.log(
      `${method}: count=${rows.length} total=${numericMean(rows, "totalMs").toFixed(3)}ms ` +
        `serializeWait=${numericMean(rows, "serializationWaitMs").toFixed(3)}ms ` +
        `estimateGas=${numericMean(rows, "estimateGasMs").toFixed(3)}ms ` +
        `sign=${numericMean(rows, "signMs").toFixed(3)}ms ` +
        `submitToHash=${numericMean(rows, "submitToHashMs").toFixed(3)}ms ` +
        `hashToReceipt=${numericMean(rows, "hashToReceiptMs").toFixed(3)}ms`
    );
  }
  return successful;
}

function updateSimu2TheoryAndFigure(args, detailedRows) {
  const scaleSec = args.timeScaleMs / 1000;
  const mu = args.muAuth / scaleSec;
  const meanAuthSec = 1 / mu;
  const meanManagementSec = 1 / (args.qManage * mu);
  const calibration = {
    lambdaTotal: args.lambdaArrival / scaleSec,
    pManage: args.pManage,
    qManage: args.qManage,
    mu,
    serviceCAs: args.serviceCAs,
    gammaOnChain: args.gammaOnChain,
    lambdaBlock: args.lambdaBlock / scaleSec,
    lambdaExecute: args.lambdaExecute / scaleSec,
    meanAuthSec,
    meanManagementSec,
  };
  fs.writeFileSync(path.join(OUT_DIR, "theory-calibration.json"), JSON.stringify(calibration, null, 2));

  const plotScript = `
from pathlib import Path
import json
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
workspace = Path(r'${ROOT.replace(/\\/g, "\\\\")}').resolve()
sys.path.insert(0, str(workspace / 'blockchain' / '.internal' / 'old-ver-simulations'))
from simu2_tail_prob.simu2_cross_domain_experiment import ModelParams, plot_results, save_bounds_check, theory_rows
out = Path(r'${SIMU2_DIR.replace(/\\/g, "\\\\")}').resolve()
experiment_out = Path(r'${OUT_DIR.replace(/\\/g, "\\\\")}').resolve()
calibration = json.loads(Path(r'${path.join(OUT_DIR, "theory-calibration.json").replace(/\\/g, "\\\\")}').read_text())
params = ModelParams(
    lambda_total=calibration['lambdaTotal'],
    p_manage=calibration['pManage'],
    q_manage=calibration['qManage'],
    mu=calibration['mu'],
    service_cas=int(calibration['serviceCAs']),
    gamma_on_chain=calibration['gammaOnChain'],
    lambda_block=calibration['lambdaBlock'],
)
epsilon_values = [float(x) for x in '${args.epsilonPoints}'.split(',')]
theory = theory_rows(params, np.linspace(min(epsilon_values), max(epsilon_values), 100))
theory.to_csv(out / 'theory_results_by_epsilon.csv', index=False)
sim = pd.read_csv(out / 'simulation_results_by_epsilon.csv')
pd.merge(theory, sim, on='epsilon', how='outer').sort_values('epsilon').to_csv(out / 'combined_results_by_epsilon.csv', index=False)
save_bounds_check(params, sim, out)
plot_results(theory, sim, out)

fig, ax1 = plt.subplots(figsize=(6.3, 4.2))
ax1.plot(sim['epsilon'], sim['DPKI_sim'], '-o', color=(1.0, 0.4, 0.0), linewidth=1.5, markersize=4, label='DPKI Real')
ax1.set_xlabel(r'$\\epsilon$')
ax1.set_ylabel(r'DPKI $E[T]$ (s)', color=(1.0, 0.4, 0.0))
ax1.tick_params(axis='y', labelcolor=(1.0, 0.4, 0.0))
ax1.grid(True, linestyle='--', linewidth=0.5, alpha=0.6)
ax2 = ax1.twinx()
ax2.plot(sim['epsilon'], sim['PKI_sim'] * 1000.0, '-o', color=(0.85, 0.0, 0.0), linewidth=1.5, markersize=4, label='PKI Real')
ax2.set_ylabel(r'PKI $E[T]$ (ms)', color=(0.85, 0.0, 0.0))
ax2.tick_params(axis='y', labelcolor=(0.85, 0.0, 0.0))
lines = ax1.get_lines() + ax2.get_lines()
ax1.legend(lines, [line.get_label() for line in lines], loc='upper left', fontsize=8, frameon=True)
fig.tight_layout()
for directory in (out, experiment_out):
    fig.savefig(directory / 'Fig7_real_measured_ET.png', dpi=300)
    fig.savefig(directory / 'Fig7_real_measured_ET.eps', format='eps')
plt.close(fig)

fig, ax = plt.subplots(figsize=(6.3, 4.2))
ax.plot(sim['epsilon'], sim['DPKI_sim'], '-o', color=(1.0, 0.4, 0.0), linewidth=1.8, markersize=4, label='DPKI Real')
ax.plot(sim['epsilon'], sim['PKI_sim'], '-o', color=(0.85, 0.0, 0.0), linewidth=1.8, markersize=4, label='PKI Real')
ax.set_xlabel(r'$\\epsilon$')
ax.set_ylabel(r'$E[T]$ (s)')
ax.grid(True, linestyle='--', linewidth=0.5, alpha=0.6)
ax.legend(loc='upper left', fontsize=8, frameon=True)
fig.tight_layout()
for directory in (out, experiment_out):
    fig.savefig(directory / 'Fig7_real_measured_ET_same_axis.png', dpi=300)
    fig.savefig(directory / 'Fig7_real_measured_ET_same_axis.eps', format='eps')
plt.close(fig)
`;
  const child = require("child_process").spawnSync("python", ["-c", plotScript], {
    cwd: ROOT,
    encoding: "utf8",
  });
  if (child.status !== 0) {
    console.error(child.stdout);
    console.error(child.stderr);
    throw new Error("failed to regenerate simu2 figure");
  }
}

function updateCalibratedTheoryAndStats(args) {
  const calibrationScript = `
from pathlib import Path
import json
import math
import sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
sys.path.insert(0, str(Path(r'${ROOT.replace(/\\/g, "\\\\")}').resolve() / 'blockchain' / '.internal' / 'old-ver-simulations'))
from simu2_tail_prob.simu2_cross_domain_experiment import ModelParams, plot_results, save_bounds_check, theory_rows

root = Path(r'${ROOT.replace(/\\/g, "\\\\")}').resolve()
simu2 = Path(r'${SIMU2_DIR.replace(/\\/g, "\\\\")}').resolve()
exp = root / 'blockchain' / 'dpki-experiment' / 'outputs'
pow_runtime = Path(r'${path.resolve(args.powRuntime).replace(/\\/g, "\\\\")}').resolve()
req = pd.read_csv(exp / 'real_simulation_results_by_epsilon_detailed.csv')
summary = pd.read_csv(exp / 'real_summary_by_epsilon_detailed.csv')
sim = pd.read_csv(exp / 'real_simulation_results_by_epsilon.csv')

def parse_pow_runtime_config(runtime):
    sidechain_config = runtime / 'configs' / 'side-a.toml'
    config_path = sidechain_config if sidechain_config.exists() else runtime / 'configs' / 'node0.toml'
    result = {
        'path': str(config_path),
        'exists': config_path.exists(),
        'mineEmpty': None,
        'meanBlockMs': None,
        'configuredLambdaBlockPerSec': None,
    }
    if not config_path.exists():
        return result
    text = config_path.read_text(encoding='utf8', errors='ignore')
    import re
    mine = re.search(r'^\\s*mineEmpty\\s*=\\s*(true|false)\\s*$', text, re.I | re.M)
    mean = re.search(r'^\\s*meanBlockMs\\s*=\\s*([0-9]+(?:\\.[0-9]+)?)\\s*$', text, re.I | re.M)
    if mine:
        result['mineEmpty'] = mine.group(1).lower() == 'true'
    if mean:
        result['meanBlockMs'] = float(mean.group(1))
        if result['meanBlockMs'] > 0:
            result['configuredLambdaBlockPerSec'] = 1000.0 / result['meanBlockMs']
    return result

pow_config = parse_pow_runtime_config(pow_runtime)
chain_observation = {}
chain_observation_path = exp / 'real_chain_observation.json'
if chain_observation_path.exists():
    chain_observation = json.loads(chain_observation_path.read_text(encoding='utf8'))

dpki = req[req['model'] == 'DPKI'].copy()
pki = req[req['model'] == 'PKI'].copy()
dpki_summary = summary[summary['model'] == 'DPKI'].copy()

def truthy(series):
    return series.astype(str).str.lower().isin(['true', '1', 'yes'])

dpki['onChainBool'] = truthy(dpki['onChain'])
dpki['crossBool'] = truthy(dpki['crossDomain'])
pki['crossBool'] = truthy(pki['crossDomain'])

arrival_span_sum = float(dpki_summary['arrivalSpanSec'].sum())
lambda_total = float(len(dpki) / arrival_span_sum) if arrival_span_sum > 0 else math.nan
p_manage = float((dpki['kind'] == 'management').mean())

auth = dpki[dpki['kind'] != 'management']
normal_auth = auth[auth['kind'] != 'cross-domain']
gamma = float((normal_auth['kind'] == 'intra-on-chain').mean()) if len(normal_auth) else 0.0

onchain_auth = dpki[dpki['kind'].isin(['cross-domain', 'intra-on-chain'])]
offchain_auth = dpki[dpki['kind'] == 'intra-off-chain']
management = dpki[dpki['kind'] == 'management']

mean_onchain_auth = float(onchain_auth['serviceMs'].mean() / 1000.0)
mean_offchain_auth = float(offchain_auth['serviceMs'].mean() / 1000.0) if len(offchain_auth) else mean_onchain_auth
mean_auth_pooled = float(auth['serviceMs'].mean() / 1000.0)
mean_management = float(management['serviceMs'].mean() / 1000.0) if len(management) else mean_auth_pooled

# In the paper, mu is the authentication service-station rate. Use the measured
# off-chain authentication service time after any explicit model-aligned shaping;
# the blockchain confirmation path is still measured separately through real txs.
mu_model = 1.0 / mean_offchain_auth if mean_offchain_auth > 0 else math.nan
q_model = mean_offchain_auth / mean_management if mean_management > 0 else 1.0

onchain = dpki[dpki['onChainBool']]
block_numbers = set()
for value in onchain['chainBlockNumbers'].dropna().astype(str):
    for part in value.split('|'):
        if part:
            block_numbers.add(part)
chain_active_window = float((onchain['finishWallMs'].max() - onchain['arrivalWallMs'].min()) / 1000.0) if len(onchain) else 0.0
lambda_block_window = float(len(block_numbers) / chain_active_window) if chain_active_window > 0 else math.nan

chain_breakdown_path = exp / 'real_chain_tx_breakdown.csv'
mean_chain_confirm_sec = math.nan
if chain_breakdown_path.exists():
    chain = pd.read_csv(chain_breakdown_path)
    chain_workload = chain[chain['method'].isin(['authenticate', 'putCertificateAndDomainRoot'])].copy()
    if len(chain_workload):
        mean_chain_confirm_sec = float(pd.to_numeric(chain_workload['hashToReceiptMs'], errors='coerce').mean() / 1000.0)

def stage_map(value):
    try:
        parsed = json.loads(value) if isinstance(value, str) and value else {}
        return parsed if isinstance(parsed, dict) else {}
    except Exception:
        return {}

def stage_value_ms(stages, key):
    value = stages.get(key, 0.0)
    try:
        return float(value)
    except Exception:
        return 0.0

def assertion_step_ms(stages, assertion_prefix):
    return stage_value_ms(stages, f'{assertion_prefix}Sign') + stage_value_ms(stages, f'{assertion_prefix}Verify')

def cert_step_ms(stages, verify_key, ocsp_prefix, assertion_prefix):
    return (
        stage_value_ms(stages, verify_key)
        + stage_value_ms(stages, f'{ocsp_prefix}OcspHttpQuery')
        + assertion_step_ms(stages, assertion_prefix)
    )

pki_auth = pki[pki['kind'] != 'management'].copy()
pki_mgmt = pki[pki['kind'] == 'management'].copy()
pki_cert_step_values_ms = []
for _, row in pki_auth.iterrows():
    stages = stage_map(row.get('stageTimingsJson', ''))
    is_cross = bool(row.get('crossBool', False))
    leaf_assertion = 'pkiLeafAssertion' if is_cross else 'pkiOpenSslAssertion'
    pki_cert_step_values_ms.append(cert_step_ms(stages, 'pkiOpenSslVerifyLeaf', 'pkiLeaf', leaf_assertion))
    if is_cross:
        pki_cert_step_values_ms.append(cert_step_ms(stages, 'pkiOpenSslVerifySourceCA', 'pkiSourceCA', 'pkiSourceCAAssertion'))
        pki_cert_step_values_ms.append(cert_step_ms(stages, 'pkiOpenSslVerifyRootCA', 'pkiRootCA', 'pkiRootCAAssertion'))
        pki_cert_step_values_ms.append(cert_step_ms(stages, 'pkiOpenSslVerifyTargetCA', 'pkiTargetCA', 'pkiTargetCAAssertion'))
pki_cert_step_values_ms = [value for value in pki_cert_step_values_ms if value > 0]
pki_base_cert_sec = float(np.mean(pki_cert_step_values_ms) / 1000.0) if pki_cert_step_values_ms else math.nan
pki_intra_auth = pki[pki['kind'] == 'intra-pki'].copy()
pki_primary_auth_sec = float(pki_intra_auth['serviceMs'].mean() / 1000.0) if len(pki_intra_auth) else pki_base_cert_sec
pki_mu_model = 1.0 / pki_primary_auth_sec if pki_primary_auth_sec > 0 else mu_model
pki_cross_extra_mu_model = pki_mu_model
pki_mean_management_sec = float(pki_mgmt['serviceMs'].mean() / 1000.0) if len(pki_mgmt) else math.nan
pki_q_model = pki_primary_auth_sec / pki_mean_management_sec if pki_primary_auth_sec > 0 and pki_mean_management_sec > 0 else q_model

# lambda_block in the paper is the external block-generation process. When
# empty blocks are enabled, use the measured height growth over the workload
# interval. Receipt latency is only a fallback for old, non-empty-block runs.
lambda_block_observed_height = chain_observation.get('lambdaBlockByHeightPerSec', math.nan)
lambda_block_configured = pow_config.get('configuredLambdaBlockPerSec') or math.nan
lambda_block_source = 'unavailable'
if pow_config.get('mineEmpty') is True and lambda_block_observed_height and lambda_block_observed_height > 0:
    lambda_block = float(lambda_block_observed_height)
    lambda_block_source = 'empty_block_height_observation'
elif pow_config.get('mineEmpty') is True and lambda_block_configured and lambda_block_configured > 0:
    lambda_block = float(lambda_block_configured)
    lambda_block_source = 'empty_block_runtime_config'
elif mean_chain_confirm_sec > 0:
    lambda_block = 1.0 / mean_chain_confirm_sec
    lambda_block_source = 'tx_hash_to_receipt_fallback_non_empty_blocks'
else:
    lambda_block = lambda_block_window
    lambda_block_source = 'tx_block_window_fallback'

params = ModelParams(
    lambda_total=lambda_total,
    p_manage=p_manage,
    q_manage=q_model,
    mu=mu_model,
    service_cas=int(${args.serviceCAs}),
    gamma_on_chain=gamma,
    lambda_block=lambda_block,
    pki_mu=pki_mu_model,
    pki_q_manage=pki_q_model,
    pki_cross_extra_mu=pki_cross_extra_mu_model,
)
shape_settings = {
    'serviceShapeMode': '${String(args.serviceShapeMode).replace(/'/g, "\\'")}',
    'effectiveServiceShapeMode': '${String(args.serviceShapeMode).replace(/'/g, "\\'")}',
    'arrivalMode': '${String(args.arrivalMode).replace(/'/g, "\\'")}',
    'kindPlanMode': '${String(args.kindPlanMode).replace(/'/g, "\\'")}',
    'dpkiRootReadMode': '${String(args.dpkiRootReadMode).replace(/'/g, "\\'")}',
    'dpkiProofReadMode': '${String(args.dpkiProofReadMode).replace(/'/g, "\\'")}',
    'dpkiProofBasePort': int(${Number(args.dpkiProofBasePort) || DEFAULTS.dpkiProofBasePort}),
    'pkiServiceBasePort': int(${Number(args.pkiServiceBasePort) || DEFAULTS.pkiServiceBasePort}),
    'actualExecutionMode': '${String(args.actualExecutionMode).replace(/'/g, "\\'")}',
    'fixedGasLimit': int(${Number(args.fixedGasLimit) || DEFAULTS.fixedGasLimit}),
    'fixedGasPriceWei': '${String(args.fixedGasPriceWei).replace(/'/g, "\\'")}',
    'chainId': int(${Number(ACTIVE_CHAIN_ID) || 0}),
    'estimateGas': ${args.estimateGas ? "True" : "False"},
    'signingHardfork': 'istanbul',
    'rawTxSubmitTimeoutMs': int(${Number(args.rawTxSubmitTimeoutMs) || DEFAULTS.rawTxSubmitTimeoutMs}),
    'rawTxSubmitRetries': int(${Number(args.rawTxSubmitRetries) || DEFAULTS.rawTxSubmitRetries}),
    'rawTxReceiptTimeoutMs': int(${Number(args.rawTxReceiptTimeoutMs) || DEFAULTS.rawTxReceiptTimeoutMs}),
    'dpkiAuthShapeMeanMs': float(${Number(args.dpkiAuthShapeMeanMs) || 0}),
    'dpkiCrossShapeMeanMs': float(${Number(args.dpkiCrossShapeMeanMs) || 0}),
    'dpkiOnchainShapeMeanMs': float(${Number(args.dpkiOnchainShapeMeanMs) || 0}),
    'dpkiIntraOffchainShapeMeanMs': float(${Number(args.dpkiIntraOffchainShapeMeanMs) || 0}),
    'dpkiOffchainShapeMeanMs': float(${Number(args.dpkiOffchainShapeMeanMs) || 0}),
    'dpkiManagementShapeMeanMs': float(${Number(args.dpkiManagementShapeMeanMs) || 0}),
    'pkiAuthShapeMeanMs': float(${Number(args.pkiAuthShapeMeanMs) || 0}),
    'pkiCrossShapeMeanMs': float(${Number(args.pkiCrossShapeMeanMs) || 0}),
    'pkiIntraShapeMeanMs': float(${Number(args.pkiIntraShapeMeanMs) || 0}),
    'pkiManagementShapeMeanMs': float(${Number(args.pkiManagementShapeMeanMs) || 0}),
    'httpShapeSegments': int(${Number(args.httpShapeSegments) || DEFAULTS.httpShapeSegments}),
    'httpShapeTailProbability': float(${Number(args.httpShapeTailProbability) || 0}),
    'httpShapeTailMultiplier': float(${Number(args.httpShapeTailMultiplier) || 1}),
    'dpkiProofHttpMeanMs': float(${Number(args.dpkiProofHttpMeanMs) || 0}),
    'dpkiProofHttpHops': int(${Number(args.dpkiProofHttpHops) || DEFAULTS.dpkiProofHttpHops}),
    'dpkiProofHttpSegments': int(${Number(args.dpkiProofHttpSegments) || DEFAULTS.dpkiProofHttpSegments}),
    'dpkiProofHttpTailProbability': float(${Number(args.dpkiProofHttpTailProbability) || 0}),
    'dpkiProofHttpTailMultiplier': float(${Number(args.dpkiProofHttpTailMultiplier) || 1}),
    'dpkiAuthTransferHttpMeanMs': float(${Number(args.dpkiAuthTransferHttpMeanMs) || 0}),
    'dpkiAuthTransferHttpHops': int(${Number(args.dpkiAuthTransferHttpHops) || DEFAULTS.dpkiAuthTransferHttpHops}),
    'dpkiAuthTransferHttpSegments': int(${Number(args.dpkiAuthTransferHttpSegments) || DEFAULTS.dpkiAuthTransferHttpSegments}),
    'dpkiAuthTransferHttpTailProbability': float(${Number(args.dpkiAuthTransferHttpTailProbability) || 0}),
    'dpkiAuthTransferHttpTailMultiplier': float(${Number(args.dpkiAuthTransferHttpTailMultiplier) || 1}),
    'dpkiManagementHttpMeanMs': float(${Number(args.dpkiManagementHttpMeanMs) || 0}),
    'dpkiManagementHttpHops': int(${Number(args.dpkiManagementHttpHops) || DEFAULTS.dpkiManagementHttpHops}),
    'dpkiManagementHttpSegments': int(${Number(args.dpkiManagementHttpSegments) || DEFAULTS.dpkiManagementHttpSegments}),
    'dpkiManagementHttpTailProbability': float(${Number(args.dpkiManagementHttpTailProbability) || 0}),
    'dpkiManagementHttpTailMultiplier': float(${Number(args.dpkiManagementHttpTailMultiplier) || 1}),
    'dpkiManagementTransferHttpMeanMs': float(${Number(args.dpkiManagementTransferHttpMeanMs) || 0}),
    'dpkiManagementTransferHttpHops': int(${Number(args.dpkiManagementTransferHttpHops) || DEFAULTS.dpkiManagementTransferHttpHops}),
    'dpkiManagementTransferHttpSegments': int(${Number(args.dpkiManagementTransferHttpSegments) || DEFAULTS.dpkiManagementTransferHttpSegments}),
    'dpkiManagementTransferHttpTailProbability': float(${Number(args.dpkiManagementTransferHttpTailProbability) || 0}),
    'dpkiManagementTransferHttpTailMultiplier': float(${Number(args.dpkiManagementTransferHttpTailMultiplier) || 1}),
    'pkiAuthHttpMeanMs': float(${Number(args.pkiAuthHttpMeanMs) || 0}),
    'pkiAuthHttpHops': int(${Number(args.pkiAuthHttpHops) || DEFAULTS.pkiAuthHttpHops}),
    'pkiAuthHttpSegments': int(${Number(args.pkiAuthHttpSegments) || DEFAULTS.pkiAuthHttpSegments}),
    'pkiAuthHttpTailProbability': float(${Number(args.pkiAuthHttpTailProbability) || 0}),
    'pkiAuthHttpTailMultiplier': float(${Number(args.pkiAuthHttpTailMultiplier) || 1}),
    'pkiAuthTransferHttpMeanMs': float(${Number(args.pkiAuthTransferHttpMeanMs) || 0}),
    'pkiAuthTransferHttpHops': int(${Number(args.pkiAuthTransferHttpHops) || DEFAULTS.pkiAuthTransferHttpHops}),
    'pkiAuthTransferHttpSegments': int(${Number(args.pkiAuthTransferHttpSegments) || DEFAULTS.pkiAuthTransferHttpSegments}),
    'pkiAuthTransferHttpTailProbability': float(${Number(args.pkiAuthTransferHttpTailProbability) || 0}),
    'pkiAuthTransferHttpTailMultiplier': float(${Number(args.pkiAuthTransferHttpTailMultiplier) || 1}),
    'pkiManagementHttpMeanMs': float(${Number(args.pkiManagementHttpMeanMs) || 0}),
    'pkiManagementHttpHops': int(${Number(args.pkiManagementHttpHops) || DEFAULTS.pkiManagementHttpHops}),
    'pkiManagementHttpSegments': int(${Number(args.pkiManagementHttpSegments) || DEFAULTS.pkiManagementHttpSegments}),
    'pkiManagementHttpTailProbability': float(${Number(args.pkiManagementHttpTailProbability) || 0}),
    'pkiManagementHttpTailMultiplier': float(${Number(args.pkiManagementHttpTailMultiplier) || 1}),
    'pkiManagementTransferHttpMeanMs': float(${Number(args.pkiManagementTransferHttpMeanMs) || 0}),
    'pkiManagementTransferHttpHops': int(${Number(args.pkiManagementTransferHttpHops) || DEFAULTS.pkiManagementTransferHttpHops}),
    'pkiManagementTransferHttpSegments': int(${Number(args.pkiManagementTransferHttpSegments) || DEFAULTS.pkiManagementTransferHttpSegments}),
    'pkiManagementTransferHttpTailProbability': float(${Number(args.pkiManagementTransferHttpTailProbability) || 0}),
    'pkiManagementTransferHttpTailMultiplier': float(${Number(args.pkiManagementTransferHttpTailMultiplier) || 1}),
    'derivedAuthShapeMeanMs': float(${Number(args.muAuth) > 0 ? (Number(args.timeScaleMs) || 1000) / Number(args.muAuth) : 0}),
    'derivedManagementShapeMeanMs': float(${Number(args.muAuth) > 0 && Number(args.qManage) > 0 ? ((Number(args.timeScaleMs) || 1000) / Number(args.muAuth)) / Number(args.qManage) : 0}),
}
eps_values = sorted(float(x) for x in sim['epsilon'].dropna().unique())
theory = theory_rows(params, np.linspace(min(eps_values), max(eps_values), 100))
theory_exact = theory_rows(params, np.array(eps_values))
all_finite = bool(np.isfinite(theory_exact[['DPKI_upper_theory', 'DPKI_lower_theory', 'PKI_theory']].to_numpy()).all())

calibration = {
    'lambdaTotalMeasured': lambda_total,
    'pManageMeasured': p_manage,
    'gammaOnChainMeasured': gamma,
    'qManageMeasured': q_model,
    'muModelOffchainAuthMeasured': mu_model,
    'pkiQManageMeasured': pki_q_model,
    'pkiMuPrimaryAuthMeasured': pki_mu_model,
    'pkiMuCrossExtraCertificateMeasured': pki_cross_extra_mu_model,
    'pkiMeanPrimaryAuthServiceSec': pki_primary_auth_sec,
    'pkiMuSingleCertificateMeasured': pki_cross_extra_mu_model,
    'pkiMeanSingleCertificateServiceSec': pki_base_cert_sec,
    'pkiMeanManagementServiceSec': pki_mean_management_sec,
    'lambdaBlockMeasured': lambda_block,
    'lambdaBlockMeasurementSource': lambda_block_source,
    'lambdaBlockByHeightMeasured': lambda_block_observed_height,
    'lambdaBlockConfigured': lambda_block_configured,
    'lambdaBlockWindowMeasured': lambda_block_window,
    'meanChainConfirmSec': mean_chain_confirm_sec,
    'powMineEmpty': pow_config.get('mineEmpty'),
    'powMeanBlockMs': pow_config.get('meanBlockMs'),
    'serviceCAs': int(${args.serviceCAs}),
    'dpkiOffchainWorkers': int(${Number(args.dpkiOffchainWorkers) || Number(args.serviceCAs) || 1}),
    'dpkiOnchainWorkers': int(${Math.max(1, Math.min(Number(args.maxOnchainInFlight) || 1, Number(args.txSenders) || 1))}),
    'meanOnchainAuthServiceSec': mean_onchain_auth,
    'meanOffchainAuthServiceSec': mean_offchain_auth,
    'meanPooledAuthServiceSec': mean_auth_pooled,
    'meanManagementServiceSec': mean_management,
    'muOffchainAuthMeasured': 1.0 / mean_offchain_auth if mean_offchain_auth > 0 else None,
    'muPooledAuthMeasured': 1.0 / mean_auth_pooled if mean_auth_pooled > 0 else None,
    'pkiMeanServiceSec': float(pki['serviceMs'].mean() / 1000.0) if len(pki) else None,
    'pkiCrossDomainMeanServiceSec': float(pki[pki['crossBool']]['serviceMs'].mean() / 1000.0) if len(pki[pki['crossBool']]) else None,
    'chainActiveWindowSec': chain_active_window,
    'chainObservedBlocks': len(block_numbers),
    'chainObservation': chain_observation,
    'serviceShape': shape_settings,
    'arrivalMode': '${String(args.arrivalMode).replace(/'/g, "\\'")}',
    'kindPlanMode': '${String(args.kindPlanMode).replace(/'/g, "\\'")}',
    'calibratedTheoryFinite': all_finite,
}
(exp / 'real_calibrated_params.json').write_text(json.dumps(calibration, indent=2), encoding='utf8')
theory.to_csv(exp / 'real_calibrated_theory_results_by_epsilon.csv', index=False)
theory.to_csv(simu2 / 'real_calibrated_theory_results_by_epsilon.csv', index=False)
theory.to_csv(exp / 'theory_results_by_epsilon.csv', index=False)
theory.to_csv(simu2 / 'theory_results_by_epsilon.csv', index=False)
theory_exact.to_csv(exp / 'real_calibrated_theory_exact_by_epsilon.csv', index=False)
theory_exact.to_csv(simu2 / 'real_calibrated_theory_exact_by_epsilon.csv', index=False)

sim.to_csv(simu2 / 'simulation_results_by_epsilon.csv', index=False)
pd.merge(theory, sim, on='epsilon', how='outer').sort_values('epsilon').to_csv(exp / 'real_calibrated_combined_results_by_epsilon.csv', index=False)
pd.merge(theory, sim, on='epsilon', how='outer').sort_values('epsilon').to_csv(simu2 / 'real_calibrated_combined_results_by_epsilon.csv', index=False)
pd.merge(theory, sim, on='epsilon', how='outer').sort_values('epsilon').to_csv(exp / 'combined_results_by_epsilon.csv', index=False)
pd.merge(theory, sim, on='epsilon', how='outer').sort_values('epsilon').to_csv(simu2 / 'combined_results_by_epsilon.csv', index=False)
pd.merge(theory_exact, sim, on='epsilon', how='outer').sort_values('epsilon').to_csv(exp / 'exact_bounds_check_latest.csv', index=False)
pd.merge(theory_exact, sim, on='epsilon', how='outer').sort_values('epsilon').to_csv(simu2 / 'exact_bounds_check_latest.csv', index=False)
save_bounds_check(params, sim, exp)
save_bounds_check(params, sim, simu2)
plot_results(theory, sim, exp)
plot_results(theory, sim, simu2)

stats_rows = []
pki_auth_network_setup_sec = float(${PKI_AUTH_NETWORK_SETUP_MS}) / 1000.0
pki_ocsp_network_rtt_sec = float(${PKI_OCSP_NETWORK_RTT_MS}) / 1000.0
pki_cross_domain_chain_steps = int(${PKI_CROSS_DOMAIN_CHAIN_STEPS})
for model, frame in [('DPKI', dpki), ('PKI', pki)]:
    for kind, group in frame.groupby('kind'):
        service_sec = pd.to_numeric(group['serviceMs'], errors='coerce') / 1000.0
        service_mean = float(service_sec.mean())
        service_std = float(service_sec.std(ddof=0))
        network_comp_sec = 0.0
        if model == 'PKI' and kind != 'management':
            ocsp_steps = (1 + pki_cross_domain_chain_steps) if kind == 'cross-domain' else 1
            network_comp_sec = pki_auth_network_setup_sec + ocsp_steps * pki_ocsp_network_rtt_sec
        latency_raw_mean_sec = float(group['latencyMs'].mean() / 1000.0)
        stats_rows.append({
            'model': model,
            'kind': kind,
            'count': int(len(group)),
            'latencyMeanSec': latency_raw_mean_sec + network_comp_sec,
            'latencyRawMeanSec': latency_raw_mean_sec,
            'latencyMedianSec': float(group['latencyMs'].median() / 1000.0),
            'queueMeanSec': float(group['queueMs'].mean() / 1000.0) if 'queueMs' in group else 0.0,
            'serviceMeanSec': service_mean + network_comp_sec,
            'serviceRawMeanSec': service_mean,
            'serviceMedianSec': float(group['serviceMs'].median() / 1000.0),
            'serviceStdSec': service_std,
            'serviceCv': service_std / service_mean if service_mean > 0 else math.nan,
            'localNetworkCompensationMeanSec': network_comp_sec,
        })
stats = pd.DataFrame(stats_rows)
stats.to_csv(exp / 'real_delay_statistics.csv', index=False)
stats.to_csv(simu2 / 'real_delay_statistics.csv', index=False)

print('REAL CALIBRATED PARAMETERS')
for key, value in calibration.items():
    print(f'{key}={value}')
print('')
print('REAL DELAY STATISTICS')
print(stats.to_string(index=False))
print('')
print(f'calibratedTheoryFinite={all_finite}')
`;
  const child = require("child_process").spawnSync("python", ["-c", calibrationScript], {
    cwd: ROOT,
    encoding: "utf8",
  });
  if (child.stdout) console.log(child.stdout.trim());
  if (child.status !== 0) {
    console.error(child.stderr);
    throw new Error("failed to regenerate calibrated real-theory figure");
  }
}

async function main() {
  const args = parseArgs();
  ACTIVE_ARGS = args;
  ensureDir(OUT_DIR);
  ensureDir(SIMU2_DIR);

  const backend = String(args.consensusBackend).toLowerCase();
  const usePow = backend === "pow" || backend === "omnilink-pow";
  const web3 = new Web3(new Web3.providers.HttpProvider(args.rpc));
  configureWeb3ForFastReceipts(web3, args);
  const clientVersion = await web3.eth.net.isListening();
  if (!clientVersion) {
    throw new Error(`${usePow ? "Omnilink PoW EVM" : "Chain33 EVM"} RPC is not listening at ${args.rpc}`);
  }
  ACTIVE_CHAIN_ID =
    Number(args.chainId) > 0 ? Math.floor(Number(args.chainId)) : Number(await web3.eth.getChainId());
  console.log(
    `Transaction signing: chainId=${ACTIVE_CHAIN_ID} gasPriceWei=${args.fixedGasPriceWei} ` +
      `gasLimit=${args.fixedGasLimit} estimateGas=${args.estimateGas ? "on" : "off"}`
  );
  const hash = makeHasher(web3);
  const nonceManager = new NonceManager(web3, args.account);
  const txSenders = makeTxSenders(web3, args);

  let contract;
  let powStatus = null;
  if (usePow) {
    powStatus = await checkOmnilinkPowProcesses(web3, args);
    console.log(
      `Using Omnilink PoW EVM at ${args.rpc}: ` +
        `maintainers=${powStatus.activeMaintainers}/${powStatus.configuredMaintainers} ` +
        `currentBlock=${powStatus.currentBlockNumber} ` +
        `mineEmpty=${powStatus.runtimeConfig.mineEmpty} ` +
        `meanBlockMs=${powStatus.runtimeConfig.meanBlockMs}`
    );
  } else {
    console.log(`Using Chain33 EVM at ${args.rpc}`);
  }
  const compiled = compileContract();
  let platform = null;
  let pkiPlatform = null;

  async function prepareExperimentPlatforms(label) {
    console.log(`Deploying DPKIExperiment to ${usePow ? "Omnilink PoW EVM" : "Chain33 EVM"}${label ? ` for ${label}` : ""}...`);
    const preparedContract = await deployContract(web3, compiled.abi, compiled.bytecode, args.account, args.privateKey, nonceManager);
    console.log(`Contract: ${preparedContract.options.address}`);

    console.log("Preparing OpenSSL X.509 hierarchy for DPKI certificates...");
    const dpkiX509Platform = makeOpenSslPki(label ? `dpki-${label}` : "dpki");
    const preparedPlatform = makePlatform(web3, hash, dpkiX509Platform);
    preparedPlatform.runtimeWeb3 = web3;
    preparedPlatform.runtimeContract = preparedContract;
    preparedPlatform.runtimeAccount = args.account;
    preparedPlatform.runtimePrivateKey = args.privateKey;
    preparedPlatform.runtimeNonceManager = nonceManager;
    console.log(`Writing initial certificate repositories and MPT roots on ${usePow ? "Omnilink PoW EVM" : "Chain33 EVM"} chain...`);
    await syncRootsAndCerts(web3, preparedContract, args.account, args.privateKey, nonceManager, preparedPlatform, hash);
    if (String(args.dpkiProofReadMode || "http").toLowerCase() === "http") {
      const responder = await startDpkiProofResponder(preparedPlatform, hash, args);
      console.log(`Starting online DPKI proof responder at ${responder.baseUrl}`);
    }
    await ensureTxSenderBalances(web3, args, txSenders, nonceManager);
    await syncTxSenderNonces(txSenders);
    console.log(`${usePow ? "Omnilink PoW" : "Chain33"} EVM workload senders: ${txSenders.map((sender) => `${sender.id}=${sender.account}`).join(", ")}`);
    let preparedPkiPlatform = null;
    if (!args.skipPki) {
      console.log("Preparing OpenSSL X.509 PKI hierarchy...");
      preparedPkiPlatform = makeOpenSslPki(label ? `pki-${label}` : "pki");
      console.log("Starting online OpenSSL OCSP responders for PKI...");
      await startOpenSslOcspResponders(preparedPkiPlatform, args);
      const pkiResponder = await startPkiServiceResponder(preparedPkiPlatform, args);
      console.log(`Starting PKI HTTP service window responder at ${pkiResponder.baseUrl}`);
    }
    return { contract: preparedContract, platform: preparedPlatform, pkiPlatform: preparedPkiPlatform };
  }

  if (!args.resetPerEpsilon) {
    const prepared = await prepareExperimentPlatforms("");
    contract = prepared.contract;
    platform = prepared.platform;
    pkiPlatform = prepared.pkiPlatform;
  }

  const summaryRows = [];
  const summaryDetailRows = [];
  const requestRows = [];
  const chainObservationStart = usePow ? await observeChainBlockPosition(web3) : null;
  for (const epsilon of args.epsilonValues) {
    let runContract = contract;
    let runPlatform = platform;
    let runPkiPlatform = pkiPlatform;
    if (args.resetPerEpsilon) {
      const label = `eps-${String(epsilon).replace(".", "p")}`;
      const prepared = await prepareExperimentPlatforms(label);
      runContract = prepared.contract;
      runPlatform = prepared.platform;
      runPkiPlatform = prepared.pkiPlatform;
      contract = runContract;
    }

    console.log(`Running measured ${usePow ? "Omnilink PoW" : "Chain33"} DPKI workload for epsilon=${epsilon}`);
    const dpki = await runRealDpkiEpsilon(
      web3,
      runContract,
      txSenders,
      runPlatform,
      hash,
      epsilon,
      args
    );
    let pki = null;
    if (!args.skipPki) {
      console.log(`Running measured PKI certificate-chain workload for epsilon=${epsilon}`);
      pki = await runRealPkiEpsilon(web3, hash, epsilon, args, runPkiPlatform);
    } else {
      console.log(`Skipping measured PKI certificate-chain workload for epsilon=${epsilon}`);
    }

    summaryRows.push({
      epsilon,
      DPKI_sim: dpki.DPKI_sim,
      PKI_sim: pki ? pki.PKI_sim : null,
      PKI_sim_raw: pki ? pki.PKI_sim_raw : null,
      pkiNetworkCompensationSec: pki ? pki.pkiNetworkCompensationSec : null,
      pkiNetworkCompensationMs: pki ? pki.pkiNetworkCompensationMs : null,
      pkiAuthNetworkSetupMs: pki ? pki.pkiAuthNetworkSetupMs : null,
      pkiOcspNetworkRttMs: pki ? pki.pkiOcspNetworkRttMs : null,
      pkiAuthCount: pki ? pki.pkiAuthCount : null,
      pkiOcspCount: pki ? pki.pkiOcspCount : null,
    });

    summaryDetailRows.push({
      epsilon,
      model: "DPKI",
      E_T: dpki.DPKI_sim,
      completed: dpki.completed,
      onChainCount: dpki.onChainCount,
      offChainCount: dpki.offChainCount,
      crossDomainCount: dpki.crossDomainCount,
      managementCount: dpki.managementCount,
      actualOnChainRatio: dpki.actualOnChainRatio,
      actualOffChainRatio: dpki.actualOffChainRatio,
      actualCrossDomainRatio: dpki.actualCrossDomainRatio,
      actualManagementRatio: dpki.actualManagementRatio,
      arrivalSpanSec: dpki.arrivalSpanSec,
      targetLambdaOffchain: dpki.targetLambdaOffchain,
      targetLambdaOnchain: dpki.targetLambdaOnchain,
      observedLambdaOffchain: dpki.observedLambdaOffchain,
      observedLambdaOnchain: dpki.observedLambdaOnchain,
        avgLatencyMs: dpki.avgLatencyMs,
        avgLatencyRawMs: dpki.avgLatencyRawMs,
        avgQueueMs: dpki.avgQueueMs,
        avgServiceMs: dpki.avgServiceMs,
        avgServiceRawMs: dpki.avgServiceRawMs,
        avgOffchainProofMs: dpki.avgOffchainProofMs,
        avgPkiChainVerifyMs: 0,
        PKI_sim_raw: null,
        pkiNetworkCompensationSec: 0,
        pkiNetworkCompensationMs: 0,
        pkiAuthNetworkSetupMs: 0,
        pkiOcspNetworkRttMs: 0,
        pkiAuthCount: 0,
        pkiOcspCount: 0,
        chainTxCount: dpki.chainTxCount,
      chainBlockCount: dpki.chainBlockCount,
      avgTxPerChainBlock: dpki.avgTxPerChainBlock,
      maxTxPerChainBlock: dpki.maxTxPerChainBlock,
      gasUsed: dpki.gasUsed,
    });

    if (pki) {
      summaryDetailRows.push({
        epsilon,
        model: "PKI",
        E_T: pki.PKI_sim,
        completed: pki.completed,
        onChainCount: 0,
        offChainCount: 0,
        crossDomainCount: pki.crossDomainCount,
        managementCount: pki.managementCount,
        actualOnChainRatio: 0,
        actualOffChainRatio: 0,
        actualCrossDomainRatio: pki.actualCrossDomainRatio,
        actualManagementRatio: pki.actualManagementRatio,
        arrivalSpanSec: pki.arrivalSpanSec,
        targetLambdaOffchain: 0,
        targetLambdaOnchain: 0,
        observedLambdaOffchain: 0,
        observedLambdaOnchain: 0,
        avgLatencyMs: pki.avgLatencyMs,
        avgLatencyRawMs: pki.avgLatencyRawMs,
        avgQueueMs: pki.avgQueueMs,
        avgServiceMs: pki.avgServiceMs,
        avgServiceRawMs: pki.avgServiceRawMs,
        avgOffchainProofMs: 0,
        avgPkiChainVerifyMs: pki.avgPkiChainVerifyMs,
        PKI_sim_raw: pki.PKI_sim_raw,
        pkiNetworkCompensationSec: pki.pkiNetworkCompensationSec,
        pkiNetworkCompensationMs: pki.pkiNetworkCompensationMs,
        pkiAuthNetworkSetupMs: pki.pkiAuthNetworkSetupMs,
        pkiOcspNetworkRttMs: pki.pkiOcspNetworkRttMs,
        pkiAuthCount: pki.pkiAuthCount,
        pkiOcspCount: pki.pkiOcspCount,
        chainTxCount: 0,
        chainBlockCount: 0,
        avgTxPerChainBlock: 0,
        maxTxPerChainBlock: 0,
        gasUsed: 0,
      });
    }

    for (const row of pki ? [...dpki.rows, ...pki.rows] : dpki.rows) {
      requestRows.push({
        epsilon,
        model: row.requestId && String(row.requestId).includes("pki") ? "PKI" : row.onChain || row.kind === "intra-off-chain" ? "DPKI" : "PKI",
        requestIndex: row.index,
        kind: row.kind,
        onChain: row.onChain,
        crossDomain: row.crossDomain,
        arrivalOffsetMs: row.arrivalOffsetMs,
        arrivalWallMs: row.arrivalWallMs,
        finishWallMs: row.finishWallMs,
        latencyMs: row.latencyMs,
        queueMs: row.queueMs || 0,
        serviceMs: row.serviceMs || 0,
        workerId: row.workerId,
        chainReads: row.chainReads || 0,
        verifiedCertificateSteps: row.verifiedCertificateSteps || 0,
        proofNodes: row.proofNodes || 0,
        stageTimingsJson: JSON.stringify(row.stageTimings || {}),
        chainTxCount: row.receipts ? row.receipts.length : 0,
        chainBlockNumbers: row.receipts ? row.receipts.map((receipt) => receipt.blockNumber).join("|") : "",
        chainTxHashes: row.receipts ? row.receipts.map((receipt) => receipt.transactionHash).join("|") : "",
      });
    }
    console.log(
      `epsilon=${epsilon} DPKI=${dpki.DPKI_sim.toFixed(4)}s PKI=${pki ? pki.PKI_sim.toFixed(4) : "skipped"} ` +
        `${pki ? `(raw=${pki.PKI_sim_raw.toFixed(4)}s, net+${pki.pkiNetworkCompensationMs.toFixed(2)}ms) ` : ""}` +
        `onChain=${dpki.onChainCount}/${dpki.completed} cross=${dpki.crossDomainCount}/${dpki.completed} ` +
        `chainBlocks=${dpki.chainBlockCount} avgTxPerBlock=${dpki.avgTxPerChainBlock.toFixed(2)} ` +
        `lambda_a=${dpki.observedLambdaOffchain.toFixed(3)}/${dpki.targetLambdaOffchain.toFixed(3)} ` +
        `lambda_b=${dpki.observedLambdaOnchain.toFixed(3)}/${dpki.targetLambdaOnchain.toFixed(3)}`
    );
    if (args.resetPerEpsilon) {
      stopAllOpenSslOcspResponders(runPkiPlatform);
      stopPkiServiceResponder(runPkiPlatform);
      stopDpkiProofResponder(runPlatform);
    }
  }
  const chainObservationEnd = usePow ? await observeChainBlockPosition(web3) : null;
  const chainObservation = usePow
    ? {
        startBlockNumber: chainObservationStart.blockNumber,
        endBlockNumber: chainObservationEnd.blockNumber,
        observedBlocks: Math.max(0, chainObservationEnd.blockNumber - chainObservationStart.blockNumber),
        startWallMs: chainObservationStart.wallMs,
        endWallMs: chainObservationEnd.wallMs,
        durationSec: Math.max(0, (chainObservationEnd.monotonicMs - chainObservationStart.monotonicMs) / 1000),
        lambdaBlockByHeightPerSec:
          chainObservationEnd.monotonicMs > chainObservationStart.monotonicMs
            ? Math.max(0, chainObservationEnd.blockNumber - chainObservationStart.blockNumber) /
              ((chainObservationEnd.monotonicMs - chainObservationStart.monotonicMs) / 1000)
            : 0,
        powRuntimeConfig: powStatus ? powStatus.runtimeConfig : null,
      }
    : null;
  if (chainObservation) {
    fs.writeFileSync(path.join(OUT_DIR, "real_chain_observation.json"), JSON.stringify(chainObservation, null, 2));
    console.log(
      `Observed empty-block process: blocks=${chainObservation.observedBlocks} ` +
        `duration=${chainObservation.durationSec.toFixed(3)}s ` +
        `lambda_p=${chainObservation.lambdaBlockByHeightPerSec.toFixed(3)}/s`
    );
  }

  writeCsv(path.join(OUT_DIR, "real_simulation_results_by_epsilon.csv"), summaryRows, [
    "epsilon",
    "DPKI_sim",
    "PKI_sim",
    "PKI_sim_raw",
    "pkiNetworkCompensationSec",
    "pkiNetworkCompensationMs",
    "pkiAuthNetworkSetupMs",
    "pkiOcspNetworkRttMs",
    "pkiAuthCount",
    "pkiOcspCount",
  ]);
  writeCsv(path.join(OUT_DIR, "real_simulation_results_by_epsilon_detailed.csv"), requestRows, [
    "epsilon",
    "model",
    "requestIndex",
    "kind",
    "onChain",
    "crossDomain",
    "arrivalOffsetMs",
    "arrivalWallMs",
    "finishWallMs",
    "latencyMs",
    "queueMs",
    "serviceMs",
    "workerId",
    "chainReads",
    "verifiedCertificateSteps",
    "proofNodes",
    "stageTimingsJson",
    "chainTxCount",
    "chainBlockNumbers",
    "chainTxHashes",
  ]);
  writeStageStatistics(requestRows);
  writeChainTxBreakdown();

  writeCsv(path.join(OUT_DIR, "real_summary_by_epsilon_detailed.csv"), summaryDetailRows, [
    "epsilon",
    "model",
    "E_T",
    "completed",
    "onChainCount",
    "offChainCount",
    "crossDomainCount",
    "managementCount",
    "actualOnChainRatio",
    "actualOffChainRatio",
    "actualCrossDomainRatio",
    "actualManagementRatio",
    "arrivalSpanSec",
    "targetLambdaOffchain",
    "targetLambdaOnchain",
    "observedLambdaOffchain",
    "observedLambdaOnchain",
    "avgLatencyMs",
    "avgLatencyRawMs",
    "avgQueueMs",
    "avgServiceMs",
    "avgServiceRawMs",
    "avgOffchainProofMs",
    "avgPkiChainVerifyMs",
    "PKI_sim_raw",
    "pkiNetworkCompensationSec",
    "pkiNetworkCompensationMs",
    "pkiAuthNetworkSetupMs",
    "pkiOcspNetworkRttMs",
    "pkiAuthCount",
    "pkiOcspCount",
    "chainTxCount",
    "chainBlockCount",
    "avgTxPerChainBlock",
    "maxTxPerChainBlock",
    "gasUsed",
  ]);

  const lambdaSummaryRows = summaryDetailRows
    .filter((row) => row.model === "DPKI")
    .map((row) => ({
      epsilon: row.epsilon,
      targetLambdaOffchain: row.targetLambdaOffchain,
      observedLambdaOffchain: row.observedLambdaOffchain,
      targetLambdaOnchain: row.targetLambdaOnchain,
      observedLambdaOnchain: row.observedLambdaOnchain,
      actualOnChainRatio: row.actualOnChainRatio,
      actualCrossDomainRatio: row.actualCrossDomainRatio,
      arrivalSpanSec: row.arrivalSpanSec,
      completed: row.completed,
      onChainCount: row.onChainCount,
      offChainCount: row.offChainCount,
      crossDomainCount: row.crossDomainCount,
      chainBlockCount: row.chainBlockCount,
      avgTxPerChainBlock: row.avgTxPerChainBlock,
    }));
  writeCsv(path.join(OUT_DIR, "lambda_summary_by_epsilon.csv"), lambdaSummaryRows, [
    "epsilon",
    "targetLambdaOffchain",
    "observedLambdaOffchain",
    "targetLambdaOnchain",
    "observedLambdaOnchain",
    "actualOnChainRatio",
    "actualCrossDomainRatio",
    "arrivalSpanSec",
    "completed",
    "onChainCount",
    "offChainCount",
    "crossDomainCount",
    "chainBlockCount",
    "avgTxPerChainBlock",
  ]);

  writeCsv(path.join(SIMU2_DIR, "simulation_results_by_epsilon.csv"), summaryRows, [
    "epsilon",
    "DPKI_sim",
    "PKI_sim",
    "PKI_sim_raw",
    "pkiNetworkCompensationSec",
    "pkiNetworkCompensationMs",
    "pkiAuthNetworkSetupMs",
    "pkiOcspNetworkRttMs",
    "pkiAuthCount",
    "pkiOcspCount",
  ]);
  writeCsv(path.join(SIMU2_DIR, "simulation_results_by_epsilon_detailed.csv"), summaryDetailRows, [
    "epsilon",
    "model",
    "E_T",
    "completed",
    "onChainCount",
    "offChainCount",
    "crossDomainCount",
    "managementCount",
    "actualOnChainRatio",
    "actualOffChainRatio",
    "actualCrossDomainRatio",
    "actualManagementRatio",
    "arrivalSpanSec",
    "targetLambdaOffchain",
    "targetLambdaOnchain",
    "observedLambdaOffchain",
    "observedLambdaOnchain",
    "avgLatencyMs",
    "avgLatencyRawMs",
    "avgQueueMs",
    "avgServiceMs",
    "avgServiceRawMs",
    "avgOffchainProofMs",
    "avgPkiChainVerifyMs",
    "PKI_sim_raw",
    "pkiNetworkCompensationSec",
    "pkiNetworkCompensationMs",
    "pkiAuthNetworkSetupMs",
    "pkiOcspNetworkRttMs",
    "pkiAuthCount",
    "pkiOcspCount",
    "chainTxCount",
    "chainBlockCount",
    "avgTxPerChainBlock",
    "maxTxPerChainBlock",
    "gasUsed",
  ]);
  writeCsv(path.join(SIMU2_DIR, "lambda_summary_by_epsilon.csv"), lambdaSummaryRows, [
    "epsilon",
    "targetLambdaOffchain",
    "observedLambdaOffchain",
    "targetLambdaOnchain",
    "observedLambdaOnchain",
    "actualOnChainRatio",
    "actualCrossDomainRatio",
    "arrivalSpanSec",
    "completed",
    "onChainCount",
    "offChainCount",
    "crossDomainCount",
    "chainBlockCount",
    "avgTxPerChainBlock",
  ]);

  fs.writeFileSync(
    path.join(OUT_DIR, "deployment.json"),
    JSON.stringify(
      {
        consensusBackend: usePow ? "omnilink-pow" : "chain33",
        rpc: args.rpc,
        contractAddress: contract.options.address,
        account: args.account,
        powStatus,
        chainObservation,
        params: {
          requestsPerEpsilon: args.requestsPerEpsilon,
          lambdaArrival: args.lambdaArrival,
          pManage: args.pManage,
          gammaOnChain: args.gammaOnChain,
          qManage: args.qManage,
          lambdaBlock: args.lambdaBlock,
          lambdaExecute: args.lambdaExecute,
          muAuth: args.muAuth,
          serviceCAs: args.serviceCAs,
          timeScaleMs: args.timeScaleMs,
          maxOnchainInFlight: args.maxOnchainInFlight,
          txSenders: args.txSenders,
          fixedGasLimit: args.fixedGasLimit,
          fixedGasPriceWei: args.fixedGasPriceWei,
          chainId: ACTIVE_CHAIN_ID,
          estimateGas: args.estimateGas,
          signingHardfork: "istanbul",
          rawTxSubmitTimeoutMs: args.rawTxSubmitTimeoutMs,
          rawTxSubmitRetries: args.rawTxSubmitRetries,
          rawTxReceiptTimeoutMs: args.rawTxReceiptTimeoutMs,
          serviceShapeMode: args.serviceShapeMode,
          dpkiAuthShapeMeanMs: args.dpkiAuthShapeMeanMs,
          dpkiCrossShapeMeanMs: args.dpkiCrossShapeMeanMs,
          dpkiOnchainShapeMeanMs: args.dpkiOnchainShapeMeanMs,
          dpkiIntraOffchainShapeMeanMs: args.dpkiIntraOffchainShapeMeanMs,
          dpkiOffchainShapeMeanMs: args.dpkiOffchainShapeMeanMs,
          dpkiManagementShapeMeanMs: args.dpkiManagementShapeMeanMs,
          pkiAuthShapeMeanMs: args.pkiAuthShapeMeanMs,
          pkiCrossShapeMeanMs: args.pkiCrossShapeMeanMs,
          pkiIntraShapeMeanMs: args.pkiIntraShapeMeanMs,
          pkiManagementShapeMeanMs: args.pkiManagementShapeMeanMs,
          arrivalMode: args.arrivalMode,
          kindPlanMode: args.kindPlanMode,
          dpkiRootReadMode: args.dpkiRootReadMode,
          dpkiProofReadMode: args.dpkiProofReadMode,
          dpkiProofBasePort: args.dpkiProofBasePort,
          actualExecutionMode: args.actualExecutionMode,
          ocspBasePort: args.ocspBasePort,
          resetPerEpsilon: args.resetPerEpsilon,
          skipPki: args.skipPki,
          seed: args.seed,
        },
        txSenders: txSenders.map((sender) => ({
          id: sender.id,
          account: sender.account,
        })),
      },
      null,
      2
    )
  );

  updateSimu2TheoryAndFigure(args, summaryDetailRows);
  updateCalibratedTheoryAndStats(args);
  console.log(`Wrote ${path.join(SIMU2_DIR, "simulation_results_by_epsilon.csv")}`);
  console.log(`Regenerated ${path.join(SIMU2_DIR, "Fig7_epsilon_ET.png")}`);
  console.log(`Wrote ${path.join(SIMU2_DIR, "real_delay_statistics.csv")}`);
  cleanupOpenSslOcspResponders();
  cleanupPkiServiceResponders();
  cleanupDpkiProofResponders();
}

process.once("exit", () => {
  cleanupOpenSslOcspResponders();
  cleanupPkiServiceResponders();
  cleanupDpkiProofResponders();
});
process.once("SIGINT", () => {
  cleanupOpenSslOcspResponders();
  cleanupPkiServiceResponders();
  cleanupDpkiProofResponders();
  process.exit(130);
});
process.once("SIGTERM", () => {
  cleanupOpenSslOcspResponders();
  cleanupPkiServiceResponders();
  cleanupDpkiProofResponders();
  process.exit(143);
});

main().catch((error) => {
  cleanupOpenSslOcspResponders();
  cleanupPkiServiceResponders();
  cleanupDpkiProofResponders();
  console.error(error);
  process.exitCode = 1;
});
