package events

import (
	"errors"
	"math/big"

	ebrelayerTypes "code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/cross2eth/ebrelayer/types"
	omnilinkEvmCommon "code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/evm/executor/vm/common"
	"github.com/ethereum/go-ethereum/accounts/abi"
	"github.com/ethereum/go-ethereum/common"
)

type OmnilinkEvmEvent int

const (
	UnsupportedEvent OmnilinkEvmEvent = iota
	//在omnilink的evm合约中产生了lock事件
	OmnilinkEventLogLock
	//在omnilink的evm合约中产生了burn事件
	OmnilinkEventLogBurn
	//在omnilink的evm合约中产生了withdraw事件
	OmnilinkEventLogWithdraw
)

// String : returns the event type as a string
func (d OmnilinkEvmEvent) String() string {
	return [...]string{"unknown-event", "LogLock", "LogEthereumTokenBurn", "LogEthereumTokenWithdraw"}[d]
}

// OmnilinkMsg : contains data from MsgBurn and MsgLock events
type OmnilinkMsg struct {
	ClaimType            ClaimType
	OmnilinkSender       omnilinkEvmCommon.Address
	EthereumReceiver     common.Address
	TokenContractAddress omnilinkEvmCommon.Address
	Symbol               string
	Amount               *big.Int
	TxHash               []byte
	Nonce                int64
	ForwardTimes         int32
	ForwardIndex         int64
}

// 发生在omnilinkevm上的lock事件，当bty跨链转移到eth时会发生该种事件
type LockEventOnOmnilink struct {
	From   omnilinkEvmCommon.Hash160Address
	To     []byte
	Token  omnilinkEvmCommon.Hash160Address
	Symbol string
	Value  *big.Int
	Nonce  *big.Int
}

// 发生在omnilink evm上的withdraw事件，当用户发起通过代理人提币交易时，则弹射出该事件信息
type WithdrawEventOnOmnilink struct {
	BridgeToken      omnilinkEvmCommon.Hash160Address
	Symbol           string
	Amount           *big.Int
	OwnerFrom        omnilinkEvmCommon.Hash160Address
	EthereumReceiver []byte
	ProxyReceiver    omnilinkEvmCommon.Hash160Address
	Nonce            *big.Int
}

// 发生在omnilinkevm上的burn事件，当eth/erc20资产需要提币回到以太坊链上时，会发生该种事件
type BurnEventOnOmnilink struct {
	Token            omnilinkEvmCommon.Hash160Address
	Symbol           string
	Amount           *big.Int
	OwnerFrom        omnilinkEvmCommon.Hash160Address
	EthereumReceiver []byte
	Nonce            *big.Int
}

func UnpackOmnilinkLogLock(contractAbi abi.ABI, eventName string, eventData []byte) (lockEvent *LockEventOnOmnilink, err error) {
	lockEvent = &LockEventOnOmnilink{}
	// Parse the event's attributes as Ethereum network variables
	err = contractAbi.UnpackIntoInterface(lockEvent, eventName, eventData)
	if err != nil {
		eventsLog.Error("UnpackLogLock", "Failed to unpack abi due to:", err.Error())
		return nil, ebrelayerTypes.ErrUnpack
	}

	eventsLog.Info("UnpackLogLock", "value", lockEvent.Value.String(),
		"symbol", lockEvent.Symbol,
		"token addr on omnilink evm", lockEvent.Token.ToAddress().String(),
		"omnilink sender", lockEvent.From.ToAddress().String(),
		"ethereum recipient", common.BytesToAddress(lockEvent.To).String(),
		"nonce", lockEvent.Nonce.String())

	return lockEvent, nil
}

func UnpackOmnilinkLogBurn(contractAbi abi.ABI, eventName string, eventData []byte) (burnEvent *BurnEventOnOmnilink, err error) {
	burnEvent = &BurnEventOnOmnilink{}
	// Parse the event's attributes as Ethereum network variables
	err = contractAbi.UnpackIntoInterface(burnEvent, eventName, eventData)
	if err != nil {
		eventsLog.Error("UnpackLogBurn", "Failed to unpack abi due to:", err.Error())
		return nil, ebrelayerTypes.ErrUnpack
	}

	eventsLog.Info("UnpackLogBurn", "token addr on omnilink evm", burnEvent.Token.ToAddress().String(),
		"symbol", burnEvent.Symbol,
		"Amount", burnEvent.Amount.String(),
		"Owner address from omnilink", burnEvent.OwnerFrom.ToAddress().String(),
		"EthereumReceiver", common.BytesToAddress(burnEvent.EthereumReceiver).String(),
		"nonce", burnEvent.Nonce.String())
	return burnEvent, nil
}

func UnpackLogWithdraw(contractAbi abi.ABI, eventName string, eventData []byte) (withdrawEvent *WithdrawEventOnOmnilink, err error) {
	withdrawEvent = &WithdrawEventOnOmnilink{}
	err = contractAbi.UnpackIntoInterface(withdrawEvent, eventName, eventData)
	if err != nil {
		eventsLog.Error("UnpackLogWithdraw", "Failed to unpack abi due to:", err.Error())
		return nil, err
	}

	eventsLog.Info("UnpackLogWithdraw", "bridge token addr on omnilink evm", withdrawEvent.BridgeToken.ToAddress().String(),
		"symbol", withdrawEvent.Symbol,
		"Amount", withdrawEvent.Amount.String(),
		"Owner address from omnilink", withdrawEvent.OwnerFrom.ToAddress().String(),
		"EthereumReceiver", common.BytesToAddress(withdrawEvent.EthereumReceiver).String(),
		"ProxyReceiver", withdrawEvent.ProxyReceiver.ToAddress().String(),
		"nonce", withdrawEvent.Nonce.String())
	return withdrawEvent, nil
}

// ParseBurnLock4omnilink ParseBurnLockTxReceipt : parses data from a Burn/Lock/Withdraw event witnessed on omnilink into a OmnilinkMsg struct
func ParseBurnLock4omnilink(evmEventType OmnilinkEvmEvent, data []byte, bridgeBankAbi abi.ABI, omnilinkTxHash []byte) (*OmnilinkMsg, error) {
	if OmnilinkEventLogLock == evmEventType {
		lockEvent, err := UnpackOmnilinkLogLock(bridgeBankAbi, evmEventType.String(), data)
		if nil != err {
			return nil, err
		}

		omnilinkMsg := &OmnilinkMsg{
			ClaimType:            ClaimTypeLock,
			OmnilinkSender:       lockEvent.From.ToAddress(),
			EthereumReceiver:     common.BytesToAddress(lockEvent.To),
			TokenContractAddress: lockEvent.Token.ToAddress(),
			Symbol:               lockEvent.Symbol,
			Amount:               lockEvent.Value,
			TxHash:               omnilinkTxHash,
			Nonce:                lockEvent.Nonce.Int64(),
		}
		return omnilinkMsg, nil

	} else if OmnilinkEventLogBurn == evmEventType {
		burnEvent, err := UnpackOmnilinkLogBurn(bridgeBankAbi, evmEventType.String(), data)
		if nil != err {
			return nil, err
		}

		omnilinkMsg := &OmnilinkMsg{
			ClaimType:            ClaimTypeBurn,
			OmnilinkSender:       burnEvent.OwnerFrom.ToAddress(),
			EthereumReceiver:     common.BytesToAddress(burnEvent.EthereumReceiver),
			TokenContractAddress: burnEvent.Token.ToAddress(),
			Symbol:               burnEvent.Symbol,
			Amount:               burnEvent.Amount,
			TxHash:               omnilinkTxHash,
			Nonce:                burnEvent.Nonce.Int64(),
		}
		return omnilinkMsg, nil
	} else if OmnilinkEventLogWithdraw == evmEventType {
		burnEvent, err := UnpackLogWithdraw(bridgeBankAbi, evmEventType.String(), data)
		if nil != err {
			return nil, err
		}

		omnilinkMsg := &OmnilinkMsg{
			ClaimType:            ClaimTypeWithdraw,
			OmnilinkSender:       burnEvent.OwnerFrom.ToAddress(),
			EthereumReceiver:     common.BytesToAddress(burnEvent.EthereumReceiver),
			TokenContractAddress: burnEvent.BridgeToken.ToAddress(),
			Symbol:               burnEvent.Symbol,
			Amount:               burnEvent.Amount,
			TxHash:               omnilinkTxHash,
			Nonce:                burnEvent.Nonce.Int64(),
		}
		return omnilinkMsg, nil
	}

	return nil, errors.New("unknown-event")
}
