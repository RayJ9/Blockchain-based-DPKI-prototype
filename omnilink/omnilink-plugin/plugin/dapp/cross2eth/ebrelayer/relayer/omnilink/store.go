package omnilink

import (
	"errors"
	"fmt"

	dbm "code.corp.bcollie.net/omnilink/omnilink-base/common/db"
	omnilinkTypes "code.corp.bcollie.net/omnilink/omnilink-base/types"
	"code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/cross2eth/ebrelayer/relayer/events"
	ebTypes "code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/cross2eth/ebrelayer/types"
	"code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/cross2eth/ebrelayer/utils"
)

//key ...
var (
	lastSyncHeightPrefix                = []byte("omnilink-lastSyncHeight:")
	eth2OmnilinkBurnLockTxStaticsPrefix = "omnilink-eth2omnilinkBurnLockStatics"
	eth2OmnilinkBurnLockTxFinished      = "omnilink-eth2OmnilinkBurnLockTxFinished"
	relayEthBurnLockTxTotalAmount       = []byte("omnilink-relayEthBurnLockTxTotalAmount")
	omnilinkBurnTxUpdateTxIndex         = []byte("omnilink-omnilinkBurnTxUpdateTxIndx")
	omnilinkLockTxUpdateTxIndex         = []byte("omnilink-omnilinkLockTxUpdateTxIndex")
	bridgeRegistryAddrOnOmnilink        = []byte("omnilink-x2EthBridgeRegistryAddrOnOmnilink")
	tokenSymbol2AddrPrefix              = []byte("omnilink-omnilinkTokenSymbol2AddrPrefix")
	multiSignAddressPrefix              = []byte("omnilink-multiSignAddress")
	symbol2Ethchain                     = []byte("omnilink-symbol2Ethchain")
	txIsRelayedUnconfirm                = []byte("omnilink-txIsRelayedUnconfirm")
	omnilinkTxRelayedAlready            = []byte("omnilink-txRelayedAlready")
	fdTx2EthTotalAmount                 = []byte("omnilink-fdTx2EthTotalAmount")
	ethTxRelayAlreadyPrefix             = []byte("omnilink-ethTxRelayAlready")
)

func ethTxRelayAlreadyKey(omnilinkTxhash string) []byte {
	return append(ethTxRelayAlreadyPrefix, []byte(fmt.Sprintf("-txHash-%s", omnilinkTxhash))...)
}

func omnilinkTxIsRelayedUnconfirmKey(txHash string) []byte {
	return append(txIsRelayedUnconfirm, []byte(fmt.Sprintf("-txHash-%s", txHash))...)
}

func omnilinkTxRelayedAlreadyKey(txHash string) []byte {
	return append(omnilinkTxRelayedAlready, []byte(fmt.Sprintf("-txHash-%s", txHash))...)
}

func tokenSymbol2AddrKey(symbol string) []byte {
	return append(tokenSymbol2AddrPrefix, []byte(fmt.Sprintf("-symbol-%s", symbol))...)
}

func calcRelayFromEthStaticsKey(txindex int64, claimType int32) []byte {
	return []byte(fmt.Sprintf("%s-%d-%012d", eth2OmnilinkBurnLockTxStaticsPrefix, claimType, txindex))
}

//未完成，处在pending状态
func calcRelayFromEthStaticsList(claimType int32) []byte {
	return []byte(fmt.Sprintf("%s-%d-", eth2OmnilinkBurnLockTxStaticsPrefix, claimType))
}

func calcFromEthFinishedStaticsKey(txindex int64, claimType int32) []byte {
	return []byte(fmt.Sprintf("%s-%d-%012d", eth2OmnilinkBurnLockTxFinished, claimType, txindex))
}

func calcFromEthFinishedStaticsList(claimType int32) []byte {
	return []byte(fmt.Sprintf("%s-%d-", eth2OmnilinkBurnLockTxFinished, claimType))
}

func (omnilinkRelayer *Relayer4Omnilink) updateFdTx2EthTotalAmount(index int64) error {
	totalTx := &omnilinkTypes.Int64{
		Data: index,
	}
	//更新成功见证的交易数
	return omnilinkRelayer.db.SetSync(fdTx2EthTotalAmount, omnilinkTypes.Encode(totalTx))
}

func (omnilinkRelayer *Relayer4Omnilink) getFdTx2EthTotalAmount() int64 {
	totalTx, _ := utils.LoadInt64FromDB(fdTx2EthTotalAmount, omnilinkRelayer.db)
	return totalTx
}

func (omnilinkRelayer *Relayer4Omnilink) getAllTxsUnconfirm() (txInfos []*ebTypes.TxRelayConfirm4Omnilink, err error) {
	helper := dbm.NewListHelper(omnilinkRelayer.db)
	datas := helper.List(txIsRelayedUnconfirm, nil, 0, dbm.ListASC)
	cnt := len(datas)
	if 0 == cnt {
		return nil, nil
	}

	txInfos = make([]*ebTypes.TxRelayConfirm4Omnilink, cnt)
	for i, data := range datas {
		txInfo := &ebTypes.TxRelayConfirm4Omnilink{}
		if err := omnilinkTypes.Decode(data, txInfo); nil != err {
			return nil, err
		}

		txInfos[i] = txInfo
	}
	return
}

func (omnilinkRelayer *Relayer4Omnilink) resetKeyOmnilinkTxRelayedAlready(txHash string) error {
	key := omnilinkTxIsRelayedUnconfirmKey(txHash)
	data, err := omnilinkRelayer.db.Get(key)
	if nil != err {
		relayerLog.Info("resetKeyTxRelayedAlready", "No data for tx", txHash)
		return err
	}
	_ = omnilinkRelayer.db.DeleteSync(key)
	setkey := omnilinkTxRelayedAlreadyKey(txHash)

	return omnilinkRelayer.db.SetSync(setkey, data)
}

func (omnilinkRelayer *Relayer4Omnilink) setOmnilinkTxIsRelayedUnconfirm(txHash string, index int64, txRelayConfirm4Omnilink *ebTypes.TxRelayConfirm4Omnilink) error {
	key := omnilinkTxIsRelayedUnconfirmKey(txHash)
	data := omnilinkTypes.Encode(txRelayConfirm4Omnilink)
	relayerLog.Info("setOmnilinkTxIsRelayedUnconfirm", "TxHash", txHash, "index", index, "ForwardTimes", txRelayConfirm4Omnilink.FdTimes)
	return omnilinkRelayer.db.SetSync(key, data)
}

func (omnilinkRelayer *Relayer4Omnilink) setEthTxRelayAlreadyInfo(ethTxhash string, relayTxDetail *ebTypes.RelayTxDetail) error {
	key := ethTxRelayAlreadyKey(ethTxhash)
	data := omnilinkTypes.Encode(relayTxDetail)
	return omnilinkRelayer.db.SetSync(key, data)
}

func (omnilinkRelayer *Relayer4Omnilink) getEthTxRelayAlreadyInfo(ethTxhash string) (*ebTypes.RelayTxDetail, error) {
	key := ethTxRelayAlreadyKey(ethTxhash)
	data, err := omnilinkRelayer.db.Get(key)
	if nil != err {
		return nil, err
	}
	var relayTxDetail ebTypes.RelayTxDetail
	err = omnilinkTypes.Decode(data, &relayTxDetail)
	return &relayTxDetail, err
}

func (omnilinkRelayer *Relayer4Omnilink) updateTotalTxAmount2Eth(txIndex int64) error {
	totalTx := &omnilinkTypes.Int64{
		Data: txIndex,
	}
	//更新成功见证的交易数
	return omnilinkRelayer.db.SetSync(relayEthBurnLockTxTotalAmount, omnilinkTypes.Encode(totalTx))
}

func (omnilinkRelayer *Relayer4Omnilink) getTotalTxAmount() int64 {
	totalTx, _ := utils.LoadInt64FromDB(relayEthBurnLockTxTotalAmount, omnilinkRelayer.db)
	return totalTx
}

func (omnilinkRelayer *Relayer4Omnilink) setLastestRelay2OmnilinkTxStatics(txIndex int64, claimType int32, data []byte) error {
	key := calcRelayFromEthStaticsKey(txIndex, claimType)
	return omnilinkRelayer.db.SetSync(key, data)
}

func (omnilinkRelayer *Relayer4Omnilink) getStatics(claimType int32, txIndex int64, count int32) ([][]byte, error) {
	//第一步：获取处在pending状态的
	keyPrefix := calcRelayFromEthStaticsList(claimType)
	keyFrom := calcRelayFromEthStaticsKey(txIndex, claimType)
	helper := dbm.NewListHelper(omnilinkRelayer.db)
	datas := helper.List(keyPrefix, keyFrom, count, dbm.ListASC)
	if nil == datas {
		return nil, errors.New("Not found")
	}

	return datas, nil
}

func (omnilinkRelayer *Relayer4Omnilink) setOmnilinkUpdateTxIndex(txindex int64, claimType events.ClaimType) error {
	txIndexWrapper := &omnilinkTypes.Int64{
		Data: txindex,
	}

	if events.ClaimTypeBurn == claimType {
		return omnilinkRelayer.db.SetSync(omnilinkBurnTxUpdateTxIndex, omnilinkTypes.Encode(txIndexWrapper))
	}
	return omnilinkRelayer.db.SetSync(omnilinkLockTxUpdateTxIndex, omnilinkTypes.Encode(txIndexWrapper))
}

func (omnilinkRelayer *Relayer4Omnilink) getOmnilinkUpdateTxIndex(claimType events.ClaimType) int64 {
	var key []byte
	if events.ClaimTypeBurn == claimType {
		key = omnilinkBurnTxUpdateTxIndex
	} else {
		key = omnilinkLockTxUpdateTxIndex
	}
	data, err := omnilinkRelayer.db.Get(key)
	if nil != err {
		return ebTypes.Invalid_Tx_Index
	}

	var txIndexWrapper omnilinkTypes.Int64
	err = omnilinkTypes.Decode(data, &txIndexWrapper)
	if nil != err {
		return ebTypes.Invalid_Tx_Index
	}
	return txIndexWrapper.Data
}

//获取上次同步到app的高度
func (omnilinkRelayer *Relayer4Omnilink) loadLastSyncHeight() int64 {
	height, err := utils.LoadInt64FromDB(lastSyncHeightPrefix, omnilinkRelayer.db)
	if nil != err && err != omnilinkTypes.ErrHeightNotExist {
		relayerLog.Error("loadLastSyncHeight", "err:", err.Error())
		return 0
	}
	return height
}

func (omnilinkRelayer *Relayer4Omnilink) setLastSyncHeight(syncHeight int64) {
	bytes := omnilinkTypes.Encode(&omnilinkTypes.Int64{Data: syncHeight})
	_ = omnilinkRelayer.db.SetSync(lastSyncHeightPrefix, bytes)
}

func (omnilinkRelayer *Relayer4Omnilink) setBridgeRegistryAddr(bridgeRegistryAddr string) error {
	return omnilinkRelayer.db.SetSync(bridgeRegistryAddrOnOmnilink, []byte(bridgeRegistryAddr))
}

func (omnilinkRelayer *Relayer4Omnilink) getBridgeRegistryAddr() (string, error) {
	addr, err := omnilinkRelayer.db.Get(bridgeRegistryAddrOnOmnilink)
	if nil != err {
		return "", err
	}
	return string(addr), nil
}

func (omnilinkRelayer *Relayer4Omnilink) SetTokenAddress(token2set *ebTypes.TokenAddress) error {
	bytes := omnilinkTypes.Encode(token2set)
	omnilinkRelayer.rwLock.Lock()
	omnilinkRelayer.symbol2Addr[token2set.Symbol] = token2set.Address
	omnilinkRelayer.rwLock.Unlock()
	return omnilinkRelayer.db.SetSync(tokenSymbol2AddrKey(token2set.Symbol), bytes)
}

func (omnilinkRelayer *Relayer4Omnilink) RestoreTokenAddress() error {
	omnilinkRelayer.rwLock.Lock()
	defer omnilinkRelayer.rwLock.Unlock()
	omnilinkRelayer.symbol2Addr[ebTypes.SYMBOL_BTY] = ebTypes.BTYAddrOmnilink

	helper := dbm.NewListHelper(omnilinkRelayer.db)
	datas := helper.List(tokenSymbol2AddrPrefix, nil, 100, dbm.ListASC)
	if nil == datas {
		return nil
	}

	for _, data := range datas {
		var token2set ebTypes.TokenAddress
		err := omnilinkTypes.Decode(data, &token2set)
		if nil != err {
			return err
		}
		relayerLog.Info("RestoreTokenAddress", "symbol", token2set.Symbol, "address", token2set.Address)
		omnilinkRelayer.symbol2Addr[token2set.Symbol] = token2set.Address
	}
	return nil
}

func (omnilinkRelayer *Relayer4Omnilink) ShowTokenAddress(token2show *ebTypes.TokenAddress) (*ebTypes.TokenAddressArray, error) {
	res := &ebTypes.TokenAddressArray{}

	if len(token2show.Symbol) > 0 {
		data, err := omnilinkRelayer.db.Get(tokenSymbol2AddrKey(token2show.Symbol))
		if err != nil {
			return nil, err
		}
		var token2set ebTypes.TokenAddress
		err = omnilinkTypes.Decode(data, &token2set)
		if nil != err {
			return nil, err
		}
		res.TokenAddress = append(res.TokenAddress, &token2set)
		return res, nil
	}
	helper := dbm.NewListHelper(omnilinkRelayer.db)
	datas := helper.List(tokenSymbol2AddrPrefix, nil, 100, dbm.ListASC)
	if nil == datas {
		return nil, errors.New("Not found")
	}

	for _, data := range datas {

		var token2set ebTypes.TokenAddress
		err := omnilinkTypes.Decode(data, &token2set)
		if nil != err {
			return nil, err
		}
		res.TokenAddress = append(res.TokenAddress, &token2set)

	}
	return res, nil
}

func (omnilinkRelayer *Relayer4Omnilink) setMultiSignAddress(address string) {
	bytes := []byte(address)
	_ = omnilinkRelayer.db.SetSync(multiSignAddressPrefix, bytes)
}

func (omnilinkRelayer *Relayer4Omnilink) getMultiSignAddress() string {
	bytes, _ := omnilinkRelayer.db.Get(multiSignAddressPrefix)
	if 0 == len(bytes) {
		return ""
	}
	return string(bytes)
}

func (omnilinkRelayer *Relayer4Omnilink) storeSymbol2chainName(symbol2Name map[string]string) {
	Symbol2EthChain := &ebTypes.Symbol2EthChain{
		Symbol2Name: symbol2Name,
	}
	data := omnilinkTypes.Encode(Symbol2EthChain)
	_ = omnilinkRelayer.db.SetSync(symbol2Ethchain, data)
}

func (omnilinkRelayer *Relayer4Omnilink) restoreSymbol2chainName() map[string]string {
	data, _ := omnilinkRelayer.db.Get(symbol2Ethchain)
	if 0 == len(data) {
		return make(map[string]string)
	}

	symbol2EthChain := &ebTypes.Symbol2EthChain{}
	if err := omnilinkTypes.Decode(data, symbol2EthChain); nil != err {
		return make(map[string]string)
	}
	return symbol2EthChain.Symbol2Name
}

//判断是否已经被处理，如果能够在数据库中找到该笔交易，则认为已经被处理
func (omnilinkRelayer *Relayer4Omnilink) checkTxProcessed(txhash string) bool {
	key1 := omnilinkTxIsRelayedUnconfirmKey(txhash)
	data, err := omnilinkRelayer.db.Get(key1)
	if 0 != len(data) && nil == err {
		return true
	}

	key2 := omnilinkTxRelayedAlreadyKey(txhash)
	data, err = omnilinkRelayer.db.Get(key2)
	if 0 != len(data) && nil == err {
		return true
	}

	return false
}
