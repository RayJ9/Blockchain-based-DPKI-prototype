// Copyright Fuzamei Corp. 2018 All Rights Reserved.
// Use of this source code is governed by a BSD-style
// license that can be found in the LICENSE file.

package executor

import (
	log "code.corp.bcollie.net/omnilink/omnilink-base/common/log/log15"
	drivers "code.corp.bcollie.net/omnilink/omnilink-base/system/dapp"
	"code.corp.bcollie.net/omnilink/omnilink-base/types"
)

var clog = log.New("module", "execs.hashlock")

const minLockTime = 60

var driverName = "hashlock"

// Init hashlock
func Init(name string, cfg *types.OmnilinkConfig, sub []byte) {
	drivers.Register(cfg, GetName(), newHashlock, cfg.GetDappFork(driverName, "Enable"))
	InitExecType()
}

//InitExecType ...
func InitExecType() {
	ety := types.LoadExecutorType(driverName)
	ety.InitFuncList(types.ListMethod(&Hashlock{}))
}

// GetName for hashlock
func GetName() string {
	return newHashlock().GetName()
}

// Hashlock driver
type Hashlock struct {
	drivers.DriverBase
}

func newHashlock() drivers.Driver {
	h := &Hashlock{}
	h.SetChild(h)
	h.SetExecutorType(types.LoadExecutorType(driverName))
	return h
}

// GetDriverName driverName
func (h *Hashlock) GetDriverName() string {
	return driverName
}

// CheckTx nil
func (h *Hashlock) CheckTx(tx *types.Transaction, index int) error {
	return nil
}

// CheckReceiptExecOk return true to check if receipt ty is ok
func (h *Hashlock) CheckReceiptExecOk() bool {
	return true
}
