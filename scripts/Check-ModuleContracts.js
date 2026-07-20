const fs = require("fs");
const path = require("path");

const root = path.resolve(__dirname, "..");
const solc = require(path.join(root, "blockchain", "dpki-experiment", "node_modules", "solc"));
const contracts = [
  "blockchain/platforms/proposed-dpki/contracts/ProposedDPKI.sol",
  "blockchain/platforms/multi-ca-dpki/contracts/ThresholdValidationDPKI.sol",
  "blockchain/platforms/full-contract-dpki/contracts/FullContractDPKI.sol",
  "blockchain/sidechain-three-chain/contracts/MainChainCARegistry.sol",
  "blockchain/sidechain-three-chain/contracts/SidechainDPKI.sol",
];

for (const relativePath of contracts) {
  const absolutePath = path.join(root, relativePath);
  const sourceDir = path.dirname(absolutePath);
  const input = {
    language: "Solidity",
    sources: { [path.basename(absolutePath)]: { content: fs.readFileSync(absolutePath, "utf8") } },
    settings: { outputSelection: { "*": { "*": ["abi", "evm.bytecode.object"] } } },
  };
  const output = JSON.parse(solc.compile(JSON.stringify(input), {
    import(importPath) {
      const candidates = [path.resolve(sourceDir, importPath), path.resolve(root, importPath)];
      const imported = candidates.find((candidate) => candidate.startsWith(root) && fs.existsSync(candidate));
      if (!imported) return { error: `Missing import: ${candidates.join(" or ")}` };
      if (!imported.startsWith(root)) return { error: `Import outside repository: ${importPath}` };
      return { contents: fs.readFileSync(imported, "utf8") };
    },
  }));
  const errors = (output.errors || []).filter((item) => item.severity === "error");
  if (errors.length) {
    throw new Error(`${relativePath}\n${errors.map((item) => item.formattedMessage).join("\n")}`);
  }
  console.log(`Contract check passed: ${relativePath}`);
}
