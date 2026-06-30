package para

import (
	"code.corp.bcollie.net/omnilink/omnilink-base/queue"
	drivers "code.corp.bcollie.net/omnilink/omnilink-base/system/mempool"
	"code.corp.bcollie.net/omnilink/omnilink-base/types"
)

//--------------------------------------------------------------------------------
// Module Mempool

func init() {
	drivers.Reg("para", New)
}

//New 创建price cache 结构的 mempool
func New(cfg *types.Mempool, sub []byte) queue.Module {
	return NewMempool(cfg)
}
