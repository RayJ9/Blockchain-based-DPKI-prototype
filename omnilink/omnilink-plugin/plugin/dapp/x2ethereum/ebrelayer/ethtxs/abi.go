package ethtxs

import (
	"strings"

	"code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/x2ethereum/ebrelayer/ethcontract/generated"
	"github.com/ethereum/go-ethereum/accounts/abi"
)

//const
const (
	BridgeBankABI     = "BridgeBankABI"
	OmnilinkBankABI   = "OmnilinkBankABI"
	OmnilinkBridgeABI = "OmnilinkBridgeABI"
	EthereumBankABI   = "EthereumBankABI"
)

//LoadABI ...
func LoadABI(contractName string) abi.ABI {
	var abiJSON string
	switch contractName {
	case BridgeBankABI:
		abiJSON = generated.BridgeBankABI
	case OmnilinkBankABI:
		abiJSON = generated.OmnilinkBankABI
	case OmnilinkBridgeABI:
		abiJSON = generated.OmnilinkBridgeABI
	case EthereumBankABI:
		abiJSON = generated.EthereumBankABI
	default:
		panic("No abi matched")
	}

	// Convert the raw abi into a usable format
	contractABI, err := abi.JSON(strings.NewReader(abiJSON))
	if err != nil {
		panic(err)
	}

	return contractABI
}
