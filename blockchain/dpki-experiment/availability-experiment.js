// Service-layer fault injection for Section V of the manuscript.
// The equal-power majority boundary is an explicit security assumption,
// not a measurement of a successful PoW takeover or a ledger rewrite.
const fs = require('fs');
const path = require('path');
const http = require('http');
const crypto = require('crypto');
const { performance } = require('perf_hooks');

function random(seed) {
  let state = seed >>> 0;
  return () => {
    state += 0x6d2b79f5;
    let n = Math.imul(state ^ (state >>> 15), 1 | state);
    n ^= n + Math.imul(n ^ (n >>> 7), 61 | n);
    return ((n ^ (n >>> 14)) >>> 0) / 4294967296;
  };
}

function validateConfig(config) {
  const c = { rounds: 10, warmupRequests: 20, probeTimeoutMs: 100,
    requestGuardMs: 120000, ...config };
  for (const name of ['rounds', 'requestsPerRound']) {
    if (!Number.isInteger(c[name]) || c[name] < 1) throw new Error(`${name} must be a positive integer`);
  }
  if (!Number.isInteger(c.warmupRequests) || c.warmupRequests < 0) throw new Error('Invalid warmupRequests');
  for (const name of ['probeTimeoutMs', 'requestGuardMs']) {
    if (!Number.isFinite(c[name]) || c[name] <= 0) throw new Error(`Invalid ${name}`);
  }
  for (const name of ['mValues', 'pfValues', 'timeoutsSec', 'scenarios']) {
    if (!Array.isArray(c[name]) || !c[name].length || new Set(c[name]).size !== c[name].length) {
      throw new Error(`${name} must contain unique values`);
    }
  }
  if (c.mValues.some(m => !Number.isInteger(m) || m < 1)) throw new Error('Invalid CA count');
  if (c.pfValues.some(p => !Number.isFinite(p) || p < 0 || p > 1)) throw new Error('Invalid failure probability');
  if (c.timeoutsSec.some(t => !Number.isFinite(t) || t < 0 || t * 1000 >= c.requestGuardMs)) {
    throw new Error('Timeout thresholds must be nonnegative and below the request guard');
  }
  if (c.scenarios.some(s => !['nonresponding', 'malicious'].includes(s))) throw new Error('Unknown fault scenario');
  if (!Number.isInteger(c.seed) || c.seed < 0 || c.seed > 0xffffffff) throw new Error('Invalid seed');
  if (typeof c.outputDir !== 'string' || !c.outputDir) throw new Error('outputDir is required');
  if (c.fixedFaultyCaIds !== undefined) {
    if (c.mValues.length !== 1 || c.pfValues.length !== 1 || !Array.isArray(c.fixedFaultyCaIds)
        || new Set(c.fixedFaultyCaIds).size !== c.fixedFaultyCaIds.length
        || c.fixedFaultyCaIds.some(i => !Number.isInteger(i) || i < 0 || i >= c.mValues[0])) {
      throw new Error('A fixed fault mask is only supported for a single diagnostic point');
    }
  }
  return c;
}

function failureReason(model, scenario, mask, designated, remoteMask, remote, crossDomain) {
  if (model === 'PKI') {
    if (mask[designated]) return 'designated_ca_fault';
    if (crossDomain && remoteMask[remote]) return 'remote_trust_path_fault';
    return null;
  }
  const j = mask.filter(Boolean).length;
  if (scenario === 'nonresponding' && j === mask.length) return 'all_service_cas_unresponsive';
  if (scenario === 'malicious' && j >= Math.ceil(mask.length / 2)) return 'equal_power_security_threshold';
  return null;
}

function classify(record, timeoutSec) {
  if (record.inherentFailure) return 'inherent_failure';
  if (!record.completedSuccessfully) return 'execution_error';
  return record.latencyMs > timeoutSec * 1000 ? 'timeout' : 'success';
}

// A shared FCFS pool, rather than one independent queue per responsive CA.
class Pool {
  constructor(ids) { this.free = [...ids]; this.waiters = []; }
  async use(fn) {
    const id = this.free.length ? this.free.shift() : await new Promise(resolve => this.waiters.push(resolve));
    try { return await fn(id); }
    finally {
      if (this.waiters.length) this.waiters.shift()(id);
      else this.free.push(id);
    }
  }
}

function callEndpoint(url, route, payload, timeoutMs) {
  return new Promise((resolve, reject) => {
    const body = JSON.stringify(payload || {});
    const req = http.request(`${url}${route}`, { method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(body) } }, res => {
      let text = '';
      res.setEncoding('utf8');
      res.on('data', chunk => { text += chunk; });
      res.on('end', () => {
        try {
          const value = JSON.parse(text);
          if (res.statusCode !== 200) throw new Error(value.error || `HTTP ${res.statusCode}`);
          resolve(value);
        } catch (error) { reject(error); }
      });
      res.on('error', reject);
    });
    const timer = setTimeout(() => {
      const error = new Error('Endpoint did not respond before the transport guard');
      error.code = 'ENDPOINT_TIMEOUT';
      req.destroy(error);
    }, timeoutMs);
    req.on('error', reject);
    req.on('close', () => clearTimeout(timer));
    req.end(body);
  });
}

async function startEndpoints(m, invoke, event) {
  const nodes = [];
  try {
    for (let caId = 0; caId < m; caId++) {
      const node = { caId, faulty: false, scenario: 'nonresponding', sockets: new Set() };
      const server = http.createServer((req, res) => {
        if (node.faulty && node.scenario === 'nonresponding') {
          event({ caId, action: 'withheld_response', route: req.url });
          req.resume();
          return; // Real silent endpoint; the probe/client owns its deadline.
        }
        let body = '';
        req.setEncoding('utf8');
        req.on('data', chunk => { body += chunk; });
        req.on('end', async () => {
          try {
            const data = JSON.parse(body || '{}');
            let result;
            if (req.url === '/health') result = { alive: true, caId };
            else if (req.url === '/status' && node.faulty) {
              event({ caId, action: 'false_certificate_status', requestId: data.requestId });
              result = { valid: false, caId }; // All test certificates are valid.
            } else if (req.url === '/status') result = { valid: true, caId };
            else if (req.url === '/execute') result = await invoke(caId, node.faulty, data);
            else throw new Error('Unknown endpoint');
            res.writeHead(200, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify(result));
          } catch (error) {
            res.writeHead(500, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify({ error: error.message }));
          }
        });
        req.on('error', () => {});
      });
      node.server = server;
      server.on('connection', socket => {
        node.sockets.add(socket);
        socket.on('close', () => node.sockets.delete(socket));
      });
      nodes.push(node);
      await new Promise((resolve, reject) => {
        server.once('error', reject);
        server.listen(0, '127.0.0.1', resolve);
      });
      node.url = `http://127.0.0.1:${server.address().port}`;
    }
    return nodes;
  } catch (error) { await stopEndpoints(nodes); throw error; }
}

async function stopEndpoints(nodes) {
  await Promise.all(nodes.map(node => new Promise(resolve => {
    for (const socket of node.sockets) socket.destroy();
    node.server.close(resolve);
  })));
}

async function installMask(nodes, mask, scenario, config, event) {
  nodes.forEach((node, i) => { node.faulty = mask[i]; node.scenario = scenario; });
  await Promise.all(nodes.map(async node => {
    let responds = false;
    try { await callEndpoint(node.url, '/health', {}, config.probeTimeoutMs); responds = true; }
    catch (error) { if (error.code !== 'ENDPOINT_TIMEOUT') throw error; }
    event({ action: 'health_probe', caId: node.caId, faulty: node.faulty, responds });
    if (responds !== !(node.faulty && scenario === 'nonresponding')) throw new Error('Fault injection health check failed');
  }));
}

function summarize(records, thresholds) {
  const groups = new Map();
  for (const r of records) {
    if (r.phase !== 'measurement') continue;
    const key = JSON.stringify([r.scenario, r.m, r.pf, r.model]);
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(r);
  }
  const rows = [];
  for (const group of groups.values()) {
    for (const timeoutSec of thresholds) {
      const counts = { success: 0, inherent_failure: 0, timeout: 0, execution_error: 0 };
      group.forEach(r => counts[classify(r, timeoutSec)]++);
      const { scenario, m, pf, model } = group[0];
      rows.push({ scenario, m, pf, model, timeoutSec, requests: group.length, ...counts,
        availability: counts.success / group.length, Fi: counts.inherent_failure / group.length,
        Ft: counts.timeout / group.length, errorRate: counts.execution_error / group.length });
    }
  }
  return rows;
}

function writeCsv(file, rows) {
  if (!rows.length) throw new Error('No measurement rows');
  const fields = Object.keys(rows[0]);
  const escape = value => JSON.stringify(String(value));
  fs.writeFileSync(file, [fields.join(','), ...rows.map(r => fields.map(k => escape(r[k])).join(','))].join('\n') + '\n');
}

async function runAvailability(config, runtime) {
  const c = validateConfig(config);
  const args = runtime.args;
  for (const key of ['lambdaArrival', 'serviceCAs', 'maxOnchainInFlight']) {
    if (!Number.isFinite(args[key]) || args[key] <= 0) throw new Error(`Invalid runtime ${key}`);
  }
  const output = path.resolve(c.outputDir);
  fs.mkdirSync(output, { recursive: true });
  const manifestPath = path.join(output, 'availability_manifest.json');
  const manifest = { runId: crypto.randomUUID(), startedAt: new Date().toISOString(), status: 'running', config: c,
    workload: { lambda: args.lambdaArrival, p: args.pManage, gamma: args.gammaOnChain, epsilon: args.epsilonValues[0] },
    faultSampling: c.fixedFaultyCaIds === undefined ? 'independent Bernoulli CAs, fixed within each round' : 'fixed mask diagnostic; not a probability-sweep estimate',
    topology: 'independent loopback HTTP CA endpoints sharing one process and the domain certificate repository',
    majorityFailure: 'paper equal-power security-boundary assumption; no consensus takeover or finalized-state modification',
    timeouts: 'classify unchanged completed request latency, including queue, detection and on-chain fallback',
    failurePartition: 'success, inherent_failure, timeout, execution_error; no dropped errors',
    theoreticalBoundsUsed: false };
  // Exclusive creation prevents mixing measurements from different invocations.
  fs.writeFileSync(manifestPath, JSON.stringify(manifest, null, 2), { flag: 'wx' });
  const rawPath = path.join(output, 'availability_requests.jsonl');
  const eventPath = path.join(output, 'availability_events.jsonl');
  fs.writeFileSync(rawPath, '', { flag: 'wx' });
  fs.writeFileSync(eventPath, '', { flag: 'wx' });
  const totals = new Map();
  let measurementRecords = 0;
  let executionErrors = 0;
  function accumulate(record) {
    if (record.error) executionErrors++;
    if (record.phase !== 'measurement') return;
    measurementRecords++;
    for (const timeoutSec of c.timeoutsSec) {
      const { scenario, m, pf, model } = record;
      const key = JSON.stringify([scenario, m, pf, model, timeoutSec]);
      if (!totals.has(key)) totals.set(key, { scenario, m, pf, model, timeoutSec, requests: 0,
        success: 0, inherent_failure: 0, timeout: 0, execution_error: 0 });
      const row = totals.get(key);
      row.requests++;
      row[classify(record, timeoutSec)]++;
    }
  }
  const summaryRows = () => [...totals.values()].map(row => ({ ...row,
    availability: row.success / row.requests, Fi: row.inherent_failure / row.requests,
    Ft: row.timeout / row.requests, errorRate: row.execution_error / row.requests }));
  let context = {};
  const event = data => fs.appendFileSync(eventPath, JSON.stringify({ runId: manifest.runId,
    time: new Date().toISOString(), ...context, ...data }) + '\n');
  const chainPool = new Pool(Array.from({ length: Math.min(args.maxOnchainInFlight, runtime.senderCount) }, (_, i) => i));
  const draw = random(c.seed);
  try {
    for (const scenario of c.scenarios) for (const m of c.mValues) {
      let activeModel = 'DPKI';
      const sourceNodes = await startEndpoints(m, async (caId, faulty, data) => {
        if (activeModel === 'DPKI' && !data.request.onChain) {
          const proof = runtime.makeProof(data.request, faulty);
          if (faulty) event({ action: 'signed_corrupt_merkle_proof', caId, requestId: data.request.requestId, proof });
          return { proof };
        }
        return activeModel === 'DPKI'
          ? runtime.executeDpki(data.request, data.senderId)
          : runtime.executePki(data.request);
      }, event);
      let remoteNodes = [];
      try {
        remoteNodes = await startEndpoints(m, async () => ({}), data => event({ ...data, domain: 'remote' }));
        for (const pf of c.pfValues) for (let round = 0; round < c.rounds; round++) {
          const mask = Array.from({ length: m }, (_, i) => c.fixedFaultyCaIds === undefined ? draw() < pf : c.fixedFaultyCaIds.includes(i));
          const remoteMask = Array.from({ length: m }, () => draw() < pf);
          context = { scenario, m, pf, round };
          const faultyCaIds = mask.flatMap((bad, i) => bad ? [i] : []);
          const remoteFaultyCaIds = remoteMask.flatMap((bad, i) => bad ? [i] : []);
          event({ action: 'install_fault_state', faultyCaIds, remoteFaultyCaIds });
          await installMask(sourceNodes, mask, scenario, c, event);
          await installMask(remoteNodes, remoteMask, scenario, c, data => event({ ...data, domain: 'remote' }));
          for (const model of ['DPKI', 'PKI']) {
            activeModel = model;
            const responsiveIds = mask.flatMap((bad, i) => bad ? [] : [i]);
            const sharedPool = new Pool(responsiveIds);
            const pkiQueues = Array.from({ length: m }, (_, i) => new Pool([i]));
            const jobs = [];
            const start = performance.now();
            let arrivalOffset = 0;
            const workloadRandom = random((c.seed + round * 65537 + m * 257 + Math.round(pf * 1000000)) >>> 0);
            const count = c.warmupRequests + c.requestsPerRound;
            for (let index = 0; index < count; index++) {
              if (index) arrivalOffset += -Math.log(1 - workloadRandom()) * 1000 / args.lambdaArrival;
              await new Promise(resolve => setTimeout(resolve, Math.max(0, start + arrivalOffset - performance.now())));
              const req = runtime.makeRequest(model, workloadRandom, index);
              const designated = Math.floor(workloadRandom() * m);
              const remote = Math.floor(workloadRandom() * m);
              const arrival = performance.now();
              const rec = { runId: manifest.runId, ...context, model, index,
                phase: index < c.warmupRequests ? 'warmup' : 'measurement', requestId: req.requestId,
                kind: req.kind, originalOnChain: req.onChain, crossDomain: req.crossDomain,
                designatedCaId: designated, remoteCaId: remote, faultyCaIds, remoteFaultyCaIds,
                securityThreshold: Math.ceil(m / 2), arrivalWallMs: arrival,
                scheduledArrivalMs: start + arrivalOffset, arrivedAt: new Date().toISOString(),
                inherentFailure: failureReason(model, scenario, mask, designated, remoteMask, remote, req.crossDomain),
                completedSuccessfully: false, fallbackOnChain: false, proofRejected: false,
                actualCaId: null, queueMs: 0, serviceMs: 0, latencyMs: null, receipts: [], error: null };
              const job = (async () => {
                let service = 0;
                async function measured(fn) {
                  const before = performance.now();
                  try { return await fn(); } finally { service += performance.now() - before; }
                }
                async function onchain() {
                  return chainPool.use(async senderId => measured(async () => {
                    const healthy = responsiveIds[0];
                    rec.actualCaId = healthy;
                    const result = await callEndpoint(sourceNodes[healthy].url, '/execute',
                      { request: { ...req, onChain: true, kind: req.kind === 'intra-off-chain' ? 'intra-on-chain' : req.kind }, senderId }, c.requestGuardMs);
                    rec.receipts = result.receipts || [];
                  }));
                }
                try {
                  if (rec.inherentFailure) {
                    // Exercise a compromised PKI endpoint to retain the false answer as evidence.
                    if (model === 'PKI' && scenario === 'malicious') {
                      const node = mask[designated] ? sourceNodes[designated] : remoteNodes[remote];
                      rec.injectedStatus = await measured(() => callEndpoint(node.url, '/status', { requestId: req.requestId }, c.requestGuardMs));
                    }
                    event({ action: 'inherent_failure', model, requestId: req.requestId, reason: rec.inherentFailure });
                  } else if (model === 'PKI') {
                    await pkiQueues[designated].use(async id => measured(async () => {
                      rec.actualCaId = id;
                      await callEndpoint(sourceNodes[id].url, '/execute', { request: req }, c.requestGuardMs);
                    }));
                    rec.completedSuccessfully = true;
                  } else if (req.onChain) {
                    await onchain(); rec.completedSuccessfully = true;
                  } else {
                    const verify = async id => measured(async () => {
                      rec.actualCaId = id;
                      const response = await callEndpoint(sourceNodes[id].url, '/execute', { request: req }, c.requestGuardMs);
                      await runtime.verifyOffchain(req, response.proof);
                    });
                    try {
                      if (scenario === 'malicious' && mask[designated]) await verify(designated);
                      else await sharedPool.use(verify);
                    } catch (error) {
                      if (error.code !== 'INVALID_MERKLE_PROOF') throw error;
                      rec.proofRejected = true;
                      event({ action: 'merkle_proof_rejected', model, requestId: req.requestId, caId: rec.actualCaId });
                      rec.fallbackOnChain = true;
                      await onchain();
                    }
                    rec.completedSuccessfully = true;
                  }
                } catch (error) { rec.error = String(error.stack || error); }
                finally {
                  rec.finishWallMs = performance.now();
                  rec.latencyMs = rec.finishWallMs - arrival;
                  rec.serviceMs = service;
                  rec.queueMs = rec.latencyMs - service;
                  accumulate(rec);
                  fs.appendFileSync(rawPath, JSON.stringify(rec) + '\n');
                }
              })();
              jobs.push(job);
            }
            await Promise.all(jobs);
            if (executionErrors) throw new Error(`Execution errors recorded (${executionErrors}); inspect request logs before using availability estimates`);
            console.log(`[availability] ${scenario} m=${m} pf=${pf} round=${round} ${model} j=${faultyCaIds.length}/${m} requests=${c.requestsPerRound}`);
          }
        }
      } finally { await stopEndpoints([...sourceNodes, ...remoteNodes]); }
    }
    writeCsv(path.join(output, 'availability_summary.csv'), summaryRows());
    manifest.status = 'complete';
    manifest.measurementRecords = measurementRecords;
  } catch (error) { manifest.status = 'failed'; manifest.error = String(error.stack || error); throw error; }
  finally {
    manifest.finishedAt = new Date().toISOString();
    manifest.requestLogSha256 = crypto.createHash('sha256').update(fs.readFileSync(rawPath)).digest('hex');
    fs.writeFileSync(manifestPath, JSON.stringify(manifest, null, 2));
  }
  return { manifest, summary: summaryRows() };
}

module.exports = { validateConfig, random, failureReason, classify, summarize, Pool,
  callEndpoint, startEndpoints, stopEndpoints, installMask, runAvailability };
