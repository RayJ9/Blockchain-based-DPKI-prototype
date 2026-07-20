pragma solidity ^0.5.0;

import "../../openzeppelin-solidity/contracts/math/SafeMath.sol";
import "./BridgeToken.sol";

/**
 * @title OmnilinkBank
 * @dev Manages the deployment and minting of ERC20 compatible BridgeTokens
 *      which represent assets based on the Omnilink blockchain.
 **/

contract OmnilinkBank {

    using SafeMath for uint256;

    uint256 public bridgeTokenCount;
    mapping(address => bool) public bridgeTokenWhitelist;
    mapping(bytes32 => bool) public bridgeTokenCreated;
    mapping(bytes32 => OmnilinkDeposit) omnilinkDeposits;
    mapping(bytes32 => OmnilinkBurn) omnilinkBurns;
    mapping(address => DepositBurnCount) depositBurnCounts;
    mapping(bytes32 => address) public token2address;

    struct OmnilinkDeposit {
        bytes omnilinkSender;
        address payable ethereumRecipient;
        address bridgeTokenAddress;
        uint256 amount;
        bool exist;
        uint256 nonce;
    }

    struct DepositBurnCount {
        uint256 depositCount;
        uint256 burnCount;
    }

    struct OmnilinkBurn {
        bytes omnilinkSender;
        address payable ethereumOwner;
        address bridgeTokenAddress;
        uint256 amount;
        uint256 nonce;
    }

    /*
    * @dev: Event declarations
    */
    event LogNewBridgeToken(
        address _token,
        string _symbol
    );

    event LogBridgeTokenMint(
        address _token,
        string _symbol,
        uint256 _amount,
        address _beneficiary
    );

    event LogOmnilinkTokenBurn(
        address _token,
        string _symbol,
        uint256 _amount,
        address _ownerFrom,
        bytes _omnilinkReceiver,
        uint256 _nonce
    );

    /*
     * @dev: Modifier to make sure this symbol not created now
     */
     modifier notCreated(string memory _symbol)
     {
         require(
             !hasBridgeTokenCreated(_symbol),
             "The symbol has been created already"
         );
         _;
     }

     /*
     * @dev: Modifier to make sure this symbol not created now
     */
     modifier created(string memory _symbol)
     {
         require(
             hasBridgeTokenCreated(_symbol),
             "The symbol has not been created yet"
         );
         _;
     }

    /*
    * @dev: Constructor, sets bridgeTokenCount
    */
    constructor () public {
        bridgeTokenCount = 0;
    }

    /*
    * @dev: check whether this symbol has been created yet or not
    *
    * @param _symbol: token symbol
    * @return: true or false
    */
    function hasBridgeTokenCreated(string memory _symbol) public view returns(bool) {
        bytes32 symHash = keccak256(abi.encodePacked(_symbol));
        return bridgeTokenCreated[symHash];
    }

    /*
    * @dev: Creates a new OmnilinkDeposit with a unique ID
    *
    * @param _omnilinkSender: The sender's Omnilink address in bytes.
    * @param _ethereumRecipient: The intended recipient's Ethereum address.
    * @param _token: The currency type
    * @param _amount: The amount in the deposit.
    * @return: The newly created OmnilinkDeposit's unique id.
    */
    function newOmnilinkDeposit(
        bytes memory _omnilinkSender,
        address payable _ethereumRecipient,
        address _token,
        uint256 _amount
    )
        internal
        returns(bytes32)
    {
        DepositBurnCount memory depositBurnCount = depositBurnCounts[_token];
        depositBurnCount.depositCount = depositBurnCount.depositCount.add(1);
        depositBurnCounts[_token] = depositBurnCount;

        bytes32 depositID = keccak256(
            abi.encodePacked(
                _omnilinkSender,
                _ethereumRecipient,
                _token,
                _amount,
                depositBurnCount.depositCount
            )
        );

        omnilinkDeposits[depositID] = OmnilinkDeposit(
            _omnilinkSender,
            _ethereumRecipient,
            _token,
            _amount,
            true,
            depositBurnCount.depositCount
        );

        return depositID;
    }

    /*
    * @dev: Creates a new OmnilinkBurn with a unique ID
        *
        * @param _omnilinkSender: The sender's Omnilink address in bytes.
        * @param _ethereumOwner: The owner's Ethereum address.
        * @param _token: The token Address
        * @param _amount: The amount to be burned.
        * @param _nonce: The nonce indicates the burn count for this token
        * @return: The newly created OmnilinkBurn's unique id.
        */
        function newOmnilinkBurn(
            bytes memory _omnilinkSender,
            address payable _ethereumOwner,
            address _token,
            uint256 _amount,
            uint256 nonce
        )
            internal
            returns(bytes32)
        {
            bytes32 burnID = keccak256(
                abi.encodePacked(
                    _omnilinkSender,
                    _ethereumOwner,
                    _token,
                    _amount,
                    nonce
                )
            );

            omnilinkBurns[burnID] = OmnilinkBurn(
                _omnilinkSender,
                _ethereumOwner,
                _token,
                _amount,
                nonce
            );

            return burnID;
        }


    /*
     * @dev: Deploys a new BridgeToken contract
     *
     * @param _symbol: The BridgeToken's symbol
     */
    function deployNewBridgeToken(
        string memory _symbol
    )
        internal
        notCreated(_symbol)
        returns(address)
    {
        bridgeTokenCount = bridgeTokenCount.add(1);

        // Deploy new bridge token contract
        BridgeToken newBridgeToken = (new BridgeToken)(_symbol);

        // Set address in tokens mapping
        address newBridgeTokenAddress = address(newBridgeToken);
        bridgeTokenWhitelist[newBridgeTokenAddress] = true;
        bytes32 symHash = keccak256(abi.encodePacked(_symbol));
        bridgeTokenCreated[symHash] = true;
        depositBurnCounts[newBridgeTokenAddress] = DepositBurnCount(
            uint256(0),
            uint256(0));
        token2address[symHash] = newBridgeTokenAddress;

        emit LogNewBridgeToken(
            newBridgeTokenAddress,
            _symbol
        );

        return newBridgeTokenAddress;
    }

    /*
     * @dev: Mints new omnilink tokens
     *
     * @param _omnilinkSender: The sender's Omnilink address in bytes.
     * @param _ethereumRecipient: The intended recipient's Ethereum address.
     * @param _omnilinkTokenAddress: The currency type
     * @param _symbol: omnilink token symbol
     * @param _amount: number of omnilink tokens to be minted
     */
     function mintNewBridgeTokens(
        bytes memory _omnilinkSender,
        address payable _intendedRecipient,
        address _bridgeTokenAddress,
        string memory _symbol,
        uint256 _amount
    )
        internal
    {
        // Must be whitelisted bridge token
        require(
            bridgeTokenWhitelist[_bridgeTokenAddress],
            "Token must be a whitelisted bridge token"
        );

        // Mint bridge tokens
        require(
            BridgeToken(_bridgeTokenAddress).mint(
                _intendedRecipient,
                _amount
            ),
            "Attempted mint of bridge tokens failed"
        );

        newOmnilinkDeposit(
            _omnilinkSender,
            _intendedRecipient,
            _bridgeTokenAddress,
            _amount
        );

        emit LogBridgeTokenMint(
            _bridgeTokenAddress,
            _symbol,
            _amount,
            _intendedRecipient
        );
    }

    /*
     * @dev: Burn omnilink tokens
     *
     * @param _from: The address to be burned from
     * @param _omnilinkReceiver: The receiver's Omnilink address in bytes.
     * @param _omnilinkTokenAddress: The token address of omnilink asset issued on ethereum
     * @param _amount: number of omnilink tokens to be minted
     */
    function burnOmnilinkTokens(
        address payable _from,
        bytes memory _omnilinkReceiver,
        address _omnilinkTokenAddress,
        uint256 _amount
    )
        internal
    {
        // Must be whitelisted bridge token
        require(
            bridgeTokenWhitelist[_omnilinkTokenAddress],
            "Token must be a whitelisted bridge token"
        );

        // burn bridge tokens
        BridgeToken bridgeTokenInstance = BridgeToken(_omnilinkTokenAddress);
        bridgeTokenInstance.burnFrom(_from, _amount);

        DepositBurnCount memory depositBurnCount = depositBurnCounts[_omnilinkTokenAddress];
        require(
            depositBurnCount.burnCount + 1 > depositBurnCount.burnCount,
            "burn nonce is not available"
        );
        depositBurnCount.burnCount = depositBurnCount.burnCount.add(1);
        depositBurnCounts[_omnilinkTokenAddress] = depositBurnCount;

        newOmnilinkBurn(
            _omnilinkReceiver,
            _from,
            _omnilinkTokenAddress,
            _amount,
            depositBurnCount.burnCount
        );

        emit LogOmnilinkTokenBurn(
            _omnilinkTokenAddress,
            bridgeTokenInstance.symbol(),
            _amount,
            _from,
            _omnilinkReceiver,
            depositBurnCount.burnCount
        );
    }

    /*
    * @dev: Checks if an individual OmnilinkDeposit exists.
    *
    * @param _id: The unique OmnilinkDeposit's id.
    * @return: Boolean indicating if the OmnilinkDeposit exists in memory.
    */
    function isLockedOmnilinkDeposit(
        bytes32 _id
    )
        internal
        view
        returns(bool)
    {
        return(omnilinkDeposits[_id].exist);
    }

  /*
    * @dev: Gets an item's information
    *
    * @param _Id: The item containing the desired information.
    * @return: Sender's address.
    * @return: Recipient's address in bytes.
    * @return: Token address.
    * @return: Amount of ethereum/erc20 in the item.
    * @return: Unique nonce of the item.
    */
    function getOmnilinkDeposit(
        bytes32 _id
    )
        internal
        view
        returns(bytes memory, address payable, address, uint256)
    {
        OmnilinkDeposit memory deposit = omnilinkDeposits[_id];

        return(
            deposit.omnilinkSender,
            deposit.ethereumRecipient,
            deposit.bridgeTokenAddress,
            deposit.amount
        );
    }

    function getToken2address(string memory _symbol)
        created(_symbol)
        public view returns(address)
    {
        bytes32 symHash = keccak256(abi.encodePacked(_symbol));
        return token2address[symHash];
    }
}