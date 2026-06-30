package types

import (
	"code.corp.bcollie.net/omnilink/omnilink-base/pluginmgr"
	"code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/rollup/commands"
	"code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/rollup/executor"
	"code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/rollup/rpc"
	rolluptypes "code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/rollup/types"
)

/*
 * 初始化dapp相关的组件
 */

func init() {
	pluginmgr.Register(&pluginmgr.PluginBase{
		Name:     rolluptypes.RollupX,
		ExecName: executor.GetName(),
		Exec:     executor.Init,
		Cmd:      commands.Cmd,
		RPC:      rpc.Init,
	})
}
