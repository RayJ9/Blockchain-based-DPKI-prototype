module.exports = {
  "traditional-pki": require("./platforms/centralized-pki"),
  "proposed-dpki": require("./platforms/proposed-dpki"),
  "threshold-validation-dpki": require("./platforms/multi-ca-dpki"),
  "full-contract-onchain": require("./platforms/full-contract-dpki"),
};
