const fs = require("fs");
const path = require("path");
const { performance } = require("perf_hooks");
const crypto = require("crypto");

const ROOT = path.resolve(__dirname, "..", "..", "..");
const OUT_DIR = __dirname;
const CONTRACT_PATH = path.join(ROOT, "dpki-experiment-prototype", "contracts", "DPKIExperiment.sol");
const PROTOTYPE_NODE_MODULES = path.join(ROOT, "dpki-experiment-prototype", "node_modules");

const solc = require(path.join(PROTOTYPE_NODE_MODULES, "solc"));
const Web3 = require(path.join(PROTOTYPE_NODE_MODULES, "web3"));
const rlp = require(path.join(PROTOTYPE_NODE_MODULES, "rlp"));

const DEFAULTS = {
  rpc: "http://127.0.0.1:8545",
  account: "0xab7F5238cbEfB02062241cf979e4994b656FB944",
  privateKey: "0x73e66f099144f820753aa3a5e131785b528081da572e16339fcd02de05de719e",
  requests: 2000,
  gas: 8000000,
  gasPrice: "1",
  chainId: 0,
};

function parseArgs() {
  const args = { ...DEFAULTS };
  for (let i = 2; i < process.argv.length; i += 1) {
    const arg = process.argv[i];
    const next = process.argv[i + 1];
    if (arg === "--rpc" && next) args.rpc = next, i += 1;
    else if (arg === "--account" && next) args.account = next, i += 1;
    else if (arg === "--private-key" && next) args.privateKey = next, i += 1;
    else if (arg === "--requests" && next) args.requests = Number(next), i += 1;
    else if (arg === "--gas" && next) args.gas = Number(next), i += 1;
    else if (arg === "--gas-price" && next) args.gasPrice = String(next), i += 1;
    else if (arg === "--chain-id" && next) args.chainId = Number(next), i += 1;
    else if (arg === "--help") {
      console.log("Usage: node run_full_contract_baseline.js [--requests N] [--rpc URL]");
      process.exit(0);
    }
  }
  if (!args.privateKey.startsWith("0x")) args.privateKey = `0x${args.privateKey}`;
  return args;
}

function sha256Hex(text) {
  return crypto.createHash("sha256").update(String(text)).digest("hex");
}

function bytes32(web3, text) {
  return web3.utils.keccak256(`0x${sha256Hex(text)}`);
}

function derivePrivateKey(seed) {
  return `0x${sha256Hex(seed)}`;
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
          "*": ["abi", "evm.bytecode"],
        },
      },
    },
  };
  const output = JSON.parse(solc.compile(JSON.stringify(input)));
  const errors = output.errors || [];
  const fatal = errors.filter((item) => item.severity === "error");
  if (fatal.length) {
    throw new Error(fatal.map((item) => item.formattedMessage).join("\n"));
  }
  const compiled = output.contracts["DPKIExperiment.sol"].DPKIExperiment;
  return {
    abi: compiled.abi,
    bytecode: `0x${compiled.evm.bytecode.object}`,
  };
}

function percentile(sortedValues, p) {
  if (!sortedValues.length) return 0;
  const pos = (sortedValues.length - 1) * p;
  const lower = Math.floor(pos);
  const upper = Math.ceil(pos);
  if (lower === upper) return sortedValues[lower];
  const weight = pos - lower;
  return sortedValues[lower] * (1 - weight) + sortedValues[upper] * weight;
}

function mean(values) {
  if (!values.length) return 0;
  return values.reduce((acc, value) => acc + value, 0) / values.length;
}

function std(values) {
  if (!values.length) return 0;
  const avg = mean(values);
  return Math.sqrt(values.reduce((acc, value) => acc + (value - avg) ** 2, 0) / values.length);
}

function receiptLogBytes(receipt) {
  return (receipt.logs || []).reduce((total, log) => {
    const topicBytes = (log.topics || []).length * 32;
    const data = log.data || "0x";
    const dataBytes = Math.max(0, (data.length - 2) / 2);
    return total + topicBytes + dataBytes;
  }, 0);
}

function receiptOk(receipt) {
  if (receipt.status === true || receipt.status === 1) return true;
  if (typeof receipt.status === "string") {
    return receipt.status === "0x1" || receipt.status.toLowerCase() === "true";
  }
  return receipt.status === undefined || receipt.status === null;
}

function encodedBytes(encoded) {
  return Math.max(0, (encoded.length - 2) / 2);
}

function contractAddressFrom(sender, nonce, web3) {
  const encoded = rlp.encode([Buffer.from(sender.slice(2), "hex"), nonce]);
  const digest = web3.utils.keccak256(`0x${Buffer.from(encoded).toString("hex")}`);
  return web3.utils.toChecksumAddress(`0x${digest.slice(-40)}`);
}

function transactionSigningFields(args) {
  return {
    gasPrice: String(args.gasPrice),
  };
}

let rpcId = 1;

async function jsonRpc(args, method, params = [], timeoutMs = 30000) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(args.rpc, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ jsonrpc: "2.0", id: rpcId += 1, method, params }),
      signal: controller.signal,
    });
    const payload = await response.json();
    if (payload.error) {
      throw new Error(payload.error.message || JSON.stringify(payload.error));
    }
    return payload.result;
  } finally {
    clearTimeout(timer);
  }
}

function rpcQuantityToNumber(value) {
  if (typeof value === "number") return value;
  if (typeof value === "string" && value.startsWith("0x")) return Number.parseInt(value, 16);
  return Number(value || 0);
}

async function sendRawTransaction(args, rawTransaction) {
  return jsonRpc(args, "eth_sendRawTransaction", [rawTransaction], 30000);
}

async function waitReceipt(args, txHash, timeoutMs = 120000) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    const receipt = await jsonRpc(args, "eth_getTransactionReceipt", [txHash], 10000);
    if (receipt) {
      receipt.gasUsed = rpcQuantityToNumber(receipt.gasUsed);
      return receipt;
    }
    await new Promise((resolve) => setTimeout(resolve, 10));
  }
  throw new Error(`Timed out waiting for receipt ${txHash}`);
}

async function waitRpc(web3) {
  try {
    await web3.eth.net.isListening();
  } catch (error) {
    throw new Error(`RPC is not listening. Start Omnilink PoW first. ${error.message}`);
  }
}

async function deploy(web3, abi, bytecode, args) {
  let nonce = await web3.eth.getTransactionCount(args.account, "pending");
  async function send(method, to = null) {
    let gasEstimate = 0;
    try {
      gasEstimate = Number(await method.estimateGas({ from: args.account }));
    } catch (_) {
      gasEstimate = 0;
    }
    const gasLimit = Math.max(args.gas, gasEstimate > 0 ? Math.ceil(gasEstimate * 2) + 100000 : 0);
    const data = method.encodeABI();
    const txNonce = nonce;
    const tx = {
      from: args.account,
      to,
      data,
      gas: gasLimit,
      nonce,
      ...transactionSigningFields(args),
    };
    nonce += 1;
    const signed = await web3.eth.accounts.signTransaction(tx, args.privateKey);
    const txHash = await sendRawTransaction(args, signed.rawTransaction);
    const receipt = await waitReceipt(args, txHash);
    if (!receiptOk(receipt)) {
      throw new Error(`Transaction failed during deploy/setup: ${txHash}`);
    }
    return { receipt, rawBytes: encodedBytes(signed.rawTransaction), inputBytes: encodedBytes(data), nonce: txNonce, gasEstimate, gasLimit };
  }

  const contract = new web3.eth.Contract(abi);
  const deployTx = contract.deploy({ data: bytecode });
  const result = await send(deployTx);
  const contractAddress = result.receipt.contractAddress || contractAddressFrom(args.account, result.nonce, web3);
  return {
    contract: new web3.eth.Contract(abi, contractAddress),
    nextNonce: nonce,
  };
}

async function sendContractTx(web3, contract, method, args, nonceRef) {
  let gasEstimate = 0;
  try {
    gasEstimate = Number(await method.estimateGas({ from: args.account }));
  } catch (_) {
    gasEstimate = 0;
  }
  const gasLimit = Math.max(args.gas, gasEstimate > 0 ? Math.ceil(gasEstimate * 2) + 100000 : 0);
  const data = method.encodeABI();
  const tx = {
    from: args.account,
    to: contract.options.address,
    data,
    gas: gasLimit,
    nonce: nonceRef.value,
    ...transactionSigningFields(args),
  };
  nonceRef.value += 1;
  const signed = await web3.eth.accounts.signTransaction(tx, args.privateKey);
  const start = performance.now();
  const txHash = await sendRawTransaction(args, signed.rawTransaction);
  const receipt = await waitReceipt(args, txHash);
  const latencyMs = performance.now() - start;
  if (!receiptOk(receipt)) {
    throw new Error(`Contract transaction failed: ${txHash}`);
  }
  const receiptGas = Number(receipt.gasUsed || 0);
  const gasUsed = gasEstimate > 0 ? gasEstimate : receiptGas;
  return {
    latencyMs,
    gasUsed,
    gasLimit,
    txHash,
    inputBytes: encodedBytes(data),
    rawTxBytes: encodedBytes(signed.rawTransaction),
    receiptLogBytes: receiptLogBytes(receipt),
  };
}

function certRecord(web3, domain, subject, addressSeed) {
  const account = web3.eth.accounts.privateKeyToAccount(derivePrivateKey(`fig4-full-contract:${addressSeed}`));
  const certKey = bytes32(web3, `${domain}:${subject}:cert-key`);
  return {
    domainId: bytes32(web3, `domain:${domain}`),
    subjectId: bytes32(web3, `subject:${subject}`),
    subjectAddress: account.address,
    certHash: bytes32(web3, `${domain}:${subject}:cert-hash`),
    certKey,
    account,
  };
}

function authData(web3, requestClass, index, source, target) {
  return [
    bytes32(web3, `${requestClass}:${index}:request`),
    source.domainId,
    target.domainId,
    source.subjectId,
    target.subjectId,
    bytes32(web3, `${requestClass}:${index}:nonce`),
  ];
}

function signAssertion(web3, contract, data, source, timestamp, crossDomain, certKeys, certHashes, signer) {
  const checkHash = web3.utils.keccak256(web3.eth.abi.encodeParameters(["bytes32[]", "bytes32[]"], [certKeys, certHashes]));
  const digest = web3.utils.soliditySha3(
    { type: "address", value: contract.options.address },
    { type: "bytes32", value: data[0] },
    { type: "bytes32", value: data[1] },
    { type: "bytes32", value: data[2] },
    { type: "bytes32", value: data[3] },
    { type: "bytes32", value: data[4] },
    { type: "bytes32", value: data[5] },
    { type: "address", value: source.subjectAddress },
    { type: "uint256", value: timestamp },
    { type: "bool", value: crossDomain },
    { type: "bytes32", value: checkHash },
  );
  return signer.account.sign(digest).signature;
}

function stateWriteBytes(requestClass) {
  if (requestClass === "management") return 288;
  return 544;
}

function summarize(requestClass, rows, issueUpdateMs = 0) {
  const latencies = rows.map((row) => row.latencyMs);
  const sorted = [...latencies].sort((a, b) => a - b);
  const contractMean = mean(latencies);
  const normalized = latencies.map((value) => value + issueUpdateMs);
  const sortedNorm = [...normalized].sort((a, b) => a - b);
  return {
    mechanism: "full-contract-onchain",
    requestClass,
    count: rows.length,
    meanLatencyMs: mean(normalized),
    medianLatencyMs: percentile(sortedNorm, 0.5),
    p95LatencyMs: percentile(sortedNorm, 0.95),
    stdLatencyMs: std(normalized),
    meanNormalizedLatencyMs: mean(normalized),
    medianNormalizedLatencyMs: percentile(sortedNorm, 0.5),
    p95NormalizedLatencyMs: percentile(sortedNorm, 0.95),
    stdNormalizedLatencyMs: std(normalized),
    meanGasUsed: mean(rows.map((row) => row.gasUsed)),
    meanTxInputBytes: mean(rows.map((row) => row.inputBytes)),
    meanRawTxBytes: mean(rows.map((row) => row.rawTxBytes)),
    meanReceiptLogBytes: mean(rows.map((row) => row.receiptLogBytes)),
    meanStateWriteBytesEstimated: stateWriteBytes(requestClass),
    meanStatusValidationMs: 0,
    meanCertVerificationMs: 0,
    meanCertChecks: requestClass === "cross-on-chain" ? 2 : requestClass === "intra-on-chain" ? 1 : 0,
    meanIssueUpdateMs: issueUpdateMs,
    meanQueueDelayMs: 0,
    meanWaitMs: 0,
    meanInterarrivalMs: 0,
    meanServiceMs: contractMean,
    meanContractExecutionMs: contractMean,
  };
}

function csvEscape(value) {
  if (value === null || value === undefined) return "";
  const text = String(value);
  if (/[",\n\r]/.test(text)) return `"${text.replace(/"/g, '""')}"`;
  return text;
}

function writeCsv(filePath, rows, columns) {
  const lines = [columns.join(",")];
  for (const row of rows) {
    lines.push(columns.map((column) => csvEscape(row[column])).join(","));
  }
  fs.writeFileSync(filePath, `${lines.join("\n")}\n`);
}

async function main() {
  const args = parseArgs();
  fs.mkdirSync(OUT_DIR, { recursive: true });
  const web3 = new Web3(new Web3.providers.HttpProvider(args.rpc));
  await waitRpc(web3);

  const compiled = compileContract();
  const deployment = await deploy(web3, compiled.abi, compiled.bytecode, args);
  const contract = deployment.contract;
  const nonceRef = { value: deployment.nextNonce };

  const now = Math.floor(Date.now() / 1000);
  const notAfter = now + 10 * 365 * 24 * 60 * 60;
  const repoRoot = bytes32(web3, "fig4-full-contract:repo-root");
  const source = certRecord(web3, "domain-a", "entity-a", "source");
  const target = certRecord(web3, "domain-b", "entity-b", "target");
  const service = certRecord(web3, "main", "service-a", "service");

  for (const record of [source, service, target]) {
    await sendContractTx(
      web3,
      contract,
      contract.methods.putCertificateAndDomainRoot(
        record.certKey,
        record.domainId,
        record.subjectId,
        record.subjectAddress,
        record.certHash,
        0,
        notAfter,
        repoRoot,
      ),
      args,
      nonceRef,
    );
  }

  const requestCount = Math.max(1, Math.floor(args.requests));
  const allRows = [];
  const classes = ["intra-on-chain", "cross-on-chain", "management"];
  const byClass = new Map(classes.map((name) => [name, []]));

  for (const requestClass of classes) {
    console.log(`Running full-contract ${requestClass}: ${requestCount} requests`);
    for (let i = 0; i < requestCount; i += 1) {
      let txResult;
      if (requestClass === "management") {
        const managed = certRecord(web3, "domain-a", `managed-${i}`, `managed-${i}`);
        txResult = await sendContractTx(
          web3,
          contract,
          contract.methods.putCertificateAndDomainRoot(
            managed.certKey,
            managed.domainId,
            managed.subjectId,
            managed.subjectAddress,
            managed.certHash,
            0,
            notAfter,
            bytes32(web3, `fig4-full-contract:repo-root:${i}`),
          ),
          args,
          nonceRef,
        );
      } else {
        const crossDomain = requestClass === "cross-on-chain";
        const certs = crossDomain ? [source, service] : [source];
        const certKeys = certs.map((record) => record.certKey);
        const certHashes = certs.map((record) => record.certHash);
        const data = authData(web3, requestClass, i, source, target);
        const timestamp = Math.floor(Date.now() / 1000);
        const signature = signAssertion(web3, contract, data, source, timestamp, crossDomain, certKeys, certHashes, service);
        txResult = await sendContractTx(
          web3,
          contract,
          contract.methods.authenticateSigned(
            data,
            source.subjectAddress,
            timestamp,
            crossDomain,
            certKeys,
            certHashes,
            service.subjectAddress,
            signature,
          ),
          args,
          nonceRef,
        );
      }
      const row = {
        mechanism: "full-contract-onchain",
        requestClass,
        index: i,
        ...txResult,
      };
      byClass.get(requestClass).push(row);
      allRows.push(row);
    }
  }

  const summaryRows = classes.map((requestClass) => summarize(requestClass, byClass.get(requestClass), requestClass === "management" ? 98.3603983527422 : 0));
  const metricColumns = [
    "mechanism",
    "requestClass",
    "index",
    "latencyMs",
    "gasUsed",
    "gasLimit",
    "txHash",
    "inputBytes",
    "rawTxBytes",
    "receiptLogBytes",
  ];
  const summaryColumns = [
    "mechanism",
    "requestClass",
    "count",
    "meanLatencyMs",
    "medianLatencyMs",
    "p95LatencyMs",
    "stdLatencyMs",
    "meanNormalizedLatencyMs",
    "medianNormalizedLatencyMs",
    "p95NormalizedLatencyMs",
    "stdNormalizedLatencyMs",
    "meanGasUsed",
    "meanTxInputBytes",
    "meanRawTxBytes",
    "meanReceiptLogBytes",
    "meanStateWriteBytesEstimated",
    "meanStatusValidationMs",
    "meanCertVerificationMs",
    "meanCertChecks",
    "meanIssueUpdateMs",
    "meanQueueDelayMs",
    "meanWaitMs",
    "meanInterarrivalMs",
    "meanServiceMs",
    "meanContractExecutionMs",
  ];

  writeCsv(path.join(OUT_DIR, "full_contract_request_metrics.csv"), allRows, metricColumns);
  writeCsv(path.join(OUT_DIR, "full_contract_summary_by_request_class.csv"), summaryRows, summaryColumns);
  fs.writeFileSync(
    path.join(OUT_DIR, "full_contract_manifest.json"),
    `${JSON.stringify({ generatedAt: new Date().toISOString(), rpc: args.rpc, requests: requestCount, contractAddress: contract.options.address }, null, 2)}\n`,
  );
  console.log(`Saved ${path.join(OUT_DIR, "full_contract_summary_by_request_class.csv")}`);
}

main().catch((error) => {
  console.error(error && error.stack ? error.stack : error);
  process.exit(1);
});
