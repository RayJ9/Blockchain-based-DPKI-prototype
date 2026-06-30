package omnilink

import (
	"strings"

	"code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/cross2eth/ebrelayer/relayer/events"

	omnilinkEvm "code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/cross2eth/contracts/contracts4omnilink/generated"
	"github.com/ethereum/go-ethereum/accounts/abi"
)

func (relayer *Relayer4Omnilink) prePareSubscribeEvent() {
	var eventName string
	contractABI, err := abi.JSON(strings.NewReader(omnilinkEvm.BridgeBankABI))
	if err != nil {
		panic(err)
	}

	eventName = events.OmnilinkEventLogLock.String()
	relayer.bridgeBankEventLockSig = contractABI.Events[eventName].ID.Hex()
	eventName = events.OmnilinkEventLogBurn.String()
	relayer.bridgeBankEventBurnSig = contractABI.Events[eventName].ID.Hex()
	eventName = events.OmnilinkEventLogWithdraw.String()
	relayer.bridgeBankEventWithdrawSig = contractABI.Events[eventName].ID.Hex()

	relayer.bridgeBankAbi = contractABI

	relayerLog.Info("prePareSubscribeEvent", "bridgeBankEventLockSig", relayer.bridgeBankEventLockSig,
		"bridgeBankEventBurnSig", relayer.bridgeBankEventBurnSig, "bridgeBankEventWithdrawSig", relayer.bridgeBankEventWithdrawSig)
}
