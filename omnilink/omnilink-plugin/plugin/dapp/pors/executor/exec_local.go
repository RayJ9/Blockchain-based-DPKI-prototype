// Copyright Fuzamei Corp. 2018 All Rights Reserved.
// Use of this source code is governed by a BSD-style
// license that can be found in the LICENSE file.

package executor

import (
	"bytes"
	"encoding/binary"
	"strings"

	"code.corp.bcollie.net/omnilink/omnilink-base/types"
	pty "code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/pors/types"
)

// ExecLocal_Node method
func (val *Pors) ExecLocal_PowerUpdate(node *pty.PorsPowerUpdate, tx *types.Transaction, receipt *types.ReceiptData, index int) (*types.LocalDBSet, error) {
	set := &types.LocalDBSet{}
	clog.Error("ExecLocal_PowerUpdate", "address", node.GetAddress(), "power", node.GetPower())

	usedAddr := strings.ToUpper(strings.TrimPrefix(node.Address, "0x"))

	key := CalcPorsNodeUpdateAddressKey(usedAddr)
	clog.Error("ExecLocal_PowerUpdate", "used address in key", usedAddr, "key", key)
	value, err := val.GetLocalDB().Get(key)
	if err != nil {
		clog.Error("ExecLocal_PowerUpdate get localdb err", "error", err)
		return nil, err
	}
	var oldItem pty.PorsNodePower
	err = types.Decode(value, &oldItem)
	if err != nil {
		clog.Error("ExecLocal_PowerUpdate decode value", "error", err)
		return nil, err
	}
	clog.Error("ExecLocal_PowerUpdate found the old Item")
	// find this height, if not exist update, else omit it
	// not sure this height is same as exec height
	/*
		updatedInThisHeightKey := CalcPorsNodeUpdateAddressHeightKey(node.Address, val.GetHeight())
		updatedThisHeight := false

		clog.Error("ExecLocal_PowerUpdate before check height once")
		value, err = val.GetLocalDB().Get(updatedInThisHeightKey)
		if err == nil {
			exist, err := bytesToBool(value)
			if err != nil {
				return nil, err
			}
			updatedThisHeight = exist
		}
		if updatedThisHeight {
			return nil, nil
		}
		clog.Error("ExecLocal_PowerUpdate after check height once")

		//updatedKV := &types.KeyValue{Key: updatedInThisHeightKey, Value: boolToBytes(true)}
	*/
	item := &pty.PorsNodePower{
		Address: oldItem.Address,
		Power:   oldItem.Power + node.Power,
	}
	clog.Error("ExecLocal_PowerUpdate updated value", "address", item.Address, "power", item.Power, "bytes", types.Encode(item))
	set.KV = append(set.KV, &types.KeyValue{Key: key, Value: types.Encode(item)})

	return set, nil
}

// ExecLocal_BlockInfo method
func (val *Pors) ExecLocal_BlockInfo(blockInfo *pty.PorsBlockInfo, tx *types.Transaction, receipt *types.ReceiptData, index int) (*types.LocalDBSet, error) {
	clog.Error("ExecLocal_BlockInfo")
	set := &types.LocalDBSet{}
	key := CalcPorsNodeBlockInfoHeightKey(val.GetHeight())
	set.KV = append(set.KV, &types.KeyValue{Key: key, Value: types.Encode(blockInfo)})

	if blockInfo.GetBlock().GetHeader().Height == 1 {
		for _, v := range blockInfo.GetState().GetValidators().GetValidators() {
			key := CalcPorsNodeUpdateAddressKey(v.Address)
			clog.Error("ExecLocal_BlockInfo", "val address", v.Address, "calc key", key)
			powerValue := &pty.PorsNodePower{
				Address: v.GetAddress(),
				Power:   v.GetVotingPower(),
			}
			clog.Error("ExecLocal_BlockInfo", "address", powerValue.Address, "bytes", types.Encode(powerValue))
			keyV := &types.KeyValue{Key: key, Value: types.Encode(powerValue)}
			set.KV = append(set.KV, keyV)
		}
	}

	return set, nil
}

func boolToBytes(b bool) []byte {
	var buf bytes.Buffer
	binary.Write(&buf, binary.LittleEndian, b)

	return buf.Bytes()
}

func bytesToBool(data []byte) (bool, error) {
	var b bool
	buf := bytes.NewReader(data)
	err := binary.Read(buf, binary.LittleEndian, &b)
	return b, err
}
