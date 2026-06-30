package executor

import (
	log "code.corp.bcollie.net/omnilink/omnilink-base/common/log/log15"
	drivers "code.corp.bcollie.net/omnilink/omnilink-base/system/dapp"
	"code.corp.bcollie.net/omnilink/omnilink-base/types"
	x2eTy "code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/x2ethereum/types"
)

/*
 * 执行器相关定义
 * 重载基类相关接口
 */

var (
	//日志
	elog = log.New("module", "x2ethereum.executor")
)

var driverName = x2eTy.X2ethereumX

// Init register dapp
func Init(name string, cfg *types.OmnilinkConfig, sub []byte) {
	drivers.Register(cfg, GetName(), newX2ethereum, cfg.GetDappFork(driverName, "Enable"))
	InitExecType()

}

// InitExecType Init Exec Type
func InitExecType() {
	ety := types.LoadExecutorType(driverName)
	ety.InitFuncList(types.ListMethod(&x2ethereum{}))
}

type x2ethereum struct {
	drivers.DriverBase
}

func newX2ethereum() drivers.Driver {
	t := &x2ethereum{}
	t.SetChild(t)
	t.SetExecutorType(types.LoadExecutorType(driverName))
	return t
}

// GetName get driver name
func GetName() string {
	return newX2ethereum().GetName()
}

func (x *x2ethereum) GetDriverName() string {
	return driverName
}

// CheckTx 实现自定义检验交易接口，供框架调用
// todo
// 实现
func (x *x2ethereum) CheckTx(tx *types.Transaction, index int) error {
	//var action x2ethereumtypes.X2EthereumAction
	//err := types.Decode(tx.Payload, &action)
	//if action.Ty
	return nil
}
