// Copyright Fuzamei Corp. 2018 All Rights Reserved.
// Use of this source code is governed by a BSD-style
// license that can be found in the LICENSE file.

package relay

import (
	"code.corp.bcollie.net/omnilink/omnilink-base/pluginmgr"
	"code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/relay/commands"
	"code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/relay/executor"
	"code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/relay/rpc"
	"code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/relay/types"
)

func init() {
	pluginmgr.Register(&pluginmgr.PluginBase{
		Name:     types.RelayX,
		ExecName: executor.GetName(),
		Exec:     executor.Init,
		Cmd:      commands.RelayCmd,
		RPC:      rpc.Init,
	})
}
