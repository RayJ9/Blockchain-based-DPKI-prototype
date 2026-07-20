// Copyright Fuzamei Corp. 2018 All Rights Reserved.
// Use of this source code is governed by a BSD-style
// license that can be found in the LICENSE file.

package ticket

import (
	"code.corp.bcollie.net/omnilink/omnilink-base/pluginmgr"
	"code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/ticket/commands"
	"code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/ticket/executor"
	"code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/ticket/rpc"
	"code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/ticket/types"

	// init wallet
	_ "code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/ticket/wallet"
)

func init() {
	pluginmgr.Register(&pluginmgr.PluginBase{
		Name:     types.TicketX,
		ExecName: executor.GetName(),
		Exec:     executor.Init,
		Cmd:      commands.TicketCmd,
		RPC:      rpc.Init,
	})
}
