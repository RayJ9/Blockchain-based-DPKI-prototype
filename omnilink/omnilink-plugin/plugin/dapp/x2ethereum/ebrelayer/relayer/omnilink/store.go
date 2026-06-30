package omnilink

import (
	"fmt"
	"sync/atomic"

	"code.corp.bcollie.net/omnilink/omnilink-base/types"
	ebTypes "code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/x2ethereum/ebrelayer/types"
	"code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/x2ethereum/ebrelayer/utils"
	"github.com/ethereum/go-ethereum/common"
)

//key ...
var (
	lastSyncHeightPrefix               = []byte("lastSyncHeight:")
	omnilinkToEthBurnLockTxHashPrefix  = "omnilinkToEthBurnLockTxHash"
	omnilinkToEthBurnLockTxTotalAmount = []byte("omnilinkToEthBurnLockTxTotalAmount")
	EthTxStatusCheckedIndex            = []byte("EthTxStatusCheckedIndex")
)

func calcRelay2EthTxhash(txindex int64) []byte {
	return []byte(fmt.Sprintf("%s-%012d", omnilinkToEthBurnLockTxHashPrefix, txindex))
}

func (omnilinkRelayer *Relayer4Omnilink) updateTotalTxAmount2Eth(total int64) error {
	totalTx := &types.Int64{
		Data: atomic.LoadInt64(&omnilinkRelayer.totalTx4OmnilinkToEth),
	}
	//更新成功见证的交易数
	return omnilinkRelayer.db.Set(omnilinkToEthBurnLockTxTotalAmount, types.Encode(totalTx))
}

func (omnilinkRelayer *Relayer4Omnilink) getTotalTxAmount2Eth() int64 {
	totalTx, _ := utils.LoadInt64FromDB(omnilinkToEthBurnLockTxTotalAmount, omnilinkRelayer.db)
	return totalTx
}

func (omnilinkRelayer *Relayer4Omnilink) setLastestRelay2EthTxhash(status, txhash string, txIndex int64) error {
	key := calcRelay2EthTxhash(txIndex)
	ethTxStatus := &ebTypes.EthTxStatus{
		Status: status,
		Txhash: txhash,
	}
	data := types.Encode(ethTxStatus)
	return omnilinkRelayer.db.Set(key, data)
}

func (omnilinkRelayer *Relayer4Omnilink) getEthTxhash(txIndex int64) (common.Hash, error) {
	key := calcRelay2EthTxhash(txIndex)
	ethTxStatus := &ebTypes.EthTxStatus{}
	data, err := omnilinkRelayer.db.Get(key)
	if nil != err {
		return common.Hash{}, err
	}
	err = types.Decode(data, ethTxStatus)
	if nil != err {
		return common.Hash{}, err
	}
	return common.HexToHash(ethTxStatus.Txhash), nil
}

func (omnilinkRelayer *Relayer4Omnilink) setStatusCheckedIndex(txIndex int64) error {
	index := &types.Int64{
		Data: txIndex,
	}
	data := types.Encode(index)
	return omnilinkRelayer.db.Set(EthTxStatusCheckedIndex, data)
}

func (omnilinkRelayer *Relayer4Omnilink) getStatusCheckedIndex() int64 {
	index, _ := utils.LoadInt64FromDB(EthTxStatusCheckedIndex, omnilinkRelayer.db)
	return index
}

//获取上次同步到app的高度
func (omnilinkRelayer *Relayer4Omnilink) loadLastSyncHeight() int64 {
	height, err := utils.LoadInt64FromDB(lastSyncHeightPrefix, omnilinkRelayer.db)
	if nil != err && err != types.ErrHeightNotExist {
		relayerLog.Error("loadLastSyncHeight", "err:", err.Error())
		return 0
	}
	return height
}

func (omnilinkRelayer *Relayer4Omnilink) setLastSyncHeight(syncHeight int64) {
	bytes := types.Encode(&types.Int64{Data: syncHeight})
	_ = omnilinkRelayer.db.Set(lastSyncHeightPrefix, bytes)
}
