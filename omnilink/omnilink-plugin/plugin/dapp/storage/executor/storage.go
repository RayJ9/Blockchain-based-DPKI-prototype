package executor

import (
	log "code.corp.bcollie.net/omnilink/omnilink-base/common/log/log15"
	drivers "code.corp.bcollie.net/omnilink/omnilink-base/system/dapp"
	"code.corp.bcollie.net/omnilink/omnilink-base/types"
	storagetypes "code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/storage/types"
)

/*
 * 执行器相关定义
 * 重载基类相关接口
 */

var (
	//日志
	elog = log.New("module", "storage.executor")
)

var driverName = storagetypes.StorageX

// Init register dapp
func Init(name string, cfg *types.OmnilinkConfig, sub []byte) {
	drivers.Register(cfg, GetName(), newStorage, cfg.GetDappFork(driverName, "Enable"))
	InitExecType()
}

// InitExecType Init Exec Type
func InitExecType() {
	ety := types.LoadExecutorType(driverName)
	ety.InitFuncList(types.ListMethod(&storage{}))
}

type storage struct {
	drivers.DriverBase
}

func newStorage() drivers.Driver {
	t := &storage{}
	t.SetChild(t)
	t.SetExecutorType(types.LoadExecutorType(driverName))
	return t
}

// GetName get driver name
func GetName() string {
	return newStorage().GetName()
}

func (s *storage) GetDriverName() string {
	return driverName
}

//ExecutorOrder Exec 的时候 同时执行 ExecLocal
func (s *storage) ExecutorOrder() int64 {
	cfg := s.GetAPI().GetConfig()
	if cfg.IsDappFork(s.GetHeight(), storagetypes.StorageX, storagetypes.ForkStorageLocalDB) {
		return drivers.ExecLocalSameTime
	}
	return s.DriverBase.ExecutorOrder()
}

// CheckTx 实现自定义检验交易接口，供框架调用
func (s *storage) CheckTx(tx *types.Transaction, index int) error {
	// implement code
	return nil
}
