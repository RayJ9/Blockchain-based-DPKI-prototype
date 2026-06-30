package types

import (
	"code.corp.bcollie.net/omnilink/omnilink-base/pluginmgr"
	"code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/exchange/commands"
	"code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/exchange/executor"
	"code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/exchange/rpc"
	exchangetypes "code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/exchange/types"
)

/*
 * 初始化dapp相关的组件
 */

func init() {
	pluginmgr.Register(&pluginmgr.PluginBase{
		Name:     exchangetypes.ExchangeX,
		ExecName: executor.GetName(),
		Exec:     executor.Init,
		Cmd:      commands.Cmd,
		RPC:      rpc.Init,
	})
}
