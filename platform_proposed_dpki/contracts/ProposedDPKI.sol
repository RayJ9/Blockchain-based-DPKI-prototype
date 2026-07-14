// SPDX-License-Identifier: MIT
pragma solidity ^0.5.17;
pragma experimental ABIEncoderV2;

import "../../dpki-experiment-prototype/contracts/DPKIExperiment.sol";

// Module-local deployment entrypoint; protocol logic lives in the canonical
// contract used by the Fig5-Fig10 experiment runtime.
contract ProposedDPKI is DPKIExperiment {}
