// SPDX-License-Identifier: MIT
pragma solidity ^0.5.17;
pragma experimental ABIEncoderV2;

import "../../../experiments/baseline-comparison/prototype_baseline_benchmark/contracts/Fig4BaselineBenchmark.sol";

contract ThresholdValidationDPKI is Fig4BaselineBenchmark {
    constructor(address[] memory validators)
        Fig4BaselineBenchmark(validators)
        public
    {}
}
