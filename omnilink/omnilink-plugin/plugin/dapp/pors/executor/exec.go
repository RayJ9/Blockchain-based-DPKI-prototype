// Copyright Fuzamei Corp. 2018 All Rights Reserved.
// Use of this source code is governed by a BSD-style
// license that can be found in the LICENSE file.

package executor

import (
	"bytes"
	"encoding/hex"
	"errors"
	"fmt"
	"strings"

	"code.corp.bcollie.net/omnilink/omnilink-base/common/crypto"
	dbm "code.corp.bcollie.net/omnilink/omnilink-base/common/db"
	"code.corp.bcollie.net/omnilink/omnilink-base/types"
	"code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/crypto/bls"
	pty "code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/pors/types"
)

/*
1. 在节点没有新增的情况下，只有现有的几个节点可以报，如果现有的几个节点在genesis时定下来了，那么，应该是从
genesis找到这几个node
2. 每次发处理更新交易的时候，只有本节点可以更新自己的node，或者说，它本就不需要一个pubkey，因为从交易里能找到pubkey
3. 每次更新，我会检查高度，理论上是出块以后再更新
4. 更新的节点power必须带上高度，这里会对高度进行检查
*/

// Exec_Node method
func (p *Pors) Exec_PowerUpdate(nodeUpdate *pty.PorsPowerUpdate, tx *types.Transaction, index int) (*types.Receipt, error) {
	//GetMainHeight
	clog.Error("Exec_PowerUpdate", "address", nodeUpdate.GetAddress(), "power", nodeUpdate.GetPower(), "from", tx.From())
	chainHeight := p.GetHeight()
	if nodeUpdate.Height != chainHeight {
		clog.Error("Pors exec node height mismatch", "node.Height", nodeUpdate.Height, "chain.Height", chainHeight)
		return nil, errors.New("node height must equals to chain height")
	}

	if nodeUpdate.Height < pty.PorsNodeUpdateStartBlock {
		clog.Error("Pors exec node height too low", "node.Height", nodeUpdate.Height, "PorsNodeUpdateStartBlock", pty.PorsNodeUpdateStartBlock)
		return nil, errors.New("node height is too low")
	}

	if !isValidNode(nodeUpdate.GetAddress(), tx.From(), p.GetStateDB()) {
		return nil, errors.New("not valid node")
	}

	if nodeUpdate.GetProof() == nil {
		clog.Info("Pors exec node escaping proof verification, it should can't be omit later versions")
	} else if !isProofValid(chainHeight, nodeUpdate.GetAddress(), nodeUpdate.GetProof(), nodeUpdate.Power) {
		clog.Error("Pors check proof invalid")
		return nil, errors.New("proof invalid")
	}

	// the power should be in range
	if nodeUpdate.GetPower() < 0 {
		return nil, errors.New("validator power must not be negative")
	}
	receipt := &types.Receipt{Ty: types.ExecOk, KV: nil, Logs: nil}
	return receipt, nil
}

// Exec_BlockInfo method
func (p *Pors) Exec_BlockInfo(blockInfo *pty.PorsBlockInfo, tx *types.Transaction, index int) (*types.Receipt, error) {
	// one time record for later nodes update validation
	kvs := []*types.KeyValue{}

	if blockInfo.GetBlock().GetHeader().GetHeight() == 1 {
		key := MavlPorsBlockInfoHeightKey(blockInfo.GetBlock().GetHeader().GetHeight())
		kv := &types.KeyValue{Key: key, Value: types.Encode(blockInfo)}
		kvs = append(kvs, kv)
	}

	receipt := &types.Receipt{Ty: types.ExecOk, KV: kvs, Logs: nil}
	return receipt, nil
}

func isProofValid(chainHeight int64, address string, proof *pty.PowerProof, power int64) bool {
	message := fmt.Sprintf("%s:%d", address, chainHeight)
	clog.Info("Pors check message", "message", message)
	if int(power) != len(proof.PubkeyBytes) {
		clog.Error("Pors check power differs from proof pubkey number", "power", power, "pubkey number", len(proof.PubkeyBytes))
		return false
	}
	bDriver := bls.Driver{}
	pubKeys := []crypto.PubKey{}
	for _, pubBytes := range proof.PubkeyBytes {
		pubStr := hex.EncodeToString(pubBytes)
		if !isPubKeyValid(pubStr) {
			clog.Error("Pors check pub key not valid", "pubkeystr", pubStr)
			return false
		}
		pubKey, err := bDriver.PubKeyFromBytes(pubBytes)
		if err != nil {
			clog.Error("Pors check pub from bytes")
			return false
		}
		pubKeys = append(pubKeys, pubKey)
	}
	/*
		aggKeys, err := bDriver.AggregatePublic(pubKeys)
		if err != nil {
			clog.Error("Pors aggregate public keys error", err)
			return false
		}
	*/
	sig, err := bDriver.SignatureFromBytes(proof.AggregatedSig)
	if err != nil {
		clog.Error("Pors get agg sig from bytes", err)
		return false
	}

	err = bDriver.VerifyAggregatedOne(pubKeys, []byte(message), sig)
	if err != nil {
		clog.Error("Pors verify message with signature", err)
		return false
	}

	return true
}

func isPubKeyValid(pubStr string) bool {
	// should check from KV
	return true
}

func isValidNode(updateAddr string, txAddr string, db dbm.KV) bool {
	// find block info of height 0, then compare all the validators
	key := MavlPorsBlockInfoHeightKey(1)
	value, err := db.Get([]byte(key))
	if err != nil {
		clog.Error("GetBlockInfo failed")
		return false
	}

	clog.Error("isValidNode", "updateAddr", updateAddr, "len", len(updateAddr))
	var item pty.PorsBlockInfo
	err = types.Decode(value, &item)
	if err != nil {
		clog.Error("decodePorsBlockInfo failed")
		return false
	}

	if updateAddr != txAddr {
		clog.Error("update address not equal to tx address")
		return false
	}

	updateBytes, err := hex.DecodeString(strings.TrimPrefix(updateAddr, "0x"))
	if err != nil {
		clog.Error("hex decode updateAddr failed")
		return false
	}

	for i, v := range item.State.Validators.Validators {
		clog.Error("isValidNode", "i", i, "address", v.Address, "len", len(v.Address))
		vAddr, err := hex.DecodeString(strings.TrimPrefix(v.Address, "0x"))
		if err != nil {
			clog.Error("hex decode validator error")
			return false
		}
		if bytes.Equal(updateBytes, vAddr) {
			return true
		}
	}

	return false
}
