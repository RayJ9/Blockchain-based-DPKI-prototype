package mempool

import (
	"code.corp.bcollie.net/omnilink/omnilink-base/queue"
	"code.corp.bcollie.net/omnilink/omnilink-base/system/mempool"
	"code.corp.bcollie.net/omnilink/omnilink-base/types"
)

// New new mempool queue module
func New(cfg *types.OmnilinkConfig) queue.Module {
	mcfg := cfg.GetModuleConfig().Mempool
	sub := cfg.GetSubConfig().Mempool
	con, err := mempool.Load(mcfg.Name)
	if err != nil {
		panic("Unsupported mempool type:" + mcfg.Name + " " + err.Error())
	}
	subcfg, ok := sub[mcfg.Name]
	if !ok {
		subcfg = nil
	}
	obj := con(mcfg, subcfg)
	return obj
}
