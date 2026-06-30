package ethtxs

import (
	"strings"

	"code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/cross2eth/contracts/contracts4eth/generated"
	"github.com/ethereum/go-ethereum/accounts/abi"
)

//const
const (
	BridgeBankABI     = "BridgeBankABI"
	OmnilinkBankABI   = "OmnilinkBankABI"
	OmnilinkBridgeABI = "OmnilinkBridgeABI"
	EthereumBankABI   = "EthereumBankABI"
	OracleABI         = "OracleABI"
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
	case OracleABI:
		abiJSON = generated.OracleABI
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
