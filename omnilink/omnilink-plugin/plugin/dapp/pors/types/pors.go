// Copyright Fuzamei Corp. 2018 All Rights Reserved.
// Use of this source code is governed by a BSD-style
// license that can be found in the LICENSE file.

package types

import (
	"encoding/json"

	log "code.corp.bcollie.net/omnilink/omnilink-base/common/log/log15"
	"code.corp.bcollie.net/omnilink/omnilink-base/types"
)

var tlog = log.New("module", "exectype."+PorsX)

func init() {
	types.AllowUserExec = append(types.AllowUserExec, []byte(PorsX))
	types.RegFork(PorsX, InitFork)
	types.RegExec(PorsX, InitExecutor)
}

//InitFork ...
func InitFork(cfg *types.OmnilinkConfig) {
	cfg.RegisterDappFork(PorsX, "Enable", 0)
}

//InitExecutor ...
func InitExecutor(cfg *types.OmnilinkConfig) {
	types.RegistorExecutor(PorsX, NewType(cfg))
}

// PorsType stuct
type PorsType struct {
	types.ExecTypeBase
}

// NewType method
func NewType(cfg *types.OmnilinkConfig) *PorsType {
	c := &PorsType{}
	c.SetChild(c)
	c.SetConfig(cfg)
	return c
}

// GetName 获取执行器名称
func (t *PorsType) GetName() string {
	return PorsX
}

// GetPayload method
func (t *PorsType) GetPayload() types.Message {
	return &PorsExecAction{}
}

// GetTypeMap method
func (t *PorsType) GetTypeMap() map[string]int32 {
	return map[string]int32{
		ActionPowerUpdate: PorsActionPowerUpdate,
		ActionBlockInfo:   PorsActionBlockInfo,
	}
}

// GetLogMap method
func (t *PorsType) GetLogMap() map[int64]*types.LogInfo {
	return map[int64]*types.LogInfo{}
}

// CreateTx ...
func (t *PorsType) CreateTx(action string, message json.RawMessage) (*types.Transaction, error) {
	return nil, nil
}
