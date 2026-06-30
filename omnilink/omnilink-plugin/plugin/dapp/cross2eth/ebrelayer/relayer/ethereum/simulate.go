package ethereum

import (
	"math/big"

	"code.corp.bcollie.net/omnilink/omnilink-base/common/address"
	"code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/cross2eth/ebrelayer/relayer/ethereum/ethtxs"
	"code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/cross2eth/ebrelayer/relayer/events"
	ebTypes "code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/cross2eth/ebrelayer/types"
	"code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/cross2eth/ebrelayer/utils"
	ethcommon "github.com/ethereum/go-ethereum/common"
)

var clientChainID = int64(0)
var bridgeBankAddr = "0x8afdadfc88a1087c9a1d6c0f5dd04634b87f303a"

func (ethRelayer *Relayer4Ethereum) SimLockFromEth(lock *ebTypes.LockEthErc20) error {
	amount := big.NewInt(1)
	amount, _ = amount.SetString(utils.TrimZeroAndDot(lock.Amount), 10)

	addr, err := address.NewBtcAddress(lock.OmnilinkReceiver)
	if nil != err {
		return err
	}

	lockEvent := &events.LockEvent{
		From:   ethcommon.HexToAddress(lock.OwnerKey),
		To:     addr.Hash160[:],
		Token:  ethcommon.HexToAddress(lock.TokenAddr),
		Symbol: "ETH",
		Value:  amount,
		Nonce:  big.NewInt(1),
	}
	prophecyClaim, err := ethtxs.LogLockToEthBridgeClaim(lockEvent, clientChainID, bridgeBankAddr, "", 18)
	if err != nil {
		return err
	}

	ethRelayer.ethBridgeClaimChan <- prophecyClaim

	return nil
}

func (ethRelayer *Relayer4Ethereum) SimBurnFromEth(burn *ebTypes.Burn) error {
	relayerLog.Info("SimBurnFromEth", "burn", burn)
	amount := big.NewInt(1)
	amount, _ = amount.SetString(utils.TrimZeroAndDot(burn.Amount), 10)

	addr, err := address.NewBtcAddress(burn.OmnilinkReceiver)
	if nil != err {
		return err
	}

	burnEvent := &events.BurnEvent{
		Token:            ethcommon.HexToAddress(burn.TokenAddr), //ethcommon.Address
		Symbol:           "BTY",
		Amount:           amount,
		OwnerFrom:        ethcommon.HexToAddress(burn.OwnerKey), //将owner 作为地址来用，只是为了测试使用
		OmnilinkReceiver: addr.Hash160[:],                       //[]byte
		Nonce:            big.NewInt(1),                         //*big.Int
	}
	// Parse the LogLock event's payload into a struct
	prophecyClaim, err := ethtxs.LogBurnToEthBridgeClaim(burnEvent, clientChainID, bridgeBankAddr, "", 8)
	if err != nil {
		return err
	}
	relayerLog.Info("SimBurnFromEth", "OmnilinkReceiver", prophecyClaim.OmnilinkReceiver)

	ethRelayer.ethBridgeClaimChan <- prophecyClaim

	return nil
}
