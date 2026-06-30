package omnilink

import (
	"bytes"
	"context"
	"crypto/ecdsa"
	"errors"
	"fmt"
	"os"
	"sync"
	"sync/atomic"
	"time"

	dbm "code.corp.bcollie.net/omnilink/omnilink-base/common/db"
	log "code.corp.bcollie.net/omnilink/omnilink-base/common/log/log15"
	"code.corp.bcollie.net/omnilink/omnilink-base/rpc/jsonclient"
	rpctypes "code.corp.bcollie.net/omnilink/omnilink-base/rpc/types"
	omnilinkTypes "code.corp.bcollie.net/omnilink/omnilink-base/types"
	"code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/x2ethereum/ebrelayer/ethcontract/generated"
	"code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/x2ethereum/ebrelayer/ethinterface"
	relayerTx "code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/x2ethereum/ebrelayer/ethtxs"
	"code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/x2ethereum/ebrelayer/events"
	syncTx "code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/x2ethereum/ebrelayer/relayer/omnilink/transceiver/sync"
	ebTypes "code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/x2ethereum/ebrelayer/types"
	"code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/x2ethereum/ebrelayer/utils"
	"code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/x2ethereum/types"
	ethCommon "github.com/ethereum/go-ethereum/common"
)

var relayerLog = log.New("module", "omnilink_relayer")

//Relayer4Omnilink ...
type Relayer4Omnilink struct {
	syncTxReceipts      *syncTx.TxReceipts
	ethClient           ethinterface.EthClientSpec
	rpcLaddr            string //用户向指定的blockchain节点进行rpc调用
	fetchHeightPeriodMs int64
	db                  dbm.DB
	lastHeight4Tx       int64 //等待被处理的具有相应的交易回执的高度
	matDegree           int32 //成熟度         heightSync2App    matDegress   height
	//passphase            string
	privateKey4Ethereum   *ecdsa.PrivateKey
	ethSender             ethCommon.Address
	bridgeRegistryAddr    ethCommon.Address
	oracleInstance        *generated.Oracle
	totalTx4OmnilinkToEth int64
	statusCheckedIndex    int64
	ctx                   context.Context
	rwLock                sync.RWMutex
	unlock                chan int
}

// StartOmnilinkRelayer : initializes a relayer which witnesses events on the omnilink network and relays them to Ethereum
func StartOmnilinkRelayer(ctx context.Context, syncTxConfig *ebTypes.SyncTxConfig, registryAddr, provider string, db dbm.DB) *Relayer4Omnilink {
	chian33Relayer := &Relayer4Omnilink{
		rpcLaddr:            syncTxConfig.OmnilinkHost,
		fetchHeightPeriodMs: syncTxConfig.FetchHeightPeriodMs,
		unlock:              make(chan int),
		db:                  db,
		ctx:                 ctx,
		bridgeRegistryAddr:  ethCommon.HexToAddress(registryAddr),
	}

	syncCfg := &ebTypes.SyncTxReceiptConfig{
		OmnilinkHost:      syncTxConfig.OmnilinkHost,
		PushHost:          syncTxConfig.PushHost,
		PushName:          syncTxConfig.PushName,
		PushBind:          syncTxConfig.PushBind,
		StartSyncHeight:   syncTxConfig.StartSyncHeight,
		StartSyncSequence: syncTxConfig.StartSyncSequence,
		StartSyncHash:     syncTxConfig.StartSyncHash,
	}

	client, err := relayerTx.SetupWebsocketEthClient(provider)
	if err != nil {
		panic(err)
	}
	chian33Relayer.ethClient = client
	chian33Relayer.totalTx4OmnilinkToEth = chian33Relayer.getTotalTxAmount2Eth()
	chian33Relayer.statusCheckedIndex = chian33Relayer.getStatusCheckedIndex()

	go chian33Relayer.syncProc(syncCfg)
	return chian33Relayer
}

//QueryTxhashRelay2Eth ...
func (omnilinkRelayer *Relayer4Omnilink) QueryTxhashRelay2Eth() ebTypes.Txhashes {
	txhashs := utils.QueryTxhashes([]byte(omnilinkToEthBurnLockTxHashPrefix), omnilinkRelayer.db)
	return ebTypes.Txhashes{Txhash: txhashs}
}

func (omnilinkRelayer *Relayer4Omnilink) syncProc(syncCfg *ebTypes.SyncTxReceiptConfig) {
	_, _ = fmt.Fprintln(os.Stdout, "Pls unlock or import private key for Omnilink relayer")
	<-omnilinkRelayer.unlock
	_, _ = fmt.Fprintln(os.Stdout, "Omnilink relayer starts to run...")

	omnilinkRelayer.syncTxReceipts = syncTx.StartSyncTxReceipt(syncCfg, omnilinkRelayer.db)
	omnilinkRelayer.lastHeight4Tx = omnilinkRelayer.loadLastSyncHeight()

	oracleInstance, err := relayerTx.RecoverOracleInstance(omnilinkRelayer.ethClient, omnilinkRelayer.bridgeRegistryAddr, omnilinkRelayer.bridgeRegistryAddr)
	if err != nil {
		panic(err.Error())
	}
	omnilinkRelayer.oracleInstance = oracleInstance

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
	omnilinkRelayer.rwLock.Lock()
	for omnilinkRelayer.statusCheckedIndex < omnilinkRelayer.totalTx4OmnilinkToEth {
		index := omnilinkRelayer.statusCheckedIndex + 1
		txhash, err := omnilinkRelayer.getEthTxhash(index)
		if nil != err {
			relayerLog.Error("onNewHeightProc", "getEthTxhash for index ", index, "error", err.Error())
			break
		}
		status := relayerTx.GetEthTxStatus(omnilinkRelayer.ethClient, txhash)
		//按照提交交易的先后顺序检查交易，只要出现当前交易还在pending状态，就不再检查后续交易，等到下个区块再从该交易进行检查
		//TODO:可能会由于网络和打包挖矿的原因，使得交易执行顺序和提交顺序有差别，后续完善该检查逻辑
		if status == relayerTx.EthTxPending.String() {
			break
		}
		_ = omnilinkRelayer.setLastestRelay2EthTxhash(status, txhash.Hex(), index)
		atomic.AddInt64(&omnilinkRelayer.statusCheckedIndex, 1)
		_ = omnilinkRelayer.setStatusCheckedIndex(omnilinkRelayer.statusCheckedIndex)
	}
	omnilinkRelayer.rwLock.Unlock()
	//未达到足够的成熟度，不进行处理
	//  +++++++++||++++++++++++||++++++++++||
	//           ^             ^           ^
	// lastHeight4Tx    matDegress   currentHeight
	for omnilinkRelayer.lastHeight4Tx+int64(omnilinkRelayer.matDegree)+1 <= currentHeight {
		relayerLog.Info("onNewHeightProc", "currHeight", currentHeight, "lastHeight4Tx", omnilinkRelayer.lastHeight4Tx)

		lastHeight4Tx := omnilinkRelayer.lastHeight4Tx
		TxReceipts, err := omnilinkRelayer.syncTxReceipts.GetNextValidTxReceipts(lastHeight4Tx)
		if nil == TxReceipts || nil != err {
			if err != nil {
				relayerLog.Error("onNewHeightProc", "Failed to GetNextValidTxReceipts due to:", err.Error())
			}
			break
		}
		relayerLog.Debug("onNewHeightProc", "currHeight", currentHeight, "valid tx receipt with height:", TxReceipts.Height)

		txs := TxReceipts.Tx
		for i, tx := range txs {
			//检查是否为lns的交易(包括平行链：user.p.xxx.lns)，将闪电网络交易进行收集
			if 0 != bytes.Compare(tx.Execer, []byte(relayerTx.X2Eth)) &&
				(len(tx.Execer) > 4 && string(tx.Execer[(len(tx.Execer)-4):]) != "."+relayerTx.X2Eth) {
				relayerLog.Debug("onNewHeightProc, the tx is not x2ethereum", "Execer", string(tx.Execer), "height:", TxReceipts.Height)
				continue
			}
			var ss types.X2EthereumAction
			_ = omnilinkTypes.Decode(tx.Payload, &ss)
			actionName := ss.GetActionName()
			if relayerTx.BurnAction == actionName || relayerTx.LockAction == actionName {
				relayerLog.Debug("^_^ ^_^ Processing omnilink tx receipt", "ActionName", actionName, "fromAddr", tx.From(), "exec", string(tx.Execer))
				actionEvent := getOracleClaimType(actionName)
				if err := omnilinkRelayer.handleBurnLockMsg(actionEvent, TxReceipts.ReceiptData[i], tx.Hash()); nil != err {
					errInfo := fmt.Sprintf("Failed to handleBurnLockMsg due to:%s", err.Error())
					panic(errInfo)
				}
			}
		}
		omnilinkRelayer.lastHeight4Tx = TxReceipts.Height
		omnilinkRelayer.setLastSyncHeight(omnilinkRelayer.lastHeight4Tx)
	}
}

// getOracleClaimType : sets the OracleClaim's claim type based upon the witnessed event type
func getOracleClaimType(eventType string) events.Event {
	var claimType events.Event

	switch eventType {
	case events.MsgBurn.String():
		claimType = events.Event(events.ClaimTypeBurn)
	case events.MsgLock.String():
		claimType = events.Event(events.ClaimTypeLock)
	default:
		panic(errors.New("eventType invalid"))
	}

	return claimType
}

// handleBurnLockMsg : parse event data as a OmnilinkMsg, package it into a ProphecyClaim, then relay tx to the Ethereum Network
func (omnilinkRelayer *Relayer4Omnilink) handleBurnLockMsg(claimEvent events.Event, receipt *omnilinkTypes.ReceiptData, omnilinkTxHash []byte) error {
	relayerLog.Info("handleBurnLockMsg", "Received tx with hash", ethCommon.Bytes2Hex(omnilinkTxHash))

	// Parse the witnessed event's data into a new OmnilinkMsg
	omnilinkMsg := relayerTx.ParseBurnLockTxReceipt(claimEvent, receipt)
	if nil == omnilinkMsg {
		//收到执行失败的交易，直接跳过
		relayerLog.Error("handleBurnLockMsg", "Received failed tx with hash", ethCommon.Bytes2Hex(omnilinkTxHash))
		return nil
	}

	// Parse the OmnilinkMsg into a ProphecyClaim for relay to Ethereum
	prophecyClaim := relayerTx.OmnilinkMsgToProphecyClaim(*omnilinkMsg)

	// Relay the OmnilinkMsg to the Ethereum network
	txhash, err := relayerTx.RelayOracleClaimToEthereum(omnilinkRelayer.oracleInstance, omnilinkRelayer.ethClient, omnilinkRelayer.ethSender, claimEvent, prophecyClaim, omnilinkRelayer.privateKey4Ethereum, omnilinkTxHash)
	if nil != err {
		return err
	}

	//保存交易hash，方便查询
	atomic.AddInt64(&omnilinkRelayer.totalTx4OmnilinkToEth, 1)
	txIndex := atomic.LoadInt64(&omnilinkRelayer.totalTx4OmnilinkToEth)
	if err = omnilinkRelayer.updateTotalTxAmount2Eth(txIndex); nil != err {
		relayerLog.Error("handleLogNewProphecyClaimEvent", "Failed to RelayLockToOmnilink due to:", err.Error())
		return err
	}
	if err = omnilinkRelayer.setLastestRelay2EthTxhash(relayerTx.EthTxPending.String(), txhash, txIndex); nil != err {
		relayerLog.Error("handleLogNewProphecyClaimEvent", "Failed to RelayLockToOmnilink due to:", err.Error())
		return err
	}
	return nil
}
