// Copyright Fuzamei Corp. 2018 All Rights Reserved.
// Use of this source code is governed by a BSD-style
// license that can be found in the LICENSE file.

package executor

import (
	"code.corp.bcollie.net/omnilink/omnilink-base/common"
	nty "code.corp.bcollie.net/omnilink/omnilink-base/system/dapp/none/types"
	"code.corp.bcollie.net/omnilink/omnilink-base/types"
)

// Exec_CommitDelayTx exec commit dealy transaction
func (n *None) Exec_CommitDelayTx(commit *nty.CommitDelayTx, tx *types.Transaction, index int) (*types.Receipt, error) {

	receipt := &types.Receipt{Ty: types.ExecOk}
	delayInfo := &nty.CommitDelayTxLog{}
	delayTx := &types.Transaction{}
	txByte, err := common.FromHex(commit.GetDelayTx())
	if err != nil || types.Decode(txByte, delayTx) != nil {
		return nil, errDecodeDelayTx
	}
	delayTxHash := delayTx.Hash()
	cfg := n.GetAPI().GetConfig()
	if cfg.IsDappFork(n.GetHeight(), nty.NoneX, nty.ForkUseTimeDelay) {
		delayInfo.DelayBeginTimestamp = n.GetBlockTime()
	} else {
		delayInfo.DelayBeginHeight = n.GetHeight()
	}

	delayInfo.Submitter = tx.From()
	receipt.KV = append(receipt.KV,
		&types.KeyValue{Key: formatDelayTxKey(delayTxHash), Value: types.Encode(delayInfo)})

	// 交易哈希只做回执展示信息，不需要保存到链上
	delayInfo.DelayTxHash = common.ToHex(delayTxHash)
	receipt.Logs = append(receipt.Logs,
		&types.ReceiptLog{Ty: nty.TyCommitDelayTxLog, Log: types.Encode(delayInfo)})

	return receipt, nil
}
