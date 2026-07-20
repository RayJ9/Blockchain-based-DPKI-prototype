// Copyright Fuzamei Corp. 2018 All Rights Reserved.
// Use of this source code is governed by a BSD-style
// license that can be found in the LICENSE file.

package types

import (
	"encoding/json"

	"code.corp.bcollie.net/omnilink/omnilink-base/common/address"
	log "code.corp.bcollie.net/omnilink/omnilink-base/common/log/log15"
	"code.corp.bcollie.net/omnilink/omnilink-base/types"
)

var tlog = log.New("module", "exectype."+QbftNodeX)

func init() {
	types.AllowUserExec = append(types.AllowUserExec, []byte(QbftNodeX))
	types.RegFork(QbftNodeX, InitFork)
	types.RegExec(QbftNodeX, InitExecutor)
}

//InitFork ...
func InitFork(cfg *types.OmnilinkConfig) {
	cfg.RegisterDappFork(QbftNodeX, "Enable", 0)
}

//InitExecutor ...
func InitExecutor(cfg *types.OmnilinkConfig) {
	types.RegistorExecutor(QbftNodeX, NewType(cfg))
}

// QbftNodeType stuct
type QbftNodeType struct {
	types.ExecTypeBase
}

// NewType method
func NewType(cfg *types.OmnilinkConfig) *QbftNodeType {
	c := &QbftNodeType{}
	c.SetChild(c)
	c.SetConfig(cfg)
	return c
}

// GetName 获取执行器名称
func (t *QbftNodeType) GetName() string {
	return QbftNodeX
}

// GetPayload method
func (t *QbftNodeType) GetPayload() types.Message {
	return &QbftNodeAction{}
}

// GetTypeMap method
func (t *QbftNodeType) GetTypeMap() map[string]int32 {
	return map[string]int32{
		"Node":      QbftNodeActionUpdate,
		"BlockInfo": QbftNodeActionBlockInfo,
	}
}

// GetLogMap method
func (t *QbftNodeType) GetLogMap() map[int64]*types.LogInfo {
	return map[int64]*types.LogInfo{}
}

// CreateTx ...
func (t *QbftNodeType) CreateTx(action string, message json.RawMessage) (*types.Transaction, error) {
	tlog.Debug("qbftNode.CreateTx", "action", action)
	cfg := t.GetConfig()
	if action == ActionNodeUpdate {
		var param NodeUpdateTx
		err := json.Unmarshal(message, &param)
		if err != nil {
			tlog.Error("qbftNode.CreateTx", "err", err)
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

	v := &QbftNode{
		PubKey: parm.PubKey,
		Power:  parm.Power,
	}
	update := &QbftNodeAction{
		Ty:    QbftNodeActionUpdate,
		Value: &QbftNodeAction_Node{v},
	}

	execName := cfg.ExecName(QbftNodeX)
	tx := &types.Transaction{
		Execer:  []byte(execName),
		Payload: types.Encode(update),
		To:      address.ExecAddress(execName),
	}
	tx, err := types.FormatTx(cfg, execName, tx)
	if err != nil {
		return nil, err
	}
	return tx, nil
}
