package js

import (
	"code.corp.bcollie.net/omnilink/omnilink-base/pluginmgr"
	"code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/js/executor"
	ptypes "code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/js/types"

	// init auto test
	_ "code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/js/autotest"
	"code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/js/command"
)

func init() {
	pluginmgr.Register(&pluginmgr.PluginBase{
		Name:     ptypes.JsX,
		ExecName: executor.GetName(),
		Exec:     executor.Init,
		Cmd:      command.JavaScriptCmd,
		RPC:      nil,
	})
}
