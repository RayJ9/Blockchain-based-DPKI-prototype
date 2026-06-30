package multisig

import (
	"code.corp.bcollie.net/omnilink/omnilink-base/pluginmgr"
	_ "code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/multisig/autotest" //register auto test
	"code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/multisig/commands"
	"code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/multisig/executor"
	"code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/multisig/rpc"
	mty "code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/multisig/types"
	_ "code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/multisig/wallet" // register wallet package
)

func init() {
	pluginmgr.Register(&pluginmgr.PluginBase{
		Name:     mty.MultiSigX,
		ExecName: executor.GetName(),
		Exec:     executor.Init,
		Cmd:      commands.MultiSigCmd,
		RPC:      rpc.Init,
	})
}
