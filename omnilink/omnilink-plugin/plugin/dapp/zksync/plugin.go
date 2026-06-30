package wasm

import (
	"code.corp.bcollie.net/omnilink/omnilink-base/pluginmgr"
	"code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/zksync/commands"
	"code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/zksync/executor"
	"code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/zksync/rpc"
	"code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/zksync/types"
)

func init() {
	pluginmgr.Register(&pluginmgr.PluginBase{
		Name:     types.Zksync,
		ExecName: executor.GetName(),
		Exec:     executor.Init,
		Cmd:      commands.ZksyncCmd,
		RPC:      rpc.Init,
	})
}
