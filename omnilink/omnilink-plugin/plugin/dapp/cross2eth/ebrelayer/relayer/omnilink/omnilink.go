package omnilink

import (
	"context"
	"crypto/ecdsa"
	"errors"
	"fmt"
	"math/big"
	"os"
	"strings"
	"sync"
	"sync/atomic"
	"time"

	omnilinkEvmCommon "code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/evm/executor/vm/common"

	evmtypes "code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/evm/types"

	"code.corp.bcollie.net/omnilink/omnilink-base/common"
	omnilinkCrypto "code.corp.bcollie.net/omnilink/omnilink-base/common/crypto"
	dbm "code.corp.bcollie.net/omnilink/omnilink-base/common/db"
	log "code.corp.bcollie.net/omnilink/omnilink-base/common/log/log15"
	"code.corp.bcollie.net/omnilink/omnilink-base/rpc/jsonclient"
	rpctypes "code.corp.bcollie.net/omnilink/omnilink-base/rpc/types"
	omnilinkTypes "code.corp.bcollie.net/omnilink/omnilink-base/types"
	"code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/cross2eth/ebrelayer/relayer/events"
	syncTx "code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/cross2eth/ebrelayer/relayer/omnilink/transceiver/sync"
	ebTypes "code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/cross2eth/ebrelayer/types"
	"code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/cross2eth/ebrelayer/utils"
	"github.com/ethereum/go-ethereum/accounts/abi"
	"github.com/ethereum/go-ethereum/crypto"
)

var relayerLog = log.New("module", "omnilink_relayer")

//Relayer4Omnilink ...
type Relayer4Omnilink struct {
	syncEvmTxLogs       *syncTx.EVMTxLogs
	rpcLaddr            string //用户向指定的blockchain节点进行rpc调用
	omnilinkRpcUrls     []string
	chainName           string //用来区别主链中继还是平行链，主链为空，平行链则是user.p.xxx.
	chainID             int32
	fetchHeightPeriodMs int64
	db                  dbm.DB
	lastHeight4Tx       int64 //等待被处理的具有相应的交易回执的高度
	matDegree           int32 //成熟度         heightSync2App    matDegress   height

	privateKey4Omnilink        omnilinkCrypto.PrivKey
	privateKey4Omnilink_ecdsa  *ecdsa.PrivateKey
	ctx                        context.Context
	rwLock                     sync.RWMutex
	unlockChan                 chan int
	bridgeBankEventLockSig     string
	bridgeBankEventBurnSig     string
	bridgeBankEventWithdrawSig string
	bridgeBankAbi              abi.ABI
	totalTx4RelayEth2chai33    int64
	//新增//
	ethBridgeClaimChan        <-chan *ebTypes.EthBridgeClaim
	txRelayAckRecvChan        <-chan *ebTypes.TxRelayAck
	txRelayAckSendChan        map[string]chan<- *ebTypes.TxRelayAck
	omnilinkMsgChan           map[string]chan<- *events.OmnilinkMsg
	bridgeRegistryAddr        string
	oracleAddr                string
	bridgeBankAddr            string
	mulSignAddr               string
	deployResult              *X2EthDeployResult
	symbol2Addr               map[string]string
	bridgeSymbol2EthChainName map[string]string //在omnilink上发行的跨链token的名称到以太坊链的名称映射
	processWithDraw           bool
	delayedSend               bool
	delayedSendTime           int64
}

type OmnilinkStartPara struct {
	ChainName          string
	Ctx                context.Context
	SyncTxConfig       *ebTypes.SyncTxConfig
	BridgeRegistryAddr string
	DBHandle           dbm.DB
	EthBridgeClaimChan <-chan *ebTypes.EthBridgeClaim
	TxRelayAckRecvChan <-chan *ebTypes.TxRelayAck
	TxRelayAckSendChan map[string]chan<- *ebTypes.TxRelayAck
	OmnilinkMsgChan    map[string]chan<- *events.OmnilinkMsg
	ChainID            int32
	ProcessWithDraw    bool
	DelayedSend        bool
	DelayedSendTime    int64
}

// StartOmnilinkRelayer : initializes a relayer which witnesses events on the omnilink network and relays them to Ethereum
func StartOmnilinkRelayer(startPara *OmnilinkStartPara) *Relayer4Omnilink {
	omnilinkRelayer := &Relayer4Omnilink{
		rpcLaddr:                startPara.SyncTxConfig.OmnilinkHost,
		omnilinkRpcUrls:         startPara.SyncTxConfig.OmnilinkRpcUrls,
		chainName:               startPara.ChainName,
		chainID:                 startPara.ChainID,
		fetchHeightPeriodMs:     startPara.SyncTxConfig.FetchHeightPeriodMs,
		unlockChan:              make(chan int),
		db:                      startPara.DBHandle,
		ctx:                     startPara.Ctx,
		bridgeRegistryAddr:      startPara.BridgeRegistryAddr,
		ethBridgeClaimChan:      startPara.EthBridgeClaimChan,
		txRelayAckRecvChan:      startPara.TxRelayAckRecvChan,
		txRelayAckSendChan:      startPara.TxRelayAckSendChan,
		omnilinkMsgChan:         startPara.OmnilinkMsgChan,
		totalTx4RelayEth2chai33: 0,
		symbol2Addr:             make(map[string]string),
		processWithDraw:         startPara.ProcessWithDraw,
		delayedSend:             startPara.DelayedSend,
		delayedSendTime:         startPara.DelayedSendTime,
	}

	syncCfg := &ebTypes.SyncTxReceiptConfig{
		OmnilinkHost:      startPara.SyncTxConfig.OmnilinkHost,
		PushHost:          startPara.SyncTxConfig.PushHost,
		PushName:          startPara.SyncTxConfig.PushName,
		PushBind:          startPara.SyncTxConfig.PushBind,
		StartSyncHeight:   startPara.SyncTxConfig.StartSyncHeight,
		StartSyncSequence: startPara.SyncTxConfig.StartSyncSequence,
		StartSyncHash:     startPara.SyncTxConfig.StartSyncHash,
		KeepAliveDuration: startPara.SyncTxConfig.KeepAliveDuration,
	}

	registrAddrInDB, err := omnilinkRelayer.getBridgeRegistryAddr()
	//如果输入的registry地址非空，且和数据库保存地址不一致，则直接使用输入注册地址
	if omnilinkRelayer.bridgeRegistryAddr != "" && nil == err && registrAddrInDB != omnilinkRelayer.bridgeRegistryAddr {
		relayerLog.Error("StartOmnilinkRelayer", "BridgeRegistry is setted already with value", registrAddrInDB,
			"but now setting to", startPara.BridgeRegistryAddr)
		_ = omnilinkRelayer.setBridgeRegistryAddr(startPara.BridgeRegistryAddr)
	} else if startPara.BridgeRegistryAddr == "" && registrAddrInDB != "" {
		//输入地址为空，且数据库中保存地址不为空，则直接使用数据库中的地址
		omnilinkRelayer.bridgeRegistryAddr = registrAddrInDB
	}
	omnilinkRelayer.totalTx4RelayEth2chai33 = omnilinkRelayer.getTotalTxAmount()
	if 0 == omnilinkRelayer.totalTx4RelayEth2chai33 {
		statics := &ebTypes.Ethereum2OmnilinkStatics{}
		data := omnilinkTypes.Encode(statics)
		err := omnilinkRelayer.setLastestRelay2OmnilinkTxStatics(0, int32(events.ClaimTypeLock), data)
		if err != nil {
			relayerLog.Error("StartOmnilinkRelayer", "setLastestRelay2OmnilinkTxStatics ClaimTypeLock error", err.Error())
		}
		err = omnilinkRelayer.setLastestRelay2OmnilinkTxStatics(0, int32(events.ClaimTypeBurn), data)
		if err != nil {
			relayerLog.Error("StartOmnilinkRelayer", "setLastestRelay2OmnilinkTxStatics ClaimTypeBurn error", err.Error())
		}
	}

	go omnilinkRelayer.syncProc(syncCfg)
	return omnilinkRelayer
}

func (omnilinkRelayer *Relayer4Omnilink) syncProc(syncCfg *ebTypes.SyncTxReceiptConfig) {
	_, _ = fmt.Fprintln(os.Stdout, "Pls unlock or import private key for Omnilink relayer")
	<-omnilinkRelayer.unlockChan
	_, _ = fmt.Fprintln(os.Stdout, "Omnilink relayer starts to run...")
	if err := omnilinkRelayer.RestoreTokenAddress(); nil != err {
		relayerLog.Info("Failed to RestoreTokenAddress")
		return
	}
	setChainID(omnilinkRelayer.chainID)
	//如果该中继器的bridgeRegistryAddr为空，就说明合约未部署，需要等待部署成功之后再继续
	if "" == omnilinkRelayer.bridgeRegistryAddr {
		omnilinktxLog.Debug("bridgeRegistryAddr empty")
		<-omnilinkRelayer.unlockChan
	}
	//如果oracleAddr为空，则通过bridgeRegistry合约进行查询
	if "" != omnilinkRelayer.bridgeRegistryAddr && "" == omnilinkRelayer.oracleAddr {
		oracleAddr, bridgeBankAddr := recoverContractAddrFromRegistry(omnilinkRelayer.bridgeRegistryAddr, omnilinkRelayer.rpcLaddr)
		if "" == oracleAddr || "" == bridgeBankAddr {
			panic("Failed to recoverContractAddrFromRegistry")
		}
		omnilinkRelayer.oracleAddr = oracleAddr
		omnilinkRelayer.bridgeBankAddr = bridgeBankAddr
		omnilinktxLog.Debug("recoverContractAddrFromRegistry", "bridgeRegistryAddr", omnilinkRelayer.bridgeRegistryAddr,
			"oracleAddr", omnilinkRelayer.oracleAddr, "bridgeBankAddr", omnilinkRelayer.bridgeBankAddr)
	}

	syncCfg.Contracts = append(syncCfg.Contracts, omnilinkRelayer.bridgeBankAddr)
	omnilinkRelayer.syncEvmTxLogs = syncTx.StartSyncEvmTxLogs(syncCfg, omnilinkRelayer.db)
	omnilinkRelayer.lastHeight4Tx = omnilinkRelayer.loadLastSyncHeight()
	omnilinkRelayer.mulSignAddr = omnilinkRelayer.getMultiSignAddress()
	omnilinkRelayer.bridgeSymbol2EthChainName = omnilinkRelayer.restoreSymbol2chainName()
	omnilinkRelayer.prePareSubscribeEvent()
	timer := time.NewTicker(time.Duration(omnilinkRelayer.fetchHeightPeriodMs) * time.Millisecond)
	for {
		select {
		case <-timer.C:
			height := omnilinkRelayer.getCurrentHeight()
			relayerLog.Debug("syncProc", "getCurrentHeight", height)
			omnilinkRelayer.onNewHeightProc(height)

		case <-omnilinkRelayer.ctx.Done():
			timer.Stop()
			return

		case ethBridgeClaim := <-omnilinkRelayer.ethBridgeClaimChan:
			omnilinkRelayer.relayLockBurnToOmnilink(ethBridgeClaim)

		case txRelayAck := <-omnilinkRelayer.txRelayAckRecvChan:
			omnilinkRelayer.procTxRelayAck(txRelayAck)
		}
	}
}

func (omnilinkRelayer *Relayer4Omnilink) getCurrentHeight() int64 {
	var res rpctypes.Header
	ctx := jsonclient.NewRPCCtx(omnilinkRelayer.rpcLaddr, "Omnilink.GetLastHeader", nil, &res)
	_, err := ctx.RunResult()
	if nil != err {
		relayerLog.Error("getCurrentHeight", "Failede due to:", err.Error())
	}
	return res.Height
}

func (omnilinkRelayer *Relayer4Omnilink) onNewHeightProc(currentHeight int64) {
	//检查已经提交的交易结果
	omnilinkRelayer.updateTxStatus()
	omnilinkRelayer.checkTxRelay2Ethereum()

	//未达到足够的成熟度，不进行处理
	//  +++++++++||++++++++++++||++++++++++||
	//           ^             ^           ^
	// lastHeight4Tx    matDegress   currentHeight
	for omnilinkRelayer.lastHeight4Tx+int64(omnilinkRelayer.matDegree)+1 <= currentHeight {
		relayerLog.Info("onNewHeightProc", "currHeight", currentHeight, "lastHeight4Tx", omnilinkRelayer.lastHeight4Tx)

		lastHeight4Tx := omnilinkRelayer.lastHeight4Tx
		txLogs, err := omnilinkRelayer.syncEvmTxLogs.GetNextValidEvmTxLogs(lastHeight4Tx)
		if nil == txLogs || nil != err {
			if err != nil {
				relayerLog.Error("onNewHeightProc", "Failed to GetNextValidTxReceipts due to:", err.Error())
			}
			break
		}
		relayerLog.Debug("onNewHeightProc", "currHeight", currentHeight, "valid tx receipt with height:", txLogs.Height)

		txAndLogs := txLogs.TxAndLogs
		for _, txAndLog := range txAndLogs {
			tx := txAndLog.Tx

			//确认订阅的evm交易类型和合约地址
			if !strings.Contains(string(tx.Execer), "evm") {
				relayerLog.Error("onNewHeightProc received logs not from evm tx", "tx.Execer", string(tx.Execer))
				continue
			}

			var evmAction evmtypes.EVMContractAction
			err := omnilinkTypes.Decode(tx.Payload, &evmAction)
			if nil != err {
				relayerLog.Error("onNewHeightProc", "Failed to decode action for tx with hash", common.ToHex(tx.Hash()))
				continue
			}

			//确认监听的合约地址
			if evmAction.ContractAddr != omnilinkRelayer.bridgeBankAddr {
				relayerLog.Error("onNewHeightProc received logs not from bridgeBank", "evmAction.ContractAddr", evmAction.ContractAddr)
				continue
			}

			for _, evmlog := range txAndLog.LogsPerTx.Logs {
				var evmEventType events.OmnilinkEvmEvent
				if omnilinkRelayer.bridgeBankEventBurnSig == common.ToHex(evmlog.Topic[0]) {
					evmEventType = events.OmnilinkEventLogBurn
				} else if omnilinkRelayer.bridgeBankEventLockSig == common.ToHex(evmlog.Topic[0]) {
					evmEventType = events.OmnilinkEventLogLock
				} else if omnilinkRelayer.bridgeBankEventWithdrawSig == common.ToHex(evmlog.Topic[0]) {
					evmEventType = events.OmnilinkEventLogWithdraw
				} else {
					continue
				}

				if evmEventType == events.OmnilinkEventLogWithdraw && !omnilinkRelayer.processWithDraw {
					//代理提币消息只由代理提币节点处理
					continue
				}
				if evmEventType != events.OmnilinkEventLogWithdraw && omnilinkRelayer.processWithDraw {
					//lock和burn消息消息只由普通中继节点处理
					continue
				}

				if err := omnilinkRelayer.handleBurnLockWithdrawEvent(evmEventType, evmlog.Data, tx.Hash()); nil != err {
					relayerLog.Error("onNewHeightProc", "Failed to handleBurnLockWithdrawEvent due to:%s", err.Error())
				}

			}
		}
		omnilinkRelayer.lastHeight4Tx = txLogs.Height
		omnilinkRelayer.setLastSyncHeight(omnilinkRelayer.lastHeight4Tx)
	}
}

// handleBurnLockMsg : parse event data as a OmnilinkMsg, package it into a ProphecyClaim, then relay tx to the Ethereum Network
func (omnilinkRelayer *Relayer4Omnilink) handleBurnLockWithdrawEvent(evmEventType events.OmnilinkEvmEvent, data []byte, omnilinkTxHash []byte) error {
	txHashStr := common.ToHex(omnilinkTxHash)
	relayerLog.Info("handleBurnLockWithdrawEvent", "Received tx with hash", txHashStr)

	// 删除已发送校验, 如果ethereum端发生交易后没有打包, 可重新再发生
	//if omnilinkRelayer.checkTxProcessed(txHashStr) {
	//	relayerLog.Info("handleBurnLockWithdrawEvent", "Tx has been already Processed with hash:", txHashStr)
	//	return nil
	//}

	// Parse the witnessed event's data into a new OmnilinkMsg
	omnilinkMsg, err := events.ParseBurnLock4omnilink(evmEventType, data, omnilinkRelayer.bridgeBankAbi, omnilinkTxHash)
	if nil != err {
		return err
	}
	fdIndex := omnilinkRelayer.getFdTx2EthTotalAmount() + 1
	omnilinkMsg.ForwardTimes = 1
	omnilinkMsg.ForwardIndex = fdIndex

	relayerLog.Info("handleBurnLockWithdrawEvent", "Going to send omnilinkMsg.ClaimType", omnilinkMsg.ClaimType.String())

	var chainName string
	//specical process: withdraw YCC　only to bsc
	if events.OmnilinkEventLogWithdraw == evmEventType && "YCC" == omnilinkMsg.Symbol {
		chainName = ebTypes.BinanceChainName
	} else {
		ok := false
		chainName, ok = omnilinkRelayer.bridgeSymbol2EthChainName[omnilinkMsg.Symbol]
		if !ok {
			relayerLog.Error("handleBurnLockWithdrawEvent", "No bridgeSymbol2EthChainName", omnilinkMsg.Symbol)
			return errors.New("ErrNoEthChainName4BridgeSymbol")
		}
	}

	channel, ok := omnilinkRelayer.omnilinkMsgChan[chainName]
	if !ok {
		relayerLog.Error("handleBurnLockWithdrawEvent", "No bridgeSymbol2EthChainName", chainName)
		return errors.New("ErrNoOmnilinkMsgChan4EthChainName")
	}

	_ = omnilinkRelayer.updateFdTx2EthTotalAmount(fdIndex)
	txRelayConfirm4Omnilink := &ebTypes.TxRelayConfirm4Omnilink{
		EventType:   int32(evmEventType),
		Data:        data,
		FdTimes:     1,
		FdIndex:     fdIndex,
		ToChainName: chainName,
		TxHash:      omnilinkTxHash,
		Resend:      false,
	}

	if omnilinkRelayer.delayedSend {
		go omnilinkRelayer.delayedSendTxs(chainName, omnilinkMsg, omnilinkTxHash, txRelayConfirm4Omnilink)
	} else {
		channel <- omnilinkMsg
		//relayomnilinkToEthereumCheckPonit 1:send omnilinkMsg to ethereum relay service
		relayerLog.Info("handleBurnLockWithdrawEvent::relayomnilinkToEthereumCheckPonit_1", "omnilinkTxHash", txHashStr, "ForwardIndex", omnilinkMsg.ForwardIndex, "FdTimes", 1)
		err = omnilinkRelayer.setOmnilinkTxIsRelayedUnconfirm(txHashStr, fdIndex, txRelayConfirm4Omnilink)
	}

	return err
}

func (omnilinkRelayer *Relayer4Omnilink) delayedSendTxs(chainName string, omnilinkMsg *events.OmnilinkMsg, omnilinkTxHash []byte, txRelayConfirm4Omnilink *ebTypes.TxRelayConfirm4Omnilink) {
	delayedSendTime := time.Duration(omnilinkRelayer.delayedSendTime) * time.Millisecond
	relayerLog.Debug("delayedSendTxs", "setEthTxWaitingForSend omnilinkTxHash", common.ToHex(omnilinkTxHash))
	time.Sleep(delayedSendTime)
	channel, ok := omnilinkRelayer.omnilinkMsgChan[chainName]
	if !ok {
		relayerLog.Error("handleBurnLockWithdrawEvent", "No bridgeSymbol2EthChainName", chainName)
		return
	}

	channel <- omnilinkMsg

	//relayomnilinkToEthereumCheckPonit 1:send omnilinkMsg to ethereum relay service
	relayerLog.Info("handleBurnLockWithdrawEvent::relayomnilinkToEthereumCheckPonit_1", "omnilinkTxHash", common.ToHex(omnilinkTxHash), "ForwardIndex", omnilinkMsg.ForwardIndex, "FdTimes", 1)
	_ = omnilinkRelayer.setOmnilinkTxIsRelayedUnconfirm(common.ToHex(omnilinkTxHash), txRelayConfirm4Omnilink.FdIndex, txRelayConfirm4Omnilink)
}

func (omnilinkRelayer *Relayer4Omnilink) ResendOmnilinkEvent(height int64) (err error) {
	txLogs, err := omnilinkRelayer.syncEvmTxLogs.GetNextValidEvmTxLogs(height)
	if nil == txLogs || nil != err {
		if err != nil {
			relayerLog.Error("ResendOmnilinkEvent", "Failed to GetNextValidTxReceipts due to:", err.Error())
			return err
		}
		return nil
	}
	relayerLog.Debug("ResendOmnilinkEvent", "lastHeight4Tx", omnilinkRelayer.lastHeight4Tx, "valid tx receipt with height:", txLogs.Height)

	txAndLogs := txLogs.TxAndLogs
	for _, txAndLog := range txAndLogs {
		tx := txAndLog.Tx

		//确认订阅的evm交易类型和合约地址
		if !strings.Contains(string(tx.Execer), "evm") {
			relayerLog.Error("ResendOmnilinkEvent received logs not from evm tx", "tx.Execer", string(tx.Execer))
			continue
		}

		var evmAction evmtypes.EVMContractAction
		err := omnilinkTypes.Decode(tx.Payload, &evmAction)
		if nil != err {
			relayerLog.Error("ResendOmnilinkEvent", "Failed to decode action for tx with hash", common.ToHex(tx.Hash()))
			continue
		}

		//确认监听的合约地址
		if evmAction.ContractAddr != omnilinkRelayer.bridgeBankAddr {
			relayerLog.Error("ResendOmnilinkEvent received logs not from bridgeBank", "evmAction.ContractAddr", evmAction.ContractAddr)
			continue
		}

		for _, evmlog := range txAndLog.LogsPerTx.Logs {
			var evmEventType events.OmnilinkEvmEvent
			if omnilinkRelayer.bridgeBankEventBurnSig == common.ToHex(evmlog.Topic[0]) {
				evmEventType = events.OmnilinkEventLogBurn
			} else if omnilinkRelayer.bridgeBankEventLockSig == common.ToHex(evmlog.Topic[0]) {
				evmEventType = events.OmnilinkEventLogLock
			} else if omnilinkRelayer.bridgeBankEventWithdrawSig == common.ToHex(evmlog.Topic[0]) {
				evmEventType = events.OmnilinkEventLogWithdraw
			} else {
				continue
			}

			if evmEventType == events.OmnilinkEventLogWithdraw && !omnilinkRelayer.processWithDraw {
				//代理提币消息只由代理提币节点处理
				continue
			}
			if evmEventType != events.OmnilinkEventLogWithdraw && omnilinkRelayer.processWithDraw {
				//lock和burn消息消息只由普通中继节点处理
				continue
			}

			if err := omnilinkRelayer.handleBurnLockWithdrawEvent(evmEventType, evmlog.Data, tx.Hash()); nil != err {
				return err
			}
		}
	}

	return nil
}

func (omnilinkRelayer *Relayer4Omnilink) checkIsResendEthClaim(claim *ebTypes.EthBridgeClaim) bool {
	if claim.ForwardTimes <= 1 {
		return false
	}
	ethTxHash := claim.EthTxHash
	relayerLog.Info("checkIsResendEthClaim", "Received the same EthBridgeClaim more than once with times", claim.ForwardTimes, "tx hash string", ethTxHash)
	relayTxDetail, _ := omnilinkRelayer.getEthTxRelayAlreadyInfo(ethTxHash)
	if nil == relayTxDetail {
		relayerLog.Info("checkIsResendEthClaim::haven't relay yet")
		return false
	}

	//if relay already, just ack it
	omnilinkRelayer.txRelayAckSendChan[claim.ChainName] <- &ebTypes.TxRelayAck{
		TxHash:  ethTxHash,
		FdIndex: claim.ForwardIndex,
	}
	relayerLog.Info("checkIsResendEthClaim", "have relay already with tx hash:", relayTxDetail.Txhash)
	return true
}

func (omnilinkRelayer *Relayer4Omnilink) relayLockBurnToOmnilink(claim *ebTypes.EthBridgeClaim) {
	relayerLog.Debug("relayLockBurnToOmnilink", "new EthBridgeClaim received", claim)
	if omnilinkRelayer.checkIsResendEthClaim(claim) {
		return
	}

	nonceBytes := big.NewInt(claim.Nonce).Bytes()
	bigAmount := big.NewInt(0)
	bigAmount.SetString(claim.Amount, 10)
	amountBytes := bigAmount.Bytes()
	claimID := crypto.Keccak256Hash(nonceBytes, []byte(claim.EthereumSender), []byte(claim.OmnilinkReceiver), []byte(claim.Symbol), amountBytes)

	// Sign the hash using the active validator's private key
	signature, err := utils.SignClaim4Evm(claimID, omnilinkRelayer.privateKey4Omnilink_ecdsa)
	if nil != err {
		panic("SignClaim4Evm due to" + err.Error())
	}

	var tokenAddr string
	operationType := events.ClaimType(claim.ClaimType).String()
	if int32(events.ClaimTypeBurn) == claim.ClaimType {
		//burn 分支
		if ebTypes.SYMBOL_BTY == claim.Symbol {
			tokenAddr = ebTypes.BTYAddrOmnilink
		} else {
			tokenAddr = getLockedTokenAddress(omnilinkRelayer.bridgeBankAddr, claim.Symbol, omnilinkRelayer.rpcLaddr)
			if "" == tokenAddr {
				relayerLog.Error("relayLockBurnToOmnilink", "No locked token address created for symbol", claim.Symbol)
				return
			}
		}
	} else {
		//lock 分支
		if _, ok := omnilinkRelayer.bridgeSymbol2EthChainName[claim.Symbol]; !ok {
			omnilinkRelayer.bridgeSymbol2EthChainName[claim.Symbol] = claim.ChainName
			omnilinkRelayer.storeSymbol2chainName(omnilinkRelayer.bridgeSymbol2EthChainName)
		}
		//如果是代理打币节点，则只收集symbol和chain name相关信息
		if omnilinkRelayer.processWithDraw {
			return
		}

		var exist bool
		tokenAddr, exist = omnilinkRelayer.symbol2Addr[claim.Symbol]
		if !exist {
			tokenAddr = getBridgeToken2address(omnilinkRelayer.bridgeBankAddr, claim.Symbol, omnilinkRelayer.rpcLaddr)
			if "" == tokenAddr {
				relayerLog.Error("relayLockBurnToOmnilink", "No bridge token address created for symbol", claim.Symbol)
				return
			}
			relayerLog.Info("relayLockBurnToOmnilink", "Succeed to get bridge token address for symbol", claim.Symbol,
				"address", tokenAddr)

			token2set := &ebTypes.TokenAddress{
				Address:   tokenAddr,
				Symbol:    claim.Symbol,
				ChainName: ebTypes.OmnilinkBlockChainName,
			}
			if err := omnilinkRelayer.SetTokenAddress(token2set); nil != err {
				relayerLog.Info("relayLockBurnToOmnilink", "Failed to SetTokenAddress due to", err.Error())
			}
		}
	}

	//因为发行的合约的精度为8，所以需要进行相应的缩放
	if 8 != claim.Decimal {
		if claim.Decimal > 8 {
			dist := claim.Decimal - 8
			value, exist := utils.Decimal2value[int(dist)]
			if !exist {
				panic(fmt.Sprintf("does support for decimal, %d", claim.Decimal))
			}
			bigAmount.Div(bigAmount, big.NewInt(value))
			claim.Amount = bigAmount.String()
		} else {
			dist := 8 - claim.Decimal
			value, exist := utils.Decimal2value[int(dist)]
			if !exist {
				panic(fmt.Sprintf("does support for decimal, %d", claim.Decimal))
			}
			bigAmount.Mul(bigAmount, big.NewInt(value))
			claim.Amount = bigAmount.String()
		}
	}

	parameter := fmt.Sprintf("newOracleClaim(%d, %s, %s, %s, %s, %s, %s, %s)",
		claim.ClaimType,
		claim.EthereumSender,
		claim.OmnilinkReceiver,
		tokenAddr,
		claim.Symbol,
		claim.Amount,
		claimID.String(),
		common.ToHex(signature))
	relayerLog.Info("relayLockBurnToOmnilink", "parameter", parameter)

	txhash, err := relayEvmTx2Omnilink(omnilinkRelayer.privateKey4Omnilink, claim, parameter, omnilinkRelayer.oracleAddr, omnilinkRelayer.chainName, omnilinkRelayer.omnilinkRpcUrls)
	if err != nil {
		relayerLog.Error("relayLockBurnToOmnilink", "Failed to RelayEvmTx2Omnilink due to:", err.Error(), "EthereumTxhash", claim.EthTxHash)
		return
	}

	omnilinkRelayer.txRelayAckSendChan[claim.ChainName] <- &ebTypes.TxRelayAck{
		TxHash:  claim.EthTxHash,
		FdIndex: claim.ForwardIndex,
	}
	//relayEthereum2omnilinkCheckPonit 2:send ack
	relayerLog.Info("relayLockBurnToOmnilink::relayEthereum2omnilinkCheckPonit_2::sendAck", "ethTxhash", claim.EthTxHash, "ForwardIndex", claim.ForwardIndex, "FdTimes", claim.ForwardTimes)

	relayTxDetail := &ebTypes.RelayTxDetail{
		ClaimType:      claim.ClaimType,
		TxIndexRelayed: claim.ForwardIndex,
		Txhash:         txhash,
	}

	//set flag to indicate that the eth tx has been relayed to omnilink
	if err = omnilinkRelayer.setEthTxRelayAlreadyInfo(claim.EthTxHash, relayTxDetail); nil != err {
		relayerLog.Error("relayLockBurnToOmnilink", "Failed to setTxRelayAlreadyInfo due to:", err.Error())
		return
	}
	//relayEthereum2omnilinkCheckPonit 3:setFalgRelayFinish
	relayerLog.Info("relayLockBurnToOmnilink::relayEthereum2omnilinkCheckPonit_3::setFalgRelayFinish", "ethTxhash", claim.EthTxHash, "ForwardIndex", claim.ForwardIndex, "FdTimes", claim.ForwardTimes)

	//第一个有效的index从１开始，方便list
	txIndex := atomic.AddInt64(&omnilinkRelayer.totalTx4RelayEth2chai33, 1)
	if err = omnilinkRelayer.updateTotalTxAmount2Eth(txIndex); nil != err {
		relayerLog.Error("relayLockBurnToOmnilink", "Failed to updateTotalTxAmount2Eth due to:", err.Error())
		return
	}

	statics := &ebTypes.Ethereum2OmnilinkStatics{
		OmnilinkTxstatus: ebTypes.Tx_Status_Pending,
		OmnilinkTxhash:   txhash,
		EthereumTxhash:   claim.EthTxHash,
		BurnLock:         claim.ClaimType,
		EthereumSender:   claim.EthereumSender,
		OmnilinkReceiver: claim.OmnilinkReceiver,
		Symbol:           claim.Symbol,
		Amount:           claim.Amount,
		Nonce:            claim.Nonce,
		TxIndex:          txIndex,
		OperationType:    operationType,
	}
	data := omnilinkTypes.Encode(statics)
	if err = omnilinkRelayer.setLastestRelay2OmnilinkTxStatics(txIndex, claim.ClaimType, data); nil != err {
		relayerLog.Error("relayLockBurnToOmnilink", "Failed to setLastestRelay2OmnilinkTxStatics due to:", err.Error())
		return
	}
	relayerLog.Info("relayLockBurnToOmnilink::successful",
		"txIndex", txIndex,
		"OmnilinkTxhash", txhash,
		"EthereumTxhash", claim.EthTxHash,
		"type", operationType,
		"Symbol", claim.Symbol,
		"Amount", claim.Amount,
		"EthereumSender", claim.EthereumSender,
		"OmnilinkReceiver", claim.OmnilinkReceiver)
}

func (omnilinkRelayer *Relayer4Omnilink) BurnAsyncFromOmnilink(ownerPrivateKey, tokenAddr, ethereumReceiver, amount string) (string, error) {
	bn := big.NewInt(1)
	bn, _ = bn.SetString(utils.TrimZeroAndDot(amount), 10)
	return burnAsync(ownerPrivateKey, tokenAddr, ethereumReceiver, bn.Int64(), omnilinkRelayer.bridgeBankAddr, omnilinkRelayer.chainName, omnilinkRelayer.rpcLaddr)
}

func (omnilinkRelayer *Relayer4Omnilink) LockBTYAssetAsync(ownerPrivateKey, ethereumReceiver, amount string) (string, error) {
	bn := big.NewInt(1)
	bn, _ = bn.SetString(utils.TrimZeroAndDot(amount), 10)
	return lockAsync(ownerPrivateKey, ethereumReceiver, bn.Int64(), omnilinkRelayer.bridgeBankAddr, omnilinkRelayer.chainName, omnilinkRelayer.rpcLaddr)
}

//ShowBridgeRegistryAddr ...
func (omnilinkRelayer *Relayer4Omnilink) ShowBridgeRegistryAddr() (string, error) {
	if "" == omnilinkRelayer.bridgeRegistryAddr {
		return "", errors.New("the relayer is not started yet")
	}

	return omnilinkRelayer.bridgeRegistryAddr, nil
}

func (omnilinkRelayer *Relayer4Omnilink) ShowStatics(request *ebTypes.TokenStaticsRequest) (*ebTypes.TokenStaticsResponse, error) {
	res := &ebTypes.TokenStaticsResponse{}

	datas, err := omnilinkRelayer.getStatics(request.Operation, request.TxIndex, request.Count)
	if nil != err {
		return nil, err
	}
	//todo:完善分页显示功能
	for _, data := range datas {
		var statics ebTypes.Ethereum2OmnilinkStatics
		_ = omnilinkTypes.Decode(data, &statics)
		if request.Status != 0 && ebTypes.Tx_Status_Map[request.Status] != statics.OmnilinkTxstatus {
			continue
		}
		if len(request.Symbol) > 0 && request.Symbol != statics.Symbol {
			continue
		}
		res.E2Cstatics = append(res.E2Cstatics, &statics)
	}
	return res, nil
}

func (omnilinkRelayer *Relayer4Omnilink) updateTxStatus() {
	omnilinkRelayer.updateSingleTxStatus(events.ClaimTypeBurn)
	omnilinkRelayer.updateSingleTxStatus(events.ClaimTypeLock)
}

// 该函数用于定期检查是否有需要重新发送给以太坊协成的omnilink事件信息,用于产生relay event
func (omnilinkRelayer *Relayer4Omnilink) checkTxRelay2Ethereum() {
	txInfos, err := omnilinkRelayer.getAllTxsUnconfirm()
	if err != nil {
		relayerLog.Error("omnilinkRelayer::checkTxRelay2Ethereum", "Failed to getAllTxsUnconfirm due to", err.Error())
		return
	}
	if 0 == len(txInfos) {
		return
	}
	for _, txInfo := range txInfos {
		txHashStr := omnilinkEvmCommon.Bytes2Hex(txInfo.TxHash)

		if !txInfo.Resend {
			//为了防止转发出去的消息之后，下一个区块时间马上到来，首次转发的消息需要至少等一个区块间隔之后才会进行转发
			txInfo.Resend = true
			err = omnilinkRelayer.setOmnilinkTxIsRelayedUnconfirm(txHashStr, txInfo.FdIndex, txInfo)
			if nil != err {
				relayerLog.Error("omnilinkRelayer::checkTxRelay2Ethereum", "Failed to SetTxIsRelayedconfirm due to", err.Error())
				return
			}
			continue
		}

		omnilinkMsg, err := events.ParseBurnLock4omnilink(events.OmnilinkEvmEvent(txInfo.EventType), txInfo.Data, omnilinkRelayer.bridgeBankAbi, txInfo.TxHash)
		if nil != err {
			relayerLog.Error("omnilinkRelayer::checkTxRelay2Ethereum", "Failed to ParseBurnLock4omnilink due to", err.Error())
			return
		}
		txInfo.FdTimes = txInfo.FdTimes + 1
		omnilinkMsg.ForwardTimes = txInfo.FdTimes
		omnilinkMsg.ForwardIndex = txInfo.FdIndex

		channel, ok := omnilinkRelayer.omnilinkMsgChan[txInfo.ToChainName]
		if !ok {
			relayerLog.Error("omnilinkRelayer::checkTxRelay2Ethereum", "No omnilinkMsgChan for ethereum chain with name", txInfo.ToChainName)
			return
		}
		channel <- omnilinkMsg

		//relayomnilinkToEthereumCheckPonit 5: checkTxRelay2Ethereum
		relayerLog.Info("omnilinkRelayer::relayomnilinkToEthereumCheckPonit_5::checkTxRelay2Ethereum", "omnilinkTxHash", txHashStr, "ForwardIndex", omnilinkMsg.ForwardIndex, "FdTimes", omnilinkMsg.ForwardTimes)
		err = omnilinkRelayer.setOmnilinkTxIsRelayedUnconfirm(txHashStr, txInfo.FdIndex, txInfo)
		if nil != err {
			relayerLog.Error("omnilinkRelayer::checkTxRelay2Ethereum", "Failed to SetTxIsRelayedconfirm due to", err.Error())
			return
		}
	}
}

//用于omnilink的事件信息被中继之后的ack信息，重置标志位
func (omnilinkRelayer *Relayer4Omnilink) procTxRelayAck(ack *ebTypes.TxRelayAck) {
	//reset with another key to exclude from the check list to resend the same message
	if err := omnilinkRelayer.resetKeyOmnilinkTxRelayedAlready(ack.TxHash); nil != err {
		relayerLog.Error("omnilinkRelayer::procTxRelayAck", "Failed to resetKeyTxRelayedAlready due to:", err.Error())
		return
	}
	//relayomnilinkToEthereumCheckPonit 4: recv ack from ethereum relay service
	relayerLog.Info("omnilinkRelayer::procTxRelayAck::relayomnilinkToEthereumCheckPonit_4", "omnilinkTxHash", ack.TxHash, "ForwardIndex", ack.FdIndex)
}

func (omnilinkRelayer *Relayer4Omnilink) updateSingleTxStatus(claimType events.ClaimType) {
	txIndex := omnilinkRelayer.getOmnilinkUpdateTxIndex(claimType)
	datas, _ := omnilinkRelayer.getStatics(int32(claimType), txIndex, 0)
	if nil == datas {
		return
	}
	for _, data := range datas {
		var statics ebTypes.Ethereum2OmnilinkStatics
		_ = omnilinkTypes.Decode(data, &statics)
		result := GetTxStatusByHashesRpc(statics.OmnilinkTxhash, omnilinkRelayer.rpcLaddr)
		//当前处理机制比较简单，如果发现该笔交易未执行，就不再产寻后续交易的回执
		if ebTypes.Invalid_OmnilinkTx_Status == result {
			relayerLog.Debug("omnilinkRelayer::updateSingleTxStatus", "no receipt for tx index", statics.TxIndex)
			break
		}
		status := ebTypes.Tx_Status_Success
		if result != omnilinkTypes.ExecOk {
			status = ebTypes.Tx_Status_Failed
		}
		statics.OmnilinkTxstatus = status
		dataNew := omnilinkTypes.Encode(&statics)
		_ = omnilinkRelayer.setLastestRelay2OmnilinkTxStatics(statics.TxIndex, int32(claimType), dataNew)
		_ = omnilinkRelayer.setOmnilinkUpdateTxIndex(statics.TxIndex, claimType)
		relayerLog.Debug("updateSingleTxStatus", "TxIndex", statics.TxIndex, "operationType", statics.OperationType, "txHash", statics.OmnilinkTxhash, "updated status", status)
	}
}

func (omnilinkRelayer *Relayer4Omnilink) SetupMulSign(setupMulSign *ebTypes.SetupMulSign) (string, error) {
	if "" == omnilinkRelayer.mulSignAddr {
		return "", ebTypes.ErrMulSignNotDeployed
	}

	return setupMultiSign(setupMulSign.OperatorPrivateKey, omnilinkRelayer.mulSignAddr, omnilinkRelayer.chainName, omnilinkRelayer.rpcLaddr, setupMulSign.Owners)
}

func (omnilinkRelayer *Relayer4Omnilink) SafeTransfer(para *ebTypes.SafeTransfer) (string, error) {
	if "" == omnilinkRelayer.mulSignAddr {
		return "", ebTypes.ErrMulSignNotDeployed
	}

	return safeTransfer(para.OwnerPrivateKeys[0], omnilinkRelayer.mulSignAddr, omnilinkRelayer.chainName,
		omnilinkRelayer.rpcLaddr, para.To, para.Token, para.OwnerPrivateKeys, para.Amount)
}

func (omnilinkRelayer *Relayer4Omnilink) SetMultiSignAddr(address string) {
	omnilinkRelayer.rwLock.Lock()
	omnilinkRelayer.mulSignAddr = address
	omnilinkRelayer.rwLock.Unlock()

	omnilinkRelayer.setMultiSignAddress(address)
}

func (omnilinkRelayer *Relayer4Omnilink) GetMultiSignAddr() string {
	return omnilinkRelayer.getMultiSignAddress()
}

func (omnilinkRelayer *Relayer4Omnilink) WithdrawFromOmnilink(ownerPrivateKey, tokenAddr, ethereumReceiver, amount string) (string, error) {
	bn := big.NewInt(1)
	bn, _ = bn.SetString(utils.TrimZeroAndDot(amount), 10)
	return withdrawAsync(ownerPrivateKey, tokenAddr, ethereumReceiver, bn.Int64(), omnilinkRelayer.bridgeBankAddr, omnilinkRelayer.chainName, omnilinkRelayer.rpcLaddr)
}

func (omnilinkRelayer *Relayer4Omnilink) BurnWithIncreaseAsyncFromOmnilink(ownerPrivateKey, tokenAddr, ethereumReceiver, amount string) (string, error) {
	bn := big.NewInt(1)
	bn, _ = bn.SetString(utils.TrimZeroAndDot(amount), 10)
	return burnWithIncreaseAsync(ownerPrivateKey, tokenAddr, ethereumReceiver, bn.Int64(), omnilinkRelayer.bridgeBankAddr, omnilinkRelayer.chainName, omnilinkRelayer.rpcLaddr)
}
