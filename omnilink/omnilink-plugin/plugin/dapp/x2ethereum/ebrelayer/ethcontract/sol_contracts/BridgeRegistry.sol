pragma solidity ^0.5.0;

contract BridgeRegistry {

    address public omnilinkBridge;
    address public bridgeBank;
    address public oracle;
    address public valset;
    uint256 public deployHeight;

    event LogContractsRegistered(
        address _omnilinkBridge,
        address _bridgeBank,
        address _oracle,
        address _valset
    );
    
    constructor(
        address _omnilinkBridge,
        address _bridgeBank,
        address _oracle,
        address _valset
    )
        public
    {
        omnilinkBridge = _omnilinkBridge;
        bridgeBank = _bridgeBank;
        oracle = _oracle;
        valset = _valset;
        deployHeight = block.number;

        emit LogContractsRegistered(
            omnilinkBridge,
            bridgeBank,
            oracle,
            valset
        );
    }
}