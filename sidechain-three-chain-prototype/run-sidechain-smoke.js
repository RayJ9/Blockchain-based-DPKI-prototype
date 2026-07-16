"use strict";

const fs = require("fs");
const path = require("path");
const crypto = require("crypto");
const childProcess = require("child_process");

const ROOT = path.resolve(__dirname, "..");
const Web3 = require(path.join(ROOT, "dpki-experiment-prototype", "node_modules", "web3"));
const solc = require(path.join(ROOT, "dpki-experiment-prototype", "node_modules", "solc"));

const PRIVATE_KEY = "0x73e66f099144f820753aa3a5e131785b528081da572e16339fcd02de05de719e";
const ENDPOINTS = {
  main: "http://127.0.0.1:18645",
  sideA: "http://127.0.0.1:18745",
  sideB: "http://127.0.0.1:18845",
};
const OUTPUT_DIR = path.resolve(
  process.env.SIDECHAIN_OUTPUT_DIR || path.join(__dirname, "outputs", new Date().toISOString().replace(/[:.]/g, "-")),
);
const CONTRACT_DIR = path.join(__dirname, "contracts");
const CERT_DIR = path.join(OUTPUT_DIR, "certificates");

fs.mkdirSync(CERT_DIR, { recursive: true });

function sha256(buffer) {
  return `0x${crypto.createHash("sha256").update(buffer).digest("hex")}`;
}

function runOpenSsl(args, cwd) {
  const result = childProcess.spawnSync("openssl", args, { cwd, encoding: "utf8" });
  if (result.status !== 0) {
    throw new Error(`openssl ${args.join(" ")} failed:\n${result.stdout}\n${result.stderr}`);
  }
  return (result.stdout || "").trim();
}

function createCertificateHierarchy(label, commonName) {
  const dir = path.join(CERT_DIR, label);
  fs.mkdirSync(dir, { recursive: true });
  runOpenSsl([
    "req", "-x509", "-newkey", "rsa:2048", "-nodes", "-sha256", "-days", "2",
    "-keyout", "ca.key.pem", "-out", "ca.cert.pem", "-subj", `/CN=${label}-Root-CA`,
  ], dir);
  runOpenSsl([
    "req", "-newkey", "rsa:2048", "-nodes", "-sha256",
    "-keyout", "leaf.key.pem", "-out", "leaf.csr.pem", "-subj", `/CN=${commonName}`,
  ], dir);
  runOpenSsl([
    "x509", "-req", "-in", "leaf.csr.pem", "-CA", "ca.cert.pem", "-CAkey", "ca.key.pem",
    "-CAcreateserial", "-out", "leaf.cert.pem", "-days", "1", "-sha256",
  ], dir);

  const caPem = fs.readFileSync(path.join(dir, "ca.cert.pem"));
  const leafPem = fs.readFileSync(path.join(dir, "leaf.cert.pem"));
  const publicKey = runOpenSsl(["x509", "-in", "leaf.cert.pem", "-pubkey", "-noout"], dir);
  const details = runOpenSsl([
    "x509", "-in", "leaf.cert.pem", "-noout", "-subject", "-issuer", "-serial", "-dates", "-fingerprint", "-sha256",
  ], dir);
  const record = {
    label,
    commonName,
    caSha256: sha256(caPem),
    certificateSha256: sha256(leafPem),
    publicKeySha256: sha256(Buffer.from(publicKey, "utf8")),
    certificateBytes: leafPem.length,
    details,
    certificatePath: path.join(dir, "leaf.cert.pem"),
  };
  console.log(`[CERTIFICATE][${label}] ${JSON.stringify(record)}`);
  console.log(`[CERTIFICATE][${label}][OPENSSL]\n${details}`);
  console.log(`[CERTIFICATE][${label}][PEM]\n${leafPem.toString("utf8").trim()}`);
  return record;
}

function compileContracts() {
  const sources = {};
  for (const name of ["MainChainCARegistry.sol", "SidechainDPKI.sol"]) {
    sources[name] = { content: fs.readFileSync(path.join(CONTRACT_DIR, name), "utf8") };
  }
  const input = {
    language: "Solidity",
    sources,
    settings: { outputSelection: { "*": { "*": ["abi", "evm.bytecode.object"] } } },
  };
  const output = JSON.parse(solc.compile(JSON.stringify(input)));
  const errors = (output.errors || []).filter((item) => item.severity === "error");
  if (errors.length) {
    throw new Error(errors.map((item) => item.formattedMessage).join("\n"));
  }
  return {
    main: output.contracts["MainChainCARegistry.sol"].MainChainCARegistry,
    side: output.contracts["SidechainDPKI.sol"].SidechainDPKI,
  };
}

function receiptView(chainName, operation, receipt, timing) {
  return {
    chain: chainName,
    operation,
    transactionHash: receipt.transactionHash,
    blockNumber: receipt.blockNumber,
    transactionIndex: receipt.transactionIndex,
    gasUsed: receipt.gasUsed,
    status: Boolean(receipt.status),
    contractAddress: receipt.contractAddress || null,
    elapsedMs: timing.elapsedMs,
    hashObservedMs: timing.hashObservedMs,
    eventCount: (receipt.logs || []).length,
  };
}

async function sendSigned(web3, chainName, account, transaction, operation, receipts) {
  const chainId = await web3.eth.getChainId();
  const nonce = await web3.eth.getTransactionCount(account.address, "pending");
  const tx = {
    from: account.address,
    to: transaction.to,
    data: transaction.data,
    gas: transaction.gas || 7000000,
    gasPrice: "1",
    nonce,
    chainId,
  };
  const signed = await account.signTransaction(tx);
  const started = process.hrtime.bigint();
  let hashObservedMs = null;
  const promi = web3.eth.sendSignedTransaction(signed.rawTransaction);
  promi.once("transactionHash", (hash) => {
    hashObservedMs = Number(process.hrtime.bigint() - started) / 1e6;
    console.log(`[TX_SUBMITTED][${chainName}] operation=${operation} hash=${hash}`);
  });
  const receipt = await promi;
  const summary = receiptView(chainName, operation, receipt, {
    elapsedMs: Number(process.hrtime.bigint() - started) / 1e6,
    hashObservedMs,
  });
  receipts.push(summary);
  console.log(`[RECEIPT][${chainName}] ${JSON.stringify(summary)}`);
  return receipt;
}

async function deploy(web3, chainName, account, artifact, args, label, receipts) {
  const contract = new web3.eth.Contract(artifact.abi);
  const data = contract.deploy({ data: `0x${artifact.evm.bytecode.object}`, arguments: args }).encodeABI();
  const receipt = await sendSigned(web3, chainName, account, { data, gas: 7000000 }, `deploy:${label}`, receipts);
  return new web3.eth.Contract(artifact.abi, receipt.contractAddress);
}

async function sendMethod(web3, chainName, account, method, operation, receipts) {
  return sendSigned(web3, chainName, account, {
    to: method._parent._address,
    data: method.encodeABI(),
    gas: 3000000,
  }, operation, receipts);
}

async function chainDescriptor(name, web3) {
  const [chainId, blockNumber, listening] = await Promise.all([
    web3.eth.getChainId(),
    web3.eth.getBlockNumber(),
    web3.eth.net.isListening(),
  ]);
  const descriptor = { name, endpoint: ENDPOINTS[name], chainId, blockNumber, listening };
  console.log(`[CHAIN] ${JSON.stringify(descriptor)}`);
  return descriptor;
}

async function main() {
  console.log(`[SESSION] output=${OUTPUT_DIR}`);
  const web3 = {
    main: new Web3(ENDPOINTS.main),
    sideA: new Web3(ENDPOINTS.sideA),
    sideB: new Web3(ENDPOINTS.sideB),
  };
  const accounts = {};
  for (const name of Object.keys(web3)) {
    accounts[name] = web3[name].eth.accounts.privateKeyToAccount(PRIVATE_KEY);
    web3[name].eth.accounts.wallet.add(accounts[name]);
  }

  const chains = [];
  for (const name of ["main", "sideA", "sideB"]) {
    chains.push(await chainDescriptor(name, web3[name]));
  }
  const ids = {
    sideA: web3.main.utils.keccak256("omnilink-sidechain-a"),
    sideB: web3.main.utils.keccak256("omnilink-sidechain-b"),
  };
  const certificates = {
    sideA: createCertificateHierarchy("side-a", "entity-a.example"),
    sideB: createCertificateHierarchy("side-b", "entity-b.example"),
  };
  const caIds = {
    sideA: web3.main.utils.keccak256(certificates.sideA.caSha256),
    sideB: web3.main.utils.keccak256(certificates.sideB.caSha256),
  };
  const certIds = {
    sideA: web3.sideA.utils.keccak256("entity-a.example"),
    sideB: web3.sideB.utils.keccak256("entity-b.example"),
  };
  const subjectIds = {
    sideA: web3.sideA.utils.keccak256("subject:entity-a.example"),
    sideB: web3.sideB.utils.keccak256("subject:entity-b.example"),
  };

  const artifacts = compileContracts();
  const receipts = [];
  const mainRegistry = await deploy(web3.main, "main", accounts.main, artifacts.main, [], "MainChainCARegistry", receipts);
  const sideA = await deploy(web3.sideA, "sideA", accounts.sideA, artifacts.side, [ids.sideA, caIds.sideA], "SidechainDPKI-A", receipts);
  const sideB = await deploy(web3.sideB, "sideB", accounts.sideB, artifacts.side, [ids.sideB, caIds.sideB], "SidechainDPKI-B", receipts);

  await sendMethod(
    web3.main,
    "main",
    accounts.main,
    mainRegistry.methods.registerCA(caIds.sideA, accounts.main.address, web3.main.utils.keccak256("Sidechain A CA metadata")),
    "register-ca-a",
    receipts,
  );
  await sendMethod(
    web3.main,
    "main",
    accounts.main,
    mainRegistry.methods.registerCA(caIds.sideB, accounts.main.address, web3.main.utils.keccak256("Sidechain B CA metadata")),
    "register-ca-b",
    receipts,
  );

  const now = Math.floor(Date.now() / 1000);
  const issueArgs = (name) => [
    certIds[name],
    subjectIds[name],
    certificates[name].certificateSha256,
    certificates[name].publicKeySha256,
    now - 60,
    now + 86400,
  ];
  await sendMethod(web3.sideA, "sideA", accounts.sideA, sideA.methods.issueCertificate(...issueArgs("sideA")), "issue-certificate-a", receipts);
  await sendMethod(web3.sideB, "sideB", accounts.sideB, sideB.methods.issueCertificate(...issueArgs("sideB")), "issue-certificate-b", receipts);

  const roots = {
    sideA: web3.sideA.utils.soliditySha3(
      { type: "bytes32", value: ids.sideA },
      { type: "bytes32", value: certIds.sideA },
      { type: "bytes32", value: certificates.sideA.certificateSha256 },
      { type: "uint8", value: 1 },
    ),
    sideB: web3.sideB.utils.soliditySha3(
      { type: "bytes32", value: ids.sideB },
      { type: "bytes32", value: certIds.sideB },
      { type: "bytes32", value: certificates.sideB.certificateSha256 },
      { type: "uint8", value: 1 },
    ),
  };
  await sendMethod(web3.sideA, "sideA", accounts.sideA, sideA.methods.updateStateRoot(roots.sideA), "update-state-root-a", receipts);
  await sendMethod(web3.sideB, "sideB", accounts.sideB, sideB.methods.updateStateRoot(roots.sideB), "update-state-root-b", receipts);

  const sideHeights = {
    sideA: await web3.sideA.eth.getBlockNumber(),
    sideB: await web3.sideB.eth.getBlockNumber(),
  };
  console.log(`[RELAY] sideA root=${roots.sideA} height=${sideHeights.sideA} -> main`);
  await sendMethod(
    web3.main,
    "main",
    accounts.main,
    mainRegistry.methods.submitCheckpoint(ids.sideA, caIds.sideA, roots.sideA, sideHeights.sideA),
    "relay-checkpoint-a",
    receipts,
  );
  console.log(`[RELAY] sideB root=${roots.sideB} height=${sideHeights.sideB} -> main`);
  await sendMethod(
    web3.main,
    "main",
    accounts.main,
    mainRegistry.methods.submitCheckpoint(ids.sideB, caIds.sideB, roots.sideB, sideHeights.sideB),
    "relay-checkpoint-b",
    receipts,
  );

  const [sourceCert, sourceValid, sourceCheckpoint, sourceCa] = await Promise.all([
    sideA.methods.certificates(certIds.sideA).call(),
    sideA.methods.verifyCertificate(certIds.sideA, certificates.sideA.certificateSha256).call(),
    mainRegistry.methods.checkpoints(ids.sideA).call(),
    mainRegistry.methods.certificateAuthorities(caIds.sideA).call(),
  ]);
  const accepted = Boolean(sourceValid)
    && Boolean(sourceCa.active)
    && sourceCert.certHash.toLowerCase() === certificates.sideA.certificateSha256.toLowerCase()
    && sourceCheckpoint.stateRoot.toLowerCase() === roots.sideA.toLowerCase()
    && sourceCheckpoint.caId.toLowerCase() === caIds.sideA.toLowerCase();
  console.log(`[VERIFY][A->B] ${JSON.stringify({ sourceValid, caActive: sourceCa.active, checkpointRoot: sourceCheckpoint.stateRoot, accepted })}`);
  if (!accepted) {
    throw new Error("cross-domain verification failed");
  }

  const requestId = web3.sideB.utils.keccak256(`cross-domain:${Date.now()}`);
  await sendMethod(
    web3.sideB,
    "sideB",
    accounts.sideB,
    sideB.methods.recordCrossDomainAuthentication(
      requestId,
      ids.sideA,
      certIds.sideA,
      certificates.sideA.certificateSha256,
      sourceCheckpoint.stateRoot,
      accepted,
    ),
    "record-cross-domain-auth-a-to-b",
    receipts,
  );
  const storedResult = await sideB.methods.crossDomainResults(requestId).call();
  if (!storedResult.accepted) {
    throw new Error("target sidechain did not retain the accepted result");
  }

  const summary = {
    completedAt: new Date().toISOString(),
    architecture: "three independent Omnilink chains with an application-level checkpoint relay",
    chains,
    contracts: {
      mainRegistry: mainRegistry.options.address,
      sideA: sideA.options.address,
      sideB: sideB.options.address,
    },
    identifiers: { sidechainIds: ids, caIds, certIds, stateRoots: roots, requestId },
    certificates,
    crossDomainVerification: {
      source: "sideA",
      target: "sideB",
      accepted: Boolean(storedResult.accepted),
      checkpoint: sourceCheckpoint.stateRoot,
      recordedAt: storedResult.recordedAt,
    },
    receipts,
  };
  fs.writeFileSync(path.join(OUTPUT_DIR, "experiment_summary.json"), JSON.stringify(summary, null, 2));
  fs.writeFileSync(path.join(OUTPUT_DIR, "receipts.json"), JSON.stringify(receipts, null, 2));
  fs.writeFileSync(path.join(OUTPUT_DIR, "certificates.json"), JSON.stringify(certificates, null, 2));
  console.log(`[SUCCESS] Three-chain sidechain prototype completed. Summary: ${path.join(OUTPUT_DIR, "experiment_summary.json")}`);
}

main().catch((error) => {
  console.error(`[FAILED] ${error.stack || error.message}`);
  process.exitCode = 1;
});
