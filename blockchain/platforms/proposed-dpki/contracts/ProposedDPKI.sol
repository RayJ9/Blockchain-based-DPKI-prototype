// SPDX-License-Identifier: MIT
pragma solidity ^0.5.17;
pragma experimental ABIEncoderV2;

import "blockchain/dpki-experiment/contracts/DPKIExperiment.sol";

// Module-local deployment entrypoint; protocol logic lives in the canonical
// contract used by the parameter-sweep and availability experiment runtime.
contract ProposedDPKI is DPKIExperiment {}
