package types

import (
	"code.corp.bcollie.net/omnilink/omnilink-base/pluginmgr"
	"code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/storage/commands"
	"code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/storage/executor"
	"code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/storage/rpc"
	storagetypes "code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/storage/types"
)

/*
 * 初始化dapp相关的组件
 */

func init() {
	pluginmgr.Register(&pluginmgr.PluginBase{
		Name:     storagetypes.StorageX,
		ExecName: executor.GetName(),
		Exec:     executor.Init,
		Cmd:      commands.Cmd,
		RPC:      rpc.Init,
	})
}
