package wasm

import (
	"code.corp.bcollie.net/omnilink/omnilink-base/pluginmgr"
	"code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/wasm/commands"
	"code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/wasm/executor"
	"code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/wasm/rpc"
	"code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/wasm/types"
)

func init() {
	pluginmgr.Register(&pluginmgr.PluginBase{
		Name:     types.WasmX,
		ExecName: executor.GetName(),
		Exec:     executor.Init,
		Cmd:      commands.Cmd,
		RPC:      rpc.Init,
	})
}
