pragma solidity ^0.5.0;

import "./OmnilinkBank.sol";
import "./EthereumBank.sol";
import "../Oracle.sol";
import "../OmnilinkBridge.sol";

/**
 * @title BridgeBank
 * @dev Bank contract which coordinates asset-related functionality.
 *      OmnilinkBank manages the minting and burning of tokens which
 *      represent Omnilink based assets, while EthereumBank manages
 *      the locking and unlocking of Ethereum and ERC20 token assets
 *      based on Ethereum.
 **/

contract BridgeBank is OmnilinkBank, EthereumBank {

    using SafeMath for uint256;
    
    address public operator;
    Oracle public oracle;
    OmnilinkBridge public omnilinkBridge;

    /*
    * @dev: Constructor, sets operator
    */
    constructor (
        address _operatorAddress,
        address _oracleAddress,
        address _omnilinkBridgeAddress
    )
        public
    {
        operator = _operatorAddress;
        oracle = Oracle(_oracleAddress);
        omnilinkBridge = OmnilinkBridge(_omnilinkBridgeAddress);
    }

    /*
    * @dev: Modifier to restrict access to operator
    */
    modifier onlyOperator() {
        require(
            msg.sender == operator,
            'Must be BridgeBank operator.'
        );
        _;
    }

    /*
    * @dev: Modifier to restrict access to the oracle
    */
    modifier onlyOracle()
    {
        require(
            msg.sender == address(oracle),
            "Access restricted to the oracle"
        );
        _;
    }

    /*
    * @dev: Modifier to restrict access to the omnilink bridge
    */
    modifier onlyOmnilinkBridge()
    {
        require(
            msg.sender == address(omnilinkBridge),
            "Access restricted to the omnilink bridge"
        );
        _;
    }

   /*
    * @dev: Fallback function allows operator to send funds to the bank directly
    *       This feature is used for testing and is available at the operator's own risk.
    */
    function() external payable onlyOperator {}

    /*
    * @dev: Creates a new BridgeToken
    *
    * @param _symbol: The new BridgeToken's symbol
    * @return: The new BridgeToken contract's address
    */
    function createNewBridgeToken(
        string memory _symbol
    )
        public
        onlyOperator
        returns(address)
    {
        return deployNewBridgeToken(_symbol);
    }

    /*
     * @dev: Mints new BankTokens
     *
     * @param _omnilinkSender: The sender's Omnilink address in bytes.
     * @param _ethereumRecipient: The intended recipient's Ethereum address.
     * @param _omnilinkTokenAddress: The currency type
     * @param _symbol: omnilink token symbol
     * @param _amount: number of omnilink tokens to be minted
     */
     function mintBridgeTokens(
        bytes memory _omnilinkSender,
        address payable _intendedRecipient,
        address _bridgeTokenAddress,
        string memory _symbol,
        uint256 _amount
    )
        public
        onlyOmnilinkBridge
    {
        return mintNewBridgeTokens(
            _omnilinkSender,
            _intendedRecipient,
            _bridgeTokenAddress,
            _symbol,
            _amount
        );
    }

    /*
     * @dev: Burns bank tokens
     *
     * @param _omnilinkReceiver: The _omnilink receiver address in bytes.
     * @param _omnilinkTokenAddress: The currency type
     * @param _amount: number of omnilink tokens to be burned
     */
    function burnBridgeTokens(
        bytes memory _omnilinkReceiver,
        address _omnilinkTokenAddress,
        uint256 _amount
    )
        public
    {
        return burnOmnilinkTokens(
            msg.sender,
            _omnilinkReceiver,
            _omnilinkTokenAddress,
             _amount
        );
    }

    /*
    * @dev: Locks received Ethereum funds.
    *
    * @param _recipient: bytes representation of destination address.
    * @param _token: token address in origin chain (0x0 if ethereum)
    * @param _amount: value of deposit
    */
    function lock(
        bytes memory _recipient,
        address _token,
        uint256 _amount
    )
        public
        availableNonce()
        payable
    {
        string memory symbol;

        // Ethereum deposit
        if (msg.value > 0) {
          require(
              _token == address(0),
              "Ethereum deposits require the 'token' address to be the null address"
            );
          require(
              msg.value == _amount,
              "The transactions value must be equal the specified amount (in wei)"
            );

          // Set the the symbol to ETH
          symbol = "ETH";
          // ERC20 deposit
        } else {
          require(
              BridgeToken(_token).transferFrom(msg.sender, address(this), _amount),
              "Contract token allowances insufficient to complete this lock request"
          );
          // Set symbol to the ERC20 token's symbol
          symbol = BridgeToken(_token).symbol();
        }

        lockFunds(
            msg.sender,
            _recipient,
            _token,
            symbol,
            _amount
        );
    }

   /*
    * @dev: Unlocks Ethereum and ERC20 tokens held on the contract.
    *
    * @param _recipient: recipient's Ethereum address
    * @param _token: token contract address
    * @param _symbol: token symbol
    * @param _amount: wei amount or ERC20 token count
\   */
     function unlock(
        address payable _recipient,
        address _token,
        string memory _symbol,
        uint256 _amount
    )
        public
        onlyOmnilinkBridge
        hasLockedFunds(
            _token,
            _amount
        )
        canDeliver(
            _token,
            _amount
        )
    {
        unlockFunds(
            _recipient,
            _token,
            _symbol,
            _amount
        );
    }

    /*
    * @dev: Exposes an item's current status.
    *
    * @param _id: The item in question.
    * @return: Boolean indicating the lock status.
    */
    function getOmnilinkDepositStatus(
        bytes32 _id
    )
        public
        view
        returns(bool)
    {
        return isLockedOmnilinkDeposit(_id);
    }

    /*
    * @dev: Allows access to a Omnilink deposit's information via its unique identifier.
    *
    * @param _id: The deposit to be viewed.
    * @return: Original sender's Ethereum address.
    * @return: Intended Omnilink recipient's address in bytes.
    * @return: The lock deposit's currency, denoted by a token address.
    * @return: The amount locked in the deposit.
    * @return: The deposit's unique nonce.
    */
    function viewOmnilinkDeposit(
        bytes32 _id
    )
        public
        view
        returns(bytes memory, address payable, address, uint256)
    {
        return getOmnilinkDeposit(_id);
    }

}