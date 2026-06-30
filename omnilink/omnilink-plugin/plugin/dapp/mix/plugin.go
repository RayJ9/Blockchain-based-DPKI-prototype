// Copyright Fuzamei Corp. 2018 All Rights Reserved.
// Use of this source code is governed by a BSD-style
// license that can be found in the LICENSE file.

package paracross

import (
	"code.corp.bcollie.net/omnilink/omnilink-base/pluginmgr"
	"code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/mix/commands"
	"code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/mix/executor"
	"code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/mix/rpc"
	"code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/mix/types"
	_ "code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/mix/wallet" // register wallet package
)

func init() {
	pluginmgr.Register(&pluginmgr.PluginBase{
		Name:     types.MixX,
		ExecName: executor.GetName(),
		Exec:     executor.Init,
		Cmd:      commands.MixCmd,
		RPC:      rpc.Init,
	})
}
