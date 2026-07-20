package ethtxs

// --------------------------------------------------------
//      Parser
//
//      Parses structs containing event information into
//      unsigned transactions for validators to sign, then
//      relays the data packets as transactions on the
//      omnilink Bridge.
// --------------------------------------------------------

import (
	"math/big"
	"strings"

	omnilinkTypes "code.corp.bcollie.net/omnilink/omnilink-base/types"
	"code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/x2ethereum/ebrelayer/events"
	ebrelayerTypes "code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/x2ethereum/ebrelayer/types"
	"code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/x2ethereum/types"
	"github.com/ethereum/go-ethereum/common"
)

// LogLockToEthBridgeClaim : parses and packages a LockEvent struct with a validator address in an EthBridgeClaim msg
func LogLockToEthBridgeClaim(event *events.LockEvent, ethereumChainID int64, bridgeBrankAddr string, decimal int64) (*ebrelayerTypes.EthBridgeClaim, error) {
	recipient := event.To
	if 0 == len(recipient) {
		return nil, ebrelayerTypes.ErrEmptyAddress
	}
	// Symbol formatted to lowercase
	symbol := strings.ToLower(event.Symbol)
	if symbol == "eth" && event.Token != common.HexToAddress("0x0000000000000000000000000000000000000000") {
		return nil, ebrelayerTypes.ErrAddress4Eth
	}

	witnessClaim := &ebrelayerTypes.EthBridgeClaim{}
	witnessClaim.EthereumChainID = ethereumChainID
	witnessClaim.BridgeBrankAddr = bridgeBrankAddr
	witnessClaim.Nonce = event.Nonce.Int64()
	witnessClaim.TokenAddr = event.Token.String()
	witnessClaim.Symbol = event.Symbol
	witnessClaim.EthereumSender = event.From.String()
	witnessClaim.OmnilinkReceiver = string(recipient)

	if decimal > 8 {
		event.Value = event.Value.Quo(event.Value, big.NewInt(int64(types.MultiplySpecifyTimes(1, decimal-8))))
	} else {
		event.Value = event.Value.Mul(event.Value, big.NewInt(int64(types.MultiplySpecifyTimes(1, 8-decimal))))
	}
	witnessClaim.Amount = event.Value.String()

	witnessClaim.ClaimType = types.LockClaimType
	witnessClaim.ChainName = types.LockClaim
	witnessClaim.Decimal = decimal

	return witnessClaim, nil
}

//LogBurnToEthBridgeClaim ...
func LogBurnToEthBridgeClaim(event *events.BurnEvent, ethereumChainID int64, bridgeBrankAddr string, decimal int64) (*ebrelayerTypes.EthBridgeClaim, error) {
	recipient := event.OmnilinkReceiver
	if 0 == len(recipient) {
		return nil, ebrelayerTypes.ErrEmptyAddress
	}

	witnessClaim := &ebrelayerTypes.EthBridgeClaim{}
	witnessClaim.EthereumChainID = ethereumChainID
	witnessClaim.BridgeBrankAddr = bridgeBrankAddr
	witnessClaim.Nonce = event.Nonce.Int64()
	witnessClaim.TokenAddr = event.Token.String()
	witnessClaim.Symbol = event.Symbol
	witnessClaim.EthereumSender = event.OwnerFrom.String()
	witnessClaim.OmnilinkReceiver = string(recipient)
	witnessClaim.Amount = event.Amount.String()
	witnessClaim.ClaimType = types.BurnClaimType
	witnessClaim.ChainName = types.BurnClaim
	witnessClaim.Decimal = decimal

	return witnessClaim, nil
}

// ParseBurnLockTxReceipt : parses data from a Burn/Lock event witnessed on omnilink into a OmnilinkMsg struct
func ParseBurnLockTxReceipt(claimType events.Event, receipt *omnilinkTypes.ReceiptData) *events.OmnilinkMsg {
	// Set up variables
	var omnilinkSender []byte
	var ethereumReceiver, tokenContractAddress common.Address
	var symbol string
	var amount *big.Int

	// Iterate over attributes
	for _, log := range receipt.Logs {
		if log.Ty == types.TyOmnilinkToEthLog || log.Ty == types.TyWithdrawOmnilinkLog {
			txslog.Debug("ParseBurnLockTxReceipt", "value", string(log.Log))
			var omnilinkToEth types.ReceiptOmnilinkToEth
			err := omnilinkTypes.Decode(log.Log, &omnilinkToEth)
			if err != nil {
				return nil
			}
			omnilinkSender = []byte(omnilinkToEth.OmnilinkSender)
			ethereumReceiver = common.HexToAddress(omnilinkToEth.EthereumReceiver)
			tokenContractAddress = common.HexToAddress(omnilinkToEth.TokenContract)
			symbol = omnilinkToEth.IssuerDotSymbol
			omnilinkToEth.Amount = types.TrimZeroAndDot(omnilinkToEth.Amount)
			amount = big.NewInt(1)
			amount, _ = amount.SetString(omnilinkToEth.Amount, 10)
			if omnilinkToEth.Decimals > 8 {
				amount = amount.Mul(amount, big.NewInt(int64(types.MultiplySpecifyTimes(1, omnilinkToEth.Decimals-8))))
			} else {
				amount = amount.Quo(amount, big.NewInt(int64(types.MultiplySpecifyTimes(1, 8-omnilinkToEth.Decimals))))
			}

			txslog.Info("ParseBurnLockTxReceipt", "omnilinkSender", omnilinkSender, "ethereumReceiver", ethereumReceiver.String(), "tokenContractAddress", tokenContractAddress.String(), "symbol", symbol, "amount", amount.String())
			// Package the event data into a OmnilinkMsg
			omnilinkMsg := events.NewOmnilinkMsg(claimType, omnilinkSender, ethereumReceiver, symbol, amount, tokenContractAddress)
			return &omnilinkMsg
		}
	}
	return nil
}

// OmnilinkMsgToProphecyClaim : parses event data from a OmnilinkMsg, packaging it as a ProphecyClaim
func OmnilinkMsgToProphecyClaim(event events.OmnilinkMsg) ProphecyClaim {
	claimType := event.ClaimType
	omnilinkSender := event.OmnilinkSender
	ethereumReceiver := event.EthereumReceiver
	tokenContractAddress := event.TokenContractAddress
	symbol := strings.ToLower(event.Symbol)
	amount := event.Amount

	prophecyClaim := ProphecyClaim{
		ClaimType:            claimType,
		OmnilinkSender:       omnilinkSender,
		EthereumReceiver:     ethereumReceiver,
		TokenContractAddress: tokenContractAddress,
		Symbol:               symbol,
		Amount:               amount,
	}

	return prophecyClaim
}
