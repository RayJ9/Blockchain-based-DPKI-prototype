package types

import (
	"code.corp.bcollie.net/omnilink/omnilink-base/pluginmgr"
	"code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/evmxgo/commands"
	"code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/evmxgo/executor"
	"code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/evmxgo/rpc"
	evmxgotypes "code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/evmxgo/types"
)

/*
 * 初始化dapp相关的组件
 */

func init() {
	pluginmgr.Register(&pluginmgr.PluginBase{
		Name:     evmxgotypes.EvmxgoX,
		ExecName: executor.GetName(),
		Exec:     executor.Init,
		Cmd:      commands.Cmd,
		RPC:      rpc.Init,
	})
}
