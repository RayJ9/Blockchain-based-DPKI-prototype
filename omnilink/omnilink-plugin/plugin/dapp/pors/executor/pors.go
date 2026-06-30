// Copyright Fuzamei Corp. 2018 All Rights Reserved.
// Use of this source code is governed by a BSD-style
// license that can be found in the LICENSE file.

package executor

import (
	"fmt"

	"code.corp.bcollie.net/omnilink/omnilink-base/common/address"
	log "code.corp.bcollie.net/omnilink/omnilink-base/common/log/log15"
	drivers "code.corp.bcollie.net/omnilink/omnilink-base/system/dapp"
	"code.corp.bcollie.net/omnilink/omnilink-base/types"
)

var clog = log.New("module", "execs.pors")
var driverName = "pors"

// Init method
func Init(name string, cfg *types.OmnilinkConfig, sub []byte) {
	clog.Debug("register pors execer")
	drivers.Register(cfg, GetName(), newPors, cfg.GetDappFork(driverName, "Enable"))
	InitExecType()
}

//InitExecType ...
func InitExecType() {
	ety := types.LoadExecutorType(driverName)
	ety.InitFuncList(types.ListMethod(&Pors{}))
}

// GetName method
func GetName() string {
	return newPors().GetName()
}

// Pors strucyt
type Pors struct {
	drivers.DriverBase
}

func newPors() drivers.Driver {
	n := &Pors{}
	n.SetChild(n)
	n.SetIsFree(true)
	n.SetExecutorType(types.LoadExecutorType(driverName))
	return n
}

// GetDriverName method
func (pors *Pors) GetDriverName() string {
	return driverName
}

// CheckTx method
func (pors *Pors) CheckTx(tx *types.Transaction, index int) error {
	return nil
}

func CalcPorsNodeUpdateAddressKey(addr string) []byte {
	return []byte(fmt.Sprintf("LODB-pors-Update:%s", address.FormatAddrKey(addr)))
}

func CalcPorsNodeUpdateAddressHeightKey(addr string, height int64) []byte {
	return []byte(fmt.Sprintf("LODB-pors-Update:%s:%18d", address.FormatAddrKey(addr)))
}

func CalcPorsNodeUpdateKey() []byte {
	return []byte(fmt.Sprintf("LODB-pors-Update:"))
}

// CalcPorsNodeBlockInfoHeightKey method
func CalcPorsNodeBlockInfoHeightKey(height int64) []byte {
	return []byte(fmt.Sprintf("LODB-pors-BlockInfo:%18d", height))
}

func MavlPorsBlockInfoHeightKey(height int64) []byte {
	return []byte(fmt.Sprintf("mavl-pors-BlockInfo:%18d", height))
}

// CheckReceiptExecOk return true to check if receipt ty is ok
func (pors *Pors) CheckReceiptExecOk() bool {
	return true
}
