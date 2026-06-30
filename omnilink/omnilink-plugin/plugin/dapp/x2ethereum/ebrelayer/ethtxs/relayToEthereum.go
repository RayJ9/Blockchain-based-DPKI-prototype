package ethtxs

import (
	"crypto/ecdsa"

	"code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/x2ethereum/ebrelayer/ethinterface"
	"github.com/ethereum/go-ethereum/common/hexutil"

	"code.corp.bcollie.net/omnilink/omnilink-base/common/log/log15"
	"code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/x2ethereum/ebrelayer/ethcontract/generated"
	"code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/x2ethereum/ebrelayer/events"
	"github.com/ethereum/go-ethereum/common"
	"github.com/ethereum/go-ethereum/crypto"
)

var (
	txslog = log15.New("ethereum relayer", "ethtxs")
)

//const ...
const (
	// GasLimit : the gas limit in Gwei used for transactions sent with TransactOpts
	GasLimit        = uint64(100 * 10000)
	GasLimit4Deploy = uint64(0) //此处需要设置为0,让交易自行估计,否则将会导致部署失败,TODO:其他解决途径后续调研解决
)

// RelayOracleClaimToEthereum : relays the provided burn or lock to OmnilinkBridge contract on the Ethereum network
func RelayOracleClaimToEthereum(oracleInstance *generated.Oracle, client ethinterface.EthClientSpec, sender common.Address, event events.Event, claim ProphecyClaim, privateKey *ecdsa.PrivateKey, omnilinkTxHash []byte) (txhash string, err error) {
	txslog.Info("RelayProphecyClaimToEthereum", "sender", sender.String(), "event", event, "omnilinkSender", hexutil.Encode(claim.OmnilinkSender), "ethereumReceiver", claim.EthereumReceiver.String(), "TokenAddress", claim.TokenContractAddress.String(), "symbol", claim.Symbol, "Amount", claim.Amount.String(), "claimType", claim.ClaimType.String())

	auth, err := PrepareAuth(client, privateKey, sender)
	if nil != err {
		txslog.Error("RelayProphecyClaimToEthereum", "PrepareAuth err", err.Error())
		return "", err
	}
	auth.GasLimit = GasLimit

	claimID := crypto.Keccak256Hash(omnilinkTxHash, claim.OmnilinkSender, claim.EthereumReceiver.Bytes(), []byte(claim.Symbol), claim.Amount.Bytes())

	// Sign the hash using the active validator's private key
	signature, err := SignClaim4Eth(claimID, privateKey)
	if nil != err {
		return "", err
	}

	tx, err := oracleInstance.NewOracleClaim(auth, uint8(claim.ClaimType), claim.OmnilinkSender, claim.EthereumReceiver, claim.TokenContractAddress, claim.Symbol, claim.Amount, claimID, signature)
	if nil != err {
		txslog.Error("RelayProphecyClaimToEthereum", "NewOracleClaim failed due to:", err.Error())
		return "", err
	}

	txhash = tx.Hash().Hex()
	txslog.Info("RelayProphecyClaimToEthereum", "NewOracleClaim tx hash:", txhash)
	return txhash, nil
}
