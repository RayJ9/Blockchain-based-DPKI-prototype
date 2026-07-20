// Copyright Fuzamei Corp. 2018 All Rights Reserved.
// Use of this source code is governed by a BSD-style
// license that can be found in the LICENSE file.

package executor

import (
	"code.corp.bcollie.net/omnilink/omnilink-base/types"
	pty "code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/pors/types"
)

// Query_GetQbftNodeByHeight method
func (val *Pors) Query_GetPorsNodeUpdateByHeight(in *pty.ReqPorsNodes) (types.Message, error) {
	clog.Error("Query_GetPorsNodeUpdateByHeight")
	height := in.GetHeight()

	if height <= 0 {
		return nil, types.ErrInvalidParam
	}
	key := CalcPorsNodeUpdateKey()
	values, err := val.GetLocalDB().List(key, nil, 0, 1)
	if err != nil {
		clog.Error("Query_GetPorsNodeUpdateByHeight", "getlocaldb error", err)
		return nil, err
	}
	if len(values) == 0 {
		clog.Error("Query_GetPorsNodeUpdateByHeight", "getlocaldb not found", 0)
		return nil, types.ErrNotFound
	}
	clog.Error("Query_GetPorsNodeUpdateByHeight", "len values", len(values))

	reply := &pty.PorsNodes{}
	for _, porsNodeByte := range values {
		var power pty.PorsNodePower
		clog.Error("Query_GetPorsNodeUpdateByHeight", "bytes", porsNodeByte)
		err := types.Decode(porsNodeByte, &power)
		if err != nil {
			clog.Error("Query_GetPorsNodeUpdateByHeight", "porsNodeByte decode error", err)
			return nil, err
		}
		reply.Nodes = append(reply.Nodes, &power)
	}
	return reply, nil
}

// Query_GetBlockInfoByHeight method
func (val *Pors) Query_GetBlockInfoByHeight(in *pty.ReqPorsBlockInfo) (types.Message, error) {
	height := in.GetHeight()

	if height <= 0 {
		return nil, types.ErrInvalidParam
	}
	key := CalcPorsNodeBlockInfoHeightKey(height)
	value, err := val.GetLocalDB().Get(key)
	if err != nil {
		return nil, err
	}
	if len(value) == 0 {
		return nil, types.ErrNotFound
	}

	reply := &pty.PorsBlockInfo{}
	err = types.Decode(value, reply)
	if err != nil {
		return nil, err
	}
	return reply, nil
}

// Query_GetCurrentState method
func (val *Pors) Query_GetCurrentState(in *types.ReqNil) (types.Message, error) {
	return val.GetAPI().QueryConsensusFunc("pors", "CurrentState", &types.ReqNil{})
}
