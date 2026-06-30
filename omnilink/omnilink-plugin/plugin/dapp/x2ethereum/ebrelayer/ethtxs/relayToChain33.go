package ethtxs

// ------------------------------------------------------------
//	Relay : Builds and encodes EthBridgeClaim Msgs with the
//  	specified variables, before presenting the unsigned
//      transaction to validators for optional signing.
//      Once signed, the data packets are sent as transactions
//      on the omnilink Bridge.
// ------------------------------------------------------------

import (
	"code.corp.bcollie.net/omnilink/omnilink-base/common"
	omnilinkCrypto "code.corp.bcollie.net/omnilink/omnilink-base/common/crypto"
	"code.corp.bcollie.net/omnilink/omnilink-base/rpc/jsonclient"
	rpctypes "code.corp.bcollie.net/omnilink/omnilink-base/rpc/types"
	omnilinkTypes "code.corp.bcollie.net/omnilink/omnilink-base/types"
	ebrelayerTypes "code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/x2ethereum/ebrelayer/types"
	"code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/x2ethereum/types"
)

// RelayLockToOmnilink : RelayLockToOmnilink applies validator's signature to an EthBridgeClaim message
//		containing information about an event on the Ethereum blockchain before relaying to the Bridge
func RelayLockToOmnilink(privateKey omnilinkCrypto.PrivKey, claim *ebrelayerTypes.EthBridgeClaim, rpcURL string) (string, error) {
	var res string

	params := &types.Eth2Omnilink{
		EthereumChainID:       claim.EthereumChainID,
		BridgeContractAddress: claim.BridgeBrankAddr,
		Nonce:                 claim.Nonce,
		IssuerDotSymbol:       claim.Symbol,
		TokenContractAddress:  claim.TokenAddr,
		EthereumSender:        claim.EthereumSender,
		OmnilinkReceiver:      claim.OmnilinkReceiver,
		Amount:                claim.Amount,
		ClaimType:             int64(claim.ClaimType),
		Decimals:              claim.Decimal,
	}

	pm := rpctypes.CreateTxIn{
		Execer:     X2Eth,
		ActionName: types.NameEth2OmnilinkAction,
		Payload:    omnilinkTypes.MustPBToJSON(params),
	}
	ctx := jsonclient.NewRPCCtx(rpcURL, "Omnilink.CreateTransaction", pm, &res)
	_, _ = ctx.RunResult()

	data, err := common.FromHex(res)
	if err != nil {
		return "", err
	}
	var tx omnilinkTypes.Transaction
	err = omnilinkTypes.Decode(data, &tx)
	if err != nil {
		return "", err
	}

	if tx.Fee == 0 {
		tx.Fee, err = tx.GetRealFee(1e5)
		if err != nil {
			return "", err
		}
	}
	//构建交易，验证人validator用来向omnilink合约证明自己验证了该笔从以太坊向omnilink跨链转账的交易
	tx.Sign(omnilinkTypes.SECP256K1, privateKey)

	txData := omnilinkTypes.Encode(&tx)
	dataStr := common.ToHex(txData)
	pms := rpctypes.RawParm{
		Token: "BTY",
		Data:  dataStr,
	}
	var txhash string

	ctx = jsonclient.NewRPCCtx(rpcURL, "Omnilink.SendTransaction", pms, &txhash)
	_, err = ctx.RunResult()
	return txhash, err
}

//RelayBurnToOmnilink ...
func RelayBurnToOmnilink(privateKey omnilinkCrypto.PrivKey, claim *ebrelayerTypes.EthBridgeClaim, rpcURL string) (string, error) {
	var res string

	params := &types.Eth2Omnilink{
		EthereumChainID:       claim.EthereumChainID,
		BridgeContractAddress: claim.BridgeBrankAddr,
		Nonce:                 claim.Nonce,
		IssuerDotSymbol:       claim.Symbol,
		TokenContractAddress:  claim.TokenAddr,
		EthereumSender:        claim.EthereumSender,
		OmnilinkReceiver:      claim.OmnilinkReceiver,
		Amount:                claim.Amount,
		ClaimType:             int64(claim.ClaimType),
		Decimals:              claim.Decimal,
	}

	pm := rpctypes.CreateTxIn{
		Execer:     X2Eth,
		ActionName: types.NameWithdrawEthAction,
		Payload:    omnilinkTypes.MustPBToJSON(params),
	}
	ctx := jsonclient.NewRPCCtx(rpcURL, "Omnilink.CreateTransaction", pm, &res)
	_, _ = ctx.RunResult()

	data, err := common.FromHex(res)
	if err != nil {
		return "", err
	}
	var tx omnilinkTypes.Transaction
	err = omnilinkTypes.Decode(data, &tx)
	if err != nil {
		return "", err
	}

	if tx.Fee == 0 {
		tx.Fee, err = tx.GetRealFee(1e5)
		if err != nil {
			return "", err
		}
	}
	//构建交易，验证人validator用来向omnilink合约证明自己验证了该笔从以太坊向omnilink跨链转账的交易
	tx.Sign(omnilinkTypes.SECP256K1, privateKey)

	txData := omnilinkTypes.Encode(&tx)
	dataStr := common.ToHex(txData)
	pms := rpctypes.RawParm{
		Token: "BTY",
		Data:  dataStr,
	}
	var txhash string

	ctx = jsonclient.NewRPCCtx(rpcURL, "Omnilink.SendTransaction", pms, &txhash)
	_, err = ctx.RunResult()
	return txhash, err
}
