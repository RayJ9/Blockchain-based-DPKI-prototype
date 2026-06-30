package executor

import (
	"code.corp.bcollie.net/omnilink/omnilink-base/common/crypto"
	log "code.corp.bcollie.net/omnilink/omnilink-base/common/log/log15"
	drivers "code.corp.bcollie.net/omnilink/omnilink-base/system/dapp"
	"code.corp.bcollie.net/omnilink/omnilink-base/types"
	"code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/crypto/bls"
	rolluptypes "code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/rollup/types"
)

/*
 * 执行器相关定义
 * 重载基类相关接口
 */

var (
	//日志
	elog = log.New("module", "rollup.executor")
)

var driverName = rolluptypes.RollupX
var blsDriver, _ = crypto.Load(bls.Name, -1)

// Init register dapp
func Init(name string, cfg *types.OmnilinkConfig, sub []byte) {
	drivers.Register(cfg, GetName(), newRollup, cfg.GetDappFork(driverName, "Enable"))
	InitExecType()
}

// InitExecType Init Exec Type
func InitExecType() {
	ety := types.LoadExecutorType(driverName)
	ety.InitFuncList(types.ListMethod(&rollup{}))
}

type rollup struct {
	drivers.DriverBase
}

func newRollup() drivers.Driver {
	t := &rollup{}
	t.SetChild(t)
	t.SetExecutorType(types.LoadExecutorType(driverName))
	return t
}

// GetName get driver name
func GetName() string {
	return newRollup().GetName()
}

func (r *rollup) GetDriverName() string {
	return driverName
}
