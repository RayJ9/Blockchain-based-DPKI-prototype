package executor

import (
	"strconv"

	"code.corp.bcollie.net/omnilink/omnilink-base/types"
	x2eTy "code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/x2ethereum/types"
)

/*
 * 实现交易相关数据本地执行，数据不上链
 * 非关键数据，本地存储(localDB), 用于辅助查询，效率高
 */

func (x *x2ethereum) ExecLocal_Eth2OmnilinkLock(payload *x2eTy.Eth2Omnilink, tx *types.Transaction, receiptData *types.ReceiptData, index int) (*types.LocalDBSet, error) {
	set, err := x.execLocal(receiptData)
	if err != nil {
		return set, err
	}
	return x.addAutoRollBack(tx, set.KV), nil
}

func (x *x2ethereum) ExecLocal_Eth2OmnilinkBurn(payload *x2eTy.Eth2Omnilink, tx *types.Transaction, receiptData *types.ReceiptData, index int) (*types.LocalDBSet, error) {
	set, err := x.execLocal(receiptData)
	if err != nil {
		return set, err
	}
	return x.addAutoRollBack(tx, set.KV), nil
}

func (x *x2ethereum) ExecLocal_OmnilinkToEthBurn(payload *x2eTy.OmnilinkToEth, tx *types.Transaction, receiptData *types.ReceiptData, index int) (*types.LocalDBSet, error) {
	set, err := x.execLocal(receiptData)
	if err != nil {
		return set, err
	}
	return x.addAutoRollBack(tx, set.KV), nil
}

func (x *x2ethereum) ExecLocal_OmnilinkToEthLock(payload *x2eTy.OmnilinkToEth, tx *types.Transaction, receiptData *types.ReceiptData, index int) (*types.LocalDBSet, error) {
	set, err := x.execLocal(receiptData)
	if err != nil {
		return set, err
	}
	return x.addAutoRollBack(tx, set.KV), nil
}

func (x *x2ethereum) ExecLocal_AddValidator(payload *x2eTy.MsgValidator, tx *types.Transaction, receiptData *types.ReceiptData, index int) (*types.LocalDBSet, error) {
	dbSet := &types.LocalDBSet{}
	//implement code
	return x.addAutoRollBack(tx, dbSet.KV), nil
}

func (x *x2ethereum) ExecLocal_RemoveValidator(payload *x2eTy.MsgValidator, tx *types.Transaction, receiptData *types.ReceiptData, index int) (*types.LocalDBSet, error) {
	dbSet := &types.LocalDBSet{}
	//implement code
	return x.addAutoRollBack(tx, dbSet.KV), nil
}

func (x *x2ethereum) ExecLocal_ModifyPower(payload *x2eTy.MsgValidator, tx *types.Transaction, receiptData *types.ReceiptData, index int) (*types.LocalDBSet, error) {
	dbSet := &types.LocalDBSet{}
	//implement code
	return x.addAutoRollBack(tx, dbSet.KV), nil
}

func (x *x2ethereum) ExecLocal_SetConsensusThreshold(payload *x2eTy.MsgConsensusThreshold, tx *types.Transaction, receiptData *types.ReceiptData, index int) (*types.LocalDBSet, error) {
	dbSet := &types.LocalDBSet{}
	//implement code
	return x.addAutoRollBack(tx, dbSet.KV), nil
}

//设置自动回滚
func (x *x2ethereum) addAutoRollBack(tx *types.Transaction, kv []*types.KeyValue) *types.LocalDBSet {
	dbSet := &types.LocalDBSet{}
	dbSet.KV = x.AddRollbackKV(tx, tx.Execer, kv)
	return dbSet
}

func (x *x2ethereum) execLocal(receiptData *types.ReceiptData) (*types.LocalDBSet, error) {
	dbSet := &types.LocalDBSet{}
	for _, log := range receiptData.Logs {
		switch log.Ty {
		case x2eTy.TyEth2OmnilinkLog:
			var receiptEth2Omnilink x2eTy.ReceiptEth2Omnilink
			err := types.Decode(log.Log, &receiptEth2Omnilink)
			if err != nil {
				return nil, err
			}

			nb, err := x.GetLocalDB().Get(x2eTy.CalTokenSymbolTotalLockOrBurnAmount(receiptEth2Omnilink.IssuerDotSymbol, receiptEth2Omnilink.TokenAddress, x2eTy.DirEth2Omnilink, "lock"))
			if err != nil && err != types.ErrNotFound {
				return nil, err
			}
			var now x2eTy.ReceiptQuerySymbolAssetsByTxType
			err = types.Decode(nb, &now)
			if err != nil {
				return nil, err
			}
			preAmount, _ := strconv.ParseFloat(x2eTy.TrimZeroAndDot(now.TotalAmount), 64)
			nowAmount, _ := strconv.ParseFloat(x2eTy.TrimZeroAndDot(receiptEth2Omnilink.Amount), 64)
			TokenAssetsByTxTypeBytes := types.Encode(&x2eTy.ReceiptQuerySymbolAssetsByTxType{
				TokenSymbol: receiptEth2Omnilink.IssuerDotSymbol,
				TxType:      "lock",
				TotalAmount: strconv.FormatFloat(preAmount+nowAmount, 'f', 4, 64),
				Direction:   1,
			})
			dbSet.KV = append(dbSet.KV, &types.KeyValue{
				Key:   x2eTy.CalTokenSymbolTotalLockOrBurnAmount(receiptEth2Omnilink.IssuerDotSymbol, receiptEth2Omnilink.TokenAddress, x2eTy.DirEth2Omnilink, "lock"),
				Value: TokenAssetsByTxTypeBytes,
			})

			nb, err = x.GetLocalDB().Get(x2eTy.CalTokenSymbolToTokenAddress(receiptEth2Omnilink.IssuerDotSymbol))
			if err != nil && err != types.ErrNotFound {
				return nil, err
			}
			var t x2eTy.ReceiptTokenToTokenAddress
			err = types.Decode(nb, &t)
			if err != nil {
				return nil, err
			}
			var exist bool
			for _, addr := range t.TokenAddress {
				if addr == receiptEth2Omnilink.TokenAddress {
					exist = true
				}
			}
			if !exist {
				t.TokenAddress = append(t.TokenAddress, receiptEth2Omnilink.TokenAddress)
			}
			TokenToTokenAddressBytes := types.Encode(&x2eTy.ReceiptTokenToTokenAddress{
				TokenAddress: t.TokenAddress,
			})
			dbSet.KV = append(dbSet.KV, &types.KeyValue{
				Key:   x2eTy.CalTokenSymbolToTokenAddress(receiptEth2Omnilink.IssuerDotSymbol),
				Value: TokenToTokenAddressBytes,
			})
		case x2eTy.TyWithdrawEthLog:
			var receiptEth2Omnilink x2eTy.ReceiptEth2Omnilink
			err := types.Decode(log.Log, &receiptEth2Omnilink)
			if err != nil {
				return nil, err
			}

			nb, err := x.GetLocalDB().Get(x2eTy.CalTokenSymbolTotalLockOrBurnAmount(receiptEth2Omnilink.IssuerDotSymbol, receiptEth2Omnilink.TokenAddress, x2eTy.DirEth2Omnilink, "withdraw"))
			if err != nil && err != types.ErrNotFound {
				return nil, err
			}
			var now x2eTy.ReceiptQuerySymbolAssetsByTxType
			err = types.Decode(nb, &now)
			if err != nil {
				return nil, err
			}

			preAmount, _ := strconv.ParseFloat(x2eTy.TrimZeroAndDot(now.TotalAmount), 64)
			nowAmount, _ := strconv.ParseFloat(x2eTy.TrimZeroAndDot(receiptEth2Omnilink.Amount), 64)
			TokenAssetsByTxTypeBytes := types.Encode(&x2eTy.ReceiptQuerySymbolAssetsByTxType{
				TokenSymbol: receiptEth2Omnilink.IssuerDotSymbol,
				TxType:      "withdraw",
				TotalAmount: strconv.FormatFloat(preAmount+nowAmount, 'f', 4, 64),
				Direction:   2,
			})
			dbSet.KV = append(dbSet.KV, &types.KeyValue{
				Key:   x2eTy.CalTokenSymbolTotalLockOrBurnAmount(receiptEth2Omnilink.IssuerDotSymbol, receiptEth2Omnilink.TokenAddress, x2eTy.DirEth2Omnilink, "withdraw"),
				Value: TokenAssetsByTxTypeBytes,
			})
		case x2eTy.TyOmnilinkToEthLog:
			var receiptOmnilinkToEth x2eTy.ReceiptOmnilinkToEth
			err := types.Decode(log.Log, &receiptOmnilinkToEth)
			if err != nil {
				return nil, err
			}

			nb, err := x.GetLocalDB().Get(x2eTy.CalTokenSymbolTotalLockOrBurnAmount(receiptOmnilinkToEth.IssuerDotSymbol, receiptOmnilinkToEth.TokenContract, x2eTy.DirOmnilinkToEth, "lock"))
			if err != nil && err != types.ErrNotFound {
				return nil, err
			}
			var now x2eTy.ReceiptQuerySymbolAssetsByTxType
			err = types.Decode(nb, &now)
			if err != nil {
				return nil, err
			}

			preAmount, _ := strconv.ParseFloat(x2eTy.TrimZeroAndDot(now.TotalAmount), 64)
			nowAmount, _ := strconv.ParseFloat(x2eTy.TrimZeroAndDot(receiptOmnilinkToEth.Amount), 64)
			TokenAssetsByTxTypeBytes := types.Encode(&x2eTy.ReceiptQuerySymbolAssetsByTxType{
				TokenSymbol: receiptOmnilinkToEth.IssuerDotSymbol,
				TxType:      "lock",
				TotalAmount: strconv.FormatFloat(preAmount+nowAmount, 'f', 4, 64),
				Direction:   1,
			})
			dbSet.KV = append(dbSet.KV, &types.KeyValue{
				Key:   x2eTy.CalTokenSymbolTotalLockOrBurnAmount(receiptOmnilinkToEth.IssuerDotSymbol, receiptOmnilinkToEth.TokenContract, x2eTy.DirOmnilinkToEth, "lock"),
				Value: TokenAssetsByTxTypeBytes,
			})
		case x2eTy.TyWithdrawOmnilinkLog:
			var receiptOmnilinkToEth x2eTy.ReceiptOmnilinkToEth
			err := types.Decode(log.Log, &receiptOmnilinkToEth)
			if err != nil {
				return nil, err
			}

			nb, err := x.GetLocalDB().Get(x2eTy.CalTokenSymbolTotalLockOrBurnAmount(receiptOmnilinkToEth.IssuerDotSymbol, receiptOmnilinkToEth.TokenContract, x2eTy.DirOmnilinkToEth, ""))
			if err != nil && err != types.ErrNotFound {
				return nil, err
			}
			var now x2eTy.ReceiptQuerySymbolAssetsByTxType
			err = types.Decode(nb, &now)
			if err != nil {
				return nil, err
			}

			preAmount, _ := strconv.ParseFloat(x2eTy.TrimZeroAndDot(now.TotalAmount), 64)
			nowAmount, _ := strconv.ParseFloat(x2eTy.TrimZeroAndDot(receiptOmnilinkToEth.Amount), 64)
			TokenAssetsByTxTypeBytes := types.Encode(&x2eTy.ReceiptQuerySymbolAssetsByTxType{
				TokenSymbol: receiptOmnilinkToEth.IssuerDotSymbol,
				TxType:      "withdraw",
				TotalAmount: strconv.FormatFloat(preAmount+nowAmount, 'f', 4, 64),
				Direction:   2,
			})
			dbSet.KV = append(dbSet.KV, &types.KeyValue{
				Key:   x2eTy.CalTokenSymbolTotalLockOrBurnAmount(receiptOmnilinkToEth.IssuerDotSymbol, receiptOmnilinkToEth.TokenContract, x2eTy.DirOmnilinkToEth, "withdraw"),
				Value: TokenAssetsByTxTypeBytes,
			})
		default:
			continue
		}
	}
	return dbSet, nil
}
