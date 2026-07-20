package types

import (
	"code.corp.bcollie.net/omnilink/omnilink-base/pluginmgr"
	"code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/accountmanager/commands"
	"code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/accountmanager/executor"
	"code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/accountmanager/rpc"
	accountmanagertypes "code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/accountmanager/types"
)

/*
 * 初始化dapp相关的组件
 */

func init() {
	pluginmgr.Register(&pluginmgr.PluginBase{
		Name:     accountmanagertypes.AccountmanagerX,
		ExecName: executor.GetName(),
		Exec:     executor.Init,
		Cmd:      commands.Cmd,
		RPC:      rpc.Init,
	})
}
