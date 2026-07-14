const fs = require("fs");
const path = require("path");

const root = path.resolve(__dirname, "..");
const solc = require(path.join(root, "dpki-experiment-prototype", "node_modules", "solc"));
const contracts = [
  "platform_proposed_dpki/contracts/ProposedDPKI.sol",
  "platform_threshold_dpki/contracts/ThresholdValidationDPKI.sol",
  "platform_full_contract_dpki/contracts/FullContractDPKI.sol",
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
