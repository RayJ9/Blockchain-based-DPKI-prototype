// Copyright Fuzamei Corp. 2018 All Rights Reserved.
// Use of this source code is governed by a BSD-style
// license that can be found in the LICENSE file.

package types

import (
	"encoding/hex"
	"encoding/json"

	"code.corp.bcollie.net/omnilink/omnilink-base/common/address"

	log "code.corp.bcollie.net/omnilink/omnilink-base/common/log/log15"
	"code.corp.bcollie.net/omnilink/omnilink-base/types"
)

var tlog = log.New("module", "exectype."+ValNodeX)

func init() {
	types.AllowUserExec = append(types.AllowUserExec, []byte(ValNodeX))
	types.RegFork(ValNodeX, InitFork)
	types.RegExec(ValNodeX, InitExecutor)
}

//InitFork ...
func InitFork(cfg *types.OmnilinkConfig) {
	cfg.RegisterDappFork(ValNodeX, "Enable", 0)
}

//InitExecutor ...
func InitExecutor(cfg *types.OmnilinkConfig) {
	types.RegistorExecutor(ValNodeX, NewType(cfg))
}

// ValNodeType stuct
type ValNodeType struct {
	types.ExecTypeBase
}

// NewType method
func NewType(cfg *types.OmnilinkConfig) *ValNodeType {
	c := &ValNodeType{}
	c.SetChild(c)
	c.SetConfig(cfg)
	return c
}

// GetName 获取执行器名称
func (t *ValNodeType) GetName() string {
	return ValNodeX
}

// GetPayload method
func (t *ValNodeType) GetPayload() types.Message {
	return &ValNodeAction{}
}

// GetTypeMap method
func (t *ValNodeType) GetTypeMap() map[string]int32 {
	return map[string]int32{
		"Node":      ValNodeActionUpdate,
		"BlockInfo": ValNodeActionBlockInfo,
	}
}

// GetLogMap method
func (t *ValNodeType) GetLogMap() map[int64]*types.LogInfo {
	return map[int64]*types.LogInfo{}
}

// CreateTx ...
func (t *ValNodeType) CreateTx(action string, message json.RawMessage) (*types.Transaction, error) {
	tlog.Debug("valnode.CreateTx", "action", action)
	cfg := t.GetConfig()
	if action == ActionNodeUpdate {
		var param NodeUpdateTx
		err := json.Unmarshal(message, &param)
		if err != nil {
			tlog.Error("valnode.CreateTx", "err", err)
			return nil, types.ErrInvalidParam
		}
		return CreateNodeUpdateTx(cfg, &param)
	}
	return nil, types.ErrNotSupport
}

// CreateNodeUpdateTx ...
func CreateNodeUpdateTx(cfg *types.OmnilinkConfig, parm *NodeUpdateTx) (*types.Transaction, error) {
	if parm == nil {
		tlog.Error("CreateNodeUpdateTx", "parm", parm)
		return nil, types.ErrInvalidParam
	}

	pubkeybyte, err := hex.DecodeString(parm.PubKey)
	if err != nil {
		return nil, err
	}
	v := &ValNode{
		PubKey: pubkeybyte,
		Power:  parm.Power,
	}
	update := &ValNodeAction{
		Ty:    ValNodeActionUpdate,
		Value: &ValNodeAction_Node{v},
	}

	execName := cfg.ExecName(ValNodeX)
	tx := &types.Transaction{
		Execer:  []byte(execName),
		Payload: types.Encode(update),
		To:      address.ExecAddress(execName),
	}
	tx, err = types.FormatTx(cfg, execName, tx)
	if err != nil {
		return nil, err
	}
	return tx, nil
}
