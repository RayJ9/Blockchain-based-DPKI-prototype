// Copyright Fuzamei Corp. 2018 All Rights Reserved.
// Use of this source code is governed by a BSD-style
// license that can be found in the LICENSE file.

package trade

import (
	"code.corp.bcollie.net/omnilink/omnilink-base/pluginmgr"
	_ "code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/trade/autotest" // register autotest package
	"code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/trade/commands"
	"code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/trade/executor"
	"code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/trade/rpc"
	"code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/trade/types"
)

func init() {
	pluginmgr.Register(&pluginmgr.PluginBase{
		Name:     types.TradeX,
		ExecName: executor.GetName(),
		Exec:     executor.Init,
		Cmd:      commands.TradeCmd,
		RPC:      rpc.Init,
	})
}
