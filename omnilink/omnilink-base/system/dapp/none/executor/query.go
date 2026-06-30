// Copyright Fuzamei Corp. 2018 All Rights Reserved.
// Use of this source code is governed by a BSD-style
// license that can be found in the LICENSE file.

package executor

import (
	"encoding/hex"

	ntypes "code.corp.bcollie.net/omnilink/omnilink-base/system/dapp/none/types"
	"code.corp.bcollie.net/omnilink/omnilink-base/types"
)

// Query_GetDelayTxInfo query delay tx delay begin height
func (n *None) Query_GetDelayTxInfo(req *types.ReqBytes) (types.Message, error) {

	if len(req.GetData()) == 0 {
		return nil, types.ErrInvalidParam
	}

	val, err := n.GetStateDB().Get(formatDelayTxKey(req.GetData()))
	if err != nil {
		eLog.Error("Query_GetDelayBeginHeight", "txHash", hex.EncodeToString(req.GetData()), "get db err", err)
		return nil, types.ErrGetStateDB
	}
	info := &ntypes.CommitDelayTxLog{}

	err = types.Decode(val, info)
	if err != nil {
		eLog.Error("Query_GetDelayBeginHeight", "txHash", hex.EncodeToString(req.GetData()), "get db err", err)
		return nil, types.ErrDecode
	}
	return info, nil
}
