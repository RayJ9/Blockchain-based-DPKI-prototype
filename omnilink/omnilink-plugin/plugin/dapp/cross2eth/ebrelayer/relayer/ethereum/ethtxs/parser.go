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
	"code.corp.bcollie.net/omnilink/omnilink-base/common/address"
	"code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/cross2eth/ebrelayer/relayer/events"
	ebrelayerTypes "code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/cross2eth/ebrelayer/types"
)

// LogLockToEthBridgeClaim : parses and packages a LockEvent struct with a validator address in an EthBridgeClaim msg
func LogLockToEthBridgeClaim(event *events.LockEvent, ethereumChainID int64, bridgeBrankAddr, ethTxHash string, decimal int64) (*ebrelayerTypes.EthBridgeClaim, error) {
	recipient := event.To
	if 0 == len(recipient) {
		return nil, ebrelayerTypes.ErrEmptyAddress
	}

	omnilinkReceiver := new(address.Address)
	omnilinkReceiver.SetBytes(recipient)

	witnessClaim := &ebrelayerTypes.EthBridgeClaim{}
	witnessClaim.EthereumChainID = ethereumChainID
	witnessClaim.BridgeBrankAddr = bridgeBrankAddr
	witnessClaim.Nonce = event.Nonce.Int64()
	witnessClaim.TokenAddr = event.Token.String()
	witnessClaim.Symbol = event.Symbol
	witnessClaim.EthereumSender = event.From.String()
	witnessClaim.OmnilinkReceiver = omnilinkReceiver.String()
	witnessClaim.Amount = event.Value.String()

	witnessClaim.ClaimType = int32(events.ClaimTypeLock)
	witnessClaim.ChainName = ""
	witnessClaim.Decimal = decimal
	witnessClaim.EthTxHash = ethTxHash

	return witnessClaim, nil
}

//LogBurnToEthBridgeClaim ...
func LogBurnToEthBridgeClaim(event *events.BurnEvent, ethereumChainID int64, bridgeBrankAddr, ethTxHash string, decimal int64) (*ebrelayerTypes.EthBridgeClaim, error) {
	recipient := event.OmnilinkReceiver
	if 0 == len(recipient) {
		return nil, ebrelayerTypes.ErrEmptyAddress
	}

	omnilinkReceiver := new(address.Address)
	omnilinkReceiver.SetBytes(recipient)

	witnessClaim := &ebrelayerTypes.EthBridgeClaim{}
	witnessClaim.EthereumChainID = ethereumChainID
	witnessClaim.BridgeBrankAddr = bridgeBrankAddr
	witnessClaim.Nonce = event.Nonce.Int64()
	witnessClaim.TokenAddr = event.Token.String()
	witnessClaim.Symbol = event.Symbol
	witnessClaim.EthereumSender = event.OwnerFrom.String()
	witnessClaim.OmnilinkReceiver = omnilinkReceiver.String()
	witnessClaim.Amount = event.Amount.String()
	witnessClaim.ClaimType = int32(events.ClaimTypeBurn)
	witnessClaim.ChainName = ""
	witnessClaim.Decimal = decimal
	witnessClaim.EthTxHash = ethTxHash

	return witnessClaim, nil
}

// OmnilinkMsgToProphecyClaim : parses event data from a OmnilinkMsg, packaging it as a ProphecyClaim
func OmnilinkMsgToProphecyClaim(msg events.OmnilinkMsg) ProphecyClaim {
	claimType := msg.ClaimType
	omnilinkSender := msg.OmnilinkSender
	ethereumReceiver := msg.EthereumReceiver
	symbol := msg.Symbol
	amount := msg.Amount

	prophecyClaim := ProphecyClaim{
		ClaimType:        claimType,
		OmnilinkSender:   omnilinkSender.Bytes(),
		EthereumReceiver: ethereumReceiver,
		//TokenContractAddress: tokenContractAddress,
		Symbol:         symbol,
		Amount:         amount,
		OmnilinkTxHash: msg.TxHash,
	}

	return prophecyClaim
}
