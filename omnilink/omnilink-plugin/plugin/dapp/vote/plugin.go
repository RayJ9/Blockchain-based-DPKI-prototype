package types

import (
	"code.corp.bcollie.net/omnilink/omnilink-base/pluginmgr"
	"code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/vote/commands"
	"code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/vote/executor"
	"code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/vote/rpc"
	votetypes "code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/vote/types"
)

/*
 * 初始化dapp相关的组件
 */

func init() {
	pluginmgr.Register(&pluginmgr.PluginBase{
		Name:     votetypes.VoteX,
		ExecName: executor.GetName(),
		Exec:     executor.Init,
		Cmd:      commands.Cmd,
		RPC:      rpc.Init,
	})
}
